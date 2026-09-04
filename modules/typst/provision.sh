#!/usr/bin/env bash
#
# typst/provision.sh - typst from a pinned upstream archive. Not packaged for
# 22.04 at all, and upstream's own instructions are "unpack the archive, put
# it on PATH" - the same thing, with the download pinned and verified. Only a
# musl build is published for linux x86_64; it is statically linked, so it
# runs whatever the host glibc is. `typst update` self-updates the binary in
# place, and because the pin is a floor, a copy updated that way is kept and
# noted rather than rolled back.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root
mkdir -p "$HOME/.local/bin"

# typst publishes no checksum file; this sha256 was computed from the reviewed
# download. `typst --version` prints the release tag's commit alongside the
# version (0.15.1 -> 9dfd3a08), which is a second check that the installed
# binary is built from the tag that was reviewed.
TYPST_VERSION="0.15.1"
TYPST_SHA256="a6d077d0a95eed5a2eba715b2dae06be954f624ccbf85758a03f389ded33118c"

log "typst $TYPST_VERSION"
if ! pin_satisfied typst "$TYPST_VERSION"; then
  install_release_binary \
    "https://github.com/typst/typst/releases/download/v$TYPST_VERSION/typst-x86_64-unknown-linux-musl.tar.xz" \
    "$TYPST_SHA256" "typst-x86_64-unknown-linux-musl/typst" typst 1
fi
report_stale_copies typst "$HOME/.local/bin/typst" || true
