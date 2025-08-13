import unittest
import os
import sys

# Add project root to sys.path to allow direct import of src modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.results_handler import consolidate_scan_results

class TestResultsHandler(unittest.TestCase):

    def test_consolidate_scan_results_basic_success_and_some_down(self):
        mock_scan_results_list = [
            { # Chunk 1: Successful, all hosts up
                "input_targets": ["1.1.1.1", "1.1.1.2"],
                "scan": {
                    "1.1.1.1": {"status": {"state": "up"}, "protocols": {"tcp": {80: {"state": "open"}}}},
                    "1.1.1.2": {"status": {"state": "up"}, "protocols": {"tcp": {443: {"state": "open"}}}}
                },
                "stats": {"uphosts": "2", "totalhosts": "2", "downhosts": "0"}, # Nmap scanstats
                "nmap": {"command_line": "nmap -T4 -F 1.1.1.1 1.1.1.2"}
            },
            { # Chunk 2: Successful, one host up, one host effectively "down" (no data in 'scan' dict)
                "input_targets": ["2.2.2.1", "2.2.2.2"],
                "scan": { # 2.2.2.2 is not in 'scan', so it's treated as down or filtered
                    "2.2.2.1": {"status": {"state": "up"}, "protocols": {"tcp": {22: {"state": "open"}}}}
                },
                "stats": {"uphosts": "1", "totalhosts": "2", "downhosts": "1"},
                "nmap": {"command_line": "nmap -T4 -F 2.2.2.1 2.2.2.2"}
            }
        ]

        consolidated = consolidate_scan_results(mock_scan_results_list)

        self.assertEqual(len(consolidated["hosts"]), 3, "Should have 3 hosts with scan data.")
        self.assertIn("1.1.1.1", consolidated["hosts"])
        self.assertIn("1.1.1.2", consolidated["hosts"])
        self.assertIn("2.2.2.1", consolidated["hosts"])
        self.assertEqual(len(consolidated["errors"]), 0, "Should be no consolidation errors.")

        stats = consolidated["stats"]
        self.assertEqual(stats["total_chunks"], 2)
        self.assertEqual(stats["successful_chunks"], 2) # Both chunks executed Nmap successfully
        self.assertEqual(stats["failed_chunks"], 0)
        self.assertEqual(stats["total_input_targets_processed"], 4) # Unique IPs from input_targets
        self.assertEqual(stats["total_hosts_up_reported_by_nmap"], 3) # Sum of 'uphosts' from scanstats

        self.assertCountEqual(stats["all_intended_ips"], ["1.1.1.1", "1.1.1.2", "2.2.2.1", "2.2.2.2"])
        self.assertCountEqual(stats["successfully_scanned_ips"], ["1.1.1.1", "1.1.1.2", "2.2.2.1"])
        self.assertCountEqual(stats["ips_in_failed_chunks"], [])
        # 2.2.2.2 was in input_targets but not in 'scan' data of its chunk.
        self.assertCountEqual(stats["unscanned_or_error_ips"], ["2.2.2.2"])
        self.assertEqual(stats["total_unique_hosts_found"], 3)

    def test_consolidate_scan_results_with_failed_chunk(self):
        mock_scan_results_list = [
            {
                "input_targets": ["1.1.1.1", "1.1.1.3"],
                "scan": {"1.1.1.1": {"status": {"state": "up"}}}, # 1.1.1.3 is down/filtered
                "stats": {"uphosts": "1", "totalhosts": "2", "downhosts": "1"},
                "nmap": {"command_line": "nmap -T4 -F 1.1.1.1 1.1.1.3"}
            },
            {
                "input_targets": ["3.3.3.1", "3.3.3.2"],
                "error": "Nmap execution failed for chunk", # This chunk failed
                "details": "Some nmap error string, e.g., nmap not found",
                # "stats" might be missing or minimal if nmap command itself failed
            }
        ]
        consolidated = consolidate_scan_results(mock_scan_results_list)

        self.assertEqual(len(consolidated["hosts"]), 1, "Only one host should have scan data.")
        self.assertIn("1.1.1.1", consolidated["hosts"])
        self.assertEqual(len(consolidated["errors"]), 1, "One chunk error should be recorded.")
        self.assertEqual(consolidated["errors"][0]["error_type"], "Nmap execution failed for chunk")
        self.assertCountEqual(consolidated["errors"][0]["input_targets"], ["3.3.3.1", "3.3.3.2"])

        stats = consolidated["stats"]
        self.assertEqual(stats["total_chunks"], 2)
        self.assertEqual(stats["successful_chunks"], 1) # Chunk 1 ran Nmap
        self.assertEqual(stats["failed_chunks"], 1)     # Chunk 2 had execution error
        self.assertEqual(stats["total_hosts_up_reported_by_nmap"], 1) # From chunk 1's stats
        self.assertEqual(stats["total_input_targets_processed"], 4)

        self.assertCountEqual(stats["all_intended_ips"], ["1.1.1.1", "1.1.1.3", "3.3.3.1", "3.3.3.2"])
        self.assertCountEqual(stats["successfully_scanned_ips"], ["1.1.1.1"])
        self.assertCountEqual(stats["ips_in_failed_chunks"], ["3.3.3.1", "3.3.3.2"])
        # Unscanned = (all_intended - successfully_scanned)
        # So, 1.1.1.3 (down/filtered) + 3.3.3.1, 3.3.3.2 (failed chunk)
        self.assertCountEqual(stats["unscanned_or_error_ips"], ["1.1.1.3", "3.3.3.1", "3.3.3.2"])
        self.assertEqual(stats["total_unique_hosts_found"], 1)


    def test_consolidate_scan_results_all_chunks_fail_execution(self):
        mock_scan_results_list = [
            {"input_targets": ["1.1.1.1", "1.1.1.2"], "error": "Failed 1", "details": "Detail 1"},
            {"input_targets": ["2.2.2.2", "2.2.2.3"], "error": "Failed 2", "details": "Detail 2"}
        ]
        consolidated = consolidate_scan_results(mock_scan_results_list)

        self.assertEqual(len(consolidated["hosts"]), 0)
        self.assertEqual(len(consolidated["errors"]), 2)

        stats = consolidated["stats"]
        self.assertEqual(stats["total_chunks"], 2)
        self.assertEqual(stats["successful_chunks"], 0)
        self.assertEqual(stats["failed_chunks"], 2)
        self.assertEqual(stats["total_hosts_up_reported_by_nmap"], 0)
        self.assertEqual(stats["total_input_targets_processed"], 4)

        self.assertCountEqual(stats["all_intended_ips"], ["1.1.1.1", "1.1.1.2", "2.2.2.2", "2.2.2.3"])
        self.assertCountEqual(stats["successfully_scanned_ips"], [])
        self.assertCountEqual(stats["ips_in_failed_chunks"], ["1.1.1.1", "1.1.1.2", "2.2.2.2", "2.2.2.3"])
        self.assertCountEqual(stats["unscanned_or_error_ips"], ["1.1.1.1", "1.1.1.2", "2.2.2.2", "2.2.2.3"])
        self.assertEqual(stats["total_unique_hosts_found"], 0)

    def test_consolidate_scan_results_empty_input_list(self):
        mock_scan_results_list = []
        consolidated = consolidate_scan_results(mock_scan_results_list)

        self.assertEqual(len(consolidated["hosts"]), 0)
        self.assertEqual(len(consolidated["errors"]), 0)

        stats = consolidated["stats"]
        self.assertEqual(stats["total_chunks"], 0)
        self.assertEqual(stats["successful_chunks"], 0)
        self.assertEqual(stats["failed_chunks"], 0)
        self.assertEqual(stats["total_input_targets_processed"], 0)
        self.assertEqual(stats["total_hosts_up_reported_by_nmap"], 0)
        self.assertCountEqual(stats["all_intended_ips"], [])
        self.assertCountEqual(stats["successfully_scanned_ips"], [])
        self.assertCountEqual(stats["ips_in_failed_chunks"], [])
        self.assertCountEqual(stats["unscanned_or_error_ips"], [])
        self.assertEqual(stats["total_unique_hosts_found"], 0)

    def test_consolidate_scan_results_all_targets_down_or_filtered(self):
        mock_scan_results_list = [
            {
                "input_targets": ["1.1.1.1", "1.1.1.2"],
                "scan": {}, # No host data in 'scan'
                "stats": {"uphosts": "0", "totalhosts": "2", "downhosts": "2"},
                "message": "All 2 specified target(s) are down or did not respond."
            },
            {
                "input_targets": ["2.2.2.1"],
                "scan": {}, # No host data in 'scan'
                "stats": {"uphosts": "0", "totalhosts": "1", "downhosts": "1"},
                "message": "All 1 specified target(s) are down or did not respond."
            }
        ]
        consolidated = consolidate_scan_results(mock_scan_results_list)

        self.assertEqual(len(consolidated["hosts"]), 0) # No hosts have detailed scan data
        self.assertEqual(len(consolidated["errors"]), 0) # No execution errors for chunks

        stats = consolidated["stats"]
        self.assertEqual(stats["total_chunks"], 2)
        self.assertEqual(stats["successful_chunks"], 2) # Nmap ran successfully for both
        self.assertEqual(stats["failed_chunks"], 0)
        self.assertEqual(stats["total_input_targets_processed"], 3) # 1.1.1.1, 1.1.1.2, 2.2.2.1
        self.assertEqual(stats["total_hosts_up_reported_by_nmap"], 0) # Sum of 'uphosts'

        self.assertCountEqual(stats["all_intended_ips"], ["1.1.1.1", "1.1.1.2", "2.2.2.1"])
        self.assertCountEqual(stats["successfully_scanned_ips"], []) # 'scan' dict was empty for all
        self.assertCountEqual(stats["ips_in_failed_chunks"], [])
        # All intended IPs are unscanned because 'scan' dict was empty for them
        self.assertCountEqual(stats["unscanned_or_error_ips"], ["1.1.1.1", "1.1.1.2", "2.2.2.1"])
        self.assertEqual(stats["total_unique_hosts_found"], 0)

        # Check individual chunk reports for messages
        self.assertIn("All 2 specified target(s) are down or did not respond.", consolidated["stats"]["individual_chunk_reports"][0]["message"])
        self.assertIn("All 1 specified target(s) are down or did not respond.", consolidated["stats"]["individual_chunk_reports"][1]["message"])


if __name__ == "__main__":
    unittest.main()
