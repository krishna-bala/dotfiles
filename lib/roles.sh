#!/usr/bin/env bash
#
# roles.sh - turn a machine's role selection into an ordered module list.
# Sourced by ./install and ./provision.sh after lib/common.sh; REPO_ROOT
# must point at the repo.
#
# A module is a directory under modules/ holding one tool's config
# (install.conf.yaml, applied by dotbot) and/or the provisioning that makes
# that config work (provision.sh). A role is a file under roles/ naming the
# modules a kind of machine gets, one per line; a line "@other" pulls in
# another role's modules first, so roles nest (desktop = workstation + X11).
#
# The selection a machine was last installed with is saved to
# $XDG_CONFIG_HOME/dotfiles/roles, so a bare ./install or ./provision.sh
# re-applies the same thing - the flag is only needed the first time, or to
# change a machine's kind.

ROLES_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles/roles"

# Emit every module a role or module name expands to, in order, with
# repeats (a module reached through two roles) kept for the caller to drop.
_expand_target() {
  local name="$1" line
  if [ -f "$REPO_ROOT/roles/$name" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      line="${line%%#*}"
      line="${line//[[:space:]]/}"
      [ -n "$line" ] || continue
      case "$line" in
      @*) _expand_target "${line#@}" ;;
      *)
        [ -d "$REPO_ROOT/modules/$line" ] ||
          die "roles/$name names module '$line', but modules/$line does not exist"
        printf '%s\n' "$line"
        ;;
      esac
    done <"$REPO_ROOT/roles/$name"
  elif [ -d "$REPO_ROOT/modules/$name" ]; then
    printf '%s\n' "$name"
  else
    die "unknown role or module: '$name' (roles: $(list_roles | tr '\n' ' '))"
  fi
}

# usage: resolve_modules <role-or-module>... -> module names, one per line,
# first occurrence wins so every module is applied exactly once.
resolve_modules() {
  local t
  for t in "$@"; do _expand_target "$t"; done | awk '!seen[$0]++'
}

list_roles() {
  local f
  for f in "$REPO_ROOT"/roles/*; do
    [ -f "$f" ] && basename "$f"
  done
}

# usage: check_requires <module>...
# A module may ship a `requires` file naming modules it cannot work without
# (sxhkd's bindings launch kitty; desktop-session-log greps with rg). Refuse a
# selection that leaves one out, rather than discovering it from a hotkey
# that does nothing.
check_requires() {
  local m r
  for m in "$@"; do
    [ -f "$REPO_ROOT/modules/$m/requires" ] || continue
    while IFS= read -r r || [ -n "$r" ]; do
      r="${r%%#*}"
      r="${r//[[:space:]]/}"
      [ -n "$r" ] || continue
      printf '%s\n' "$@" | grep -qx "$r" ||
        die "module '$m' requires '$r', which the selected roles do not include"
    done <"$REPO_ROOT/modules/$m/requires"
  done
}

# usage: parse_targets "$@"
# Fills TARGETS (roles/modules to apply) and PASSTHROUGH (unrecognised
# arguments, for the caller to forward or reject). --roles and --modules
# take comma-separated lists; --no-desktop is the pre-roles spelling of
# --roles workstation and still works. With no selection on the command
# line, the saved one is used.
parse_targets() {
  TARGETS=()
  PASSTHROUGH=()
  local arg
  while [ $# -gt 0 ]; do
    arg="$1"
    case "$arg" in
    --roles=* | --modules=*)
      IFS=',' read -ra _parts <<<"${arg#*=}"
      TARGETS+=("${_parts[@]}")
      ;;
    --roles | --modules)
      [ $# -ge 2 ] || die "$arg needs a value"
      IFS=',' read -ra _parts <<<"$2"
      TARGETS+=("${_parts[@]}")
      shift
      ;;
    --no-desktop)
      note "--no-desktop is the old name for --roles workstation"
      TARGETS+=(workstation)
      ;;
    *) PASSTHROUGH+=("$arg") ;;
    esac
    shift
  done
  if [ "${#TARGETS[@]}" -eq 0 ] && [ -f "$ROLES_FILE" ]; then
    mapfile -t TARGETS < <(grep -v '^\s*#' "$ROLES_FILE" | tr -s ' \t' '\n' | grep -v '^$')
    [ "${#TARGETS[@]}" -gt 0 ] && note "using saved selection from $ROLES_FILE: ${TARGETS[*]}"
  fi
  [ "${#TARGETS[@]}" -gt 0 ] ||
    die "no roles selected: pass --roles <role>[,<role>] (available: $(list_roles | tr '\n' ' ')) or --modules <module>[,...]"
}

save_targets() {
  mkdir -p "$(dirname "$ROLES_FILE")"
  printf '%s\n' "$@" >"$ROLES_FILE"
}
