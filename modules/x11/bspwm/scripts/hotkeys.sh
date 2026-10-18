#!/usr/bin/env bash
# Searchable cheatsheet of the sxhkd hotkeys. Bound to super+slash in
# sxhkdrc.
#
# Parses sxhkdrc on every run, so it can never drift from the real
# bindings. A binding's description is the first line of the comment block
# directly above it (falling back to its command), and "## Name ##" banner
# lines become section labels. Commented-out bindings are not listed.
#
# Shown with fzf in a floating, sticky kitty window rather than rofi: rofi
# grabs the keyboard, which would leave sxhkd deaf while the sheet is open.
#
# Usage: hotkeys.sh           toggle the cheatsheet window
#        hotkeys.sh --fzf     browse the table with fzf (runs inside the window)
#        hotkeys.sh --print   write the table to stdout

set -euo pipefail

SXHKDRC="${SXHKDRC:-${XDG_CONFIG_HOME:-$HOME/.config}/sxhkd/sxhkdrc}"
CLASS=sxhkd-hotkeys
KITTY="$(command -v kitty || echo "$HOME/.local/bin/kitty")"

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
            n++; chords[n] = chord; sections[n] = section; descs[n] = d
            if (length(chord) > cw) cw = length(chord)
            if (length(section) > sw) sw = length(section)
            flush_comment()
        }
        # Columns sized to their widest entry, so rows fit the window.
        END {
            for (i = 1; i <= n; i++)
                printf "%-*s  %-*s  %s\n", cw, chords[i], sw, sections[i], descs[i]
        }
    ' "$SXHKDRC"
}

case "${1:-}" in
--print)
    table
    exit 0
    ;;
--fzf)
    # Enter does nothing (the sheet is for reading); Esc closes it.
    # no-hscroll keeps the key column in view instead of scrolling a long
    # row to its match; fzf has no manual sideways scroll, so ctrl-/ (its
    # default toggle-wrap-word) wraps long rows to read them in full.
    table | fzf --no-hscroll --no-sort --layout=reverse \
        --prompt 'hotkeys> ' --header 'ctrl-/ wrap long rows   esc close' \
        --bind 'enter:ignore' || true
    exit 0
    ;;
esac

# A second press closes the open sheet instead of stacking another.
if pkill -f -- "--class $CLASS"; then
    exit 0
fi

# One-shot rule: float it centred, and keep it on every desktop so it stays
# in view while trying the hotkeys it lists.
bspc rule -a "$CLASS" -o state=floating sticky=on center=on rectangle=1200x700+0+0
exec "$KITTY" --class "$CLASS" -o font_size=11 -o remember_window_size=no \
    "$0" --fzf
