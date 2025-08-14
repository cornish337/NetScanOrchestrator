from pathlib import Path
import typer

from sqlalchemy.orm import Session

from ..db.session import init_engine, get_session
from ..db import repository as db_repo

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
def run(
    ctx: typer.Context,
    scan_run_id: int,
    max_procs: int = typer.Option(
        1,
        "--max-procs",
        min=1,
        help="Maximum number of scan jobs to execute in parallel.",
    ),
    rate_limit: float = typer.Option(
        0.0,
        "--rate-limit",
        help="Maximum jobs to start per second. Use 0 for unlimited.",
    ),
):
    """Execute all Batches for a ScanRun, creating Job records."""
    session: Session = ctx.obj
    batches = db_repo.list_batches(session)
    if not batches:
        typer.echo("No batches to run")
        raise typer.Exit(code=1)

    from ..runner import run_batches

    jobs_created = run_batches(
        session,
        scan_run_id,
        batches,
        max_procs=max_procs,
        rate_limit=rate_limit,
    )

    typer.echo(f"Executed {len(batches)} batches, {jobs_created} jobs")


if __name__ == "__main__":
    app()
