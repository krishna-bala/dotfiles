"""Tests for window-merge policies."""

import unittest

from lib.plan import PreserveByName, SpilloverModulo, SquashToFirst


class TestPreserveByName(unittest.TestCase):
    def setUp(self):
        self.p = PreserveByName()

    def test_name_match_routes_to_same_name(self):
        self.assertEqual(self.p.assign("w1", "5", ("1", "2", "3", "4", "5")), "5")

    def test_no_match_falls_back_to_first(self):
        # The personal-home → personal-solo case: source "11" has no target "11"
        # in (1..10); fallback policy says "go to first".
        self.assertEqual(
            self.p.assign("w1", "11", ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10")),
            "1",
        )

    def test_empty_targets_raises(self):
        with self.assertRaises(ValueError):
            self.p.assign("w1", "5", ())


class TestSquashToFirst(unittest.TestCase):
    def setUp(self):
        self.p = SquashToFirst()

    def test_always_first(self):
        self.assertEqual(self.p.assign("w1", "5", ("1", "2", "3")), "1")
        self.assertEqual(self.p.assign("w1", "1", ("a", "b")), "a")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            self.p.assign("w1", "5", ())


class TestSpilloverModulo(unittest.TestCase):
    def setUp(self):
        self.p = SpilloverModulo()

    def test_int_modulo(self):
        # 11 mod 3 = 2 → targets[2]
        self.assertEqual(self.p.assign("w1", "11", ("1", "2", "3")), "3")
        # 12 mod 3 = 0 → targets[0]
        self.assertEqual(self.p.assign("w1", "12", ("1", "2", "3")), "1")
        # 13 mod 3 = 1 → targets[1]
        self.assertEqual(self.p.assign("w1", "13", ("1", "2", "3")), "2")

    def test_non_numeric_falls_back_to_first(self):
        self.assertEqual(self.p.assign("w1", "named", ("a", "b", "c")), "a")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            self.p.assign("w1", "5", ())


if __name__ == "__main__":
    unittest.main()
