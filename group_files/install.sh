#!/usr/bin/env bash
# Installs group-files.sh into ~/.local/bin and its service menu into
# ~/.local/share/kio/servicemenus (Dolphin right-click menu only).
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
MENU_DIR="$HOME/.local/share/kio/servicemenus"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIN_DIR" "$MENU_DIR"

cp "$SCRIPT_DIR/group-files.sh" "$BIN_DIR/"
chmod +x "$BIN_DIR/group-files.sh"

sed "s/\[USER\]/$USER/g" "$SCRIPT_DIR/group-files.desktop" > "$MENU_DIR/group-files.desktop"

echo "Installed group_files."
