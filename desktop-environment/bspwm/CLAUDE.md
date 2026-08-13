# CLAUDE.md - BSPWM + Monitor Manager

## Commands

**Python: ALWAYS use `uv run`**

```bash
uv run python monitor-manager.py <command>   # CLI
uv run pytest                                 # all tests
uv run pytest tests/test_display.py -v        # specific test
```

**bspwmrc uses `.venv/bin/python` directly** (intentional — avoids `uv` startup cost at boot). If `.venv` doesn't exist, `uv sync` first.

## Architecture

### Boot Sequence (bspwmrc)

Ordered startup — each step depends on the previous:

1. **Wait for X** — polls `xrandr --query` for connected monitors (max 6s)
2. **Apply monitor profile** — `match --best` (stderr → log, exit code checked), then `apply-all --force`. Fallback: `xrandr --auto` + notify-send
3. **Configure bspwm** — borders, gaps, window rules (defaults; profiles override these)
4. **Launch background apps** — picom, nitrogen, redshift, nm-applet, blueman, protonvpn (all pgrep-guarded)
5. **Start sxhkd LAST** — `pkill` + 200ms wait + launch. Must be last so X key grabs succeed after monitor setup

Logs: `$XDG_STATE_HOME/bspwm/bspwm.log`, `$XDG_STATE_HOME/sxhkd/sxhkd.log`,
and `$XDG_STATE_HOME/desktop-session/boot-<boot-id>.log`. The latter captures
filtered GNOME/Mutter, bspwm, Xorg, GDM, NVIDIA, monitor, and failed-unit
events for both GNOME autostart and bspwm startup.

### Monitor Manager (Python)

Service-oriented architecture with Protocol-based dependency injection for testability.

**Services:**
- `DisplayService` (lib/display.py) — xrandr parsing and EDID extraction (read-only; application happens in the executor)
- `ProfileService` (lib/profile.py) — YAML loading with profiles/defaults.yaml merge, validation, EDID-based matching (+100/monitor match, -10/extra monitor)
- `MonitorManagerCoordinator` (lib/coordinator.py) — resolves profile aliases to actual hardware outputs via EDID→output mapping
- `SafetyService` (lib/safety.py) — pre-apply state snapshots (per-monitor desktop lists) to `$XDG_STATE_HOME/bspwm-monitor-manager/snapshots/`, pruned to the newest 20 per kind
- Default-profile preference (lib/preferences.py) — `$XDG_STATE_HOME/bspwm-monitor-manager/state.json`
- `InteractiveMenu` (lib/interactive.py) — simple-term-menu TUI for profile selection

**Reconciliation pipeline** (the current apply path, used by `plan` and `apply-all`):
- `lib/probe/` — read-only probes (xrandr, bspc, polybar) assembling a `HardwareState`
- `lib/state/` — frozen dataclasses for hardware state, plus `compile_desired(profile, alias_to_output)` → `DesiredState` (pure)
- `lib/reconciler.py` — diffs current vs desired into a typed `Plan` of ops, simulating each op against shadow state
- `lib/executor.py` — runs the Plan, minting symbolic refs ($M_n) into real ids at runtime
- `lib/renderer.py` — renders the same Plan for preview and execution
- `lib/simulate.py`, `lib/ops.py`, `lib/plan.py` — pure transition function, op types, merge policies

**CLI entry point:** `monitor-manager.py` (~950 lines). Commands:
- Read-only: `detect`, `validate`, `list`, `match` (with `--best` for scripting)
- State: `set-default`, `clear-default`
- Planning: `plan` (dry-run; renders the same Plan apply-all would run)
- Apply: `apply-all` — the single apply path, via the reconciliation pipeline
- Interactive: `interactive` (TUI; plan preview and apply both use the reconciliation pipeline via `apply_profile()`)

**apply-all sequencing:** After xrandr ops, `WaitForBspwmMonitor` polls for up to 7.5s for expected outputs to appear in bspwm before bspc desktop ops run.

### Profile System

YAML files in `profiles/`. Four sections each:

```yaml
detection:     # EDID fingerprints for hardware matching
display:       # xrandr config (resolution, position, rotation, scale, primary)
window_manager: # workspace distribution per monitor + bspwm settings
ui:            # polybar bars per monitor (orientation, font_size, modules)
```

Profiles use logical aliases (laptop, main, vertical) resolved to actual outputs at runtime.

**Current profiles:** personal-solo (eDP-1), personal-home,
work-laptop-home, work-laptop-woodinville (laptop fallback enabled), and
work-laptop-woodinville-clamshell (external monitors only). Profile matching
uses the ACPI lid state when available and skips an enabled-laptop profile
while the lid is closed. It also falls back to requiring an active Xrandr mode
when the lid state is unavailable.

