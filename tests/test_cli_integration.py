import unittest
import subprocess
import os
import tempfile
import json
import sys

class TestCLIIntegration(unittest.TestCase):

    def setUp(self):
        # Define project root assuming tests/test_cli_integration.py
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        self.test_data_dir = os.path.join(self.project_root, "tests", "test_data")
        self.input_file = os.path.join(self.test_data_dir, "integration_test_ips.txt")

        # Create a temporary directory for outputs
        self.temp_output_dir_obj = tempfile.TemporaryDirectory()
        self.temp_output_dir_path = self.temp_output_dir_obj.name
        self.output_prefix = os.path.join(self.temp_output_dir_path, "test_scan_results")

        self.cli_script_path = os.path.join(self.project_root, "nmap_parallel_scanner.py")

        # Ensure the input file exists (it should have been created in a previous step)
        if not os.path.exists(self.input_file):
            # This is a fallback, ideally the test environment setup handles this.
            print(f"Warning: Test input file {self.input_file} was missing. This test might fail or be unreliable.")
            # Attempt to create it minimally for the test to proceed, though this indicates a setup issue.
            os.makedirs(self.test_data_dir, exist_ok=True)
            with open(self.input_file, "w", encoding='utf-8') as f:
                f.write("scanme.nmap.org\n")


    def tearDown(self):
        self.temp_output_dir_obj.cleanup()

    @unittest.skipIf(os.getenv('GITHUB_ACTIONS') == 'true', "Skipping live Nmap scan in GitHub Actions to avoid network issues/blocks.")
    def test_scanner_runs_and_produces_valid_json_output(self):
        """
        Tests if the CLI scanner runs, produces a JSON output for scanme.nmap.org,
        and confirms the host is up with open TCP ports.
        This is a live test requiring Nmap installed and internet access.
        """
        nmap_options = "-T4 -F"  # -T4 for speed, -F for few (100) ports.
        output_format = "json"   # Test with JSON as it's comprehensive and easy to parse.

        command = [
            sys.executable,       # Use the same python interpreter that's running the tests
            self.cli_script_path,
            "-i", self.input_file,
            "-o", self.output_prefix,
            "-f", output_format,
            "--nmap-options", nmap_options,
            "--num-processes", "1", # Override for test speed, simplicity, and single target
            "--chunk-size", "1"     # Single target, so chunk size 1
        ]

        # For debugging test environment issues:
        print(f"\n[Test Info] Project Root: {self.project_root}")
        print(f"[Test Info] CLI Script Path: {self.cli_script_path}")
        print(f"[Test Info] Input File: {self.input_file}")
        print(f"[Test Info] Output Prefix: {self.output_prefix}")
        print(f"[Test Info] Running command: {' '.join(command)}\n")

        try:
            # Increased timeout as Nmap scans can vary in duration, especially on shared CI.
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=240) # 4 min timeout
        except subprocess.TimeoutExpired:
            self.fail(f"CLI script execution timed out after 240 seconds. Command: {' '.join(command)}")
        except Exception as e:
            self.fail(f"CLI script execution failed with an unexpected exception: {e}. Command: {' '.join(command)}")


        # Print stdout/stderr for debugging, especially on failure
        if result.stdout:
            print("CLI STDOUT:\n", result.stdout)
        if result.stderr:
            print("CLI STDERR:\n", result.stderr) # Nmap progress often goes to stderr

        self.assertEqual(result.returncode, 0, f"CLI script failed with exit code {result.returncode}. STDERR: {result.stderr}")

        expected_output_file = f"{self.output_prefix}.{output_format}"
        self.assertTrue(os.path.exists(expected_output_file), f"Output file {expected_output_file} was not created.")
        self.assertTrue(os.path.getsize(expected_output_file) > 0, f"Output file {expected_output_file} is empty.")

        # Parse the JSON output to verify content
        try:
            with open(expected_output_file, 'r', encoding='utf-8') as f:
                scan_data = json.load(f)
        except json.JSONDecodeError as e:
            self.fail(f"Could not decode JSON from output file {expected_output_file}. Error: {e}. File content (first 500 chars): {open(expected_output_file, 'r').read(500)}")
        except IOError:
            self.fail(f"Could not open output file {expected_output_file}")

        self.assertIn("hosts", scan_data, "JSON output missing 'hosts' key.")

        if not scan_data["hosts"]:
            # This can happen if scanme.nmap.org is down or filtered, or Nmap fails for other reasons.
            # Check stats for clues.
            stats = scan_data.get("stats", {})
            print("Scan data 'hosts' is empty. Stats:", stats)
            self.fail(f"No hosts found in scan results. Expected scanme.nmap.org. Unscanned/Error IPs: {stats.get('unscanned_or_error_ips')}")

        # scanme.nmap.org usually resolves to 45.33.32.156, but let's find it dynamically.
        found_scanme = False
        scanme_ip_in_results = None

        for ip, host_details in scan_data["hosts"].items():
            if isinstance(host_details.get("hostnames"), list):
                for hostname_entry in host_details["hostnames"]:
                    if isinstance(hostname_entry, dict) and hostname_entry.get("name", "").lower() == "scanme.nmap.org":
                        found_scanme = True
                        scanme_ip_in_results = ip
                        break
            if found_scanme:
                break

        self.assertTrue(found_scanme, "scanme.nmap.org not found by hostname in scan results.")
        self.assertIsNotNone(scanme_ip_in_results, "scanme_ip_in_results should be set if found_scanme is True.")

        scanme_details = scan_data["hosts"].get(scanme_ip_in_results, {})
        self.assertTrue(scanme_details, f"No details found for host {scanme_ip_in_results} (identified as scanme.nmap.org).")

        status_info = scanme_details.get("status", {})
        self.assertEqual(status_info.get("state"), "up",
                         f"scanme.nmap.org (IP: {scanme_ip_in_results}) not reported as 'up'. Status: {status_info}")

        # Check that some TCP port info is present (Nmap -F scans top 100 ports)
        # The key for protocols might be 'tcp', 'udp' etc. directly under host_details, or nested under 'protocols'
        # Based on results_handler.py, it should be host_details[proto_key]

        # Check for TCP protocol data specifically
        tcp_protocol_data = scanme_details.get("tcp")
        if not tcp_protocol_data: # Fallback if structure was different, e.g. nested under 'protocols'
            tcp_protocol_data = scanme_details.get("protocols", {}).get("tcp")

        self.assertIsNotNone(tcp_protocol_data, f"No TCP protocol data found for scanme.nmap.org (IP: {scanme_ip_in_results}). Host details: {scanme_details}")
        self.assertTrue(len(tcp_protocol_data) > 0, f"No TCP ports listed for scanme.nmap.org (IP: {scanme_ip_in_results}). TCP data: {tcp_protocol_data}")

        # Example: Check if a common port like 22 (SSH) or 80 (HTTP) is listed (state can be open, closed, or filtered)
        # This depends on scanme.nmap.org's actual state which can change.
        # For now, just checking that *some* TCP ports were found is sufficient for an integration test.


if __name__ == "__main__":
    unittest.main()
