#!/usr/bin/env bash
#
# git/provision.sh - a current git. gitconfig enables feature.manyFiles,
# whose index format git older than 2.40 refuses to read, so on Ubuntu the
# git-core PPA is added ahead of the distro package. Other Debian-family
# distros take the distro package; check `git --version` there.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root

log "git"
if [ "$(os_id)" = "ubuntu" ]; then
  if ! grep -rq "git-core/ppa" /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null; then
    pkg_ensure software-properties-common
    sudo add-apt-repository -y ppa:git-core/ppa
    sudo apt-get update -qq
  fi
fi
pkg_ensure git
git_version="$(installed_version git)"
version_ge "$git_version" 2.40 ||
  note "git $git_version is older than 2.40; gitconfig's feature.manyFiles index will not be readable by it"
