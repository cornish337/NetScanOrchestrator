import json
import os
import subprocess
import sys
import tempfile
import unittest


class TestTyperCLI(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.input_file = os.path.join(self.project_root, "tests", "test_data", "integration_test_ips.txt")
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        self.repo_path = tmp.name

    def tearDown(self):
        if os.path.exists(self.repo_path):
            os.unlink(self.repo_path)

    def run_cli(self, *args):
        cmd = [sys.executable, "-m", "src.cli.main", "--repo-file", self.repo_path, *map(str, args)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"Command {' '.join(cmd)} failed with {result.stderr}")
        return result.stdout.strip()

    def test_full_flow_creates_records(self):
        # ingest
        self.run_cli("ingest", self.input_file)
        # plan
        output = self.run_cli("plan")
        run_id = output.split()[-1]
        # split into batches of size 1
        self.run_cli("split", run_id, "--chunk-size", "1")
        # run all batches
        self.run_cli("run", run_id)

        with open(self.repo_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data.get("targets", [])), 1)
        self.assertEqual(len(data.get("scan_runs", [])), 1)
        self.assertEqual(len(data.get("batches", [])), 1)
        self.assertEqual(len(data.get("jobs", [])), 1)


if __name__ == "__main__":
    unittest.main()
