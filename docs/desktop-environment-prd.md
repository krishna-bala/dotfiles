# PRD: Desktop Environment Consolidation (bspwm / polybar / sxhkd / rofi)

Status: draft for review
Scope: bspwm, monitor-manager, polybar, rofi, sxhkd, picom, dunst, redshift,
and provisioning of all of the above
Out of scope: kitty internals, tmux, nvim (separate repo), shell config

## 1. The user, and what they actually need

This system has exactly one user: a single engineer on a corporate-managed
Linux laptop that moves between a few physical contexts (office dock with
dual monitors, home dock, secondary office, laptop alone). The repo is
co-maintained with Claude Code agents, so its legibility is part of the
product. Everything below is derived from that user's needs, ranked:

N1. Docking just works. Plugging in or unplugging produces the right
    layout, fast, without fiddling. When it fails, recovery must be
    possible blind: the failure mode is a black screen, which is precisely
    when scripts and muscle memory are all you have.

N2. Every hotkey does what it says. A binding that silently does nothing
    (missing binary, dead daemon) erodes trust in all of them. The
    keyboard surface should contain only working keys.

N3. The machine is rebuildable in an afternoon. A managed laptop can be
    reimaged or replaced on short notice. provision.sh + ./install must
    reproduce the entire working environment, including the lock screen,
    which on a corporate machine is a security requirement rather than a
    convenience.

N4. One knob, one edit. Changing a gap, border, font, or accent color
    should be a single-file change. Today several of these are 5-6 file
    edits with drift risk.

N5. The repo stays legible. Dead code, stale docs, and duplicated config
    mislead both the user-as-future-maintainer and the agents that work in
    this repo. Accurate CLAUDE.md files and an absence of vestigial paths
    are functional requirements here, because agents act on them.

Explicitly not needs: portability to other users or machines, Wayland,
visual novelty (color-cycling machinery, theme variants), or any feature
the user has not pressed a key for in months. The deep dive found several
of those; the default disposition is removal.

## 2. What exists, mapped to the needs

The architecture is strong where it matters most. N1 is substantially
solved: the monitor-manager reconciliation pipeline (probe to desired-state
to plan to executor, ~950 LOC CLI + ~3,850 LOC lib + 4,588 LOC tests) is
well-designed, and six EDID-matched profiles cover all physical contexts.
This PRD deliberately builds around that core rather than reworking it.

The gaps are at the edges, and each maps to an unmet need:

