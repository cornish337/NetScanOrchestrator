"""Background job helpers such as timeout detection."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from .db.models import Job


def requeue_timed_out_jobs(session: Session, timeout_seconds: int) -> List[Job]:
    """Requeue jobs stuck in the ``running`` state beyond ``timeout_seconds``.

    Jobs that have ``status`` set to ``"running"`` and a ``started_at`` older
    than ``timeout_seconds`` are moved back to ``queued`` with their
    ``started_at`` cleared.  The modified ``Job`` instances are returned.
    """

    threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)
    timed_out = (
        session.query(Job)
        .filter(Job.status == "running", Job.started_at != None)  # noqa: E711
        .filter(Job.started_at < threshold)
        .all()
    )

    for job in timed_out:
        job.status = "queued"
        job.started_at = None

    session.commit()
    return timed_out


__all__ = ["requeue_timed_out_jobs"]

