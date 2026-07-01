#!/usr/bin/env bash
# Bash wrapper for monitor-manager.py interactive mode
# Designed to be called from sxhkd or other hotkey daemons

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Use kitty launch script (handles font size based on resolution)
# Run monitor-manager in interactive mode with --hold to keep terminal open
~/.config/kitty/launch.sh --title "Monitor Manager" --hold bash -c "cd '$PROJECT_ROOT' && uv run python monitor-manager.py interactive"
