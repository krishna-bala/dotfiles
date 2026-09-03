# dotfiles

Personal dotfiles for four kinds of machine - a headless server, a
workstation, and a workstation running a bspwm-based X11 desktop - installed
via [Dotbot](https://github.com/anishathalye/dotbot) one module at a time.
A machine picks a **role**; a role is a list of **modules**; a module is
one tool's config plus the provisioning that makes it work.

```sh
git clone --recurse-submodules https://github.com/krishna-bala/dotfiles ~/.dotfiles
cd ~/.dotfiles
./provision.sh --roles server   # installs pinned tooling for that role
./install --roles server        # links that role's configs into $HOME
```

The selection is saved to `~/.config/dotfiles/roles`, so afterwards a bare
`./provision.sh` / `./install` re-applies it. Both are safe to re-run.
`./doctor` checks a machine against that selection without changing
anything: every link points into the checkout, rendered files exist, each
pinned tool is at or above its pin, and which overlay seams are present.

## Roles

| Role | What it is | Modules |
|---|---|---|
| `server` | a headless box reached over ssh | cli-tools bash git tmux starship nvim agents |
| `workstation` | a machine someone sits at, any desktop | server + kitty bazel node go typst |
| `desktop` | a workstation running this repo's bspwm/X11 stack | workstation + x11 |

Roles nest (`roles/workstation` starts with `@server`). Modules outside any
role are picked per host: `./install --roles desktop,wacom`. A module can
declare what it needs (`modules/x11/requires` names `kitty` and
`cli-tools`), and a selection that leaves a requirement out is refused up
front instead of failing at a hotkey.

## Layout

```
install            links the selected modules' configs (dotbot, one pass per module)
provision.sh       runs the selected modules' provision.sh in role order
doctor             read-only check of links, renders, pins, and seams
roles/             server, workstation, desktop - one module name per line
modules/<name>/    install.conf.yaml (dotbot links, sources relative to the module)
                   provision.sh     (pinned + sha256-verified tooling; standalone-runnable)
                   requires         (optional: modules this one cannot work without)
hosts/             per-machine values (see below)
apps/              applications that live here but are not dotfiles
lib/               provision-lib.sh (pins, sha256, apt), roles.sh, common.sh,
                   dotbot-plugins/render.py
docs/              the desktop PRD and AirPods-on-Linux notes
dotbot/            the Dotbot submodule
```

Modules:

- `bash`, `git`, `tmux`, `starship` - the shell. `tmux/config/` is the
  whole `~/.tmux` (plugins are submodules under it).
- `cli-tools` - fzf, ripgrep, fd, lsd, lazygit, jq, uv, glab; and
  `bin/clipimg`, the remote-side half of kitty's clipboard kitten.
- `nvim` - neovim plus the rust toolchain and tree-sitter CLI its config
  (a separate repo) builds with.
- `node`, `go`, `typst`, `bazel` - language toolchains and completions.
- `kitty` - the terminal emulator and its font. Client-side: not on servers.
- `agents` - `AGENTS.md`, linked to `~/.claude/CLAUDE.md` and
  `~/.codex/AGENTS.md`, plus the Claude Code status-line script.
- `x11` - bspwm, sxhkd, polybar (with rofi themes), picom, dunst,
  redshift, `Xresources`, the `swapescape` user unit, `lockscreen`,
  `desktop-session-log`. These stay together because sxhkd's hotkeys and
  polybar's toggle scripts reference bspwm's installed paths directly.
- `wacom` - one tablet's `xsetwacom` mapping; per-host.

Applications:

- `apps/monitor-manager/` - the EDID-based monitor-profile system bspwmrc
  runs at login (Python, with its own tests, lockfile, and `CLAUDE.md`).
  `modules/x11/provision.sh` installs it as a `uv tool` so `monitor-manager`
  is on `PATH`; the profiles it applies stay config, in
  `modules/x11/bspwm/profiles/`.

## Per-machine values

Everything is a symlink except a handful of values that genuinely differ
per machine - a panel's DPI, redshift's location, polybar's backlight and
battery names, the wifi interface to fall back to. Those are merged by
`./install` from three layers into `~/.config/dotfiles/host.env`, later
layers winning:

1. `hosts/defaults.env` - tracked, complete
2. `hosts/<hostname>.env` - tracked, for machines it's fine to describe here
3. `~/.config/dotfiles/local.env` - untracked; the private overlay's seam

Templates (`*.tmpl`, applied with the `render:` directive in a module's
`install.conf.yaml`) substitute `${NAME}` from that file and are copied,
not linked; `bspwmrc` exports it into the desktop session for polybar's
`${env:NAME:fallback}` lookups.

## Machine-local overlay

A private overlay (a company meta-repo, say) layers on top of this repo
without forking it through untracked files each config sources last, so the
overlay wins:

| Seam | Read by | For |
|---|---|---|
| `~/.config/dotfiles/env.sh` | every bash shell, before the interactive gate | PATH, proxies, `EDITOR` - things `ssh host cmd` and cron must also see |
| `~/.bashrc.local` | interactive bash, last | prompt and shell tweaks |
| `~/.bash_aliases.local` | interactive bash, after all tool blocks | aliases and functions |
| `~/.gitconfig.local` | git, included last | identity, credential helpers, any override |
| `~/.tmux.conf.local` | tmux, before tpm loads | bindings, extra `@plugin`s |
| `~/.config/kitty.local.conf` | kitty, last | font size, theme |
| `~/.config/dotfiles/local.env` | `./install` | per-machine values (above) |
| `~/.config/bspwm/profiles.d/*.yaml` | monitor-manager | private monitor profiles, shadowing tracked ones by name |

None of these are shipped here; where absent, every reference is a no-op.
`./install` runs no `clean:` pass, so a parent meta-repo that consumes this
repo as a submodule can own that single pass without conflicts.

## Provisioning

Assumes a Debian-family distro on x86_64 (tested on Ubuntu 22.04 and
24.04): package names are apt's, and the pinned release archives are
`x86_64`/`amd64` Linux builds. Every upstream download names an exact
version and is verified against a recorded sha256; the pin is a floor, so a
newer copy installed by hand is kept and reported rather than rolled back
(`FORCE_PINS=1` restores exact pins for a run). See `CLAUDE.md` for the
policy in full.

Where a distro package is new enough it is used instead of a source build:
polybar needs >= 3.7.0 (`internal/tray`) and picom >= 13, which Ubuntu
22.04 lacks and later releases may have.

## CI

`.github/workflows/ci.yml` installs the `server` role from scratch in
Ubuntu 22.04 and 24.04 containers (non-root user, `./provision.sh` +
`./install`), checks the shell and tools work, and re-runs both to prove a
converged machine is a no-op; tests `provision-lib.sh`'s sha256 refusal
and role resolution; runs the monitor-manager suite; and shellchecks every
tracked script.
