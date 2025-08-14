import asyncio
from dataclasses import dataclass
from subprocess import PIPE
from typing import List, Dict, Optional


@dataclass
class RunnerJob:
    """Specification for a job to be executed by the runner."""

    job_id: int
    address: str
    command: Optional[List[str]] = None


async def _execute(job: RunnerJob, timeout_sec: int) -> Dict:
    """Run a single job returning its execution details."""
    cmd = job.command or ["echo", job.address]
    result: Dict = {
        "job_id": job.job_id,
        "address": job.address,
        "status": "running",
    }
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=PIPE, stderr=PIPE
        )
        result["pid"] = proc.pid
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_sec
            )
            result["stdout"] = stdout.decode()
            result["stderr"] = stderr.decode()
            if proc.returncode == 0:
                result["status"] = "completed"
            elif proc.returncode < 0:
                result["status"] = "killed"
            else:
                result["status"] = "failed"
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            result.update({"stdout": "", "stderr": "", "status": "timeout"})
    except Exception as exc:  # pragma: no cover - unexpected runtime issues
        result.update({"stdout": "", "stderr": str(exc), "status": "failed"})
    return result


async def run_jobs(
    jobs: List[RunnerJob], timeout_sec: int = 30, concurrency: int = 4
) -> List[Dict]:
    """Run multiple jobs concurrently with a limit on concurrency."""
    semaphore = asyncio.Semaphore(concurrency)

    async def _runner(job: RunnerJob) -> Dict:
        async with semaphore:
            return await _execute(job, timeout_sec)

    tasks = [asyncio.create_task(_runner(job)) for job in jobs]
    return [await t for t in tasks]
