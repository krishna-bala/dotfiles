#!/usr/bin/env bash
#
# common.sh - logging and failure helpers shared by ./install, ./provision.sh,
# and everything under lib/. Source it; it is not executable on its own.
#
# Philosophy: fail early and loudly. Any failure is fatal, never
# warn-and-continue.

log() { printf '\n==> [%s] %s\n' "$(date '+%F %T')" "$*"; }
skip() { printf '    [skip] %s\n' "$*"; }
note() { printf '    [note] %s\n' "$*"; }
die() {
  printf '    [FATAL] %s\n' "$*" >&2
  exit 1
}
have() { command -v "$1" >/dev/null 2>&1; }
