# CLAUDE.md

Guidance for working on this repository.

## What this repo is

Personal dotfiles installed via Dotbot, organised as modules (one tool's
config plus its provisioning) selected by roles (`server`, `workstation`,
`desktop`). `./install --roles <role>` and `./provision.sh --roles <role>`
are the entry points; the selection is saved so later runs need no flags,
and `./doctor` checks a machine against it read-only.

Do not confuse `modules/agents/AGENTS.md` (the file this repo symlinks to
`~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` on install - user-level agent
guidance) with this file (guidance for editing this repo).

## Layout

- `roles/<name>` - one module per line; `@other` pulls in another role.
- `modules/<name>/` - `install.conf.yaml` (dotbot, sources relative to the
  module), `provision.sh` (standalone-runnable, sources
  `lib/provision-lib.sh`), optional `requires`. A module whose whole
  directory is linked (`tmux`, `kitty`) keeps its config under `config/` so
  the manifest and provisioning don't land in `$HOME`.
- `modules/x11/` - the bspwm + sxhkd + polybar stack plus picom, dunst,
  redshift, Xresources, the systemd user unit, and the X11-only scripts.
  Grouped because sxhkd's hotkeys and polybar's toggle scripts reference
  bspwm's installed config paths directly. `~/.config/bspwm` is a real
  directory with `bspwmrc`, `scripts/`, and `profiles/` linked into it, so
  an overlay's `profiles.d/` can sit beside them.
- `apps/monitor-manager/` - an application, not a dotfile: the Python
  monitor-profile system with its own tests, `pyproject.toml`, `uv.lock`,
  and `CLAUDE.md`. Installed by `modules/x11/provision.sh` as a uv tool
  (`--editable`, constrained to `uv.lock`). Anything with a test suite is
  an app and lives here, not under `modules/`.
- `hosts/` - per-machine values; `lib/` - shared shell helpers and the
  dotbot `render` plugin; `docs/` - the desktop PRD and notes.
- See `README.md` for the module-by-module breakdown.

## Architecture

- `lib/roles.sh` resolves roles to an ordered, de-duplicated module list
  and refuses a selection that violates a module's `requires`. `install`
  runs dotbot once per module (`-d modules/<m>`) with `lib/dotbot-plugins`
  loaded; `provision.sh` runs each module's `provision.sh` in role order.
  When adding a config file, add it to the module it belongs to; when
  adding a tool, add a module (or extend the one whose config assumes it)
  and list it in the roles that need it. Order within a role matters only
  for provisioning; `cli-tools` goes first because it installs curl.
- Configs are symlinked - except the few files that carry per-machine
  values, which are `*.tmpl` rendered by the `render:` directive from
  `~/.config/dotfiles/host.env` (`hosts/defaults.env` <
  `hosts/<hostname>.env` < untracked `~/.config/dotfiles/local.env`) and
  copied into place. Plain `${NAME}` substitution, error on an unknown
  name; keep templates free of literal `$`.
- Provisioning helpers (`lib/provision-lib.sh`): `pkg_ensure` installs only
  missing distro packages and refreshes the index once per run on first
  need, so a converged machine touches neither apt nor sudo;
  `pkg_candidate_version` + `version_ge` let a module take the distro
  package when it is new enough and source-build otherwise (polybar,
  picom). `require_supported_platform` states the limits up front: Debian
  family, x86_64.
- The tmux plugins (tpm, nord-tmux) and dotbot are git submodules, all anonymous-HTTPS so this repo clones without credentials.
- CI installs the `server` role from scratch in Ubuntu 22.04 and 24.04
  containers and asserts a second run is a no-op (only `[skip]`/`[note]`
  lines in `provision.log`). A module step that prints anything else when
  already satisfied breaks that check - use `skip`/`note`, and put a
  presence check in front of every install. `./doctor` finds a module's
  pins by grepping its provision.sh for `pin_satisfied <cmd> "$VAR"`, so
  keep that spelling for pinned tools.

## Supply-chain / version-pinning policy

