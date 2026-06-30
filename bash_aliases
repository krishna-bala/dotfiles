#!/bin/bash

# ======================
# >>> misc functions <<<
# ======================
rg() {
  command rg -p "$@" | less -RFX
}
# >>> misc functions end

# ============
# >>> tmux <<<
# ============
tmat() {
  if [ "$#" -eq 1 ]; then
    tmux a -t "$1"
  else
    echo "Usage: tmat <session-name>"
  fi
}

tmns() {
  if [ "$#" -eq 1 ]; then
    tmux new -s "$1"
  else
    echo "Usage: tmns <session-name>"
  fi
}

tmks() {
  if [ "$#" -eq 1 ]; then
    tmux kill-session -t "$1"
  else
    tmux kill-server
  fi
}

tmls() {
  tmux ls
}
# >>> tmux end

# ===========
# >>> git <<<
# ===========
grom() {
  git rebase -i origin/master
}

gdmb() {
  if [ "$#" -eq 0 ]; then
    git difftool --merge-base origin/master
  elif [ "$#" -eq 1 ]; then
    git difftool --merge-base "$1"
  elif [ "$#" -eq 2 ]; then
    git difftool --merge-base "$2" "$1"
  fi
}

source /usr/share/bash-completion/completions/git
__git_complete gdmb _git_difftool

gd() {
  git diff "$@"
}

gds() {
  git diff --staged "$@"
}

gr() {
  git restore "$@"
}

grs() {
  git restore --staged "$@"
}

lg() {
  lazygit
}

gwa() {
  git worktree add ".worktrees/$1" "$1"
}
__git_complete gwa _git_checkout
# >>> git end

# ===============
# >>> kittens <<<
# ===============
kssh() {
  kitty +kitten ssh "$@"
}
# ===============
