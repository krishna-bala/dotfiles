#!/usr/bin/env bash

# Open the Google Calendar PWA if one is installed, otherwise fall back to
# calendar.google.com in the default browser.
#
# Browsers install PWAs as desktop entries named
# <browser>-<app-id>-<profile>.desktop, so the filename can't be pinned;
# match on the entry's Name= instead, which is the site's app name.

apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

desktop_file=$(grep -lis '^Name=Google Calendar' "$apps_dir"/*.desktop 2>/dev/null | head -n 1)

if [[ -n "$desktop_file" ]]; then
    if command -v gtk-launch >/dev/null; then
        exec gtk-launch "$(basename "$desktop_file" .desktop)"
    elif command -v gio >/dev/null; then
        exec gio launch "$desktop_file"
    fi
fi

exec xdg-open "https://calendar.google.com/"
