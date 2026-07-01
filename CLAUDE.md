# CLAUDE.md

Guidance for working on this repository.

## What this repo is

`public-dotfiles` consolidates two formerly-separate public dotfiles repos,
`shell-env` and `desktop-environment`, into one. Full commit history from
both is preserved (merged via `git subtree`).

Do not confuse `claude/CLAUDE.md` (the file this repo symlinks to
`~/.claude/CLAUDE.md` on install — guidance for using Claude Code itself)
with this file (guidance for editing this repo).

## Layout

- `bash/`, `git/`, `tmux/`, `kitty/`, `starship/`, `claude/` — the shell/
  terminal/dev foundation (formerly `shell-env`). Each is independent of
  the others, so they get their own top-level directory rather than
  nesting under one umbrella.
- `desktop-environment/` — the bspwm + sxhkd + polybar X11 stack, plus
  picom and dunst. These stay grouped under one directory because they're
  developed and tested together (sxhkd's hotkeys and polybar's toggle
  scripts reference bspwm's installed config paths directly).
- `redshift.conf`, `Xresources`, `systemd/`, `docs/`, `bin/` — standalone
  leaf configs and scripts (from both source repos) that don't reference
  anything else, so they live at the top level.
- See `README.md` for the full directory-by-directory breakdown.

## Architecture

- [Dotbot](https://github.com/anishathalye/dotbot) drives installation via
  the single root `install.conf.yaml`; `./install` is the entry point.
  There is one dotbot submodule, shared by both halves.
- Configs are flat root-level files or per-tool directories, symlinked into
  place — no templating, no generated files.
- Provisioning is split in two, matching the two stacks: `provision-shell.sh`
  (CLI tooling: starship, fzf, lsd, fd, ripgrep, lazygit, glab, node/nvm, uv)
  and `desktop-environment/provision.sh` (X11/WM packages + the bspwm
  monitor-manager's venv). Root `provision.sh` runs both in sequence; each
  is also independently runnable and idempotent.
- Tmux plugins (tpm, nord-tmux, tmux-sensible) and dotbot itself are git
  submodules, all anonymous-HTTPS so this repo clones without credentials.

## Supply-chain / version-pinning policy

Every tool fetched from an upstream release — nvm, uv, glab, lazygit,
starship, fzf — is pinned to a specific version (no fetch-latest). Bumping a
pin is a deliberate, reviewed change: update the version variable, review the
upstream diff, then re-run the relevant `provision*.sh`. The exceptions are
tools taken from distro apt repos (lsd, fd, ripgrep, plus the X11/WM
packages) and node, which tracks the current LTS — these follow whatever the
package source provides.

## Commits

Use scoped commits (`<scope>: <description>`, e.g. `kitty: ...`, `bspwm:
...`), not conventional-commit prefixes. No `Co-Authored-By` trailers.

## Machine-local overlay seams

`bash/bashrc`, `git/gitconfig`, and `claude/CLAUDE.md` each reference an
untracked `~/*.local` sidecar behind an existence guard, so a private
overlay repo can inject machine-specific config without modifying these
files. Never add a `*.local` file to this repo; it stays public and
self-contained.
