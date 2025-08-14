"""Database repository providing high level data queries.

This module defines the :class:`Repository` used for reading information from the
scanning database.  The repository is intentionally minimal and only contains the
functionality required by the tests in this kata.
"""
from __future__ import annotations

from typing import Iterable

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

try:
    # The models are expected to be provided by the application using this
    # repository.  They are imported lazily to avoid hard dependencies here.
    from . import models  # type: ignore  # pylint: disable=import-error
except Exception:  # pragma: no cover - models may not be available during type checking
    models = None


class Repository:
    """Wraps a SQLAlchemy :class:`~sqlalchemy.orm.Session` with convenience helpers."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Job related helpers
    # ------------------------------------------------------------------
    def list_slow_jobs(self, p95_threshold: float) -> Iterable[object]:
        """Return jobs whose run duration exceeds ``p95_threshold``.

        Parameters
        ----------
        p95_threshold:
            Duration threshold in seconds. Jobs whose ``duration`` column is
            greater than or equal to this value are returned.
        """
        job_model = getattr(models, "Job")  # type: ignore[attr-defined]
        return (
            self.session.query(job_model)  # type: ignore[arg-type]
            .filter(job_model.duration >= p95_threshold)
            .order_by(job_model.duration.desc())
            .all()
        )

    # ------------------------------------------------------------------
    # Target related helpers
    # ------------------------------------------------------------------
    def list_problem_targets(self, retry_limit: int) -> Iterable[object]:
        """Return targets that have repeatedly timed out or failed.

        A target is considered problematic when either its ``timeout_count`` or
        ``failure_count`` column has reached or exceeded ``retry_limit``.
        """
        target_model = getattr(models, "Target")  # type: ignore[attr-defined]
        return (
            self.session.query(target_model)  # type: ignore[arg-type]
            .filter(
                or_(
                    target_model.timeout_count >= retry_limit,
                    target_model.failure_count >= retry_limit,
                )
            )
            .all()
        )

    # ------------------------------------------------------------------
    # Batch related helpers
    # ------------------------------------------------------------------
    def batches_for_auto_split(self) -> Iterable[object]:
        """Return batches that should be split automatically.

        A batch qualifies when it already has a ``status`` of ``"split"`` or
        when its ``timeout`` has been exceeded.
        """
        batch_model = getattr(models, "Batch")  # type: ignore[attr-defined]

        # Determine which attribute represents the timeout.  Different schemas
        # may name this column differently so we check a few common options.
        timeout_attr = None
        for name in ("timeout", "timeout_at", "expires_at"):
            if hasattr(batch_model, name):
                timeout_attr = getattr(batch_model, name)
                break
        if timeout_attr is None:
            raise AttributeError("Batch model does not define a timeout column")

        return (
            self.session.query(batch_model)  # type: ignore[arg-type]
            .filter(
                or_(
                    batch_model.status == "split",
                    timeout_attr < func.now(),
                )
            )
            .all()
        )

