# paste_into

Paste the clipboard's cut/copied files into the folder currently selected in
the active Dolphin window, without navigating into it.

## Requirements

- `qdbus6` (ships with Plasma/KDE)

## Install

```sh
./install.sh
```

Copies `paste-into-folder.py` to `~/.local/bin/`. There's no `.desktop`
service menu for this one.

## Usage

Bind it to a KDE Global Shortcut yourself — `install.sh` does not do this
part for you — in System Settings → Shortcuts → Custom Shortcuts → New →
Global Shortcut → Command/URL:

```
paste-into-folder.py
```

e.g. bound to Ctrl+Alt+V. Requires exactly one folder selected in the
active Dolphin view and something previously cut/copied onto the clipboard
(e.g. via Ctrl+X). Since this runs as a global shortcut, it only acts when
Dolphin is the focused window; otherwise it does nothing.
