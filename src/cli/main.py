from pathlib import Path
from collections import Counter
from datetime import datetime

import typer
from sqlalchemy.orm import Session

from ..db.session import init_engine, get_session
from ..db import repository as db_repo
from ..db.models import Job

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
    """Create a ScanRun and queue jobs for all targets."""
    session: Session = ctx.obj
    targets = db_repo.list_targets(session)
    if not targets:
        typer.echo("No targets to plan")
        raise typer.Exit(code=1)
    run = db_repo.create_scan_run(session, status="planned")
    for target in targets:
        db_repo.create_job(
            session, scan_run_id=run.id, target_id=target.id, status="queued"
        )
    typer.echo(f"Created scan run {run.id}")


@app.command()
def run(ctx: typer.Context, scan_run_id: int):
    """Execute all queued Jobs for a ScanRun."""
    session: Session = ctx.obj
    jobs = (
        session.query(Job)
        .filter(Job.scan_run_id == scan_run_id, Job.status == "queued")
        .all()
    )
    if not jobs:
        typer.echo("No jobs to run")
        raise typer.Exit(code=1)
    now = datetime.utcnow()
    for job in jobs:
        job.status = "completed"
        job.started_at = now
        job.completed_at = now
    db_repo.update_scan_run(session, scan_run_id, status="completed")
    session.commit()
    typer.echo(f"Executed {len(jobs)} jobs")


@app.command()
def status(ctx: typer.Context, scan_run_id: int):
    """Show the status counts for Jobs in a ScanRun."""
    session: Session = ctx.obj
    jobs = session.query(Job).filter(Job.scan_run_id == scan_run_id).all()
    if not jobs:
        typer.echo("No jobs for run")
        raise typer.Exit(code=1)
    counts = Counter(job.status for job in jobs)
    for status_name, count in counts.items():
        typer.echo(f"{status_name}: {count}")


if __name__ == "__main__":
    app()
