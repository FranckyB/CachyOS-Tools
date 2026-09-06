# group_files

Dolphin right-click menu that groups the selected files/folders into a new
subfolder, prompting for the folder name via `kdialog`.

## Requirements

- `kdialog` (ships with Plasma/KDE)

## Install

```sh
./install.sh
```

Copies `group-files.py` to `~/.local/bin/` and installs the **Group Files
into Folder** service menu into `~/.local/share/kio/servicemenus/`.

## Usage

Select one or more files/folders in Dolphin, right-click, and choose **Group
Files into Folder**. Enter a folder name (defaults to `Group`; a numeric
suffix is added if the name is already taken) and the selected items are
moved into it. This is a Dolphin context-menu action only, not a global
shortcut.

### Optional: bind it to Ctrl+G

If you'd like to trigger this with a keyboard shortcut (e.g. Ctrl+G) instead
of right-clicking every time, you must set it up as a **Dolphin Shortcut**,
not a KDE Global Shortcut — service menu actions like this one only show up
under Dolphin's own shortcut settings, not the system-wide Custom Shortcuts:

1. Open Dolphin → Settings → Configure Shortcuts...
2. Find **Group Files into Folder** in the list.
3. Assign it the Ctrl+G shortcut.

`install.sh` does not do this part for you.

## Changes

### 2026-09-06

- Rewrote `group-files.sh` as `group-files.py`, fixing a bug where a mixed
  selection of files and folders could create the new group folder *inside*
  one of the selected folders (whenever the first selected item happened to
  be a directory, it was mistakenly treated as the target directory instead
  of using its parent). The parent directory of the first selected item is
  now always used as the target, and folders are moved along with files
  (previously only files were moved; selected folders were silently left
  behind).

