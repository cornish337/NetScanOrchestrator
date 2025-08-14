"""Job execution helpers with simple scheduling.

This module provides a helper to run scan jobs while limiting the
number of simultaneous workers and optionally rate limiting job
submissions.  The actual scanning work is intentionally minimal in
tests; the focus is on the scheduling behaviour which mimics what a
real scanner would need.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

from sqlalchemy.orm import Session

from .db import repository as db_repo


def run_batches(
    session: Session,
    scan_run_id: int,
    batches: Iterable,
    *,
    max_procs: int = 1,
    rate_limit: float = 0.0,
) -> int:
    """Execute jobs for all targets in *batches*.

    Parameters
    ----------
    session:
        Database session used to record :class:`~src.db.models.Job` entries.
    scan_run_id:
        Identifier of the :class:`~src.db.models.ScanRun` the jobs belong to.
    batches:
        Iterable of :class:`~src.db.models.Batch` instances whose targets will
        be scanned.
    max_procs:
        Maximum number of jobs to run simultaneously.  Values less than ``1``
        are treated as ``1``.
    rate_limit:
        Maximum number of jobs to start per second.  A value of ``0`` disables
        rate limiting.

    Returns
    -------
    int
        Number of jobs that were executed.
    """

    workers = max(1, int(max_procs))
    delay = 1.0 / rate_limit if rate_limit > 0 else 0.0

    def _scan(target) -> int:
        """Placeholder for real scan work.

        In the real implementation this would invoke a network scanner.  For
        the purposes of the kata and tests it simply returns immediately after
        an optional tiny sleep.
        """
        if delay:
            # Sleep is handled before submission for rate limiting; keep the
            # worker fast.  The sleep here is merely defensive in case a real
            # scan is swapped in that needs to respect pacing itself.
            pass
        return target.id

    futures = []
    last_launch = 0.0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for batch in batches:
            for target in batch.targets:
                if delay:
                    now = time.monotonic()
                    wait = (last_launch + delay) - now
                    if wait > 0:
                        time.sleep(wait)
                    last_launch = time.monotonic()
                futures.append((target.id, executor.submit(_scan, target)))

        for target_id, fut in futures:
            fut.result()  # Propagate worker exceptions if any
            db_repo.create_job(
                session, scan_run_id=scan_run_id, target_id=target_id, status="completed"
            )

    return len(futures)
