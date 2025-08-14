from pathlib import Path
from typing import Optional

import typer

from sqlalchemy.orm import Session

from ..db.session import init_engine, get_session
from ..db import repository as db_repo
from .. import reporting

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
def ingest(ctx: typer.Context, input_file: Path):
    """Ingest targets from a file and create Target records."""
    session: Session = ctx.obj
    targets = [line.strip() for line in input_file.read_text().splitlines() if line.strip()]
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
def run(ctx: typer.Context, scan_run_id: int):
    """Execute all Batches for a ScanRun, creating Job records."""
    session: Session = ctx.obj
    batches = db_repo.list_batches(session)
    if not batches:
        typer.echo("No batches to run")
        raise typer.Exit(code=1)
    jobs_created = 0
    for batch in batches:
        for target in batch.targets:
            db_repo.create_job(
                session, scan_run_id=scan_run_id, target_id=target.id, status="completed"
            )
            jobs_created += 1
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
