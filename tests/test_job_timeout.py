import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db import repository as db_repo
from src.worker import requeue_timed_out_jobs


class TestJobTimeout(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        self.session = SessionLocal()

        # populate with a target and a scan run
        target = db_repo.create_target(self.session, address="1.1.1.1")
        run = db_repo.create_scan_run(self.session, status="running")
        # create a running job started in the past
        past = datetime.utcnow() - timedelta(seconds=120)
        self.job = db_repo.create_job(
            self.session,
            scan_run_id=run.id,
            target_id=target.id,
            status="running",
            started_at=past,
        )

    def tearDown(self):
        self.session.close()

    def test_requeue_timed_out_job(self):
        requeued = requeue_timed_out_jobs(self.session, timeout_seconds=60)
        self.assertEqual(len(requeued), 1)
        refreshed = db_repo.get_job(self.session, self.job.id)
        self.assertEqual(refreshed.status, "queued")
        self.assertIsNone(refreshed.started_at)

    def test_running_job_within_timeout_not_requeued(self):
        # create a job that started recently
        recent = datetime.utcnow() - timedelta(seconds=10)
        recent_job = db_repo.create_job(
            self.session,
            scan_run_id=self.job.scan_run_id,
            target_id=self.job.target_id,
            status="running",
            started_at=recent,
        )
        requeued = requeue_timed_out_jobs(self.session, timeout_seconds=60)
        self.assertEqual(len(requeued), 1)  # only the original job
        fresh = db_repo.get_job(self.session, recent_job.id)
        self.assertEqual(fresh.status, "running")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

