"""Main FastAPI application for the NetScanOrchestrator."""

import asyncio
import json
import os
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

# Adjust path to import from parent directories
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import models as db_models
from src.db import repository as db_repo
from src.db.session import get_session, init_engine
from src.ip_handler import expand_targets
from src.runner import run_jobs_concurrently
from web_api import deps, models
from web_ui.app import app as flask_app
from web_api.scan_manager import scan_manager

# --- FastAPI App Initialization ---

app = FastAPI(
    title="NetScanOrchestrator API",
    description="API for managing and monitoring network scans.",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Background Task Management ---

async def scan_task_wrapper(scan_run_id: int, job_ids: List[int], update_queue: asyncio.Queue):
    """A wrapper to manage the DB session for the background scan task."""
    db = get_session()
    try:
        concurrency = os.cpu_count() or 4
        timeout_sec = 600
        await run_jobs_concurrently(
            scan_run_id=scan_run_id,
            job_ids=job_ids,
            db_session=db,
            concurrency=concurrency,
            timeout_sec=timeout_sec,
            update_queue=update_queue,
        )
    finally:
        db.close()
        scan_manager.deregister_scan(str(scan_run_id))

# --- API Router Definition ---

router = APIRouter()

@router.post(
    "/api/scans",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=models.StartScanResponse,
    tags=["Scans"],
)
async def start_scan(
    scan_request: models.StartScanRequest, db: Session = Depends(deps.get_db)
):
    """Initiates a new network scan."""
    try:
        validated_targets = expand_targets(scan_request.targets, max_expand=4096)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid target specification: {e}")

    if not validated_targets:
        raise HTTPException(status_code=400, detail="No valid targets provided.")

    try:
        scan_run = db_repo.create_scan_run(
            db, status=db_models.JobStatus.PENDING, options=scan_request.nmap_options
        )
        db.commit()

        job_ids = []
        for target_address in validated_targets:
            target = db_repo.get_target_by_address(db, address=target_address)
            if not target:
                target = db_repo.create_target(db, address=target_address)
                db.commit()

            job = db_repo.create_job(
                db,
                scan_run_id=scan_run.id,
                target_id=target.id,
                status=db_models.JobStatus.PENDING,
                nmap_options=scan_request.nmap_options,
            )
            job_ids.append(job.id)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during scan setup: {e}")

    update_queue = asyncio.Queue()
    task = asyncio.create_task(scan_task_wrapper(scan_run.id, job_ids, update_queue))
    scan_manager.register_scan(str(scan_run.id), task, update_queue)

    return models.StartScanResponse(scan_id=str(scan_run.id))


@router.get(
    "/api/scans/{scan_id}",
    response_model=models.GetScanResponse,
    tags=["Scans"],
)
async def get_scan_status(scan_id: str, db: Session = Depends(deps.get_db)):
    """Retrieves the status, progress, and results of a scan."""
    try:
        run_id = int(scan_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scan_id format.")

    scan_run = db_repo.get_scan_run(db, run_id)
    if not scan_run:
        raise HTTPException(status_code=404, detail="Scan not found.")

    jobs = db_repo.list_jobs_for_scan_run(db, run_id)

    progress = models.ScanProgress(
        total_chunks=len(jobs),
        completed_chunks=sum(1 for j in jobs if j.status == db_models.JobStatus.COMPLETED),
        failed_chunks=sum(1 for j in jobs if j.status == db_models.JobStatus.FAILED),
    )

    hosts_results = {}
    for job in jobs:
        if job.results:
            latest_result = job.results[-1]
            if latest_result.summary_json:
                try:
                    summary = json.loads(latest_result.summary_json)
                    for ip, data in summary.items():
                        if not isinstance(data, dict): continue

                        hosts_results[ip] = models.HostResult(
                            status=data.get("status", {}).get("state", "unknown"),
                            ports=[int(p) for p in data.get("tcp", {}).keys()] + [int(p) for p in data.get("udp", {}).keys()],
                            reason=data.get("status", {}).get("reason", "N/A"),
                        )
                except (json.JSONDecodeError, KeyError):
                    continue

    return models.GetScanResponse(
        scan_id=scan_id,
        status=scan_run.status.name.upper(),
        progress=progress,
        results=models.ScanResults(hosts=hosts_results),
    )


@router.websocket("/ws/scans/{scan_id}")
async def websocket_endpoint(websocket: WebSocket, scan_id: str):
    """Provides real-time scan updates over a WebSocket connection."""
    await websocket.accept()
    queue = scan_manager.get_scan_queue(scan_id)

    if not queue:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Scan not found or not active")
        return

    try:
        while True:
            message = await queue.get()
            if message is None:
                break
            await websocket.send_json(message)
            queue.task_done()
    except WebSocketDisconnect:
        print(f"Client disconnected from scan {scan_id}")
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Server error")

# --- App Configuration ---

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Initialise the database engine on application startup."""
    init_engine()

@app.get("/healthz", tags=["Health"])
async def health_check():
    """A simple health check endpoint to confirm the API is running."""
    return JSONResponse(content={"status": "ok"})

# Mount the existing Flask app to handle legacy routes under /legacy
app.mount("/legacy", WSGIMiddleware(flask_app))
