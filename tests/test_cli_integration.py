import os
import subprocess
import sys
import tempfile
import unittest
import sqlite3


class TestTyperCLI(unittest.TestCase):
    """Exercise the Typer CLI using a temporary SQLite database."""

    def setUp(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.input_file = os.path.join(project_root, "tests", "test_data", "integration_test_ips.txt")
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

    def test_full_flow_status_counts(self):
        """End-to-end ingest → plan → run → status"""
        # ingest
        self.run_cli("ingest", self.input_file)
        # plan
        plan_out = self.run_cli("plan")
        run_id = int(plan_out.split()[-1])
        # run
        self.run_cli("run", run_id)
        # status
        status_out = self.run_cli("status", run_id)
        self.assertIn("completed: 1", status_out)

        # verify records exist in database
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM targets")
        self.assertEqual(cur.fetchone()[0], 1)
        cur.execute("SELECT COUNT(*) FROM scan_runs")
        self.assertEqual(cur.fetchone()[0], 1)
        cur.execute("SELECT COUNT(*) FROM jobs")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

