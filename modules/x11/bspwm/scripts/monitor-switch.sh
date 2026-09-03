#!/usr/bin/env bash
# Opens monitor-manager's interactive profile picker in a kitty window.
# Designed to be called from sxhkd or other hotkey daemons.

set -euo pipefail

MONITOR_MANAGER="$(command -v monitor-manager || echo "$HOME/.local/bin/monitor-manager")"

# Use kitty launch script (handles font size based on resolution)
# --hold keeps the window open after the picker exits
~/.config/kitty/launch.sh --title "Monitor Manager" --hold "$MONITOR_MANAGER" interactive
