# CLAUDE.md

Guidance for working on this repository.

## What this repo is

A portable shell/terminal/dev-foundation dotfiles repo: bash, git, tmux,
kitty, starship, and the `claude/` files this repo deploys to a user's
`~/.claude/`. It is one of three public repos (alongside `desktop-environment`
and `lazyvim`) pulled as submodules by a private meta-repo, but it installs
and works standalone.

Do not confuse `claude/CLAUDE.md` (the file this repo symlinks to
`~/.claude/CLAUDE.md` on install — guidance for using Claude Code itself) with
this file (guidance for editing this repo).

## Architecture

- [Dotbot](https://github.com/anishathalye/dotbot) drives installation via
  `install.conf.yaml`; `./install` is the entry point.
- Configs are flat root-level files or per-tool directories, symlinked into
  place — no templating, no generated files.
- `provision.sh` installs the CLI tooling these configs assume is present
  (starship, fzf, lsd, fd, ripgrep, lazygit, glab, node/nvm, uv). It's
  idempotent and safe to re-run.
- Tmux plugins (tpm, nord-tmux, tmux-sensible) and dotbot itself are git
  submodules, all anonymous-HTTPS so this repo clones without credentials.

## Supply-chain / version-pinning policy

`provision.sh` pins every tool to a specific version (no fetch-latest).
Bumping a pin is a deliberate, reviewed change: update the version variable,
review the upstream diff, then re-run `./provision.sh`.

## Commits

Use scoped commits (`<scope>: <description>`, e.g. `kitty: ...`, `shell:
...`), not conventional-commit prefixes. No `Co-Authored-By` trailers.

## Machine-local overlay seams

`bashrc`, `gitconfig`, and `claude/CLAUDE.md` each reference an untracked
`~/*.local` sidecar behind an existence guard, so a private overlay repo can
inject machine-specific config without modifying these files. Never add a
`*.local` file to this repo; it stays public and self-contained.
