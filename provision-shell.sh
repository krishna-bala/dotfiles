#!/usr/bin/env bash
#
# provision-shell.sh - idempotent provisioning for the shell/terminal/dev
# tools this repo's configs assume are present.
#
# Every downloaded tool is pinned to an exact version and verified against a
# recorded sha256 (helpers in provision-lib.sh). A tool already at its pin is
# skipped, so re-running is safe; any other outcome - download failure, hash
# mismatch, failed install - aborts loudly with a nonzero exit. Run ./install
# afterwards to symlink the dotfiles themselves.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=provision-lib.sh
. "$SCRIPT_DIR/provision-lib.sh"

require_not_root
init_provision_log "$SCRIPT_DIR/provision.log"

mkdir -p "$HOME/.local/bin" "$HOME/.local/share"

# ----------------------------------------------------------------------------
# Pinned versions + sha256s of the exact artifacts downloaded below. Bumping
# a pin is a deliberate, reviewed change: update the version AND its sha256
# (from the upstream release's published checksums), review the upstream
# diff, then re-run. (supply chain policy: no fetch-latest, see CLAUDE.md)
# UV_VERSION/UV_SHA256 live in provision-lib.sh, shared with the desktop half.
# ----------------------------------------------------------------------------
NVM_VERSION="v0.40.3"
NVM_INSTALL_SHA256="2d8359a64a3cb07c02389ad88ceecd43f2fa469c06104f92f98df5b6f315275f"
GLAB_VERSION="v1.102.0"
GLAB_SHA256="2e06f278bb1762126e9b695f67baf5e3210df431b2039c76c1991252bf9c0868"
LAZYGIT_VERSION="v0.62.2"
LAZYGIT_SHA256="8b9a4c2d0969cbea92b45c956dd2a44e1ba76900c9df49f1c60984045ce77984"
STARSHIP_VERSION="v1.25.1"
STARSHIP_SHA256="4488c11ca632327d1f1f16fb2f102c0646094c35479cd5435991385da43c61ac"
FZF_VERSION="v0.73.1" # bashrc's `fzf --bash` integration needs >= 0.48.0
FZF_SHA256="f3252c2c366bc1700d3c85781ec8c9695998927ac127870eb049ceea2d540f8a"

log "Provisioning started"

# ----------------------------------------------------------------------------
# apt packages (git-core PPA for a current git). These follow the distro's
# versions; only the release-tarball tools below are content-pinned.
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
# Must match bashrc's NVM_DIR logic exactly, or provisioning installs node
# somewhere the shell never looks.
if [[ -z "${XDG_CONFIG_HOME-}" ]]; then
  export NVM_DIR="$HOME/.nvm"
else
  export NVM_DIR="$XDG_CONFIG_HOME/nvm"
fi
log "nvm $NVM_VERSION + node LTS (NVM_DIR=$NVM_DIR)"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  mkdir -p "$NVM_DIR"
  # PROFILE=/dev/null: bashrc already has its own nvm block; never let the
  # installer append one to the repo-symlinked ~/.bashrc.
  PROFILE=/dev/null run_verified_installer \
    "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh" \
    "$NVM_INSTALL_SHA256"
else
  skip "nvm already installed"
fi
# shellcheck disable=SC1091
. "$NVM_DIR/nvm.sh" || die "failed to load $NVM_DIR/nvm.sh"
if ! nvm ls --no-colors lts/* >/dev/null 2>&1; then
  NVM_SYMLINK_CURRENT=true nvm install --lts || die "nvm install --lts failed"
else
  skip "node LTS already installed"
fi

# ----------------------------------------------------------------------------
# uv (python package/venv manager; pin shared with the desktop half)
# ----------------------------------------------------------------------------
install_uv

# ----------------------------------------------------------------------------
# glab (GitLab CLI)
# ----------------------------------------------------------------------------
log "glab $GLAB_VERSION"
if at_pinned_version glab "$GLAB_VERSION"; then
  skip "glab $(installed_version glab) already at pin"
else
  install_release_binary \
    "https://gitlab.com/gitlab-org/cli/-/releases/$GLAB_VERSION/downloads/glab_${GLAB_VERSION#v}_linux_amd64.tar.gz" \
    "$GLAB_SHA256" "bin/glab" glab 1
fi

# ----------------------------------------------------------------------------
# apt-managed CLI tools: lsd, fd, ripgrep (distro versions, presence-checked)
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

# ----------------------------------------------------------------------------
# Release-tarball tools: lazygit, starship, fzf (exact pin + sha256)
# ----------------------------------------------------------------------------
log "lazygit $LAZYGIT_VERSION"
if at_pinned_version lazygit "$LAZYGIT_VERSION"; then
  skip "lazygit $(installed_version lazygit) already at pin"
else
  install_release_binary \
    "https://github.com/jesseduffield/lazygit/releases/download/$LAZYGIT_VERSION/lazygit_${LAZYGIT_VERSION#v}_Linux_x86_64.tar.gz" \
    "$LAZYGIT_SHA256" "lazygit" lazygit
fi

log "starship $STARSHIP_VERSION"
if at_pinned_version starship "$STARSHIP_VERSION"; then
  skip "starship $(installed_version starship) already at pin"
else
  install_release_binary \
    "https://github.com/starship/starship/releases/download/$STARSHIP_VERSION/starship-x86_64-unknown-linux-gnu.tar.gz" \
    "$STARSHIP_SHA256" "starship" starship
fi

log "fzf $FZF_VERSION"
if at_pinned_version fzf "$FZF_VERSION"; then
  skip "fzf $(installed_version fzf) already at pin"
else
  install_release_binary \
    "https://github.com/junegunn/fzf/releases/download/$FZF_VERSION/fzf-${FZF_VERSION#v}-linux_amd64.tar.gz" \
    "$FZF_SHA256" "fzf" fzf
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
if [ "$stale_found" -eq 0 ]; then
  skip "no stale copies found"
fi

log "Provisioning complete. Run ./install to symlink dotfiles."
