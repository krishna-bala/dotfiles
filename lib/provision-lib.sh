#!/usr/bin/env bash
#
# provision-lib.sh - helpers shared by ./provision.sh and every
# modules/*/provision.sh. Source this from a script running
# `set -euo pipefail`; it is not executable on its own.
#
# Philosophy: fail early and loudly. Every download is pinned to an exact
# version and verified against a recorded sha256 before anything is
# installed; any failure is fatal, never warn-and-continue.

# shellcheck source=common.sh
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

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

# ----------------------------------------------------------------------------
# Platform. The release-tarball pins below are x86_64 builds and the package
# names are apt's, so that is what is supported; say so up front rather than
# failing partway through on a download that does not exist.
# ----------------------------------------------------------------------------
os_id() { (. /etc/os-release && printf '%s' "${ID:-unknown}"); }
os_version_id() { (. /etc/os-release && printf '%s' "${VERSION_ID:-0}"); }
# Family, not distro: what decides the package manager and package names.
os_family() {
  (
    . /etc/os-release
    case " ${ID:-} ${ID_LIKE:-} " in
    *" debian "* | *" ubuntu "*) printf 'debian' ;;
    *" fedora "* | *" rhel "*) printf 'fedora' ;;
    *" arch "*) printf 'arch' ;;
    *) printf 'unknown' ;;
    esac
  )
}
require_supported_platform() {
  local arch family
  arch="$(uname -m)"
  [ "$arch" = "x86_64" ] ||
    die "unsupported architecture $arch: every release pin in modules/*/provision.sh is an x86_64 build"
  family="$(os_family)"
  [ "$family" = "debian" ] ||
    die "unsupported distro family '$family' ($(os_id)): package names here are apt's"
}

