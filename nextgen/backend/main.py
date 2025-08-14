from typing import List, Optional, Dict, Any
import os
import asyncio
import time
import uuid
import json # Add json import
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from nmap_runner import NmapRunner
from xml_parser import parse_nmap_xml

STATE_DIR = os.environ.get("STATE_DIR", "/app/data")
SCANS_DIR = os.path.join(STATE_DIR, "scans")

app = FastAPI(title="Nmap Parallel Scanner API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
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
    max_workers: int = 2
    per_host_workers: int = 8
    host_timeout_sec: int = 60
    chunk_timeout_sec: int = 1800
    profile: str = "balanced"      # fast|balanced|thorough
    scan_type: str = "sT"          # sS requires NET_RAW; sT is safe
    ports: str = "top-1000"        # "top-1000" or "1-1024,3389"
    extra_args: str = ""           # optional raw args

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

# Event broker
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

# Runner and scheduler
RUNNER = NmapRunner(state_dir=STATE_DIR, event_cb=lambda t, p: emit(t, **p))
CHUNK_TASKS: Dict[str, asyncio.Task] = {}
RUNNER_STOP = asyncio.Event()

async def run_chunk_task(c: Chunk):
    # Execute per-host scanning, update progress, mark results
    try:
        await emit("chunk_started", chunk_id=c.id)
        c.started_at = time.time()
        c.status = ChunkStatus.RUNNING
        result = await RUNNER.scan_chunk(c.id, c.targets, STATE["settings"])
        # Mark host-level outcomes
        for ip in c.targets:
            if ip in result["failed"]:
                STATE["failed"].add(ip)
                STATE["pending"].discard(ip)
            else:
                STATE["scanned_ok"].add(ip)
                STATE["pending"].discard(ip)
        c.progress_completed = c.progress_total
        c.status = ChunkStatus.COMPLETED
        c.completed_at = time.time()
        await emit("chunk_completed", chunk_id=c.id, duration_ms=int((c.completed_at - (c.started_at or c.created_at)) * 1000))
    except asyncio.CancelledError:
        # Task was cancelled (likely via kill)
        c.status = ChunkStatus.KILLED_SLOW
        c.completed_at = time.time()
        await emit("chunk_killed", chunk_id=c.id, reason="cancelled", elapsed_ms=int((c.completed_at - (c.started_at or c.created_at)) * 1000))
        raise
    except Exception as ex:
        c.status = ChunkStatus.FAILED
        c.completed_at = time.time()
        await emit("chunk_failed", chunk_id=c.id, error=str(ex))
    finally:
        CHUNK_TASKS.pop(c.id, None)

async def scheduler_loop():
    while not RUNNER_STOP.is_set():
        settings = STATE["settings"]
        # Start queued up to max_workers
        running = [cid for cid, t in CHUNK_TASKS.items() if not t.done()]
        cap = settings["max_workers"] - len(running)
        if cap > 0:
            for c in [c for c in STATE["chunks"].values() if c.status == ChunkStatus.QUEUED][:cap]:
                # queue task
                t = asyncio.create_task(run_chunk_task(c))
                CHUNK_TASKS[c.id] = t
        await asyncio.sleep(0.5)

@app.on_event("startup")
async def on_startup():
    # Seed demo targets if empty
    if not STATE["chunks"]:
        for _ in range(2):
            new_chunk([f"10.0.0.{i}" for i in range(1, 17)])
    for c in STATE["chunks"].values():
        for ip in c.targets:
            STATE["pending"].add(ip)
    app.state.scheduler = asyncio.create_task(scheduler_loop())

@app.on_event("shutdown")
async def on_shutdown():
    RUNNER_STOP.set()
    # Abort all running chunks
    for cid in list(CHUNK_TASKS.keys()):
        await RUNNER.abort_chunk(cid)
        CHUNK_TASKS[cid].cancel()
    # Wait briefly
    await asyncio.sleep(1.0)

# REST API
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

@app.get("/chunks/{chunk_id}/details")
async def get_chunk_details(chunk_id: str):
    chunk = STATE["chunks"].get(chunk_id)
    if not chunk:
        raise HTTPException(404, "Chunk not found")

    hosts = []
    scan_dir = os.path.join(SCANS_DIR, chunk_id)
    for ip in chunk.targets:
        result_path = os.path.join(scan_dir, f"{ip}.xml")
        hosts.append({
            "ip": ip,
            "has_result": os.path.exists(result_path) and os.path.getsize(result_path) > 0
        })
    return {"id": chunk_id, "targets": hosts}


@app.get("/results/{chunk_id}/{ip}")
async def get_scan_result(chunk_id: str, ip: str):
    chunk = STATE["chunks"].get(chunk_id)
    if not chunk:
        raise HTTPException(404, "Chunk not found")
    if ip not in chunk.targets:
        raise HTTPException(400, "IP not in this chunk")

    result_path = os.path.join(SCANS_DIR, chunk_id, f"{ip}.xml")
    if not os.path.exists(result_path):
        raise HTTPException(404, "Scan result not found for this IP.")

    try:
        with open(result_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        if not xml_content.strip():
             return {"status": {"state": "down", "reason": "no-response"}}

        return parse_nmap_xml(xml_content)
    except Exception as e:
        raise HTTPException(500, f"Failed to read or parse scan result: {e}")

@app.post("/chunks/{chunk_id}/kill")
async def kill_chunk(chunk_id: str):
    c = STATE["chunks"].get(chunk_id)
    if not c:
        raise HTTPException(404, "Chunk not found")
    # Signal abort and cancel task if running
    await RUNNER.abort_chunk(chunk_id)
    t = CHUNK_TASKS.get(chunk_id)
    if t and not t.done():
        t.cancel()
    c.status = ChunkStatus.KILLED_SLOW
    c.completed_at = time.time()
    await emit("chunk_killed", chunk_id=c.id, reason="user", elapsed_ms=int((c.completed_at - (c.started_at or c.created_at)) * 1000))
    return {"ok": True}

class SplitBody(BaseModel):
    strategy: str = "binary"
    parts: Optional[int] = None

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
    # Mark parent as killed (stop if running)
    await RUNNER.abort_chunk(chunk_id)
    t = CHUNK_TASKS.get(chunk_id)
    if t and not t.done():
        t.cancel()
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

@app.get("/health")
async def health():
    return {"ok": True, "nmap_path": "nmap", "state_dir": STATE_DIR}

@app.get("/export")
async def export_results(format: str = "json"):
    if format.lower() != "json":
        raise HTTPException(400, "Unsupported format. Only JSON is currently supported.")

    consolidated_report = {
        "scan_started": None, # Placeholder
        "scan_finished": None, # Placeholder
        "hosts": {}
    }

    if not os.path.exists(SCANS_DIR):
        return consolidated_report

    all_files = []
    for chunk_id in os.listdir(SCANS_DIR):
        chunk_dir = os.path.join(SCANS_DIR, chunk_id)
        if os.path.isdir(chunk_dir):
            for filename in os.listdir(chunk_dir):
                if filename.endswith(".xml"):
                    all_files.append(os.path.join(chunk_dir, filename))

    if not all_files:
        return consolidated_report

    # Find earliest and latest scan times from chunk data for placeholders
    if STATE["chunks"]:
        start_times = [c.created_at for c in STATE["chunks"].values() if c.created_at]
        end_times = [c.completed_at for c in STATE["chunks"].values() if c.completed_at]
        if start_times:
            consolidated_report["scan_started"] = min(start_times)
        if end_times:
            consolidated_report["scan_finished"] = max(end_times)


    for filepath in all_files:
        try:
            ip = os.path.basename(filepath).replace(".xml", "")
            with open(filepath, "r", encoding="utf-8") as f:
                xml_content = f.read()

            if not xml_content.strip():
                scan_data = {"status": {"state": "down", "reason": "no-response"}}
            else:
                scan_data = parse_nmap_xml(xml_content)

            if "error" not in scan_data:
                consolidated_report["hosts"][ip] = scan_data
        except Exception:
            # Ignore files that fail to parse, could log this
            pass

    return consolidated_report

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
