#!/usr/bin/env bash
# Installs move-up.py into ~/.local/bin and its service menu into
# ~/.local/share/kio/servicemenus, then enables Dolphin's "Show full path in
# title bar" setting (required for the no-argument, active-window usage).
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
MENU_DIR="$HOME/.local/share/kio/servicemenus"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIN_DIR" "$MENU_DIR"

cp "$SCRIPT_DIR/move-up.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/move-up.py"

add_service_menu="y"
read -rp "Install Dolphin service menu entry (right-click menu + assignable shortcut)? [Y/n] " add_service_menu
if [[ ! "$add_service_menu" =~ ^[Nn]$ ]]; then
    sed "s/\[USER\]/$USER/g" "$SCRIPT_DIR/move-up.desktop" > "$MENU_DIR/move-up.desktop"
    chmod +x "$MENU_DIR/move-up.desktop"
    echo "Installed service menu into $MENU_DIR."
fi

if command -v kwriteconfig6 >/dev/null 2>&1; then
    kwriteconfig6 --file dolphinrc --group General --key ShowFullPathInTitlebar true
elif command -v kwriteconfig5 >/dev/null 2>&1; then
    kwriteconfig5 --file dolphinrc --group General --key ShowFullPathInTitlebar true
else
    echo "Note: kwriteconfig not found; enable Dolphin's 'Show full path in title bar' setting manually."
fi

echo "Installed move_up."
echo "To bind a keyboard shortcut in Dolphin: go to"
echo "Settings > Configure Keyboard Shortcuts, find 'Move Contents Up',"
echo "and assign a shortcut of your choice."