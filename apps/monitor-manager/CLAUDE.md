# CLAUDE.md - monitor-manager

EDID-based monitor-profile management for bspwm. An application that lives
in the dotfiles repo (`apps/monitor-manager`) but is not a dotfile: it has
its own package, tests, and lockfile, and is installed onto `PATH` as
`monitor-manager` by `modules/x11/provision.sh` (`uv tool install
--editable`, constrained to `uv.lock`). The config it applies - the profile
YAMLs, `bspwmrc`, the sxhkd bindings, polybar - stays in `modules/x11/`.

## Commands

```bash
uv run pytest                                 # all tests
uv run pytest tests/test_display.py -v        # specific test
uv run monitor-manager <command>              # run the CLI from the checkout
uv lock                                       # after changing dependencies
```

On an installed machine `monitor-manager` is on `PATH` and imports this
checkout (editable), so code changes take effect without re-provisioning;
dependency changes need `./provision.sh --modules x11` (or the uv tool
install line from it) to rebuild the tool venv.

## Architecture

### Boot sequence (modules/x11/bspwm/bspwmrc)

Ordered startup - each step depends on the previous:

1. **Wait for X** - polls `xrandr --query` for connected monitors (max 6s)
2. **Apply monitor profile** - `monitor-manager match --best` (stderr ->
   log, exit code checked), then `apply-all --force`. Fallback:
   `xrandr --auto` + notify-send
3. **Configure bspwm** - borders, gaps, window rules (defaults; profiles override these)
4. **Launch background apps** - picom, nitrogen, redshift, nm-applet, blueman, protonvpn (all pgrep-guarded)
5. **Start sxhkd LAST** - `pkill` + 200ms wait + launch. Must be last so X key grabs succeed after monitor setup

bspwmrc first exports `~/.config/dotfiles/host.env` (per-machine values
merged by `./install`), which is where polybar's `${env:BACKLIGHT_CARD}`
and friends and `network-env.sh`'s fallback interface come from.

Logs: `$XDG_STATE_HOME/bspwm/bspwm.log`, `$XDG_STATE_HOME/sxhkd/sxhkd.log`,
and `$XDG_STATE_HOME/desktop-session/boot-<boot-id>.log`. The latter captures
filtered GNOME/Mutter, bspwm, Xorg, GDM, NVIDIA, monitor, and failed-unit
events for both GNOME autostart and bspwm startup.

### Package layout (monitor_manager/)

Service-oriented architecture with Protocol-based dependency injection for testability.

