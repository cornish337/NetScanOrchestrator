"""Reporting utilities for summarising database state.

This module exposes convenience functions that inspect the SQLAlchemy
models and generate useful statistics.  It is intentionally lightweight
so it can be used both from the CLI and from tests.

The helpers mirror the export functionality found in
:mod:`src.results_handler` by providing simple JSON and CSV writers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import csv
import json

from sqlalchemy.orm import Session

from db.models import ScanRun, Batch, Job


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _job_duration(job: Job) -> Optional[float]:
    """Return the job duration in seconds if timestamps are available."""

    if job.started_at and job.completed_at:
        return (job.completed_at - job.started_at).total_seconds()
    return None


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_slowest_jobs(session: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """Return the ``limit`` slowest jobs sorted by duration."""

    jobs = session.query(Job).all()
    jobs_with_durations = [j for j in jobs if _job_duration(j) is not None]
    jobs_with_durations.sort(key=lambda j: _job_duration(j), reverse=True)

    rows: List[Dict[str, Any]] = []
    for job in jobs_with_durations[:limit]:
        rows.append(
            {
                "job_id": job.id,
                "scan_run_id": job.scan_run_id,
                "target": job.target.address if job.target else None,
                "duration": _job_duration(job),
                "status": job.status,
            }
        )
    return rows


def get_failed_jobs(session: Session) -> List[Dict[str, Any]]:
    """Return jobs that are not completed successfully along with errors."""

    jobs = session.query(Job).all()
    failed: List[Dict[str, Any]] = []
    for job in jobs:
        # A job is failed if its status is not 'completed' or if any associated
        # result contains an error message.  We inspect ``results`` relationship
        # in Python to avoid complex SQL for this educational project.
        error: Optional[str] = None
        for res in job.results:
            if res.stderr:
                error = res.stderr
                break
        if job.status != "completed" or error:
            failed.append(
                {
                    "job_id": job.id,
                    "scan_run_id": job.scan_run_id,
                    "target": job.target.address if job.target else None,
                    "status": job.status,
                    "error": error,
                }
            )
    return failed


def summarise_runs(session: Session) -> List[Dict[str, Any]]:
    """Return a summary per :class:`~src.db.models.ScanRun`."""

    rows: List[Dict[str, Any]] = []
    for run in session.query(ScanRun).all():
        total_jobs = len(run.jobs)
        completed = sum(1 for j in run.jobs if j.status == "completed")
        failed = total_jobs - completed
        rows.append(
            {
                "scan_run_id": run.id,
                "total_jobs": total_jobs,
                "completed_jobs": completed,
                "failed_jobs": failed,
            }
        )
    return rows


def summarise_batches(session: Session) -> List[Dict[str, Any]]:
    """Return a summary per :class:`~src.db.models.Batch`."""

    rows: List[Dict[str, Any]] = []
    for batch in session.query(Batch).all():
        job_count = sum(len(t.jobs) for t in batch.targets)
        rows.append(
            {
                "batch_id": batch.id,
                "name": batch.name,
                "target_count": len(batch.targets),
                "job_count": job_count,
            }
        )
    return rows


def summarise_jobs(session: Session) -> List[Dict[str, Any]]:
    """Return a list of individual job records."""

    rows: List[Dict[str, Any]] = []
    for job in session.query(Job).all():
        duration = _job_duration(job)
        error = None
        for res in job.results:
            if res.error:
                error = res.error
                break
        rows.append(
            {
                "job_id": job.id,
                "scan_run_id": job.scan_run_id,
                "target": job.target.address if job.target else None,
                "status": job.status,
                "duration": duration,
                "error": error,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def export_json(data: Any, output_filepath: str) -> None:
    """Write ``data`` to ``output_filepath`` in JSON format."""

    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def export_csv(rows: List[Dict[str, Any]], output_filepath: str) -> None:
    """Write list of dictionaries to ``output_filepath`` as CSV."""

    if not rows:
        # Create an empty file with no headers
        open(output_filepath, "w").close()
        return

    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with open(output_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


__all__ = [
    "get_slowest_jobs",
    "get_failed_jobs",
    "summarise_runs",
    "summarise_batches",
    "summarise_jobs",
    "export_json",
    "export_csv",
]
