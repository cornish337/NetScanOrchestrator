import os
import sys
import tempfile
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import repository as db_repo
from src import reporting

def test_summary_queries_and_exports(test_db_session):
    """
    Tests reporting queries and export functions using an isolated DB session.
    """
    session = test_db_session
    run = db_repo.create_scan_run(session, status="completed")
    t1 = db_repo.create_target(session, address="1.1.1.1")
    t2 = db_repo.create_target(session, address="2.2.2.2")
    start = datetime.utcnow()
    db_repo.create_job(
        session,
        scan_run_id=run.id,
        target_id=t1.id,
        status="completed",
        started_at=start,
        completed_at=start + timedelta(seconds=5),
    )
    j2 = db_repo.create_job(
        session,
        scan_run_id=run.id,
        target_id=t2.id,
        status="failed",
        started_at=start,
        completed_at=start + timedelta(seconds=10),
    )
    db_repo.create_result(session, job_id=j2.id, stderr="timeout")

    runs = reporting.summarise_runs(session)
    assert runs[0]["failed_jobs"] == 1

    slowest = reporting.get_slowest_jobs(session)
    assert slowest[0]["job_id"] == j2.id

    failed = reporting.get_failed_jobs(session)
    assert failed[0]["error"] == "timeout"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_json, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:

        reporting.export_json(runs, tmp_json.name)
        reporting.export_csv(runs, tmp_csv.name)

        assert os.path.getsize(tmp_json.name) > 0
        assert os.path.getsize(tmp_csv.name) > 0

    os.unlink(tmp_json.name)
    os.unlink(tmp_csv.name)
