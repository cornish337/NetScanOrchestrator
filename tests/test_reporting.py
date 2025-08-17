import os
import tempfile
from datetime import datetime, timedelta
import pytest

from src.db import repository as db_repo
from src import reporting

def test_summary_queries_and_exports(db_session):
    """
    Tests the reporting queries (summarise_runs, get_slowest_jobs, get_failed_jobs)
    and the JSON/CSV export functions.
    """
    run = db_repo.create_scan_run(db_session, status="completed")
    t1 = db_repo.create_target(db_session, address="1.1.1.1")
    t2 = db_repo.create_target(db_session, address="2.2.2.2")
    start = datetime.utcnow()

    db_repo.create_job(
        db_session,
        scan_run_id=run.id,
        target_id=t1.id,
        status="completed",
        started_at=start,
        completed_at=start + timedelta(seconds=5),
    )

    j2 = db_repo.create_job(
        db_session,
        scan_run_id=run.id,
        target_id=t2.id,
        status="failed",
        started_at=start,
        completed_at=start + timedelta(seconds=10),
    )

    db_repo.create_result(db_session, job_id=j2.id, stderr="timeout")

    runs = reporting.summarise_runs(db_session)
    assert runs[0]["failed_jobs"] == 1

    slowest = reporting.get_slowest_jobs(db_session)
    assert slowest[0]["job_id"] == j2.id

    failed = reporting.get_failed_jobs(db_session)
    assert failed[0]["error"] == "timeout"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_json, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
        tmp_json_path = tmp_json.name
        tmp_csv_path = tmp_csv.name

    try:
        reporting.export_json(runs, tmp_json_path)
        reporting.export_csv(runs, tmp_csv_path)
        assert os.path.getsize(tmp_json_path) > 0
        assert os.path.getsize(tmp_csv_path) > 0
    finally:
        os.unlink(tmp_json_path)
        os.unlink(tmp_csv_path)
