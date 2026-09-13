# move_up

Move every file and folder from the folder currently shown in the active
Dolphin window into that folder's parent, then replace the current tab with
the parent folder. The selected item does not matter; the action always uses
the folder shown in the active tab.

If the original folder is empty after the move, it is moved to trash. The
script checks that explicitly before trying to trash it.

## Requirements

- `qdbus6` (ships with Plasma/KDE)
- Dolphin's **"Show full path in title bar"** setting enabled — the current
  folder is read from the window title. `install.sh` enables this for you
  automatically.

## Install

```sh
./install.sh
```

Copies `move-up.py` to `~/.local/bin/` and installs the **Move Contents Up**
service menu into `~/.local/share/kio/servicemenus/`.

## Usage

In Dolphin, right-click anywhere in the folder view and choose
**Move Contents Up**, or assign a Dolphin-local keyboard shortcut via
**Settings -> Configure Keyboard Shortcuts**.

The script ignores file selection and instead uses whichever Dolphin window
is currently focused. It does nothing if Dolphin is not the active window.

Name collisions are handled with overwrite-style behavior: files replace
files, and folders are merged recursively into existing folders in the
parent, with conflicting entries overwritten by the moved copy.

Empty-folder cleanup uses `gio trash`, so on systems without a working GLib
trash backend the folder is left in place rather than being permanently
deleted.