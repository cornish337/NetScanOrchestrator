from pathlib import Path
from typing import Optional
from datetime import datetime
import asyncio
import typer

from sqlalchemy.orm import Session

from ..db.session import init_engine, get_session, DEFAULT_DB_PATH
from ..db import repository as db_repo
from .. import reporting
from ..ip_handler import expand_targets
from ..runner import RunnerJob, run_jobs

app = typer.Typer(help="NetScan Orchestrator CLI")


@app.callback()
def main(
    ctx: typer.Context,
    db_path: Path = typer.Option(
        Path(DEFAULT_DB_PATH),
        "--db-path",
        help="Path to SQLite state database",
        dir_okay=False,
    ),
):
    """Initialise the database engine and attach a session to context."""
    init_engine(str(db_path))
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
def plan(ctx: typer.Context):
    """Create a ScanRun covering all ingested targets."""
    session: Session = ctx.obj
    run = db_repo.create_scan_run(session, status="planned")
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
            job = db_repo.create_job(
                session,
                scan_run_id=scan_run_id,
                target_id=target.id,
                status="running",
                started_at=datetime.utcnow(),
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


@app.command()
def status(
    ctx: typer.Context,
    json_out: Optional[Path] = typer.Option(
        None, "--json-out", help="Write summary information to JSON file", dir_okay=False
    ),
    csv_out: Optional[Path] = typer.Option(
        None, "--csv-out", help="Write run summary to CSV file", dir_okay=False
    ),
):
    """Display a summary of scan runs, jobs and failures."""

    session: Session = ctx.obj

    run_summary = reporting.summarise_runs(session)
    slowest_jobs = reporting.get_slowest_jobs(session)
    failed_jobs = reporting.get_failed_jobs(session)
    export_payload = {
        "runs": run_summary,
        "slowest_jobs": slowest_jobs,
        "failed_jobs": failed_jobs,
    }

    if json_out:
        reporting.export_json(export_payload, str(json_out))
    if csv_out:
        reporting.export_csv(run_summary, str(csv_out))

    typer.echo("ScanRun Summary")
    if run_summary:
        typer.echo(f"{'Run':<5} {'Total':<6} {'Completed':<9} {'Failed':<6}")
        for row in run_summary:
            typer.echo(
                f"{row['scan_run_id']:<5} {row['total_jobs']:<6} {row['completed_jobs']:<9} {row['failed_jobs']:<6}"
            )
    else:
        typer.echo("No ScanRuns found")

    typer.echo("\nSlowest Jobs")
    if slowest_jobs:
        typer.echo(f"{'Job':<5} {'Run':<5} {'Target':<15} {'Duration':<8}")
        for row in slowest_jobs:
            duration = row['duration'] if row['duration'] is not None else 0.0
            typer.echo(
                f"{row['job_id']:<5} {row['scan_run_id']:<5} {row['target']:<15} {duration:<8.2f}"
            )
    else:
        typer.echo("No job durations")

    typer.echo("\nFailed Jobs")
    if failed_jobs:
        typer.echo(f"{'Job':<5} {'Run':<5} {'Target':<15} {'Error'}")
        for row in failed_jobs:
            typer.echo(
                f"{row['job_id']:<5} {row['scan_run_id']:<5} {row['target']:<15} {row['error'] or ''}"
            )
    else:
        typer.echo("No failed jobs")


if __name__ == "__main__":
    app()
