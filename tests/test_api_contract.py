import asyncio
import os
import sys
import json
from unittest.mock import patch, AsyncMock

import pytest
from async_asgi_testclient import TestClient as AsyncTestClient
from starlette import status
from starlette.websockets import WebSocketDisconnect

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from web_api.app import app
from web_api.deps import get_db

SAMPLE_TARGETS = ["127.0.0.1", "127.0.0.2", "127.0.0.3"]

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
@patch("web_api.app.scan_task_wrapper", new_callable=AsyncMock)
async def test_websocket_flow_and_api_parity(mock_scan_wrapper, test_db_session):
    test_finished_event = asyncio.Event()

    async def mock_bg_task(scan_run_id, job_ids, update_queue):
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        try:
            from src.db.models import JobStatus
            from src.db import repository as db_repo
            for i, job_id in enumerate(job_ids):
                target = SAMPLE_TARGETS[i]
                db_repo.update_job(db, job_id=job_id, status=JobStatus.RUNNING)
                await update_queue.put({"type": "CHUNK_UPDATE", "payload": {"chunk_id": str(job_id), "status": "RUNNING"}})
                await asyncio.sleep(0.01)
                status_val = JobStatus.COMPLETED if i % 2 == 0 else JobStatus.FAILED
                db_repo.update_job(db, job_id=job_id, status=status_val, reason="test")
                await update_queue.put({
                    "type": "CHUNK_UPDATE",
                    "payload": {"chunk_id": str(job_id), "status": status_val.name, "result": {"address": target, "status": "up" if status_val == JobStatus.COMPLETED else "down", "reason": "syn-ack"}},
                })
            db_repo.update_scan_run(db, scan_run_id, status=JobStatus.COMPLETED)
            await update_queue.put({
                "type": "SCAN_COMPLETE",
                "payload": {"scan_id": str(scan_run_id), "status": "COMPLETED", "final_results_url": f"/api/scans/{scan_run_id}"},
            })
            await update_queue.put(None)
        finally:
            db.close()
            await test_finished_event.wait()

    mock_scan_wrapper.side_effect = mock_bg_task

    async with AsyncTestClient(app) as client:
        response = await client.post("/api/scans", json={"targets": SAMPLE_TARGETS, "nmap_options": "-sT"})
        assert response.status_code == status.HTTP_202_ACCEPTED
        scan_id = response.json()["scan_id"]

        received_messages = []
        try:
            async with client.websocket_connect(f"/ws/scans/{scan_id}") as websocket:
                while True:
                    data = await websocket.receive_text()
                    received_messages.append(json.loads(data))
        except Exception:
            # This client library raises a generic Exception on disconnect.
            pass
        finally:
            test_finished_event.set()

        # Specific message count assertions
        running_updates = [msg for msg in received_messages if msg.get("type") == "CHUNK_UPDATE" and msg.get("payload", {}).get("status") == "RUNNING"]
        final_updates = [msg for msg in received_messages if msg.get("type") == "CHUNK_UPDATE" and msg.get("payload", {}).get("status") in ["COMPLETED", "FAILED"]]
        scan_complete_messages = [msg for msg in received_messages if msg["type"] == "SCAN_COMPLETE"]

        assert len(running_updates) == len(SAMPLE_TARGETS)
        assert len(final_updates) == len(SAMPLE_TARGETS)
        assert len(scan_complete_messages) == 1

        # Assert that SCAN_COMPLETE is the last message
        assert received_messages[-1]["type"] == "SCAN_COMPLETE"

        response = await client.get(f"/api/scans/{scan_id}")
        api_data = response.json()["data"]
        assert api_data["progress"]["completed_chunks"] == 2

@pytest.mark.anyio
async def test_websocket_rejects_nonexistent_scan(test_db_session):
    async with AsyncTestClient(app) as client:
        with pytest.raises(Exception) as excinfo:
            async with client.websocket_connect("/ws/scans/999999") as websocket:
                await websocket.receive_text()
        # The library raises a generic exception, but we can inspect the message inside it
        # It should contain the ASGI close event details
        assert excinfo.value.args[0]["type"] == "websocket.close"
        assert excinfo.value.args[0]["code"] == status.WS_1008_POLICY_VIOLATION


@pytest.mark.anyio
@patch("web_api.app.scan_manager.get_scan_queue", return_value=None)
async def test_websocket_rejects_completed_scan(mock_get_queue, test_db_session):
    async with AsyncTestClient(app) as client:
        with pytest.raises(Exception) as excinfo:
            async with client.websocket_connect("/ws/scans/1") as websocket:
                await websocket.receive_text()
        assert excinfo.value.args[0]["type"] == "websocket.close"
        assert excinfo.value.args[0]["code"] == status.WS_1008_POLICY_VIOLATION

@pytest.mark.anyio
async def test_cors_preflight_request(test_db_session):
    headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"}
    async with AsyncTestClient(app) as client:
        response = await client.options("/api/scans", headers=headers)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
