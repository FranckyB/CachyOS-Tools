#!/usr/bin/env bash
# Installs navigate-sibling.py into ~/.local/bin and its service menus into
# ~/.local/share/kio/servicemenus, then enables Dolphin's "Show full path in
# title bar" setting (required for the global-shortcut, no-argument usage).
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
MENU_DIR="$HOME/.local/share/kio/servicemenus"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIN_DIR" "$MENU_DIR"

cp "$SCRIPT_DIR/navigate-sibling.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/navigate-sibling.py"

for f in go-to-next-sibling.desktop go-to-prev-sibling.desktop; do
    sed "s/\[USER\]/$USER/g" "$SCRIPT_DIR/$f" > "$MENU_DIR/$f"
done

if command -v kwriteconfig6 >/dev/null 2>&1; then
    kwriteconfig6 --file dolphinrc --group General --key ShowFullPathInTitlebar true
elif command -v kwriteconfig5 >/dev/null 2>&1; then
    kwriteconfig5 --file dolphinrc --group General --key ShowFullPathInTitlebar true
else
    echo "Note: kwriteconfig not found; enable Dolphin's 'Show full path in title bar' setting manually."
fi

echo "Installed navigate_sibling."
echo "Remember to bind 'navigate-sibling.py next' / 'navigate-sibling.py prev' to Global Shortcuts yourself (System Settings > Shortcuts > Custom Shortcuts)."
