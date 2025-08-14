from pathlib import Path
import typer

from sqlalchemy.orm import Session

from ..db.session import init_engine, get_session
from ..db import repository as db_repo
from .. import planner

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
def plan(
    ctx: typer.Context,
    chunk_size: int = typer.Option(10, help="Targets per batch"),
    strategy: str = typer.Option("sequential", help="Batching strategy"),
):
    """Create a ScanRun and initial Batches."""
    session: Session = ctx.obj
    run = db_repo.create_scan_run(session, status="planned")
    planner.create_initial_batches(session, chunk_size=chunk_size, strategy=strategy)
    typer.echo(f"Created scan run {run.id}")


@app.command()
def resplit(ctx: typer.Context, job_id: int):
    """Split a batch in two based on a job that exceeded timeout."""
    session: Session = ctx.obj
    new_batches = planner.resplit_job(session, job_id)
    typer.echo(f"Created {len(new_batches)} new batches")


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
                session,
                scan_run_id=scan_run_id,
                batch_id=batch.id,
                target_id=target.id,
                status="completed",
            )
            jobs_created += 1
    typer.echo(f"Executed {len(batches)} batches")


if __name__ == "__main__":
    app()
