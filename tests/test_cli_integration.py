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
        # plan including batch creation
        output = self.run_cli("plan", "--chunk-size", "1")
        run_id = int(output.split()[-1])
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

    def test_resplit_creates_new_batches(self):
        # create a temporary input file with two targets
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp_in:
            tmp_in.write("1.1.1.1\n2.2.2.2\n")
            tmp_input = tmp_in.name
        self.run_cli("ingest", tmp_input)
        os.unlink(tmp_input)
        output = self.run_cli("plan", "--chunk-size", "2")
        run_id = int(output.split()[-1])
        self.run_cli("run", run_id)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id FROM jobs LIMIT 1")
        job_id = cur.fetchone()[0]
        conn.close()
        self.run_cli("resplit", job_id)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM batches")
        # original batch plus two child batches
        self.assertEqual(cur.fetchone()[0], 3)
        conn.close()


if __name__ == "__main__":
    unittest.main()
