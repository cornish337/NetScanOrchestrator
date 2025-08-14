from typing import List, Optional, Dict, Any
import asyncio
import time
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Nmap Parallel Scanner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChunkStatus(str):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED_SLOW = "killed-slow"

class Chunk(BaseModel):
    id: str
    targets: List[str]
    status: str = ChunkStatus.QUEUED
    created_at: float = Field(default_factory=lambda: time.time())
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress_completed: int = 0
    progress_total: int = 0
    last_heartbeat: float = Field(default_factory=lambda: time.time())
    parent_id: Optional[str] = None
    attempt: int = 0

class Settings(BaseModel):
    max_workers: int = 4
    host_timeout_sec: int = 60
    chunk_timeout_sec: int = 600
    profile: str = "balanced"

class Coverage(BaseModel):
    total: int
    completed: int
    failed: int
    pending: int
    killed: int

STATE: Dict[str, Any] = {
    "settings": Settings().dict(),
    "chunks": {},
    "scanned_ok": set(),
    "failed": set(),
    "pending": set(),
    "quarantined": set(),
}

def new_chunk(targets: List[str], parent_id: Optional[str] = None, attempt: int = 0) -> Chunk:
    cid = str(uuid.uuid4())
    c = Chunk(
        id=cid,
        targets=targets,
        status=ChunkStatus.QUEUED,
        progress_total=len(targets),
        parent_id=parent_id,
        attempt=attempt,
    )
    STATE["chunks"][cid] = c
    return c

if not STATE["chunks"]:
    for _ in range(3):
        new_chunk([f"10.0.0.{i}" for i in range(1, 33)])