# ----------------------------------------------------------------------------
# Distro packages. pkg_ensure is the one to call: it installs only what is
# missing, so a converged machine never touches apt (or sudo) at all, and
# refreshes the package index once per provisioning run, on first need.
# ----------------------------------------------------------------------------
pkg_installed() {
  case "$(os_family)" in
  debian) dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q 'install ok installed' ;;
  *) return 1 ;;
  esac
}
pkg_refresh() {
  [ "${DOTFILES_PKG_REFRESHED:-0}" = "1" ] && return 0
  case "$(os_family)" in
  debian) sudo apt-get update -qq ;;
  *) die "pkg_refresh: unsupported distro family $(os_family)" ;;
  esac
  export DOTFILES_PKG_REFRESHED=1
}
pkg_install() {
  pkg_refresh
  case "$(os_family)" in
  debian) sudo apt-get install -y -qq "$@" ;;
  *) die "pkg_install: unsupported distro family $(os_family)" ;;
  esac
}
# usage: pkg_ensure <package>...
pkg_ensure() {
  local p missing=()
  for p in "$@"; do pkg_installed "$p" || missing+=("$p"); done
  if [ "${#missing[@]}" -eq 0 ]; then
    skip "packages present: $*"
    return 0
  fi
  pkg_install "${missing[@]}"
}
# usage: pkg_candidate_version <package> -> the version apt would install, or
# nothing when the package is unknown. Lets a module take the distro package
# when it is new enough and source-build only where it is not.
pkg_candidate_version() {
  case "$(os_family)" in
  debian) apt-cache policy "$1" 2>/dev/null | awk '/Candidate:/ && $2 != "(none)" {print $2}' ;;
  *) return 0 ;;
  esac
}
# usage: version_ge <version> <floor>
version_ge() {
  [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

# usage: installed_version <cmd> [version-arg]
# Print a tool's installed version as x.y.z (PATH first, then ~/.local/bin
# and ~/.cargo/bin, which may not be on PATH yet during a fresh provision or
# in a shell that has not sourced cargo's env). Prints nothing when the tool
# is missing or its version output is unparseable. version-arg defaults to
# --version, for the tools that don't take it (go reports its version
# through a `version` subcommand and errors on --version).
installed_version() {
  local bin flag="${2:---version}"
  bin="$(command -v "$1" || true)"
  [ -z "$bin" ] && [ -x "$HOME/.local/bin/$1" ] && bin="$HOME/.local/bin/$1"
  [ -z "$bin" ] && [ -x "${CARGO_HOME:-$HOME/.cargo}/bin/$1" ] && bin="${CARGO_HOME:-$HOME/.cargo}/bin/$1"
  [ -z "$bin" ] && return 0
  "$bin" "$flag" 2>/dev/null | grep -oEm1 '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1 || true
}

# usage: at_pinned_version <cmd> <pinned-version> [version-arg]
# True only when the installed version is exactly the pin. This is the
# narrow question; pin_satisfied below asks the policy question.
at_pinned_version() {
  local cur pin="${2#v}"
  cur="$(installed_version "$1" "${3:---version}")"
  [ "$cur" = "$pin" ]
}

# usage: if ! pin_satisfied <cmd> <pinned-version> [version-arg]; then <install>
# True when the installed version is good enough to leave alone, and reports
# what it found. The pin is a floor, not an equality: a newer copy - one
# installed by hand between provisioning runs - is kept and noted rather than
# rolled back, since re-provisioning should not undo a deliberate update. The
# note is the cue to raise the floor to that version once it has proven itself.
# Missing, older, or unparseable is false, and the caller installs the pin.
#
# FORCE_PINS=1 restores exact-pin behaviour for the whole run, reinstalling
# anything that is not precisely the pin. That is the way to walk a pin
# backwards - a yanked release, a regression - where a floor would otherwise
# leave the newer copy in place.
pin_satisfied() {
  local cmd="$1" pin="${2#v}" flag="${3:---version}" cur
  cur="$(installed_version "$cmd" "$flag")"

  if [ "${FORCE_PINS:-0}" = "1" ]; then
    at_pinned_version "$cmd" "$pin" "$flag" || return 1
    skip "$cmd $cur already at pin (FORCE_PINS)"
    return 0
  fi

  [ -n "$cur" ] || return 1
  if [ "$cur" = "$pin" ]; then
    skip "$cmd $cur already at pin"
    return 0
  fi
  if version_ge "$cur" "$pin"; then
    note "$cmd $cur is newer than the pin ($2); keeping it"
    return 0
  fi
  return 1
}

# usage: verify_sha256 <file> <expected-sha256>
verify_sha256() {
  local file="$1" expected="$2"
  printf '%s  %s\n' "$expected" "$file" | sha256sum --check --quiet ||
    die "sha256 mismatch for $file (expected $expected) - refusing to install"
}

# usage: fetch_url <url> <dest-file>
# curl with retries: transient failures (connection resets, timeouts, 5xx)
# are retried before giving up, so one flaky transfer doesn't abort a whole
# provisioning run. --retry-all-errors is safe here because every download
# is sha256-verified before anything is installed.
fetch_url() {
  local url="$1" dest="$2"
  curl -fsSL --retry 5 --retry-delay 2 --retry-all-errors -o "$dest" "$url"
}

# usage: install_release_binary <url> <sha256> <member-path-in-tar> <dest-name> [strip]
# Download a release tarball, verify it against the recorded sha256, and
# install one binary from it into ~/.local/bin. tar reads the compression
# from the archive itself, so .tar.gz and .tar.xz both work. On failure the
# temp dir is left behind for inspection.
install_release_binary() {
  local url="$1" sha256="$2" member="$3" dest="$4" strip="${5:-0}"
  local tmp
  tmp="$(mktemp -d)"
  fetch_url "$url" "$tmp/archive" || die "download failed: $url"
  verify_sha256 "$tmp/archive" "$sha256"
  tar -xaf "$tmp/archive" -C "$tmp" --strip-components="$strip" "$member" ||
    die "extract failed: $member from $url"
  install -m 0755 "$tmp/$(basename "$member")" "$HOME/.local/bin/$dest" ||
    die "install failed: $dest"
  rm -rf "$tmp"
}

# usage: install_release_deb <url> <sha256> <package>
# Download a release .deb, verify it against the recorded sha256, and install
# it with dpkg. Used where upstream's .deb is the artifact users reach for by
# hand: installing the same way puts the pinned copy exactly where a manual
# `dpkg -i` would land it, so the two can't end up shadowing each other.
install_release_deb() {
  local url="$1" sha256="$2" pkg="$3"
  local tmp
  tmp="$(mktemp -d)"
  fetch_url "$url" "$tmp/$pkg.deb" || die "download failed: $url"
  verify_sha256 "$tmp/$pkg.deb" "$sha256"
  sudo dpkg -i "$tmp/$pkg.deb" || die "dpkg install failed: $pkg"
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
  fetch_url "$url" "$tmp/bundle" || die "download failed: $url"
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
  fetch_url "$url" "$tmp/installer.sh" || die "download failed: $url"
  verify_sha256 "$tmp/installer.sh" "$sha256"
  bash "$tmp/installer.sh" || die "installer failed: $url"
  rm -rf "$tmp"
}

# usage: report_stale_copies <tool> <pinned-path>
# A tool this repo manages can also exist elsewhere on PATH (old manual
# installs in /usr/local/bin, cargo, apt, or an earlier layout of these
# scripts). Flag every duplicate and say how to remove it. A duplicate that
# comes first on PATH is worse than clutter: it silently wins over the
# pinned copy, so `tool --version` reports the stale one and a re-install of
# the real thing looks like it did nothing. Returns 1 if anything was found.
report_stale_copies() {
  local tool="$1" pinned="$2" pinned_real first_real path pkg rm_hint found=0
  [ -x "$pinned" ] || return 0
  # On a merged-usr system /bin and /sbin are symlinks into /usr, so one
  # binary is reachable under two paths and would otherwise be reported as
  # a duplicate of itself. Compare the resolved file, not the spelling.
  pinned_real="$(readlink -f "$pinned")"
  first_real="$(readlink -f "$(command -v "$tool")" 2>/dev/null)"
  while IFS= read -r path; do
    [ "$(readlink -f "$path")" = "$pinned_real" ] && continue
    found=1
    # dpkg-owned copies (e.g. an old apt lsd/kitty) must go through apt,
    # since deleting the file by hand leaves dpkg in an inconsistent state
    rm_hint="sudo rm $path"
    case "$path" in "$HOME"/*) rm_hint="rm $path" ;; esac
    if pkg="$(dpkg -S "$path" 2>/dev/null | head -n1 | cut -d: -f1)" && [ -n "$pkg" ]; then
      rm_hint="sudo apt-get remove $pkg"
    fi
    if [ "$first_real" = "$pinned_real" ]; then
      note "stale $tool at $path (shadowed by $pinned; clean up with: $rm_hint)"
    else
      printf '    [WARN] %s on PATH resolves to %s, which shadows the pinned %s; remove it with: %s\n' \
        "$tool" "$path" "$pinned" "$rm_hint"
    fi
  done < <(type -aP "$tool" 2>/dev/null | awk '!seen[$0]++')
  return "$found"
}

# ----------------------------------------------------------------------------
# Nerd Fonts (one release pins all per-font archives; sha256s from the
# release's published SHA-256.txt). kitty uses JetBrainsMono; the X11 module
# adds Iosevka and FantasqueSansMono for rofi, so the pins live here.
# ----------------------------------------------------------------------------
NERD_FONTS_VERSION="v3.4.0"
# shellcheck disable=SC2034  # consumed by the scripts that source this lib
NERD_FONT_JETBRAINSMONO_SHA256="ef552a3e638f25125c6ad4c51176a6adcdce295ab1d2ffacf0db060caf8c1582"
# shellcheck disable=SC2034
NERD_FONT_IOSEVKA_SHA256="213ee24cda99ca84d0a8326de133e7e8b2baf9ba23659ce829f589f771d357d2"
# shellcheck disable=SC2034
NERD_FONT_FANTASQUESANSMONO_SHA256="462b5490475fb8560dded4eb6cdd9cfd0049b800acee329094def095557d0ffd"

# usage: install_nerd_font <ArchiveName> <sha256>
# Installs one nerd-fonts archive into a versioned directory under
# ~/.local/share/fonts/nerd-fonts/. The directory name is the pin check;
# older versions of the same font are removed so machines converge, and
# the fontconfig cache is refreshed only when something changed.
install_nerd_font() {
  local name="$1" sha256="$2"
  local fonts_root="$HOME/.local/share/fonts/nerd-fonts"
  local dest="$fonts_root/$name-$NERD_FONTS_VERSION"
  log "nerd-font $name $NERD_FONTS_VERSION"
  if [ -d "$dest" ]; then
    skip "$name $NERD_FONTS_VERSION already installed"
    return 0
  fi
  local tmp
  tmp="$(mktemp -d)"
  fetch_url \
    "https://github.com/ryanoasis/nerd-fonts/releases/download/$NERD_FONTS_VERSION/$name.tar.xz" \
    "$tmp/font.tar.xz" ||
    die "download failed: nerd-font $name $NERD_FONTS_VERSION"
  verify_sha256 "$tmp/font.tar.xz" "$sha256"
  mkdir -p "$tmp/font"
  tar -xJf "$tmp/font.tar.xz" -C "$tmp/font" || die "extract failed: $name"
  mkdir -p "$fonts_root"
  rm -rf "$fonts_root/$name-"*
  mv "$tmp/font" "$dest"
  rm -rf "$tmp"
  # The versioned dir doubles as the pin check, so it must not survive a
  # failed cache rebuild - remove it before dying to keep the step atomic.
  fc-cache -f "$fonts_root" >/dev/null ||
    { rm -rf "$dest"; die "fc-cache failed (is fontconfig installed?)"; }
}

# ----------------------------------------------------------------------------
# uv is needed by more than one module (cli-tools; the X11 module installs
# the monitor-manager with it), so its pin lives here as the single source
# of truth.
# ----------------------------------------------------------------------------
UV_VERSION="0.11.20"
UV_SHA256="5de211d9278af365497d387e25316907b3b4a9f25b4476dd6dbf238d6f85cff3"

install_uv() {
  log "uv $UV_VERSION"
  if ! pin_satisfied uv "$UV_VERSION"; then
    install_release_binary \
      "https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-x86_64-unknown-linux-gnu.tar.gz" \
      "$UV_SHA256" "uv-x86_64-unknown-linux-gnu/uv" uv 1
  fi
}