| Finding | Evidence | Need violated |
|---|---|---|
| provision.sh installs zero desktop packages (no bspwm, sxhkd, polybar, rofi, picom, dunst, lock screen, audio/brightness/screenshot tools) | provision.sh apt list | N3 |
| ~20 binaries referenced by hotkeys/autostart are unprovisioned (pactl, brightnessctl, scrot, i3lock-fancy, redshift, dunstctl, nitrogen, nm-applet, blueman, mpc, amixer...) | sxhkdrc:152-242, bspwmrc:107-118, powermenu.sh | N2, N3 |
| voice-daemon hotkey targets a daemon that exists nowhere in the repo | sxhkdrc:201 | N2 |
| Emergency display recovery hardcodes eDP-1-1 | sxhkdrc:242 | N1 (fails exactly when needed) |
| Rollback files restore bspc state only for single-monitor setups | lib/safety.py:174-186 | N1 |
| toggle_polybar.sh hardcodes top_padding 60 regardless of profile bar size | bspwm/scripts/toggle_polybar.sh:35 | N2 |
| Two apply generations coexist; superseded apply-display/wm/ui still wired to super+shift+p | monitor-manager.py, sxhkdrc:213 | N5, N1 |
| bspwm settings repeated identically in all 6 profiles; no defaults | profiles/*.yaml | N4 |
| Font family declared in 5+ places at sizes 12-18; three color palettes drifting (polybar/rofi blue-gray, kitty Tokyo Night Storm, #629dc8 accent in picom/bspwm) | colors.ini, colors.rasi, rasi themes, dunstrc, picom.conf | N4 |
| Dead/vestigial: polybar launch.sh (sources a deleted script), smart_xrandr.sh.old, bspwmrc.old, preview.*, networkmenu.rasi, random.sh, pywal.sh, [bar/tray], kitty launch.sh dead branch, color-switch machinery (19 variants x light/dark), Arch-style updates module | various (deep-dive reports) | N5 |
| Stale docs: bspwm/CLAUDE.md lists textual dep (already removed) and 4x render duplication (now 2x) | bspwm/CLAUDE.md | N5 |
| Display-render block copy-pasted; inline ApplyArgs mock | monitor-manager.py:337-351, 701-715, 750-758 | N5 |
| Snapshots and apply-auto.log unbounded; smart_* scripts log to /tmp | lib/safety.py, scripts | N5 (slow rot) |

## 3. Goals

1. A fresh machine reaches a fully working session via provision.sh +
   ./install, lock screen included (N3).
2. Every binding in sxhkdrc has a working target; recovery hotkeys work on
   any laptop output (N1, N2).
3. One apply path for monitor changes, with rollback that covers
   multi-monitor states (N1, N5).
4. Shared visual and behavioral values defined once (N4).
5. No dead code; CLAUDE.md files accurate (N5).

## 4. Non-goals

- No hotplug daemon; applying a profile stays an explicit action (login,
  hotkey, CLI). Unchanged from bspwm/PRD.md.
- No GUI configuration tools, no other window managers, no Wayland.
- No general-purpose theming framework. The fix for palette drift is
  consolidation and deletion, sized to one user, and stops short of a
  generator if a shared include file suffices.
- No preserving features no one uses (color cycling, updates module,
  network rofi menu) for completeness's sake.

## 5. Workstreams

Ordered by need priority, then by unblocking value. Each is independently
shippable as one PR, gated on `uv run pytest` (bspwm/) and a container
`./install` run.

### WS1: Trust the keyboard (N2, N1) - small, do first

- Remove the voice-daemon binding (or point it at a real daemon if one
  exists on the machine outside the repo; see 7.1).
- Emergency recovery: enable the first connected eDP-* output from xrandr
  instead of hardcoded eDP-1-1; keep it dependency-free so it works blind.
- toggle_polybar.sh: derive top_padding from the running bar's height (or
  the active profile) instead of hardcoded 60.
- Rewire super+shift+p from legacy apply-ui to the reconciliation path.
- Unify all sxhkdrc script invocations on ~/.config/bspwm/scripts/.
Acceptance: every sxhkdrc binding's target exists and works; recovery and
bar-toggle behave correctly on every profile.

### WS2: Delete the dead (N5) - zero-risk shrink

Delete: polybar/shades/launch.sh, smart_xrandr.sh.old, bspwmrc.old,
preview.ini/preview.sh, networkmenu.rasi, random.sh, pywal.sh,
color-switch.sh + colors-dark.sh/colors-light.sh (pending 7.2), the
updates/checkupdates module wiring, the unused [bar/tray] block, the dead
resolution branch in kitty/launch.sh. Correct bspwm/CLAUDE.md known-issues
(textual entry stale; render duplication count). Acceptance: rg finds no
references to deleted files; CLAUDE.md claims verified against code.

### WS3: Rebuildable machine (N3)

Add the desktop stack to provision.sh in the existing idempotent, pinned
style: bspwm, sxhkd, polybar, rofi, picom, dunst, redshift, brightnessctl,
pulseaudio-utils, scrot, libnotify-bin, network-manager-gnome, blueman, a
lock screen (per 7.3), xinput, and wallpaper handling (nitrogen or drop it,
per 7.1). Apt versions on Ubuntu 24.04 are acceptable for all of these;
none need source builds. Acceptance: fresh VM/container provision +
install + bspwm login produces working bar, launcher, notifications,
volume/brightness keys, screenshots, and lock.

### WS4: One knob, one edit (N4)

- Profile defaults: compile_desired gains a defaults layer (format per
  7.4); the 6 profiles shrink to deltas. Changing window_gap becomes a
  one-line edit.
- Single accent/palette source for the values that must agree (bspwm
  border colors, picom shadow, polybar/rofi palette, dunst urgency
  colors), via one include/generated file. Font family + sizes declared
  once. Kitty's theme stays separate unless 7.5 says otherwise.
Acceptance: gap/border/accent/font changes are each a one-file edit;
compiled DesiredState for existing profiles is byte-identical before and
after the defaults migration (equivalence test).

### WS5: One apply path, real rollback (N1, N5)

- Retire apply-display/apply-wm/apply-ui (disposition per 7.6).
- Extract the duplicated display-render block; replace the ApplyArgs mock
  with a plain function call.
- Plan-based rollback: serialize the executed Plan, generate its inverse,
  cover multi-monitor states (the "PR 5" already noted in cmd_apply_all).
- Bound state: prune snapshots to last 20, rotate apply-auto.log, move
  smart_* logs to $XDG_STATE_HOME/bspwm/.
Acceptance: CLI help shows one apply path; a 2-monitor rollback restores
desktops in test; state dirs bounded after repeated applies.

## 6. Sequencing

WS1 (keyboard trust, smallest) -> WS2 (deletions) -> WS3 (provisioning,
validates on fresh container) -> WS4 (defaults/palette) -> WS5
(consolidation + rollback). WS1 and WS2 could land same-day; WS5 is the
only one touching the reconciliation core and goes last, protected by the
existing test suite plus the WS4 equivalence tests.

## 7. Decisions (resolved 2026-06-11)

1. voice-daemon: remove the binding. nitrogen: keep, and provision it in
   WS3.
2. Color-cycling machinery: delete.
3. Lock screen: plain i3lock behind a small wrapper, provisioned in WS3.
4. Defaults format: profiles/defaults.yaml merged at load.
5. Theme direction: keep the kitty/polybar split; fix only the
   rofi/polybar duplication.
6. Legacy CLI commands: delete outright.
7. personal-* profiles: keep.

## 8. Risks

- Desktop apt packages pull large dependency trees on a managed machine;
  review the WS3 package list against the security stack before merging.
- WS4/WS5 touch compile_desired and the executor; mitigated by the 4.5k
  LOC test suite and the byte-equivalence test added before migration.
- Visual outcomes (WS4 palette, bar padding) cannot be fully verified
  headless; final check happens on the workstation after merge.