class EventBroker:
    def __init__(self):
        self.queues: List[asyncio.Queue] = []
        self.lock = asyncio.Lock()

    async def connect(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        async with self.lock:
            self.queues.append(q)
        return q

    async def disconnect(self, q: asyncio.Queue):
        async with self.lock:
            if q in self.queues:
                self.queues.remove(q)

    async def publish(self, event: Dict[str, Any]):
        async with self.lock:
            for q in list(self.queues):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    pass

broker = EventBroker()

async def emit(event_type: str, **payload):
    await broker.publish({"type": event_type, "ts": time.time(), **payload})

RUNNER_TASK: Optional[asyncio.Task] = None
RUNNER_STOP = asyncio.Event()

async def runner_loop():
    while not RUNNER_STOP.is_set():
        running = [c for c in STATE["chunks"].values() if c.status == ChunkStatus.RUNNING]
        queued = [c for c in STATE["chunks"].values() if c.status == ChunkStatus.QUEUED]
        cap = STATE["settings"]["max_workers"] - len(running)
        for c in queued[:max(0, cap)]:
            c.status = ChunkStatus.RUNNING
            c.started_at = time.time()
            await emit("chunk_started", chunk_id=c.id)

        for c in [c for c in STATE["chunks"].values() if c.status == ChunkStatus.RUNNING]:
            if c.progress_completed < c.progress_total:
                step = min(5, c.progress_total - c.progress_completed)
                c.progress_completed += step
                c.last_heartbeat = time.time()
                await emit(
                    "chunk_progress",
                    chunk_id=c.id,
                    completed_hosts=c.progress_completed,
                    total_hosts=c.progress_total,
                    elapsed_ms=int((time.time() - (c.started_at or c.created_at)) * 1000),
                    last_heartbeat_ms=0,
                )
            if c.progress_completed >= c.progress_total:
                c.status = ChunkStatus.COMPLETED
                c.completed_at = time.time()
                for ip in c.targets:
                    STATE["scanned_ok"].add(ip)
                    STATE["pending"].discard(ip)
                await emit("chunk_completed", chunk_id=c.id, duration_ms=int((c.completed_at - (c.started_at or c.created_at)) * 1000))

        await asyncio.sleep(1.0)

@app.on_event("startup")
async def on_startup():
    for c in STATE["chunks"].values():
        for ip in c.targets:
            STATE["pending"].add(ip)
    global RUNNER_TASK
    RUNNER_TASK = asyncio.create_task(runner_loop())

@app.on_event("shutdown")
async def on_shutdown():
    RUNNER_STOP.set()
    if RUNNER_TASK:
        await asyncio.wait([RUNNER_TASK], timeout=2)

@app.post("/targets/import")
async def import_targets(file: UploadFile = File(...), chunk_size: int = Form(256)):
    data = (await file.read()).decode("utf-8", errors="ignore").splitlines()
    targets = [t.strip() for t in data if t.strip()]
    if not targets:
        raise HTTPException(400, "No targets provided")
    created = []
    for i in range(0, len(targets), chunk_size):
        c = new_chunk(targets[i:i+chunk_size])
        for ip in c.targets:
            STATE["pending"].add(ip)
        created.append(c.id)
        await emit("chunk_created", chunk_id=c.id, total_hosts=c.progress_total)
    return {"created": created, "count": len(created)}

@app.get("/chunks")
async def list_chunks(status: Optional[str] = None, limit: int = 100, offset: int = 0):
    items = list(STATE["chunks"].values())
    if status:
        items = [c for c in items if c.status == status]
    total = len(items)
    items = items[offset:offset+limit]
    return {"total": total, "items": [c.dict() for c in items]}

@app.get("/chunks/{chunk_id}")
async def get_chunk(chunk_id: str):
    c = STATE["chunks"].get(chunk_id)
    if not c:
        raise HTTPException(404, "Chunk not found")
    return c

@app.post("/chunks/{chunk_id}/kill")
async def kill_chunk(chunk_id: str):
    c = STATE["chunks"].get(chunk_id)
    if not c:
        raise HTTPException(404, "Chunk not found")
    if c.status not in [ChunkStatus.RUNNING, ChunkStatus.QUEUED]:
        raise HTTPException(400, "Chunk not running/queued")
    c.status = ChunkStatus.KILLED_SLOW
    c.completed_at = time.time()
    await emit("chunk_killed", chunk_id=c.id, reason="user", elapsed_ms=int((c.completed_at - (c.started_at or c.created_at)) * 1000))
    return {"ok": True}

class SplitBody(BaseModel):
    strategy: str = "binary"
    parts: Optional[int] = None
    ranges: Optional[List[List[int]]] = None

@app.post("/chunks/{chunk_id}/split")
async def split_chunk(chunk_id: str, body: SplitBody):
    c = STATE["chunks"].get(chunk_id)
    if not c:
        raise HTTPException(404, "Chunk not found")
    n = body.parts or 2
    targets = c.targets
    size = max(1, len(targets) // n)
    kids = []
    for i in range(0, len(targets), size):
        child = new_chunk(targets[i:i+size], parent_id=c.id, attempt=c.attempt+1)
        for ip in child.targets:
            STATE["pending"].add(ip)
        kids.append(child.id)
        await emit("chunk_created", chunk_id=child.id, parent_id=c.id, total_hosts=child.progress_total, strategy=body.strategy)
    c.status = ChunkStatus.KILLED_SLOW
    c.completed_at = time.time()
    await emit("chunk_split", chunk_id=c.id, children=kids, strategy=body.strategy)
    return {"children": kids}

@app.post("/chunks/{chunk_id}/requeue")
async def requeue_chunk(chunk_id: str):
    c = STATE["chunks"].get(chunk_id)
    if not c:
        raise HTTPException(404, "Chunk not found")
    if c.status == ChunkStatus.RUNNING:
        raise HTTPException(400, "Already running")
    c.status = ChunkStatus.QUEUED
    c.started_at = None
    c.completed_at = None
    c.attempt += 1
    await emit("chunk_requeued", chunk_id=c.id)
    return {"ok": True}

@app.patch("/settings")
async def update_settings(s: Settings):
    STATE["settings"].update(s.dict())
    await emit("settings_updated", **STATE["settings"])
    return STATE["settings"]

@app.get("/coverage")
async def coverage():
    completed = len(STATE["scanned_ok"])
    failed = len(STATE["failed"])
    pending = len(STATE["pending"])
    killed = len([c for c in STATE["chunks"].values() if c.status == ChunkStatus.KILLED_SLOW])
    total = completed + failed + pending
    return Coverage(total=total, completed=completed, failed=failed, pending=pending, killed=killed)

@app.get("/metrics")
async def metrics():
    running = len([c for c in STATE["chunks"].values() if c.status == ChunkStatus.RUNNING])
    queued = len([c for c in STATE["chunks"].values() if c.status == ChunkStatus.QUEUED])
    return {"running": running, "queued": queued, "chunks": len(STATE["chunks"])}

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    q = await broker.connect()
    try:
        await ws.send_json({"type": "hello", "ts": time.time()})
        while True:
            event = await q.get()
            await ws.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await broker.disconnect(q)
