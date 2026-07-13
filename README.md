# dotfiles

Personal dotfiles: a shell/terminal/dev foundation plus a bspwm-based X11
desktop. Everything installs via [Dotbot](https://github.com/anishathalye/dotbot)
from the repo root; the desktop half is skippable with `--no-desktop`.

## Layout

Shell/terminal/dev foundation — these tools don't reference each other, so
each gets its own top-level directory:

- `bash/` — `bashrc`, `bash_aliases`, `profile`, `inputrc`,
  `bazel_completions.bash`
- `git/` — `gitconfig`, `gitmessage`, `git-prompt.sh`, `lazygit.yml`
- `tmux/` — `tmux.conf`, `settings.conf`, plugins via submodules (tpm,
  nord-tmux, tmux-sensible)
- `kitty/` — config, themes, `launch.sh`, `zenmode.py`
- `starship/` — `starship.toml` (prompt theming)
- `claude/` — files this repo deploys to `~/.claude/` (`CLAUDE.md`,
  `status-line.sh`)

Desktop:

- `desktop-environment/` — `bspwm/`, `sxhkd/`, `polybar/`, `picom.conf`,
  `dunstrc`. These stay grouped in one directory because they're developed
  and tested together: sxhkd's hotkeys and polybar's toggle scripts
  reference bspwm's installed `~/.config/bspwm` paths directly.
  `bspwm/` also contains the Python monitor-manager (EDID-based
  monitor-profile system) — see `desktop-environment/bspwm/CLAUDE.md`.
- `redshift.conf`, `Xresources`, `systemd/` (user units), `docs/` (PRD +
  AirPods-on-Linux notes) — standalone leaf configs with no cross-references
  to the bspwm stack or to each other, so they live at the top level.

Shared:

- `bin/` — helper scripts installed to `~/.local/bin` (`wacominit`,
  `lockscreen`, `clipimg`) plus a placeholder for future shell helpers.
- `dotbot/` — the single, shared Dotbot submodule.
- `install.conf.yaml` / `install-desktop.conf.yaml` — the two Dotbot
  configs: the shell/terminal/dev half (always applied) and the
  desktop-environment half (skipped by `./install --no-desktop`).
- `install` — the Dotbot wrapper script; runs both configs by default.
- `provision.sh` / `provision-shell.sh` / `desktop-environment/provision.sh`
  — see below. `provision-lib.sh` holds the helpers both scripts share
  (version pinning, sha256 verification, fail-fast install).
- `.github/workflows/ci.yml` — runs the monitor-manager test suite and
  shellcheck over every tracked shell script on each push/PR.

## Install

Provisioning assumes Ubuntu 22.04+ on x86_64: package names are apt's,
a PPA is added for git, and the pinned release tarballs are the
`x86_64`/`amd64` Linux builds.

```sh
git clone --recurse-submodules https://github.com/krishna-bala/dotfiles
cd dotfiles
./provision.sh   # installs pinned CLI tooling + X11/WM packages
./install        # symlinks everything into place via dotbot
```

`./install` is safe to re-run; it relinks everything via dotbot. Any
arguments other than `--no-desktop` are forwarded to dotbot itself.

### Shell-only machines (no desktop)

On machines that shouldn't get the X11/bspwm customization — remote boxes,
servers, containers — pass `--no-desktop` to both scripts:

```sh
./provision.sh --no-desktop  # shell/terminal/dev tooling only
./install --no-desktop       # links only the shell half's configs
```

`--no-desktop` skips `desktop-environment/provision.sh` and the
`install-desktop.conf.yaml` dotbot pass, so no X11 packages are installed
and none of the desktop configs (bspwm/sxhkd/polybar/picom/dunst,
`Xresources`, `swapescape.service`, `wacominit`/`lockscreen`/`clipimg`) are
linked. The two provisioning halves also remain independently runnable:

```sh
./provision-shell.sh               # shell/terminal/dev tooling only
./desktop-environment/provision.sh # X11/WM packages + bspwm venv only
```

## Machine-local overlay

A few files source an untracked, machine-local sidecar if present, so a
private overlay (e.g. a company meta-repo) can layer config on top without
forking this repo:

- `bash/bashrc` sources `~/.bashrc.local` if it exists (e.g. work-specific
  env vars)
- `claude/CLAUDE.md` imports `~/.claude/CLAUDE.local.md` if it exists
- `git/gitconfig` includes `~/.gitconfig.local` if it exists (identity,
  credential helpers)

None of these sidecars are shipped here; on a personal machine they're
simply absent and every reference is a no-op.

## Used as a submodule

A private meta-repo can pull this repo in as a submodule, run this repo's
`install` (or its own dotbot pass over this repo's files), and then apply
its overlay last. This repo intentionally does not run `clean: ["~"]` in
its dotbot configs, so a parent meta-repo can own that single pass
without conflicts.
