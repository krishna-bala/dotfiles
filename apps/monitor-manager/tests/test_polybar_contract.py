"""The env-var contract between the reconciler and the polybar config.

The reconciler launches each bar with MONITOR, FONT_0/FONT_1, and
MODULES_LEFT/CENTER/RIGHT in its environment, and the tracked polybar
config reads them back with ${env:NAME:fallback}. Neither side used to
name the other; this test does, so renaming a variable on one side fails
here instead of producing a bar with the wrong font at the next login.
"""

import re
from pathlib import Path

from monitor_manager.reconciler import POLYBAR_ENV_VARS, bar_env
from monitor_manager.state.desired import DesiredBar

# apps/monitor-manager/tests -> repo root -> the x11 module's polybar config
POLYBAR_CONFIG = Path(__file__).resolve().parents[3] / "modules" / "x11" / "polybar" / "shades"

# What the reconciler exports; the polybar config may not read anything
# outside this set (plus the host values below).
EMITTED = set(POLYBAR_ENV_VARS)

# Machine values bspwmrc exports from ~/.config/dotfiles/host.env
# (hosts/defaults.env in the repo); these are allowed too.
HOST_ENV = {"BACKLIGHT_CARD", "BATTERY", "ADAPTER"}


def _env_lookups() -> set:
    names = set()
    for ini in POLYBAR_CONFIG.glob("*.ini"):
        names.update(re.findall(r"\$\{env:([A-Z0-9_]+)", ini.read_text()))
    return names


def test_polybar_config_reads_only_variables_something_exports():
    assert POLYBAR_CONFIG.is_dir(), POLYBAR_CONFIG
    unknown = _env_lookups() - EMITTED - HOST_ENV
    assert not unknown, f"polybar config reads env vars nothing sets: {sorted(unknown)}"


def test_polybar_config_reads_every_variable_the_reconciler_emits():
    missing = EMITTED - _env_lookups()
    assert not missing, f"reconciler exports vars the polybar config ignores: {sorted(missing)}"


def test_reconciler_emits_exactly_the_documented_set():
    bar = DesiredBar(
        output="DP-1",
        orientation="horizontal",
        font_size=16,
        modules_left="launcher workspaces",
        modules_center="date time",
        modules_right="network tray",
    )
    env = dict(bar_env(bar, owns_tray=True))
    assert set(env) == EMITTED
    assert env["MONITOR"] == "DP-1"
    assert env["MODULES_RIGHT"] == "network tray"
    assert dict(bar_env(bar, owns_tray=False))["MODULES_RIGHT"] == "network"
