# CLAUDE.md

Guidance for working on this repository.

## What this repo is

Personal dotfiles: a shell/terminal/dev foundation plus a bspwm-based X11
desktop, installed via Dotbot from the repo root. The desktop half is
optional: `--no-desktop` on `./install` and `./provision.sh` skips it.

Do not confuse `claude/CLAUDE.md` (the file this repo symlinks to
`~/.claude/CLAUDE.md` on install — guidance for using Claude Code itself)
with this file (guidance for editing this repo).

## Layout

- `bash/`, `git/`, `tmux/`, `kitty/`, `starship/`, `claude/` — the shell/
  terminal/dev foundation. Each is independent of the others, so they get
  their own top-level directory rather than nesting under one umbrella.
- `desktop-environment/` — the bspwm + sxhkd + polybar X11 stack, plus
  picom and dunst. These stay grouped under one directory because they're
  developed and tested together (sxhkd's hotkeys and polybar's toggle
  scripts reference bspwm's installed config paths directly).
- `redshift.conf`, `Xresources`, `systemd/`, `docs/`, `bin/` — standalone
  leaf configs and scripts that don't reference anything else, so they live
  at the top level.
- See `README.md` for the full directory-by-directory breakdown.

## Architecture

- [Dotbot](https://github.com/anishathalye/dotbot) drives installation via
  two root configs — `install.conf.yaml` (shell/terminal/dev, always
  applied) and `install-desktop.conf.yaml` (the desktop-environment links
  and steps, skipped when `./install` is given `--no-desktop`); `./install`
  is the entry point. There is one dotbot submodule, shared by both halves.
  When adding a config file, put its entry in whichever half it belongs to;
  anything X11-dependent goes in the desktop config.
- Configs are flat root-level files or per-tool directories, symlinked into
  place — no templating, no generated files.
- Provisioning is split in two, matching the two stacks: `provision-shell.sh`
  (CLI tooling: starship, fzf, lsd, fd, ripgrep, lazygit, glab, node/nvm,
  uv, rust/tree-sitter, plus the kitty and neovim bundles) and
  `desktop-environment/provision.sh` (X11/WM packages + the bspwm
  monitor-manager's venv). Root `provision.sh` runs both in sequence
  (`--no-desktop` skips the X11 half); each is also independently runnable
  and idempotent, and both source the shared `provision-lib.sh`. Targets
  Ubuntu 22.04+ on x86_64 only.
- Tmux plugins (tpm, nord-tmux, tmux-sensible) and dotbot itself are git
  submodules, all anonymous-HTTPS so this repo clones without credentials.

## Supply-chain / version-pinning policy

Every tool fetched from an upstream release — nvm, uv, glab, lazygit,
starship, fzf, lsd, kitty, neovim, go, typst, and the Nerd Fonts (JetBrainsMono,
Iosevka, FantasqueSansMono) — names an exact version (no fetch-latest) and
is verified against a recorded sha256 before installing (helpers live in
`provision-lib.sh`).

A pin is a floor, not an equality. It is the version a fresh machine gets
and the minimum these configs are known to work with; an installed copy at
or above it is left alone, and one that is newer — updated by hand between
runs — is reported and kept rather than rolled back. Re-provisioning is not
supposed to undo a deliberate update, and that note is the cue to raise the
floor once the newer version has proven itself. Older, missing, or
unparseable installs the pin. `FORCE_PINS=1 ./provision-shell.sh` restores
exact-pin behaviour for a run, which is how a pin gets walked backwards
after a bad release. The trade is that machines no longer converge on
identical binaries; the guarantee kept is that nothing is ever fetched
unpinned or unverified.

Raising a pin is a deliberate, reviewed change: update the version variable
and its sha256 (from the upstream release's published checksums where they
exist; kitty, neovim, and typst publish none, so their hashes are computed
from the reviewed download), review the upstream diff, then re-run the relevant
`provision*.sh`. The
monitor-manager's Python dependencies are pinned the same way via the
committed `uv.lock`; all syncs run `--locked`. The rust toolchain is pinned the same way
(verified rustup-init, pinned toolchain version), and the tree-sitter CLI
is built from source at a pinned version with it — upstream prebuilts
target glibc 2.39 and won't run on 22.04; cargo verifies every crate
against the crates.io registry checksums. The desktop half source-builds
two more: polybar, pinned by sha256 over the release tarball upstream
uploads (22.04's 3.5.7 predates the `internal/tray` module the bars use),
and picom, the one artifact pinned by git commit rather than hash (22.04
packages v9) — upstream uploads nothing, and hashing GitHub's generated tag
archive pins bytes GitHub can regenerate, so the commit id serves as the
content hash and a re-pointed tag aborts the build. The exceptions are tools
taken from distro apt repos (fd, ripgrep, plus the X11/WM packages) and
node, which tracks the current LTS — these follow whatever the package
source provides. protonvpn-app is deliberately unprovisioned (Proton's own
repo; bspwmrc pgrep-guards it).

## Commits

Use scoped commits (`<scope>: <description>`, e.g. `kitty: ...`, `bspwm:
...`), not conventional-commit prefixes. No `Co-Authored-By` trailers.

## Machine-local overlay seams

`bash/bashrc`, `bash/bash_aliases`, `git/gitconfig`, and `claude/CLAUDE.md`
each reference an untracked `~/*.local` sidecar behind an existence guard,
so a private overlay repo can inject machine-specific config without
modifying these files. Never add a `*.local` file to this repo; it stays
public and self-contained. The same split applies to config that isn't a
sidecar: work-machine bspwm profiles live in the overlay, not in
`desktop-environment/bspwm/profiles/`.
