import asyncio
import json
import os
import tempfile
from datetime import datetime
from subprocess import PIPE
from typing import List, Optional, Any, Dict

import nmap
from sqlalchemy.orm import Session

from db import repository as db_repo
from db.models import Job, JobStatus


def _create_ws_message(msg_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a dictionary formatted for WebSocket messages."""
    return {"type": msg_type, "payload": payload}


def _parse_nmap_xml_from_string(xml_string: str) -> Dict[str, Any]:
    """Parses nmap XML output from a string into a dictionary using a temporary file."""
    tmp_path = None
    try:
        # Use a temporary file to leverage python-nmap's file-based parsing
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".xml") as tmp:
            tmp.write(xml_string)
            tmp_path = tmp.name

        scanner = nmap.PortScanner()
        scan_data = scanner.analyse_nmap_xml_scan(nmap_output_file=tmp_path)
        # We are interested in the 'scan' dictionary which contains host details
        return scan_data.get('scan', {})
    except Exception:
        # Return an empty dict if any parsing error occurs
        return {}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


async def _send_chunk_update(
    queue: asyncio.Queue, job: Job, status: JobStatus, summary: Optional[Dict[str, Any]] = None
):
    """Constructs and sends a CHUNK_UPDATE message to the queue."""
    if not queue:
        return

    api_status = status.name.upper()

    # Create a minimal result payload from the summary if available
    minimal_result = {}
    if summary and job.target:
        host_data = summary.get(job.target.address, {})
        if host_data:
             minimal_result = {
                "address": job.target.address,
                "status": host_data.get("status", {}).get("state", "unknown"),
                "reason": host_data.get("status", {}).get("reason", "N/A"),
            }

    payload = {
        "chunk_id": str(job.id),
        "status": api_status,
        "result": minimal_result,
    }
    await queue.put(_create_ws_message("CHUNK_UPDATE", payload))


async def execute_job(
    job_id: int,
    db_session: Session,
    timeout_sec: int,
    update_queue: Optional[asyncio.Queue] = None,
):
    """
    Fetches a job from the database, executes nmap, saves the full result summary,
    and sends real-time updates.
    """
    job = db_repo.get_job(db_session, job_id)
    if not job or not job.target:
        return

    base_command = ["nmap", "-oX", "-", "-T4"]
    nmap_flags = job.nmap_options or (job.scan_run.options if job.scan_run else None)
    if nmap_flags:
        base_command.extend(nmap_flags.split())
    command = base_command + [job.target.address]

    proc = None
    final_status = JobStatus.FAILED
    summary_dict = None

    try:
        proc = await asyncio.create_subprocess_exec(*command, stdout=PIPE, stderr=PIPE)

        db_repo.update_job(
            db_session, job_id=job.id, pid=proc.pid, status=JobStatus.RUNNING, started_at=datetime.utcnow()
        )
        await _send_chunk_update(update_queue, job, JobStatus.RUNNING)

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
        stdout_str = stdout.decode(errors="ignore")
        stderr_str = stderr.decode(errors="ignore")

        final_status = JobStatus.COMPLETED if proc.returncode == 0 else JobStatus.FAILED

        summary_json_str = None
        if stdout_str and final_status == JobStatus.COMPLETED:
            summary_dict = _parse_nmap_xml_from_string(stdout_str)
            if summary_dict:
                summary_json_str = json.dumps(summary_dict)

        db_repo.update_job(
            db_session,
            job_id=job.id,
            exit_code=proc.returncode,
            status=final_status,
            reason="completed" if final_status == JobStatus.COMPLETED else "nmap_error",
            completed_at=datetime.utcnow(),
        )
        db_repo.create_result(
            db_session, job_id=job.id, stdout=stdout_str, stderr=stderr_str, summary_json=summary_json_str
        )

    except asyncio.TimeoutError:
        if proc: proc.kill(); await proc.wait()
        final_status = JobStatus.FAILED
        db_repo.update_job(db_session, job_id=job.id, status=final_status, reason="timeout", completed_at=datetime.utcnow())
    except Exception as e:
        final_status = JobStatus.FAILED
        db_repo.update_job(db_session, job_id=job.id, status=final_status, reason=f"runner_exception: {str(e)}", completed_at=datetime.utcnow())
    finally:
        final_job_state = db_repo.get_job(db_session, job_id)
        if final_job_state:
            await _send_chunk_update(update_queue, final_job_state, final_status, summary_dict)


async def run_jobs_concurrently(
    scan_run_id: int,
    job_ids: List[int],
    db_session: Session,
    concurrency: int,
    timeout_sec: int,
    update_queue: Optional[asyncio.Queue] = None,
):
    """Runs jobs with concurrency, sends updates, and a final completion message."""
    semaphore = asyncio.Semaphore(concurrency)
    scan_run = db_repo.get_scan_run(db_session, scan_run_id)
    if not scan_run: return

    db_repo.update_scan_run(db_session, scan_run_id, status=JobStatus.RUNNING)

    async def run_with_semaphore(job_id: int):
        async with semaphore:
            await execute_job(job_id, db_session, timeout_sec, update_queue)

    tasks = [run_with_semaphore(job_id) for job_id in job_ids]
    await asyncio.gather(*tasks)

    if update_queue:
        all_jobs = db_repo.list_jobs_for_scan_run(db_session, scan_run_id)
        final_scan_status = JobStatus.COMPLETED
        if any(j.status == JobStatus.FAILED for j in all_jobs):
            final_scan_status = JobStatus.FAILED

        db_repo.update_scan_run(db_session, scan_run_id, status=final_scan_status, completed_at=datetime.utcnow())

        payload = {
            "scan_id": str(scan_run_id),
            "status": final_scan_status.name.upper(),
            "final_results_url": f"/api/scans/{scan_run_id}",
        }
        await update_queue.put(_create_ws_message("SCAN_COMPLETE", payload))
        await update_queue.put(None)
