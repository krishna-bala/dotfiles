#!/usr/bin/env bash
# Searchable cheatsheet of the sxhkd hotkeys. Bound to super+slash in
# sxhkdrc.
#
# Parses sxhkdrc on every run, so it can never drift from the real
# bindings. A binding's description is the first line of the comment block
# directly above it (falling back to its command), and "## Name ##" banner
# lines become section labels. Commented-out bindings are not listed.
#
# Usage: hotkeys.sh           show in rofi
#        hotkeys.sh --print   write the table to stdout

set -euo pipefail

SXHKDRC="${SXHKDRC:-${XDG_CONFIG_HOME:-$HOME/.config}/sxhkd/sxhkdrc}"
THEME="$HOME/.config/polybar/shades/scripts/rofi/launcher.rasi"

table() {
    awk '
        function flush_comment() { desc = ""; in_comment = 0 }
        /^#+$/                 { next }
        /^## .* ##$/           { section = $0; gsub(/^## | ##$/, "", section); flush_comment(); next }
        /^#/                   {
            line = $0; sub(/^#[[:space:]]*/, "", line)
            if (!in_comment && line != "") { desc = line; in_comment = 1 }
            next
        }
        /^[[:space:]]*$/       { flush_comment(); next }
        /^[[:space:]]/         { if (pending) { emit($0) } ; next }
        {
            chord = $0
            gsub(/@/, "", chord)
            # "{_,shift + }w" -> "[shift +] w": an optional modifier
            while (match(chord, /\{_,[^}]*\}/)) {
                opt = substr(chord, RSTART + 3, RLENGTH - 4)
                sub(/ $/, "", opt)
                chord = substr(chord, 1, RSTART - 1) "[" opt "] " substr(chord, RSTART + RLENGTH)
            }
            pending = 1
        }
        function emit(cmd,   d) {
            pending = 0
            d = desc
            if (d == "") { d = cmd; sub(/^[[:space:]]+/, "", d) }
            if (length(d) > 70) d = substr(d, 1, 67) "..."
            printf "%-38s  %-26s  %s\n", chord, section, d
            flush_comment()
        }
    ' "$SXHKDRC"
}

if [ "${1:-}" = "--print" ]; then
    table
    exit 0
fi

# Rofi grabs the keyboard, so pressing the hotkey again would do nothing;
# a second press closes the open cheatsheet instead of stacking another.
if pgrep -f 'rofi .*-p hotkeys' >/dev/null; then
    pkill -f 'rofi .*-p hotkeys'
    exit 0
fi

table | rofi -dmenu -i -no-custom -p hotkeys \
    -theme "$THEME" \
    -theme-str 'window { width: 1200px; }' \
    -theme-str 'element-text { font: "JetBrainsMono Nerd Font Mono 13"; }' \
    -theme-str 'listview { lines: 18; }' \
    >/dev/null || true