### Shell Scripts (scripts/)

- `apply-auto.sh` — re-detect topology, apply best profile via reconciliation (super+alt+r, super+alt+shift+p)
- `smart_focus.sh` — focus node in direction, fall through to monitor at edge
- `smart_send.sh` — swap with neighbor node, or move to adjacent monitor
- `smart_resize.sh` — expand toward direction if neighbor exists, else contract
- `toggle_polybar.sh` — show/hide polybar; saves/restores per-monitor top_padding in `$XDG_STATE_HOME/bspwm/`
- `monocle-border.sh` — event-driven border width (thick in monocle, thin otherwise)
- `monitor-switch.sh` — launches interactive TUI in kitty terminal
- `capture-fixture.sh` — captures xrandr/bspc state as test fixtures

### Polybar

adi1090x "shades" theme. Single `[bar/main]` definition, customized per-monitor via env vars from UIService. `pin-workspaces = true` — each bar shows only its monitor's desktops.

The tray is the `internal/tray` module, which needs polybar >= 3.7.0 — 22.04
packages 3.5.7, where it silently does nothing, so `desktop-environment/
provision.sh` builds a pinned 3.7.2 from source into `~/.local`. Profiles do
not name `tray` in their modules: two bars listing it race for tray clients,
so `_reconcile_polybar` appends it to the right block of the bar on the
`primary` output and strips it from every other bar. A profile with no
`primary: true` display therefore gets no tray at all. The tray is destroyed
and rebuilt on every polybar restart, and blueman-applet only registers its
icon at startup, which is why apply-auto.sh restarts it afterwards (nm-applet
re-registers on its own).

`scripts/network-env.sh`, sourced by bspwmrc and apply-auto.sh, exports
`NETWORK_INTERFACE` (whichever interface holds the default route) and
`NETWORK_LABEL` for the network module — the literal token `%essid%` on Wi-Fi
so polybar keeps it live, or a wired link's NetworkManager connection name,
since polybar renders `%essid%` as junk on a wired interface.

### sxhkd (../sxhkd/sxhkdrc)

Key bindings reference `~/.config/bspwm/scripts/` (symlinked by Dotbot). Notable:
- `super+shift+x` — interactive monitor manager
- `super+alt+shift+p` — re-apply current profile (restarts polybar) via apply-auto.sh
- `super+alt+p` — toggle polybar visibility via toggle_polybar.sh
- `super+shift+F1` — emergency laptop display recovery (enables any connected eDP-* output)

## Testing

200 tests across 21 files. Unit tests mock hardware via Protocol implementations (MockXrandrExecutor, MockBspcExecutor, MockPolybarExecutor). Integration tests use xrandr fixture files in `tests/fixtures/xrandr/`; one safety-snapshot test shells out to real `xrandr` and needs a display (use `xvfb-run` headless).

Tests never read the tracked `profiles/` directory (production config with real-hardware EDID pins); they use the synthetic profiles in `tests/fixtures/profiles/` instead. The one exception is `test_tracked_profiles.py`, which exists to validate that the real profiles parse, merge with defaults.yaml, and pass validation. The fixture profiles' laptop edid must stay equal to the hash of the synthetic EDID in `tests/fixtures/xrandr/personal-solo-props.txt`; test_coordinator asserts this.

```bash
uv run pytest                                      # all
uv run pytest tests/test_profile.py -v             # specific
uv run pytest --cov=lib --cov-report=term-missing  # coverage
```

## Known Issues

- Rollback files are still text instructions; a serialised inverse Plan
  (true plan-based rollback) remains future work

## xrandr Constraints (learned the hard way, 2026-06-11)

- All xrandr changes go out as ONE invocation (`XrandrApplyLayout` op) with
  an explicit `--fb`. Sequential per-output calls wedge the modesetting
  driver: once any CRTC has a scale transform active, every subsequent
  screen resize fails with RRSetScreenSize BadMatch — even a bare
  `xrandr --fb`. Recovery from that state requires resetting the scaled
  output to `--scale 1x1` first.
- The probe reads xrandr's summary line, which reports post-transform
  geometry and no scale; the reconciler projects desired (mode, scale,
  rotation) into that space (`_effective_mode`) before diffing, otherwise
  scaled outputs re-modeset on every apply.
- bspwm refuses to remove a monitor's last desktop, but `bspc monitor -r`
  takes the monitor down together with one remaining empty desktop, so the
  cleanup phase leaves one behind for it.
