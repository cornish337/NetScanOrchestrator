from pathlib import Path
from datetime import datetime
import asyncio

import typer

from sqlalchemy.orm import Session

from ..db.session import init_engine, get_session
from ..db import repository as db_repo
from ..db.models import JobStatus
from ..ip_handler import expand_targets
from ..runner import RunnerJob, run_jobs

app = typer.Typer(help="NetScan Orchestrator CLI")


@app.callback()
def main(
    ctx: typer.Context,
    db_path: Path = typer.Option(
        None,
        "--db-path",
        help="Path to SQLite state database",
        dir_okay=False,
    ),
):
    """Initialise the database engine and attach a session to context."""
    init_engine(str(db_path) if db_path else None)
    ctx.obj = get_session()


@app.command()
def ingest(
    ctx: typer.Context,
    input_file: Path,
    max_expand: int = typer.Option(
        4096, "--max-expand", help="Maximum addresses allowed when expanding ranges"
    ),
):
    """Ingest targets from a file and create Target records."""
    session: Session = ctx.obj
    with input_file.open("r", encoding="utf-8") as f:
        targets = expand_targets(f, max_expand=max_expand)
    for address in targets:
        db_repo.create_target(session, address=address)
    typer.echo(f"Ingested {len(targets)} targets")


@app.command()
def plan(
    ctx: typer.Context,
    options: str = typer.Option(
        None, "--options", help="Scan options (e.g. nmap flags)", show_default=False
    ),
    notes: str = typer.Option(None, "--notes", help="Optional notes for the scan run"),
):
    """Create a ScanRun covering all ingested targets."""
    session: Session = ctx.obj
    run = db_repo.create_scan_run(
        session, status=JobStatus.PLANNED, options=options, notes=notes
    )
    typer.echo(f"Created scan run {run.id}")


@app.command()
def split(
    ctx: typer.Context,
    scan_run_id: int,
    chunk_size: int = typer.Option(10, help="Targets per batch"),
):
    """Split all Targets into Batches for a ScanRun."""
    session: Session = ctx.obj
    targets = db_repo.list_targets(session)
    if not targets:
        typer.echo("No targets to batch")
        raise typer.Exit(code=1)
    batches = []
    for i in range(0, len(targets), chunk_size):
        batch_targets = targets[i : i + chunk_size]
        batch = db_repo.create_batch(
            session,
            name=f"run{scan_run_id}_batch{i // chunk_size + 1}",
            targets=batch_targets,
        )
        batches.append(batch)
    typer.echo(f"Created {len(batches)} batches")


@app.command()
def run(
    ctx: typer.Context,
    scan_run_id: int,
    timeout_sec: int = typer.Option(30, help="Timeout for each job"),
    concurrency: int = typer.Option(4, help="Concurrent jobs"),
):
    """Execute all Batches for a ScanRun, creating Job records."""

    session: Session = ctx.obj
    batches = db_repo.list_batches(session)
    if not batches:
        typer.echo("No batches to run")
        raise typer.Exit(code=1)

    runner_jobs = []
    for batch in batches:
        for target in batch.targets:
            db_repo.create_job(
                session,
                scan_run_id=scan_run_id,
                target_id=target.id,
                status=JobStatus.COMPLETED,
"""            job = db_repo.create_job(
                session,
                scan_run_id=scan_run_id,
                target_id=target.id,
                status="running",
                started_at=datetime.utcnow(),
"""
            )
            runner_jobs.append(RunnerJob(job_id=job.id, address=target.address))

    results = asyncio.run(run_jobs(runner_jobs, timeout_sec=timeout_sec, concurrency=concurrency))

    timed_out_targets = []
    for res in results:
        db_repo.create_result(
            session, job_id=res["job_id"], output=res.get("stdout"), error=res.get("stderr")
        )
        db_repo.update_job(
            session,
            res["job_id"],
            status=res["status"],
            completed_at=datetime.utcnow(),
        )
        if res["status"] == "timeout":
            timed_out_targets.append(res["address"])

    # Queue new batches for timed-out targets so planner can retry
    for address in timed_out_targets:
        target = next(
            (t for t in db_repo.list_targets(session) if t.address == address), None
        )
        if target:
            db_repo.create_batch(
                session,
                name=f"retry_{target.id}_{int(datetime.utcnow().timestamp())}",
                targets=[target],
            )

    typer.echo(f"Executed {len(batches)} batches")


if __name__ == "__main__":
    app()
