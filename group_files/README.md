# group_files

Dolphin right-click menu that groups the selected files into a new subfolder,
prompting for the folder name via `kdialog`.

## Requirements

- `kdialog` (ships with Plasma/KDE)

## Install

```sh
./install.sh
```

Copies `group-files.sh` to `~/.local/bin/` and installs the **Group Files
into Folder** service menu into `~/.local/share/kio/servicemenus/`.

## Usage

Select one or more files in Dolphin, right-click, and choose **Group Files
into Folder**. Enter a folder name (defaults to `Group`; a numeric suffix is
added if the name is already taken) and the selected files are moved into it.
This is a Dolphin context-menu action only, not a global shortcut.

### Optional: bind it to Ctrl+G

If you'd like to trigger this with a keyboard shortcut (e.g. Ctrl+G) instead
of right-clicking every time, you must set it up as a **Dolphin Shortcut**,
not a KDE Global Shortcut — service menu actions like this one only show up
under Dolphin's own shortcut settings, not the system-wide Custom Shortcuts:

1. Open Dolphin → Settings → Configure Shortcuts...
2. Find **Group Files into Folder** in the list.
3. Assign it the Ctrl+G shortcut.

`install.sh` does not do this part for you.
