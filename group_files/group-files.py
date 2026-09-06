#!/usr/bin/env python3
"""
Move the selected files/folders into a new folder, prompting for the folder
name via kdialog.

Intended to be bound to a keyboard shortcut *inside Dolphin itself* (Settings
-> Configure Keyboard Shortcuts -> assign a key to the "Group Files into
Folder" service-menu action installed by install.sh), rather than a KDE
global shortcut.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(0)

    paths = [Path(p) for p in sys.argv[1:]]

    # All selected items share the same parent directory; use the first
    # one's parent regardless of whether it's itself a file or a folder.
    target_dir = paths[0].parent

    # Prompt for folder name via kdialog.
    default_name = "Group"
    result = subprocess.run(
        ["kdialog", "--title", "Group Files", "--inputbox", "Enter folder name:", default_name],
        capture_output=True, text=True,
    )
    name = result.stdout.strip()

    # User cancelled or closed the dialog.
    if not name:
        return

    # Sanitize the name (remove slashes).
    name = name.replace("/", "")

    # If the name already exists, increment it.
    base = name
    counter = 1
    while (target_dir / name).exists():
        name = f"{base}_{counter:02d}"
        counter += 1

    new_folder = target_dir / name
    new_folder.mkdir()

    moved = 0
    for path in paths:
        # Skip anything that no longer exists and never move the new folder
        # into itself.
        if not path.exists() or path == new_folder:
            continue
        destination = new_folder / path.name
        if destination.exists():
            continue
        shutil.move(str(path), str(destination))
        moved += 1

    print(f"Moved {moved} item(s) into: {new_folder}")


if __name__ == "__main__":
    main()
