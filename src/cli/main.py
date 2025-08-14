from pathlib import Path
from typing import Optional
import typer

from ..repository import Repository

app = typer.Typer(help="NetScan Orchestrator CLI")


@app.callback()
def main(ctx: typer.Context, repo_file: Path = typer.Option(Path("data/state.json"), help="Path to repository file", dir_okay=False)):
    """Initialise repository and attach to context."""
    ctx.obj = Repository(repo_file)


@app.command()
def ingest(ctx: typer.Context, input_file: Path):
    """Ingest targets from a file and create Target records."""
    repo: Repository = ctx.obj
    targets = [line.strip() for line in input_file.read_text().splitlines() if line.strip()]
    for t in targets:
        repo.create_target(t)
    typer.echo(f"Ingested {len(targets)} targets")


@app.command()
def plan(ctx: typer.Context):
    """Create a ScanRun covering all ingested targets."""
    repo: Repository = ctx.obj
    target_ids = [t.id for t in repo.list_targets()]
    run = repo.create_scan_run(target_ids)
    typer.echo(f"Created scan run {run.id}")


@app.command()
def split(ctx: typer.Context, scan_run_id: str, chunk_size: int = typer.Option(10, help="Targets per batch")):
    """Split a ScanRun into Batches."""
    repo: Repository = ctx.obj
    run = repo.get_scan_run(scan_run_id)
    if not run:
        typer.echo(f"Scan run {scan_run_id} not found")
        raise typer.Exit(code=1)
    batches = []
    targets = run.target_ids
    for i in range(0, len(targets), chunk_size):
        batch_targets = targets[i:i + chunk_size]
        batch = repo.create_batch(scan_run_id, batch_targets)
        batches.append(batch)
    typer.echo(f"Created {len(batches)} batches")


@app.command()
def run(ctx: typer.Context, scan_run_id: str):
    """Execute all Batches for a ScanRun, creating Job records."""
    repo: Repository = ctx.obj
    batches = repo.list_batches(scan_run_id)
    if not batches:
        typer.echo("No batches to run")
        raise typer.Exit(code=1)
    for batch in batches:
        artifact = f"artifact_{batch.id}.txt"
        repo.create_job(batch.id, artifact=artifact, status="completed")
    typer.echo(f"Executed {len(batches)} batches")


if __name__ == "__main__":
    app()
