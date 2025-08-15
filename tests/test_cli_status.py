import os
import subprocess
import sys
import tempfile
import unittest


class TestCLIStatusCommand(unittest.TestCase):
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
        return result.stdout

    def test_status_command_outputs_tables(self):
        self.run_cli("ingest", self.input_file)
        output = self.run_cli("plan")
        run_id = int(output.split()[-1])
        self.run_cli("split", run_id, "--chunk-size", "1")
        self.run_cli("run", run_id)
        status_output = self.run_cli("status")
        self.assertIn("ScanRun Summary", status_output)
        self.assertIn("Job   Run   Target          Duration", status_output)
        self.assertIn("No failed jobs", status_output)


if __name__ == "__main__":
    unittest.main()