**Services:**
- `DisplayService` (display.py) - xrandr parsing and EDID extraction (read-only; application happens in the executor)
- `ProfileService` (profile.py) - YAML loading with defaults.yaml merge, validation, EDID-based matching (+100/monitor match, -10/extra monitor). Reads a **search path**: `~/.config/bspwm/profiles` (the tracked profiles, linked by `./install`) then `~/.config/bspwm/profiles.d` (a real directory for an overlay's private profiles; a name there shadows a tracked one; `defaults.yaml` comes from the first directory that has one)
- `MonitorManagerCoordinator` (coordinator.py) - resolves profile aliases to actual hardware outputs via EDID->output mapping
- `SafetyService` (safety.py) - pre-apply state snapshots (per-monitor desktop lists) to `$XDG_STATE_HOME/bspwm-monitor-manager/snapshots/`, pruned to the newest 20 per kind
- Default-profile preference (preferences.py) - `$XDG_STATE_HOME/bspwm-monitor-manager/state.json`
- `InteractiveMenu` (interactive.py) - simple-term-menu TUI for profile selection

**Reconciliation pipeline** (the current apply path, used by `plan` and `apply-all`):
- `probe/` - read-only probes (xrandr, bspc, polybar) assembling a `HardwareState`
- `state/` - frozen dataclasses for hardware state, plus `compile_desired(profile, alias_to_output)` -> `DesiredState` (pure)
- `reconciler.py` - diffs current vs desired into a typed `Plan` of ops, simulating each op against shadow state. `bar_env()` / `POLYBAR_ENV_VARS` are the one place the polybar env contract is written down
- `executor.py` - runs the Plan, minting symbolic refs ($M_n) into real ids at runtime
- `renderer.py` - renders the same Plan for preview and execution
- `simulate.py`, `ops.py`, `plan.py` - pure transition function, op types, merge policies

**CLI entry point:** `cli.py` (`monitor-manager` console script, ~600 lines). Commands:
- Read-only: `detect`, `validate`, `list`, `match` (with `--best` for scripting)
- State: `set-default`, `clear-default`
- Planning: `plan` (dry-run; renders the same Plan apply-all would run)
- Apply: `apply-all` - the single apply path, via the reconciliation pipeline
- Interactive: `interactive` (TUI; plan preview and apply both use the reconciliation pipeline via `apply_profile()`)

**apply-all sequencing:** After xrandr ops, `WaitForBspwmMonitor` polls for up to 7.5s for expected outputs to appear in bspwm before bspc desktop ops run.

### Profile system

YAML files in `modules/x11/bspwm/profiles/` (tracked) and
`~/.config/bspwm/profiles.d/` (overlay). Four sections each:

```yaml
detection:     # EDID fingerprints for hardware matching
display:       # xrandr config (resolution, position, rotation, scale, primary)
window_manager: # workspace distribution per monitor + bspwm settings
ui:            # polybar bars per monitor (orientation, font_size, modules)
```

Profiles use logical aliases (laptop, main, vertical) resolved to actual outputs at runtime.

Profile matching uses the ACPI lid state when available and skips an
enabled-laptop profile while the lid is closed. It also falls back to
requiring an active Xrandr mode when the lid state is unavailable. That
check is the only thing separating a docked profile from its clamshell
twin, and a work-laptop profile from a personal one that shares the same
external monitors.

### Shell scripts (modules/x11/bspwm/scripts/)

- `apply-auto.sh` - re-detect topology, apply best profile via reconciliation (super+alt+r, super+alt+shift+p)
- `smart_focus.sh` - focus node in direction, fall through to monitor at edge
- `smart_send.sh` - swap with neighbor node, or move to adjacent monitor
- `smart_resize.sh` - expand toward direction if neighbor exists, else contract
- `toggle_polybar.sh` - show/hide polybar; saves/restores per-monitor top_padding in `$XDG_STATE_HOME/bspwm/`
- `monocle-border.sh` - event-driven border width (thick in monocle, thin otherwise)
- `monitor-switch.sh` - launches the interactive TUI in a kitty window
- `network-env.sh` - sourced by bspwmrc and apply-auto.sh; exports `NETWORK_INTERFACE` / `NETWORK_LABEL`

Developer tooling for this app's fixtures lives with the app, in
`apps/monitor-manager/scripts/`: `capture-fixture.sh` captures xrandr/bspc
state as test fixtures and `redact-edid.py` strips EDID bytes before they
touch disk.

### Polybar

adi1090x "shades" theme. Single `[bar/main]` definition, customized per-monitor via env vars from the reconciler. `pin-workspaces = true` - each bar shows only its monitor's desktops.

The env contract: the reconciler launches each bar with `MONITOR`,
`FONT_0`/`FONT_1`, and `MODULES_LEFT/CENTER/RIGHT`; the polybar config
reads them with `${env:NAME:fallback}`. `tests/test_polybar_contract.py`
holds both sides to that list, so renaming one side fails in CI.

The tray is the `internal/tray` module, which needs polybar >= 3.7.0 -
22.04 packages 3.5.7, where it silently does nothing, so
`modules/x11/provision.sh` builds a pinned 3.7.2 from source there (and
takes the distro package where it is new enough). Profiles do not name
`tray` in their modules: two bars listing it race for tray clients, so
`_reconcile_polybar` appends it to the right block of the bar on the
`primary` output and strips it from every other bar. A profile with no
`primary: true` display therefore gets no tray at all. The tray is destroyed
and rebuilt on every polybar restart, and blueman-applet only registers its
icon at startup, which is why apply-auto.sh restarts it afterwards (nm-applet
re-registers on its own).

`network-env.sh` exports `NETWORK_INTERFACE` (whichever interface holds the
default route, else `NETWORK_FALLBACK_IFACE` from host.env), and on a
wired link `NETWORK_LABEL` (its NetworkManager connection name). Both are
read by the network module's `polybar/shades/scripts/network-label.sh`,
a custom/script module rather than polybar's `internal/network`. Wi-Fi leaves
`NETWORK_LABEL` unset: the script resolves the live SSID and signal strength
itself, so roaming needs no bar restart.

### sxhkd (modules/x11/sxhkd/sxhkdrc)

Key bindings reference `~/.config/bspwm/scripts/` (symlinked by Dotbot). Notable:
- `super+shift+x` - interactive monitor manager
- `super+alt+shift+p` - re-apply current profile (restarts polybar) via apply-auto.sh
- `super+alt+p` - toggle polybar visibility via toggle_polybar.sh
- `super+shift+F1` - emergency laptop display recovery (enables any connected eDP-* output)

## Testing

~210 tests across 23 files. Unit tests mock hardware via Protocol
implementations (MockXrandrExecutor, MockBspcExecutor, MockPolybarExecutor).
Integration tests use xrandr fixture files in `tests/fixtures/xrandr/`; one
safety-snapshot test shells out to real `xrandr` and skips without a
`DISPLAY` (CI runs it under `xvfb-run`).

Tests never read the tracked profiles (production config with real-hardware
EDID pins); they use the synthetic profiles in `tests/fixtures/profiles/`
instead. The one exception is `test_tracked_profiles.py`, which validates
that the real profiles in `modules/x11/bspwm/profiles/` parse, merge with
defaults.yaml, pass validation, and pin only hashed EDIDs. The fixture
profiles' laptop edid must stay equal to the hash of the synthetic EDID in
`tests/fixtures/xrandr/personal-solo-props.txt`; test_coordinator asserts this.

```bash
uv run pytest                                                   # all
uv run pytest tests/test_profile.py -v                          # specific
uv run pytest --cov=monitor_manager --cov-report=term-missing   # coverage
```

## Known issues

- Rollback files are still text instructions; a serialised inverse Plan
  (true plan-based rollback) remains future work
- `cli.py` is exercised only indirectly (test_cli.py mirrors its logic
  rather than calling it), and the lid-state branch of profile matching has
  no unit test
- `rich` is a declared dependency nothing imports

## xrandr constraints (learned the hard way, 2026-06-11)

- All xrandr changes go out as ONE invocation (`XrandrApplyLayout` op) with
  an explicit `--fb`. Sequential per-output calls wedge the modesetting
  driver: once any CRTC has a scale transform active, every subsequent
  screen resize fails with RRSetScreenSize BadMatch - even a bare
  `xrandr --fb`. Recovery from that state requires resetting the scaled
  output to `--scale 1x1` first.
- The probe reads xrandr's summary line, which reports post-transform
  geometry and no scale; the reconciler projects desired (mode, scale,
  rotation) into that space (`_effective_mode`) before diffing, otherwise
  scaled outputs re-modeset on every apply.
- bspwm refuses to remove a monitor's last desktop, but `bspc monitor -r`
  takes the monitor down together with one remaining empty desktop, so the
  cleanup phase leaves one behind for it.
