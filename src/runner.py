import asyncio
from datetime import datetime
from subprocess import PIPE
from typing import List

from .db.session import Session
from .db import repository as db_repo
from .db.models import Job, JobStatus


async def execute_job(job_id: int, db_session: Session, timeout_sec: int):
    """
    Fetches a job from the database and executes it using nmap.

    This function is designed to be the main execution unit for a single scan job.
    It handles the entire lifecycle of the job:
    1. Fetches the job and its associated target from the database.
    2. Constructs and executes the nmap command.
    3. Updates the job's PID and status to RUNNING in the database.
    4. Waits for the command to complete, handling timeouts.
    5. Records the results (stdout, stderr, exit code) and updates the job status.
    """
    job = db_repo.get_job(db_session, job_id)
    if not job or not job.target:
        # Job might have been deleted or is in an invalid state
        return

    # Base nmap command. -oX - sends XML output to stdout.
    # -T4 is an aggressive timing template, good for a baseline.
    base_command = ["nmap", "-oX", "-", "-T4"]

    # Add custom flags if they exist, otherwise use run-level options
    nmap_flags = job.nmap_options or (job.scan_run.options if job.scan_run else None)
    if nmap_flags:
        base_command.extend(nmap_flags.split())

    command = base_command + [job.target.address]

    proc = None
    try:
        # Start the nmap process
        proc = await asyncio.create_subprocess_exec(
            *command, stdout=PIPE, stderr=PIPE
        )

        # Immediately update the job with PID and running status
        db_repo.update_job(
            db_session,
            job_id=job.id,
            pid=proc.pid,
            status=JobStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        # Wait for the process to finish with a timeout
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)

        # Process completed successfully
        db_repo.update_job(
            db_session,
            job_id=job.id,
            exit_code=proc.returncode,
            status=JobStatus.COMPLETED if proc.returncode == 0 else JobStatus.FAILED,
            reason="completed" if proc.returncode == 0 else "nmap_error",
            completed_at=datetime.utcnow(),
        )
        db_repo.create_result(
            db_session,
            job_id=job.id,
            stdout=stdout.decode(errors='ignore'),
            stderr=stderr.decode(errors='ignore'),
        )

    except asyncio.TimeoutError:
        if proc:
            proc.kill()
            await proc.wait()  # Ensure the process is cleaned up
        db_repo.update_job(
            db_session,
            job_id=job.id,
            status=JobStatus.FAILED,
            reason="timeout",
            completed_at=datetime.utcnow(),
        )
    except Exception as e:
        # Catch other potential errors during process execution
        db_repo.update_job(
            db_session,
            job_id=job.id,
            status=JobStatus.FAILED,
            reason=f"runner_exception: {str(e)}",
            completed_at=datetime.utcnow(),
        )


async def run_jobs_concurrently(
    job_ids: List[int], db_session: Session, concurrency: int, timeout_sec: int
):
    """
    Runs a list of jobs by their IDs with a concurrency limit.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def run_with_semaphore(job_id: int):
        async with semaphore:
            await execute_job(job_id, db_session, timeout_sec)

    tasks = [run_with_semaphore(job_id) for job_id in job_ids]
    await asyncio.gather(*tasks)
