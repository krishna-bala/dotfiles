#!/bin/sh
# Shared logic for the identity-guarding hooks in this directory. Sourced,
# never run directly (git only executes files named after a hook).
#
# These hooks apply to this repo only: ./install points this clone's
# core.hooksPath at git/hooks, and no other repo is touched. The guard exists
# to stop a work identity from ever committing here. It is a guard against
# habit, not against an attacker: --no-verify, `git -c core.hooksPath=`, and
# editing this file all bypass it. Enforcement that cannot be bypassed has to
# live on the remote.

# The only committer addresses allowed to create commits in this repo:
# the personal identity and the one Claude Code web sessions commit under.
guard_allowed_emails() {
    printf '%s\n' 'krishna0bala@proton.me' 'noreply@anthropic.com'
}

# Lowercase, since the domain half of an address is case-insensitive and the
# local half is in practice.
guard_normalize() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

# The address inside a "Name <addr> 1730000000 +0000" ident string.
guard_ident_email() {
    _ident=${1#*<}
    guard_normalize "${_ident%%>*}"
}

guard_email_allowed() {
    _candidate=$(guard_normalize "$1")
    for _allowed in $(guard_allowed_emails); do
        if [ "$_candidate" = "$_allowed" ]; then
            return 0
        fi
    done
    return 1
}

# Reject the commit about to be created if it would carry an unlisted
# committer. The committer, not the author, is the identity being checked:
# the committer is whoever is running git right now, which is the thing that
# leaks, while the author is provenance that gets preserved when you amend or
# rebase someone else's work.
guard_check_committer() {
    _email=$(guard_ident_email "$(git var GIT_COMMITTER_IDENT)")
    if guard_email_allowed "$_email"; then
        return 0
    fi

    cat >&2 <<EOF
$(basename "$0"): refusing to commit as <$_email>.

Committers allowed in this repo:
$(guard_allowed_emails | sed 's/^/  /')

Set the right identity for this repo:
  git config user.email <address>
EOF
    return 1
}
