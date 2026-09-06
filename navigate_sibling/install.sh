#!/usr/bin/env bash
# Installs navigate-sibling.py into ~/.local/bin and its service menus into
# ~/.local/share/kio/servicemenus, then enables Dolphin's "Show full path in
# title bar" setting (required for the no-argument, active-window usage).
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
MENU_DIR="$HOME/.local/share/kio/servicemenus"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIN_DIR" "$MENU_DIR"

cp "$SCRIPT_DIR/navigate-sibling.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/navigate-sibling.py"

# The service menu entries are how this tool gets a keyboard shortcut *inside*
# Dolphin (Settings -> Configure Keyboard Shortcuts), instead of a KDE global
# shortcut, so they're installed by default.
add_service_menu="y"
read -rp "Install Dolphin service menu entries (right-click menu + assignable shortcut)? [Y/n] " add_service_menu
if [[ ! "$add_service_menu" =~ ^[Nn]$ ]]; then
    for f in go-to-next-sibling.desktop go-to-prev-sibling.desktop; do
        sed "s/\[USER\]/$USER/g" "$SCRIPT_DIR/$f" > "$MENU_DIR/$f"
        chmod +x "$MENU_DIR/$f"
    done
    echo "Installed service menus into $MENU_DIR."
fi

if command -v kwriteconfig6 >/dev/null 2>&1; then
    kwriteconfig6 --file dolphinrc --group General --key ShowFullPathInTitlebar true
elif command -v kwriteconfig5 >/dev/null 2>&1; then
    kwriteconfig5 --file dolphinrc --group General --key ShowFullPathInTitlebar true
else
    echo "Note: kwriteconfig not found; enable Dolphin's 'Show full path in title bar' setting manually."
fi

echo "Installed navigate_sibling."
echo "To bind keyboard shortcuts to Dolphin: in Dolphin, go to"
echo "Settings > Configure Keyboard Shortcuts, find 'Go to Next/Previous Sibling Folder',"
echo "and assign a shortcut of your choice key to each."
