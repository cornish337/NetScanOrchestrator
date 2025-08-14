import os
import tempfile
import unittest
from datetime import datetime, timedelta

from src.db.session import init_engine, get_session
from src.db import repository as db_repo
from src import reporting


class TestReportingModule(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        self.db_path = tmp.name
        init_engine(self.db_path)
        self.session = get_session()

    def tearDown(self):
        self.session.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_summary_queries_and_exports(self):
        run = db_repo.create_scan_run(self.session, status="completed")
        t1 = db_repo.create_target(self.session, address="1.1.1.1")
        t2 = db_repo.create_target(self.session, address="2.2.2.2")
        start = datetime.utcnow()
        db_repo.create_job(
            self.session,
            scan_run_id=run.id,
            target_id=t1.id,
            status="completed",
            started_at=start,
            completed_at=start + timedelta(seconds=5),
        )
        j2 = db_repo.create_job(
            self.session,
            scan_run_id=run.id,
            target_id=t2.id,
            status="failed",
            started_at=start,
            completed_at=start + timedelta(seconds=10),
        )
        db_repo.create_result(self.session, job_id=j2.id, stderr="timeout")

        runs = reporting.summarise_runs(self.session)
        self.assertEqual(runs[0]["failed_jobs"], 1)

        slowest = reporting.get_slowest_jobs(self.session)
        self.assertEqual(slowest[0]["job_id"], j2.id)

        failed = reporting.get_failed_jobs(self.session)
        self.assertEqual(failed[0]["error"], "timeout")

        tmp_json = tempfile.NamedTemporaryFile(delete=False)
        tmp_json.close()
        tmp_csv = tempfile.NamedTemporaryFile(delete=False)
        tmp_csv.close()
        reporting.export_json(runs, tmp_json.name)
        reporting.export_csv(runs, tmp_csv.name)
        self.assertTrue(os.path.getsize(tmp_json.name) > 0)
        self.assertTrue(os.path.getsize(tmp_csv.name) > 0)
        os.unlink(tmp_json.name)
        os.unlink(tmp_csv.name)


if __name__ == "__main__":
    unittest.main()
