# shell-env

Portable shell and terminal foundation: bash, git, tmux, kitty, starship, and
Claude Code config. Self-contained and installable on any personal Linux
machine on its own; also consumed as a submodule by a private meta-repo that
layers machine-local config on top.

## What's here

- Bash: `bashrc`, `bash_aliases`, `profile`, `inputrc`
- Git: `gitconfig`, `gitmessage`, `git-prompt.sh`, `lazygit.yml`
- `starship.toml` (prompt theming)
- `bazel_completions.bash`
- `tmux/` + `tmux.conf` (plugins via submodules: tpm, nord-tmux, tmux-sensible)
- `kitty/` (config, themes, `launch.sh`, `zenmode.py`)
- `claude/` — files this repo deploys to `~/.claude/` (`CLAUDE.md`, `status-line.sh`)
- `bin/` — convention for future shell helper scripts installed to `~/.local/bin`

## Install

```sh
git clone --recurse-submodules https://github.com/krishna-bala/shell-env
cd shell-env
./provision.sh   # installs pinned CLI tooling (starship, fzf, lsd, fd, rg, lazygit, glab, node, uv)
./install        # symlinks the configs into place via dotbot
```

`./install` is safe to re-run; it relinks everything via dotbot.

## Machine-local overlay

A few files source an untracked, machine-local sidecar if present, so a
private overlay (e.g. a company meta-repo) can layer config on top without
forking this repo:

- `bashrc` sources `~/.bashrc.local` if it exists (e.g. work-specific env vars)
- `claude/CLAUDE.md` imports `~/.claude/CLAUDE.local.md` if it exists
- `gitconfig` includes `~/.gitconfig.local` if it exists (identity, credential helpers)

None of these sidecars are shipped here; on a personal machine they're simply
absent and every reference is a no-op.

## Used as a submodule

A private meta-repo can pull this repo in as a submodule, run this repo's
`install` (or its own dotbot pass over this repo's files), and then apply its
overlay last. This repo intentionally does not run `clean: ["~"]` in its
`install.conf.yaml`, so a parent meta-repo can own that single pass without
conflicts.
