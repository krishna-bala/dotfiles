#!/bin/bash

SOCKET_PATH="${XDG_RUNTIME_DIR:-/tmp}/kitty-$USER"
KITTY="$(command -v kitty || echo "$HOME/.local/bin/kitty")"
# The size kitty.conf sets; passed explicitly because --override below would
# otherwise reset it. Read from the config so there is one place to change it.
font_size="$(awk '$1 == "font_size" {print $2; exit}' "$HOME/.config/kitty/kitty.conf")"
font_size="${font_size:-12.0}"

if [ ! -x "$KITTY" ]; then
  printf 'kitty executable not found: %s\n' "$KITTY" >&2
  exit 1
fi

# --home flag forces local home directory (avoids inheriting kitten ssh sessions)
CWD="current"
if [ "$1" = "--home" ]; then
  CWD="$HOME"
  shift
fi

# If socket exists and is alive, use remote control to create a new OS window
if [ -S "$SOCKET_PATH" ] && "$KITTY" @ --to "unix:$SOCKET_PATH" ls &>/dev/null; then
  # Note: Cannot override font_size with remote control, uses existing instance settings
  exec "$KITTY" @ --to "unix:$SOCKET_PATH" launch --type=os-window --cwd="$CWD" "$@"
else
  rm -f "$SOCKET_PATH"
  [ "$CWD" = "current" ] && CWD="$PWD"
  exec "$KITTY" --listen-on "unix:$SOCKET_PATH" --override "font_size=$font_size" --directory="$CWD" "$@"
fi
