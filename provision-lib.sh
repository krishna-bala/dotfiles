#!/usr/bin/env bash
#
# provision-lib.sh - helpers shared by provision-shell.sh and
# desktop-environment/provision.sh. Source this from a script running
# `set -euo pipefail`; it is not executable on its own.
#
# Philosophy: fail early and loudly. Every download is pinned to an exact
# version and verified against a recorded sha256 before anything is
# installed; any failure is fatal, never warn-and-continue.

log() { printf '\n==> [%s] %s\n' "$(date '+%F %T')" "$*"; }
skip() { printf '    [skip] %s\n' "$*"; }
die() {
  printf '    [FATAL] %s\n' "$*" >&2
  exit 1
}
have() { command -v "$1" >/dev/null 2>&1; }

# User-level installs go to ~/.local, ~/.nvm, etc.; sudo is used where needed.
require_not_root() {
  [ "$(id -u)" -ne 0 ] || die "do not run provisioning as root"
}

# Append all output to the given log file, trimmed to the last 2000 lines so
# it never grows unbounded.
init_provision_log() {
  local log_file="$1"
  if [ -f "$log_file" ]; then
    tail -n 2000 "$log_file" >"$log_file.tmp" && mv "$log_file.tmp" "$log_file"
  fi
  exec > >(tee -a "$log_file") 2>&1
}

# Print a tool's installed version as x.y.z (PATH first, then ~/.local/bin,
# which may not be on PATH yet during a fresh provision). Prints nothing when
# the tool is missing or its version output is unparseable.
installed_version() {
  local bin
  bin="$(command -v "$1" || true)"
  [ -z "$bin" ] && [ -x "$HOME/.local/bin/$1" ] && bin="$HOME/.local/bin/$1"
  [ -z "$bin" ] && return 0
  "$bin" --version 2>/dev/null | grep -oEm1 '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1 || true
}

# usage: at_pinned_version <cmd> <pinned-version>
# True only when the installed version is exactly the pin. Anything else -
# missing, older, newer, unparseable - fails, and the caller reinstalls the
# pinned artifact so every machine converges to the same binary.
at_pinned_version() {
  local cur pin="${2#v}"
  cur="$(installed_version "$1")"
  [ "$cur" = "$pin" ]
}

# usage: verify_sha256 <file> <expected-sha256>
verify_sha256() {
  local file="$1" expected="$2"
  printf '%s  %s\n' "$expected" "$file" | sha256sum --check --quiet ||
    die "sha256 mismatch for $file (expected $expected) - refusing to install"
}

# usage: install_release_binary <url> <sha256> <member-path-in-tar> <dest-name> [strip]
# Download a release tarball, verify it against the recorded sha256, and
# install one binary from it into ~/.local/bin. On failure the temp dir is
# left behind for inspection.
install_release_binary() {
  local url="$1" sha256="$2" member="$3" dest="$4" strip="${5:-0}"
  local tmp
  tmp="$(mktemp -d)"
  curl -fsSL -o "$tmp/archive.tar.gz" "$url" || die "download failed: $url"
  verify_sha256 "$tmp/archive.tar.gz" "$sha256"
  tar -xzf "$tmp/archive.tar.gz" -C "$tmp" --strip-components="$strip" "$member" ||
    die "extract failed: $member from $url"
  install -m 0755 "$tmp/$(basename "$member")" "$HOME/.local/bin/$dest" ||
    die "install failed: $dest"
  rm -rf "$tmp"
}

# usage: install_release_bundle <url> <sha256> <app-dir> <strip> <bin>...
# Download a multi-file release bundle (an app that needs its lib/ and
# share/ next to its binary), verify it against the recorded sha256, unpack
# it to ~/.local/<app-dir>, and symlink the named bin/ entries into
# ~/.local/bin. The old app dir is replaced only after a verified extract.
install_release_bundle() {
  local url="$1" sha256="$2" app="$3" strip="$4"
  shift 4
  local tmp bin
  tmp="$(mktemp -d)"
  curl -fsSL -o "$tmp/bundle" "$url" || die "download failed: $url"
  verify_sha256 "$tmp/bundle" "$sha256"
  mkdir -p "$tmp/app"
  tar -xaf "$tmp/bundle" -C "$tmp/app" --strip-components="$strip" ||
    die "extract failed: $url"
  rm -rf "${HOME:?}/.local/$app"
  mv "$tmp/app" "$HOME/.local/$app"
  for bin in "$@"; do
    [ -x "$HOME/.local/$app/bin/$bin" ] || die "bundle $app has no bin/$bin"
    ln -sf "$HOME/.local/$app/bin/$bin" "$HOME/.local/bin/$bin"
  done
  rm -rf "$tmp"
}

# usage: run_verified_installer <url> <sha256>
# Download an installer script, verify its content hash, then execute it.
# The version pin in the URL alone isn't enough: a tag can be re-pointed
# upstream, but the content hash can't lie.
run_verified_installer() {
  local url="$1" sha256="$2"
  local tmp
  tmp="$(mktemp -d)"
  curl -fsSL -o "$tmp/installer.sh" "$url" || die "download failed: $url"
  verify_sha256 "$tmp/installer.sh" "$sha256"
  bash "$tmp/installer.sh" || die "installer failed: $url"
  rm -rf "$tmp"
}

# ----------------------------------------------------------------------------
# uv is needed by both halves (shell dev tooling; building the bspwm
# monitor-manager venv), so its pin lives here as the single source of truth.
# ----------------------------------------------------------------------------
UV_VERSION="0.11.20"
UV_SHA256="5de211d9278af365497d387e25316907b3b4a9f25b4476dd6dbf238d6f85cff3"

install_uv() {
  log "uv $UV_VERSION"
  if at_pinned_version uv "$UV_VERSION"; then
    skip "uv $(installed_version uv) already at pin"
  else
    install_release_binary \
      "https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-x86_64-unknown-linux-gnu.tar.gz" \
      "$UV_SHA256" "uv-x86_64-unknown-linux-gnu/uv" uv 1
  fi
}
