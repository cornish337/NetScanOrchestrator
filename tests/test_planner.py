import os
import tempfile
import unittest

from src import planner
from src.db.session import init_engine, get_session
from src.db import repository as db_repo
from src.db.models import Base


class PlannerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile(delete=False)
        cls.tmp.close()
        init_engine(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.tmp.name)

    def setUp(self):
        self.session = get_session()
        engine = self.session.get_bind()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def tearDown(self):
        self.session.close()

    def _create_targets(self, count: int):
        for i in range(count):
            db_repo.create_target(self.session, address=f"10.0.0.{i}")

    def test_create_initial_batches(self):
        self._create_targets(3)
        batches = planner.create_initial_batches(self.session, chunk_size=2, strategy="test")
        self.assertEqual(len(batches), 2)
        self.assertEqual(batches[0].strategy, "test")
        self.assertEqual(len(batches[0].targets), 2)
        self.assertEqual(len(batches[1].targets), 1)

    def test_resplit_job_creates_child_batches(self):
        self._create_targets(4)
        run = db_repo.create_scan_run(self.session, status="planned")
        batches = planner.create_initial_batches(self.session, chunk_size=4, strategy="orig")
        batch = batches[0]
        # Create a job associated with this batch
        job = db_repo.create_job(
            self.session,
            scan_run_id=run.id,
            batch_id=batch.id,
            target_id=batch.targets[0].id,
            status="timeout",
        )
        new_batches = planner.resplit_job(self.session, job.id)
        self.assertEqual(len(new_batches), 2)
        for nb in new_batches:
            self.assertEqual(nb.parent_batch_id, batch.id)
            self.assertEqual(nb.strategy, batch.strategy)
        # Parent batch should have no targets after split
        refreshed_parent = db_repo.get_batch(self.session, batch.id)
        self.assertEqual(len(refreshed_parent.targets), 0)


if __name__ == "__main__":
    unittest.main()
