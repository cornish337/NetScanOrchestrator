import unittest

from src.planner import split_fixed_size, split_binary


class TestPlanner(unittest.TestCase):
    def test_split_fixed_size(self):
        items = list(range(1, 8))
        self.assertEqual(
            split_fixed_size(items, 3),
            [[1, 2, 3], [4, 5, 6], [7]],
        )

    def test_split_binary_even(self):
        items = list(range(1, 9))
        self.assertEqual(
            split_binary(items, 2),
            [[1, 2], [3, 4], [5, 6], [7, 8]],
        )

    def test_split_binary_uneven(self):
        items = list(range(1, 6))
        self.assertEqual(
            split_binary(items, 2),
            [[1, 2], [3], [4, 5]],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

