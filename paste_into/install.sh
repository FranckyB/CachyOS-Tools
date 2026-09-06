#!/usr/bin/env bash
# Installs paste-into-folder.py into ~/.local/bin and its service menu into
# ~/.local/share/kio/servicemenus, so a shortcut can be assigned to it inside
# Dolphin itself (Settings > Configure Keyboard Shortcuts).
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
MENU_DIR="$HOME/.local/share/kio/servicemenus"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIN_DIR" "$MENU_DIR"

cp "$SCRIPT_DIR/paste-into-folder.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/paste-into-folder.py"

sed "s/\[USER\]/$USER/g" "$SCRIPT_DIR/paste-into-folder.desktop" > "$MENU_DIR/paste-into-folder.desktop"
chmod +x "$MENU_DIR/paste-into-folder.desktop"

echo "Installed paste_into."
echo "To bind a keyboard shortcut to Dolphin: in Dolphin, go to"
echo "Settings > Configure Keyboard Shortcuts, find 'Paste Into Folder', and assign a"
echo "shortcut key to it."
