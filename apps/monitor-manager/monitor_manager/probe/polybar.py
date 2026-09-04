"""Probe running polybar PIDs via pgrep."""

import subprocess
from typing import Optional, Protocol, Tuple


class PgrepRunner(Protocol):
    """Source of polybar PIDs (one per running instance)."""

    def list_polybar_pids(self) -> Tuple[int, ...]:
        ...


class SubprocessPgrepRunner:
    def list_polybar_pids(self) -> Tuple[int, ...]:
        try:
            result = subprocess.run(
                ["pgrep", "-x", "polybar"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return ()
        if result.returncode != 0:
            return ()
        return tuple(int(line) for line in result.stdout.split() if line.strip())


class PolybarProbe:
    """Reports running polybar PIDs."""

    def __init__(self, runner: Optional[PgrepRunner] = None):
        self._runner = runner or SubprocessPgrepRunner()

    def read(self) -> Tuple[int, ...]:
        return self._runner.list_polybar_pids()
