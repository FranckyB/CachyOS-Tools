# paste_into

Paste the clipboard's cut/copied files into the folder currently selected in
the active Dolphin window, without navigating into it.

## Requirements

- `qdbus6` (ships with Plasma/KDE)

## Install

```sh
./install.sh
```

Copies `paste-into-folder.py` to `~/.local/bin/` and installs the **Paste
Into Folder** service menu entry into `~/.local/share/kio/servicemenus/` —
this is what lets you assign a keyboard shortcut *inside Dolphin itself*
(see below).

## Usage

**Dolphin-scoped keyboard shortcut (recommended):** in Dolphin, go to
**Settings → Configure Keyboard Shortcuts**, find **Paste Into Folder**, and
assign a key combination to it (e.g. Ctrl+Alt+V). Because this is a
Dolphin-local shortcut rather than a KDE **global** shortcut (System
Settings → Shortcuts → Custom Shortcuts), the key combination is only
grabbed while Dolphin has focus — other applications never lose access to
it.

**Dolphin right-click menu:** right-click a selected folder and choose
**Paste Into Folder**.

Requires exactly one folder selected in the active Dolphin view and
something previously cut/copied onto the clipboard (e.g. via Ctrl+X). It
does nothing if Dolphin isn't the active window.

## Changes

### 2026-09-06

- Switched from a KDE **global** shortcuts to a Dolphin-local one (bound via
  Dolphin's own Settings → Configure Keyboard Shortcuts, using the new
  `paste-into-folder.desktop` service menu entry installed by `install.sh`).
  A global shortcut grabs the key combination system-wide, so other apps
  lose access to it even when Dolphin isn't focused; a Dolphin-local
  shortcut only fires while Dolphin has focus, leaving the key combination
  free elsewhere.

