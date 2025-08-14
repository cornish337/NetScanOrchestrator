import os
import sys
import unittest

# Allow importing from the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.ip_handler import expand_targets, chunk_ips


class TestExpandTargets(unittest.TestCase):
    def test_ignore_blank_and_comments(self):
        lines = ["", "# comment", "8.8.8.8", "scanme.nmap.org # trailing"]
        expected = ["8.8.8.8", "scanme.nmap.org"]
        self.assertEqual(expand_targets(lines, max_expand=10), expected)

    def test_cidr_expansion(self):
        lines = ["192.0.2.0/30"]
        expected = ["192.0.2.1", "192.0.2.2"]
        self.assertEqual(expand_targets(lines, max_expand=10), expected)

    def test_range_expansion(self):
        lines = ["192.0.2.1-192.0.2.3"]
        expected = ["192.0.2.1", "192.0.2.2", "192.0.2.3"]
        self.assertEqual(expand_targets(lines, max_expand=10), expected)

    def test_hostname_passthrough(self):
        lines = ["my-host.example"]
        self.assertEqual(expand_targets(lines, max_expand=10), ["my-host.example"])

    def test_max_expand_guard(self):
        lines = ["10.0.0.0/24"]
        with self.assertRaises(ValueError):
            expand_targets(lines, max_expand=100)


class TestChunkIPs(unittest.TestCase):
    def test_chunk_ips_basic_even_division(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4"]
        expected = [["1.1.1.1", "2.2.2.2"], ["3.3.3.3", "4.4.4.4"]]
        self.assertEqual(chunk_ips(ips, chunk_size=2), expected)

    def test_chunk_ips_basic_uneven_division(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4", "5.5.5.5"]
        expected = [["1.1.1.1", "2.2.2.2"], ["3.3.3.3", "4.4.4.4"], ["5.5.5.5"]]
        self.assertEqual(chunk_ips(ips, chunk_size=2), expected)

    def test_chunk_ips_size_larger_than_list(self):
        ips = ["1.1.1.1", "2.2.2.2"]
        expected = [["1.1.1.1", "2.2.2.2"]]
        self.assertEqual(chunk_ips(ips, chunk_size=5), expected)

    def test_chunk_ips_size_equal_to_list_size(self):
        ips = ["1.1.1.1", "2.2.2.2"]
        expected = [["1.1.1.1", "2.2.2.2"]]
        self.assertEqual(chunk_ips(ips, chunk_size=2), expected)

    def test_chunk_ips_size_one(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        expected = [["1.1.1.1"], ["2.2.2.2"], ["3.3.3.3"]]
        self.assertEqual(chunk_ips(ips, chunk_size=1), expected)

    def test_chunk_ips_size_zero_default(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        expected = [ips]
        self.assertEqual(chunk_ips(ips, chunk_size=0), expected)
        self.assertEqual(chunk_ips(ips), expected)

    def test_chunk_ips_empty_ip_list(self):
        self.assertEqual(chunk_ips([], chunk_size=2), [])


if __name__ == "__main__":
    unittest.main()

