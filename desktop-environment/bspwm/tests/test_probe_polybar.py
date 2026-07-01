"""Tests for polybar probe."""

import unittest

from lib.probe.polybar import PolybarProbe


class _FakeRunner:
    def __init__(self, pids):
        self._pids = pids

    def list_polybar_pids(self):
        return self._pids


class TestPolybarProbe(unittest.TestCase):
    def test_no_polybar_running(self):
        self.assertEqual(PolybarProbe(runner=_FakeRunner(())).read(), ())

    def test_one_polybar_running(self):
        self.assertEqual(PolybarProbe(runner=_FakeRunner((1234,))).read(), (1234,))

    def test_multiple_polybar_running(self):
        self.assertEqual(
            PolybarProbe(runner=_FakeRunner((1234, 5678, 9012))).read(),
            (1234, 5678, 9012),
        )


if __name__ == "__main__":
    unittest.main()
