#!/usr/bin/env bash
#
# go/provision.sh - the go toolchain from a pinned upstream archive
# (~/.local/go, go/gofmt symlinked into ~/.local/bin). 22.04's golang-go is
# 1.18, far behind the toolchain any current module expects. Fetched from
# dl.google.com, which is where go.dev/dl's links resolve to, so this is
# upstream's own artifact. The archive is a self-contained GOROOT and the go
# command finds it by resolving its own symlink, so ~/.local/bin/go works
# without setting GOROOT. Binaries from `go install` land in ~/go/bin, which
# bashrc adds to PATH.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root
mkdir -p "$HOME/.local/bin"

# go sha256 is upstream's published checksum for this archive (go.dev/dl lists
# one per file). Upstream names .0 releases "go1.27", not "go1.27.0", so the
# pin is whatever `go version` prints minus the "go" prefix.
GO_VERSION="1.26.5"
GO_SHA256="5c2c3b16caefa1d968a94c1daca04a7ca301a496d9b086e17ad77bb81393f053"

log "go $GO_VERSION"
if ! pin_satisfied go "$GO_VERSION" version; then
  install_release_bundle \
    "https://dl.google.com/go/go$GO_VERSION.linux-amd64.tar.gz" \
    "$GO_SHA256" go 1 go gofmt
fi
report_stale_copies go "$HOME/.local/bin/go" || true
report_stale_copies gofmt "$HOME/.local/bin/gofmt" || true
