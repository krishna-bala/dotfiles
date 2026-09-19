#!/usr/bin/env bash
# Build the SNI-to-XEmbed bridge with guards for Proton GTK4's missing
# IconPixmap/ToolTip properties. Keep the system's unmanaged copy untouched.
set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"
require_not_root

SNIXEMBED_COMMIT="6339bafee3c766be3525f20f9766b04e5860536f"
SNIXEMBED_PATCH="$MODULE_DIR/patches/snixembed-optional-properties.patch"
patch_hash="$(sha256sum "$SNIXEMBED_PATCH" | cut -c1-12)"
SNIXEMBED_VERSION="6339baf-proton-$patch_hash"
SNIXEMBED_BIN="$HOME/.local/bin/snixembed-proton"

log "snixembed (Proton-compatible SNI bridge)"
if [ -x "$SNIXEMBED_BIN" ] &&
   [ "$("$SNIXEMBED_BIN" --version)" = "version: $SNIXEMBED_VERSION" ]; then
  skip "snixembed $SNIXEMBED_VERSION already installed"
  exit 0
fi

pkg_ensure git build-essential valac pkg-config libgtk-3-dev libdbusmenu-gtk3-dev
tray_build_dir="$(mktemp -d)"
trap 'rm -rf "$tray_build_dir"' EXIT
git -C "$tray_build_dir" init --quiet
git -C "$tray_build_dir" fetch --quiet --depth 1 \
  https://git.sr.ht/~steef/snixembed "$SNIXEMBED_COMMIT"
git -C "$tray_build_dir" -c advice.detachedHead=false checkout --quiet FETCH_HEAD
[ "$(git -C "$tray_build_dir" rev-parse HEAD)" = "$SNIXEMBED_COMMIT" ] ||
  die "snixembed source did not match the reviewed commit"
git -C "$tray_build_dir" apply --check "$SNIXEMBED_PATCH"
git -C "$tray_build_dir" apply "$SNIXEMBED_PATCH"
printf 'const string VERSION = "%s";\n' "$SNIXEMBED_VERSION" > "$tray_build_dir/version.vala"
# Upstream's phony version target would replace our patch-aware build stamp.
make -C "$tray_build_dir" -o version.vala
mkdir -p "$HOME/.local/bin"
install -m755 "$tray_build_dir/snixembed" "$SNIXEMBED_BIN"
note "installed snixembed $SNIXEMBED_VERSION"
