import os
import subprocess
import sys
import tempfile
import unittest
import sqlite3


class TestTyperCLI(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.input_file = os.path.join(self.project_root, "tests", "test_data", "integration_test_ips.txt")
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        self.db_path = tmp.name

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def run_cli(self, *args):
        cmd = [
            sys.executable,
            "-m",
            "src.cli.main",
            "--db-path",
            self.db_path,
            *map(str, args),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"Command {' '.join(cmd)} failed with {result.stderr}")
        return result.stdout.strip()

    def test_full_flow_creates_records(self):
        # ingest
        self.run_cli("ingest", self.input_file)
        # plan
        output = self.run_cli("plan")
        run_id = int(output.split()[-1])
        # split into batches of size 1
        self.run_cli("split", run_id, "--chunk-size", "1")
        # run all batches
        self.run_cli("run", run_id)

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM targets")
        self.assertEqual(cur.fetchone()[0], 1)
        cur.execute("SELECT COUNT(*) FROM scan_runs")
        self.assertEqual(cur.fetchone()[0], 1)
        cur.execute("SELECT COUNT(*) FROM batches")
        self.assertEqual(cur.fetchone()[0], 1)
        cur.execute("SELECT COUNT(*) FROM jobs")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()

    def test_ingest_is_idempotent(self):
        """Test that running ingest twice with the same file does not create duplicates."""
        # Run ingest for the first time
        output1 = self.run_cli("ingest", self.input_file)
        self.assertIn("Ingested 1 new targets", output1)
        self.assertIn("Skipped 0 duplicates", output1)

        # Run ingest for the second time
        output2 = self.run_cli("ingest", self.input_file)
        self.assertIn("Ingested 0 new targets", output2)
        self.assertIn("Skipped 1 duplicates", output2)

        # Verify the total number of targets in the database
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM targets")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()


if __name__ == "__main__":
    unittest.main()
