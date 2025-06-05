import unittest
import os
import sys
import tempfile

# Add project root to sys.path to allow direct import of src modules
# This is common for test files located in a 'tests' subdirectory.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.ip_handler import read_ips_from_file, chunk_ips

class TestIPHandler(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir_path = self.temp_dir_obj.name
        self.test_file_path = os.path.join(self.temp_dir_path, "test_ips.txt")

    def tearDown(self):
        # Cleanup the temporary directory
        self.temp_dir_obj.cleanup()

    def test_read_ips_from_file_valid_content(self):
        content = "192.168.1.1\n\n10.0.0.1\n 127.0.0.1 \nscanme.nmap.org\n192.168.1.0/24\n"
        with open(self.test_file_path, "w", encoding='utf-8') as f:
            f.write(content)

        expected_ips = ["192.168.1.1", "10.0.0.1", "127.0.0.1", "scanme.nmap.org", "192.168.1.0/24"]
        # Assuming read_ips_from_file is called from project root, so path is direct.
        # If tests are run from 'tests' dir, path needs to be relative or absolute.
        # The sys.path modification should handle imports, file paths are separate.
        self.assertEqual(read_ips_from_file(self.test_file_path), expected_ips)

    def test_read_ips_from_file_non_existent(self):
        # Current implementation of read_ips_from_file prints an error and returns []
        # for FileNotFoundError. This test verifies that behavior.
        # If the design were to re-raise FileNotFoundError, the test would be:
        # with self.assertRaises(FileNotFoundError):
        # read_ips_from_file("non_existent_file.txt")
        # For now, checking the actual behavior:
        # Redirect stdout to check print message? For simplicity, just check return.
        # Note: Suppressing print for this test case could be done with a context manager if needed.
        self.assertEqual(read_ips_from_file("non_existent_file.txt"), [])

    def test_read_ips_from_file_empty_file(self):
        with open(self.test_file_path, "w", encoding='utf-8') as f:
            f.write("") # Empty file
        self.assertEqual(read_ips_from_file(self.test_file_path), [])

    def test_read_ips_from_file_file_with_only_empty_lines(self):
        with open(self.test_file_path, "w", encoding='utf-8') as f:
            f.write("\n\n\n") # File with only empty lines
        self.assertEqual(read_ips_from_file(self.test_file_path), [])

    def test_chunk_ips_basic_even_division(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4"]
        chunk_size = 2
        expected = [["1.1.1.1", "2.2.2.2"], ["3.3.3.3", "4.4.4.4"]]
        self.assertEqual(chunk_ips(ips, chunk_size=chunk_size), expected)

    def test_chunk_ips_basic_uneven_division(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4", "5.5.5.5"]
        chunk_size = 2
        expected = [["1.1.1.1", "2.2.2.2"], ["3.3.3.3", "4.4.4.4"], ["5.5.5.5"]]
        self.assertEqual(chunk_ips(ips, chunk_size=chunk_size), expected)

    def test_chunk_ips_size_larger_than_list(self):
        ips = ["1.1.1.1", "2.2.2.2"]
        chunk_size = 5
        expected = [["1.1.1.1", "2.2.2.2"]] # Should return one chunk with all IPs
        self.assertEqual(chunk_ips(ips, chunk_size=chunk_size), expected)

    def test_chunk_ips_size_equal_to_list_size(self):
        ips = ["1.1.1.1", "2.2.2.2"]
        chunk_size = 2
        expected = [["1.1.1.1", "2.2.2.2"]]
        self.assertEqual(chunk_ips(ips, chunk_size=chunk_size), expected)

    def test_chunk_ips_size_one(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        chunk_size = 1
        expected = [["1.1.1.1"], ["2.2.2.2"], ["3.3.3.3"]]
        self.assertEqual(chunk_ips(ips, chunk_size=chunk_size), expected)

    def test_chunk_ips_size_zero_or_none_default_behavior(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        # Current implementation: chunk_size=0 (or default) means one large chunk.
        expected_one_chunk = [ips]
        self.assertEqual(chunk_ips(ips, chunk_size=0), expected_one_chunk)
        self.assertEqual(chunk_ips(ips), expected_one_chunk) # Test default chunk_size

    def test_chunk_ips_empty_ip_list(self):
        ips = []
        self.assertEqual(chunk_ips(ips, chunk_size=2), [])
        self.assertEqual(chunk_ips(ips, chunk_size=0), [])
        self.assertEqual(chunk_ips(ips, custom_ranges=[["1.1.1.1"]]), []) # If ips is empty, custom_ranges ignored. This is current behavior.

    def test_chunk_ips_with_custom_ranges_provided(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4"] # These IPs are ignored if custom_ranges is used
        custom_ranges = [["10.0.0.1"], ["10.0.0.2", "10.0.0.3"]]
        self.assertEqual(chunk_ips(ips, chunk_size=2, custom_ranges=custom_ranges), custom_ranges)

    def test_chunk_ips_with_empty_custom_ranges(self):
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        custom_ranges = [] # Empty custom_ranges list
        # Should fall back to default chunking logic based on chunk_size
        expected_chunk_size_2 = [["1.1.1.1", "2.2.2.2"], ["3.3.3.3"]]
        self.assertEqual(chunk_ips(ips, chunk_size=2, custom_ranges=custom_ranges), expected_chunk_size_2)

        expected_chunk_size_0 = [ips] # single chunk
        self.assertEqual(chunk_ips(ips, chunk_size=0, custom_ranges=custom_ranges), expected_chunk_size_0)

    def test_chunk_ips_with_custom_ranges_and_empty_ips(self):
        ips = []
        custom_ranges = [["10.0.0.1"], ["10.0.0.2", "10.0.0.3"]]
        # If main `ips` list is empty, `chunk_ips` returns `[]` immediately, regardless of custom_ranges.
        self.assertEqual(chunk_ips(ips, custom_ranges=custom_ranges), [])


if __name__ == "__main__":
    # This allows running the tests directly from this file: python tests/test_ip_handler.py
    # It's also discoverable by `python -m unittest discover tests` from project root.
    unittest.main()
```
