#!/usr/bin/env bash
#
# git/provision.sh - a current git. gitconfig enables feature.manyFiles,
# whose index format git older than 2.40 refuses to read, so on Ubuntu the
# git-core PPA is added ahead of the distro package. Other Debian-family
# distros take the distro package and get a note if it is too old.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root

# gitconfig's feature.manyFiles writes an index git < 2.40 cannot read, so
# that is the floor. pkg_ensure only installs what is missing; an old git
# already on the box has to be upgraded explicitly, from the PPA on Ubuntu.
GIT_MIN_VERSION="2.40"

log "git (>= $GIT_MIN_VERSION)"
git_version="$(installed_version git)"
if [ -n "$git_version" ] && version_ge "$git_version" "$GIT_MIN_VERSION"; then
  skip "git $git_version satisfies the $GIT_MIN_VERSION floor"
else
  if [ "$(os_id)" = "ubuntu" ]; then
    if ! grep -rq "git-core/ppa" /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null; then
      pkg_ensure software-properties-common
      sudo add-apt-repository -y ppa:git-core/ppa
      sudo apt-get update -qq
      export DOTFILES_PKG_REFRESHED=1
    fi
  fi
  pkg_install git
  git_version="$(installed_version git)"
  version_ge "$git_version" "$GIT_MIN_VERSION" ||
    note "git $git_version is still older than $GIT_MIN_VERSION; gitconfig's feature.manyFiles index will not be readable by it"
fi
