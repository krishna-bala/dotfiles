#!/bin/bash
# shellcheck disable=SC1091,SC1090

# NOTE: Environment variable inheritance chain:
#   GDM Xsession → ~/.profile → ~/.bashrc → bspwm → sxhkd → terminals
#
# Adding/changing vars: Edit here, new terminals pick it up immediately
# Removing vars: Requires logout (sxhkd inherits at login and persists)

# Ensure ~/.local/bin is on PATH for non-interactive shells too (dedup-guarded)
[[ ":$PATH:" != *":$HOME/.local/bin:"* ]] && export PATH="$HOME/.local/bin:$PATH"

# If not running interactively, don't do anything
[ "$PS1" = "" ] && return

shopt -s histappend                # Append history file; don't overwrite.
shopt -s checkwinsize              # Update window size after each command.
HISTSIZE=                          # Maximum history length.
HISTFILESIZE=                      # Length of history file size.
HISTCONTROL=ignoredups:ignorespace # Don't duplicate lines in history.

# set variable identifying the chroot you work in (used in the prompt below)
if [ "${debian_chroot:-}" = "" ] && [ -r /etc/debian_chroot ]; then
  debian_chroot=$(cat /etc/debian_chroot)
fi

PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
  # We have color support; assume it's compliant with Ecma-48
  # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
  # a case would tend to support setf rather than setaf.)
  PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]$(__git_ps1 " (%s)")\$ '
fi

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
  test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
  alias ls='ls --color=auto'
  alias grep='grep --color=auto'
  alias fgrep='fgrep --color=auto'
  alias egrep='egrep --color=auto'
fi

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Add an "alert" alias for long running commands.  Use like so:
#   sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Alias definitions.
if [ -f ~/.bash_aliases ]; then
  . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# Terminal prompt settings
# Trim directory
export PROMPT_DIRTRIM=2
# Enable git branch in prompt
source "$HOME"/.git-prompt.sh

# pip bash completion
_pip_completion() {
  COMPREPLY=("$(COMP_WORDS="${COMP_WORDS[*]}" \
    COMP_CWORD="$COMP_CWORD" \
    PIP_AUTO_COMPLETE=1 "$1" 2>/dev/null)")
}
complete -o default -F _pip_completion pip

source "$HOME"/.bazel_completions.bash

# pyenv
if [ -d "$HOME/.pyenv" ]; then
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"
fi
# pyenv end

# pipx
if command -v pipx >/dev/null &&
  command -v register-python-argcomplete >/dev/null; then
  eval "$(register-python-argcomplete pipx)"
fi
# pipx end

# ===================================================
# >>> nvm <<<
# ===================================================
NVM_DIR=""
if [[ -z "${XDG_CONFIG_HOME-}" ]]; then
  NVM_DIR="${HOME}/.nvm"
else
  NVM_DIR="${XDG_CONFIG_HOME}/nvm"
fi
export NVM_DIR
# Maintain a ~/.nvm/current/bin symlink for tools like Mason that don't
# source bashrc
export NVM_SYMLINK_CURRENT=true

[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion
# ===================================================

# ===================================================
# >>> neovim-remote setup <<<
# ===================================================
export EDITOR=nvim
# cargo is used in nvim via mason
[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
# ===================================================

alias ls='lsd --color=auto'
alias ll='lsd -alF'
alias la='lsd -A'
alias l='lsd -CF'

# fzf integration setup
if command -v fzf >/dev/null 2>&1; then
  # Check if fzf version is 0.48.0 or later
  FZF_VERSION=$(fzf --version | cut -d ' ' -f 1)
  if [[ $(echo "$FZF_VERSION 0.48.0" | tr ' ' '\n' | sort -V | head -n 1) == "0.48.0" ]]; then
    # New method for fzf 0.48.0+
    eval "$(fzf --bash)"
  else
    # Legacy method - source ~/.fzf.bash if it exists
    [ -f ~/.fzf.bash ] && source ~/.fzf.bash
  fi
fi

# starship prompt
# Skip in non-interactive shells and dumb terminals (e.g. agentic CLIs
# like Codex/Claude Code) where prompt escapes confuse the host.
if [[ -t 1 && "$TERM" != "dumb" ]] && command -v starship &>/dev/null; then
  show_newline() {
    if [ "$NEW_LINE_BEFORE_PROMPT" = "" ]; then
      NEW_LINE_BEFORE_PROMPT=1
    elif [ "$NEW_LINE_BEFORE_PROMPT" -eq 1 ]; then
      echo ""
    fi
  }
  PROMPT_COMMAND="show_newline"
  eval "$(starship init bash)"
fi

# go install https://go.dev/doc/install
[[ -d /usr/local/go ]] && export PATH=$PATH:/usr/local/go/bin

# pnpm
export PNPM_HOME="$HOME/.local/share/pnpm"
case ":$PATH:" in
*":$PNPM_HOME:"*) ;;
*) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end

# uv autocompletion
if command -v uv &>/dev/null; then
  eval "$(uv generate-shell-completion bash)"
fi
# uv end

# Machine-local shell env (untracked; e.g. work-specific vars). No-op if absent.
[ -f "$HOME/.bashrc.local" ] && . "$HOME/.bashrc.local"
