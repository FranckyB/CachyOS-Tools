#!/usr/bin/env bash
# Installs generate_folder_thumbails.py into ~/.local/bin and its service
# menu into ~/.local/share/kio/servicemenus.
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
MENU_DIR="$HOME/.local/share/kio/servicemenus"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIN_DIR" "$MENU_DIR"

if ! python3 -c "import PIL" >/dev/null 2>&1; then
    if command -v pacman >/dev/null 2>&1; then
        echo "Pillow not found; installing python-pillow with pacman..."
        sudo pacman -S --needed python-pillow || echo "Warning: pacman install failed; install Pillow yourself with 'pip install Pillow'."
    else
        echo "Note: Pillow is required but not installed. Install it with:"
        echo "  pip install Pillow"
    fi
fi

cp "$SCRIPT_DIR/generate_folder_thumbails.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/generate_folder_thumbails.py"
cp -r "$SCRIPT_DIR/script_files" "$BIN_DIR/"

for f in generate-folder-thumbnail.desktop generate-folder-thumbnail-refresh.desktop; do
    sed "s/\[USER\]/$USER/g" "$SCRIPT_DIR/$f" > "$MENU_DIR/$f"
done

echo "Installed generate_folder_thumbnails."
