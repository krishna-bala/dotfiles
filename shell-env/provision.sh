#!/usr/bin/env bash
#
# provision.sh - idempotent provisioning for the shell/terminal/dev tools this
# repo's configs assume are present.
#
# Installs CLI tooling. Every step is guarded by an existence/version check,
# so re-running is always safe. Run ./install afterwards to symlink the
# dotfiles themselves.

set -uo pipefail

# ----------------------------------------------------------------------------
# Safety: never run as root (user-level installs go to ~/.local, ~/.cargo, etc.)
# ----------------------------------------------------------------------------
if [ "$(id -u)" -eq 0 ]; then
  echo "ERROR: do not run provision.sh as root. It uses sudo where needed." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/provision.log"

# Trim the log so it never grows unbounded
if [ -f "$LOG_FILE" ]; then
  tail -n 2000 "$LOG_FILE" >"$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
exec > >(tee -a "$LOG_FILE") 2>&1

log() { printf '\n==> [%s] %s\n' "$(date '+%F %T')" "$*"; }
skip() { printf '    [skip] %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

mkdir -p "$HOME/.local/bin" "$HOME/.local/share"

# ----------------------------------------------------------------------------
# Pinned versions - bump deliberately, review upstream changes, then re-run
# (supply chain policy: no fetch-latest, see CLAUDE.md)
# ----------------------------------------------------------------------------
NVM_VERSION="v0.40.3"
UV_VERSION="0.11.20"
GLAB_VERSION="v1.102.0"
LAZYGIT_VERSION="v0.62.2"
STARSHIP_VERSION="v1.25.1"
FZF_VERSION="v0.73.1" # bashrc's `fzf --bash` integration needs >= 0.48.0

# Print a tool's installed version as x.y.z (PATH first, then ~/.local/bin,
# which may not be on PATH yet during a fresh provision). Prints nothing when
# the tool is missing or its version output is unparseable.
installed_version() {
  local bin
  bin="$(command -v "$1" || true)"
  [ -z "$bin" ] && [ -x "$HOME/.local/bin/$1" ] && bin="$HOME/.local/bin/$1"
  [ -z "$bin" ] && return 0
  "$bin" --version 2>/dev/null | grep -oEm1 '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1
}

# usage: meets_pin <cmd> <pinned-version>
# True when the installed version is at least the pin, so a stale binary gets
# reinstalled at the pinned version. Missing/unparseable also fails the check.
meets_pin() {
  local cur pin="${2#v}"
  cur="$(installed_version "$1")"
  [ -n "$cur" ] || return 1
  [ "$(printf '%s\n' "$pin" "$cur" | sort -V | head -n1)" = "$pin" ]
}

# Download a release tarball and install one binary from it into ~/.local/bin
# usage: install_release_binary <url> <member-path-in-tar> <dest-name> [strip]
install_release_binary() {
  local url="$1" member="$2" dest="$3" strip="${4:-0}"
  local tmp
  tmp="$(mktemp -d)"
  if curl -fsSL -o "$tmp/archive.tar.gz" "$url" &&
    tar -xzf "$tmp/archive.tar.gz" -C "$tmp" --strip-components="$strip" "$member"; then
    install -m 0755 "$tmp/$(basename "$member")" "$HOME/.local/bin/$dest"
  else
    echo "    [error] failed to download/extract $url"
  fi
  rm -rf "$tmp"
}

log "Provisioning started"

# ----------------------------------------------------------------------------
# apt packages (git-core PPA for a current git)
# ----------------------------------------------------------------------------
log "System packages (apt)"
if ! command -v add-apt-repository >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq software-properties-common
fi
if ! grep -rq "git-core/ppa" /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null; then
  sudo add-apt-repository -y ppa:git-core/ppa
fi
sudo apt-get update -qq
sudo apt-get install -y -qq \
  git curl wget unzip \
  build-essential pkg-config \
  tmux jq xclip \
  bash-completion

# ----------------------------------------------------------------------------
# nvm + node LTS
# ----------------------------------------------------------------------------
export NVM_DIR="$HOME/.nvm"
log "nvm + node LTS"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh" | bash
else
  skip "nvm already installed"
fi
# shellcheck disable=SC1091
. "$NVM_DIR/nvm.sh"
if ! nvm ls --no-colors lts/* >/dev/null 2>&1; then
  NVM_SYMLINK_CURRENT=true nvm install --lts
else
  skip "node LTS already installed"
fi

# ----------------------------------------------------------------------------
# uv (python package/venv manager)
# ----------------------------------------------------------------------------
log "uv $UV_VERSION"
if meets_pin uv "$UV_VERSION"; then
  skip "uv $(installed_version uv) already installed (>= $UV_VERSION)"
else
  install_release_binary \
    "https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-x86_64-unknown-linux-gnu.tar.gz" \
    "uv-x86_64-unknown-linux-gnu/uv" uv 1
  [ -x "$HOME/.local/bin/uv" ] || echo "    [error] uv install failed"
fi

# ----------------------------------------------------------------------------
# glab (GitLab CLI)
# ----------------------------------------------------------------------------
log "glab $GLAB_VERSION"
if meets_pin glab "$GLAB_VERSION"; then
  skip "glab $(installed_version glab) already installed (>= ${GLAB_VERSION#v})"
else
  install_release_binary \
    "https://gitlab.com/gitlab-org/cli/-/releases/$GLAB_VERSION/downloads/glab_${GLAB_VERSION#v}_linux_amd64.tar.gz" \
    "bin/glab" glab 1
fi

# ----------------------------------------------------------------------------
# Rust/Go CLI tools: lsd, fd, ripgrep, lazygit, starship
# ----------------------------------------------------------------------------
log "lsd"
if have lsd; then skip "lsd already installed"; else
  sudo apt-get install -y -qq lsd || cargo install lsd
fi

log "fd"
if have fd; then
  skip "fd already installed"
else
  sudo apt-get install -y -qq fd-find
  ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd"
fi

log "ripgrep"
if have rg; then skip "ripgrep already installed"; else
  sudo apt-get install -y -qq ripgrep
fi

log "lazygit $LAZYGIT_VERSION"
if meets_pin lazygit "$LAZYGIT_VERSION"; then
  skip "lazygit $(installed_version lazygit) already installed (>= ${LAZYGIT_VERSION#v})"
else
  install_release_binary \
    "https://github.com/jesseduffield/lazygit/releases/download/$LAZYGIT_VERSION/lazygit_${LAZYGIT_VERSION#v}_Linux_x86_64.tar.gz" \
    "lazygit" lazygit
fi

log "starship $STARSHIP_VERSION"
if meets_pin starship "$STARSHIP_VERSION"; then
  skip "starship $(installed_version starship) already installed (>= ${STARSHIP_VERSION#v})"
else
  install_release_binary \
    "https://github.com/starship/starship/releases/download/$STARSHIP_VERSION/starship-x86_64-unknown-linux-gnu.tar.gz" \
    "starship" starship
fi

# ----------------------------------------------------------------------------
# fzf (GitHub release binary)
# ----------------------------------------------------------------------------
log "fzf $FZF_VERSION"
if meets_pin fzf "$FZF_VERSION"; then
  skip "fzf $(installed_version fzf) already installed (>= ${FZF_VERSION#v})"
else
  install_release_binary \
    "https://github.com/junegunn/fzf/releases/download/$FZF_VERSION/fzf-${FZF_VERSION#v}-linux_amd64.tar.gz" \
    "fzf" fzf
fi

# ----------------------------------------------------------------------------
# Stale duplicate binaries: tools this script manages in ~/.local/bin can also
# exist elsewhere on PATH (old manual installs in /usr/local/bin, cargo, apt).
# Flag every duplicate and say how to remove it. A duplicate that comes first
# on PATH is worse than clutter: it silently wins over the pinned copy.
# ----------------------------------------------------------------------------
log "Checking for stale duplicate binaries"
stale_found=0
for tool in uv glab lazygit starship fzf; do
  [ -x "$HOME/.local/bin/$tool" ] || continue
  while IFS= read -r path; do
    [ "$path" = "$HOME/.local/bin/$tool" ] && continue
    stale_found=1
    rm_cmd="sudo rm"
    case "$path" in "$HOME"/*) rm_cmd="rm" ;; esac
    if [ "$(command -v "$tool")" = "$HOME/.local/bin/$tool" ]; then
      printf '    [note] stale %s at %s (shadowed; clean up with: %s %s)\n' \
        "$tool" "$path" "$rm_cmd" "$path"
    else
      printf '    [WARN] %s on PATH resolves to %s, which shadows the pinned ~/.local/bin/%s; remove it with: %s %s\n' \
        "$tool" "$path" "$tool" "$rm_cmd" "$path"
    fi
  done < <(type -aP "$tool" 2>/dev/null | awk '!seen[$0]++')
done
[ "$stale_found" -eq 0 ] && skip "no stale copies found"

log "Provisioning complete. Run ./install to symlink dotfiles."
