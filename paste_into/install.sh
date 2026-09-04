#!/usr/bin/env bash
# Installs paste-into-folder.py into ~/.local/bin (no service menu; this is
# meant to be bound to a Global Shortcut).
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIN_DIR"

cp "$SCRIPT_DIR/paste-into-folder.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/paste-into-folder.py"

echo "Installed paste_into."
echo "Remember to bind 'paste-into-folder.py' to a Global Shortcut yourself (System Settings > Shortcuts > Custom Shortcuts)."