Every tool fetched from an upstream release - nvm, uv, glab, lazygit,
starship, fzf, lsd, kitty, neovim, go, typst, and the Nerd Fonts
(JetBrainsMono, Iosevka, FantasqueSansMono) - names an exact version (no
fetch-latest) and is verified against a recorded sha256 before installing
(helpers live in `lib/provision-lib.sh`; pins live in the module that
installs the tool, except uv's and the fonts', which several modules share
and so sit in the lib).

A pin is a floor, not an equality. It is the version a fresh machine gets
and the minimum these configs are known to work with; an installed copy at
or above it is left alone, and one that is newer - updated by hand between
runs - is reported and kept rather than rolled back. Re-provisioning is not
supposed to undo a deliberate update, and that note is the cue to raise the
floor once the newer version has proven itself. Older, missing, or
unparseable installs the pin. `FORCE_PINS=1 ./provision.sh` restores
exact-pin behaviour for a run, which is how a pin gets walked backwards
after a bad release. The trade is that machines no longer converge on
identical binaries; the guarantee kept is that nothing is ever fetched
unpinned or unverified.

Raising a pin is a deliberate, reviewed change: update the version variable
and its sha256 (from the upstream release's published checksums where they
exist; kitty, neovim, and typst publish none, so their hashes are computed
from the reviewed download), review the upstream diff, then re-run the
module's `provision.sh`. The monitor-manager's Python dependencies are
pinned the same way via the committed `uv.lock`: `uv sync --locked` in CI,
and the tool install exports the lock as a constraints file. The rust
toolchain is pinned the same way (verified rustup-init, pinned toolchain
version), and the tree-sitter CLI is built from source at a pinned version
with it - upstream prebuilts target glibc 2.39 and won't run on 22.04;
cargo verifies every crate against the crates.io registry checksums. The
x11 module source-builds two more where the distro package is too old:
polybar, pinned by sha256 over the release tarball upstream uploads
(22.04's 3.5.7 predates the `internal/tray` module the bars use), and
picom, the one artifact pinned by git commit rather than hash (22.04
packages v9) - upstream uploads nothing, and hashing GitHub's generated tag
archive pins bytes GitHub can regenerate, so the commit id serves as the
content hash and a re-pointed tag aborts the build. The exceptions are
tools taken from distro apt repos (fd, ripgrep, tmux, plus the X11/WM
packages) and node, which tracks the current LTS - these follow whatever
the package source provides. protonvpn-app is deliberately unprovisioned
(Proton's own repo; bspwmrc pgrep-guards it).

## Commits

Use scoped commits (`<scope>: <description>`, e.g. `kitty: ...`, `bspwm:
...`), not conventional-commit prefixes. No `Co-Authored-By` trailers.

## Machine-local overlay seams

Each config sources an untracked sidecar **last**, behind an existence
guard, so a private overlay repo can override anything without modifying a
tracked file: `~/.config/dotfiles/env.sh` (every bash shell, before the
interactive gate - the one place for env that non-interactive shells must
see), `~/.bashrc.local`, `~/.bash_aliases.local`, `~/.gitconfig.local`
(included at the bottom of gitconfig, so it can override any key),
`~/.tmux.conf.local`, `~/.config/kitty.local.conf` (outside the symlinked
kitty dir), `~/.config/dotfiles/local.env` (per-machine values), and
`~/.config/bspwm/profiles.d/` (private monitor profiles; a name there
shadows a tracked one). Never add a `*.local` file or an overlay profile to
this repo; it stays public and self-contained. Intentionally public
hardware-specific profiles may live in `modules/x11/bspwm/profiles/`.

`modules/git/hooks/` guards this repo's own history: `./install` points
this clone's `core.hooksPath` at it (repo-local - no other repo on the
machine is affected), and the hooks then refuse any commit or push whose
committer is not one of the two identities this repo is developed under.
The allowlist in `identity-guard.sh` is deliberately hard-coded and closed;
never add a work or otherwise private address to it - this repo is public,
so anything written there is published.
