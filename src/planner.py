"""Planning utilities for creating and splitting scan batches."""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from .db import repository as db_repo
from .db.models import Batch, Job


def create_initial_batches(session: Session, *, chunk_size: int, strategy: str) -> List[Batch]:
    """Create initial batches from all targets.

    Args:
        session: Database session.
        chunk_size: Maximum number of targets per batch.
        strategy: Strategy string to store on each batch.

    Returns:
        List of created Batch instances.
    """
    targets = db_repo.list_targets(session)
    batches: List[Batch] = []
    for idx in range(0, len(targets), chunk_size):
        batch_targets = targets[idx : idx + chunk_size]
        batch = db_repo.create_batch(
            session,
            name=f"batch{idx // chunk_size + 1}",
            targets=batch_targets,
            strategy=strategy,
        )
        batches.append(batch)
    return batches


def resplit_job(session: Session, job_id: int) -> List[Batch]:
    """Binary split the batch for the given job into two new batches.

    The original batch has its targets cleared to avoid re-processing.

    Args:
        session: Database session.
        job_id: Identifier of the job whose batch should be split.

    Returns:
        List of newly created Batch instances (empty if no split performed).
    """
    job: Job | None = db_repo.get_job(session, job_id)
    if not job or not job.batch:
        return []
    batch = job.batch
    if len(batch.targets) <= 1:
        return []
    mid = len(batch.targets) // 2
    targets1 = list(batch.targets[:mid])
    targets2 = list(batch.targets[mid:])
    new_batches: List[Batch] = []
    for i, target_list in enumerate((targets1, targets2), start=1):
        new_batch = db_repo.create_batch(
            session,
            name=f"{batch.name}_split{i}",
            targets=target_list,
            strategy=batch.strategy,
            parent_batch_id=batch.id,
        )
        new_batches.append(new_batch)
    batch.targets = []
    session.commit()
    return new_batches
