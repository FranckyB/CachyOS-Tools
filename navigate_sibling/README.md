# navigate_sibling

Go to the next/previous sibling folder of the folder currently shown in the
active Dolphin window, replacing the current tab in place. Skips hidden
folders and stops at the first/last sibling.

## Requirements

- `qdbus6` (ships with Plasma/KDE)
- Dolphin's **"Show full path in title bar"** setting enabled — the current
  folder is read from the window title. `install.sh` enables this for you
  automatically.

## Install

```sh
./install.sh
```

Copies `navigate-sibling.py` to `~/.local/bin/` and enables Dolphin's
full-path title bar setting. `install.sh` also installs the **Go to
Next/Previous Sibling Folder** service menu entries into
`~/.local/share/kio/servicemenus/` — these are what let you assign a
keyboard shortcut *inside Dolphin itself* (see below).

## Usage

**Dolphin-scoped keyboard shortcut (recommended):** in Dolphin, go to
**Settings → Configure Keyboard Shortcuts**, find **Go to Next Sibling
Folder** / **Go to Previous Sibling Folder**, and assign a key combination
to each (e.g. Meta+Right / Meta+Left). Because this is a Dolphin-local
shortcut rather than a KDE **global** shortcut (System Settings → Shortcuts
→ Custom Shortcuts), the key combination is only grabbed while Dolphin has
focus — other applications never lose access to it.

**Dolphin right-click menu:** right-click anywhere in the folder view and
choose **Go to Next Sibling Folder** / **Go to Previous Sibling Folder** —
this acts on the folder currently shown in the window, not on a selected
item.

With no path argument (the case above), the tool acts on whichever Dolphin
window is currently focused; it does nothing if Dolphin isn't the active
window.

## Changes

### 2026-09-06

- Switched from a KDE **global** shortcut to a Dolphin-local one (bound via
  Dolphin's own Settings → Configure Keyboard Shortcuts, using the service
  menu action installed by `install.sh`). A global shortcut grabs the key
  combination system-wide, so other apps lose access to it even when
  Dolphin isn't focused; a Dolphin-local shortcut only fires while Dolphin
  has focus, leaving the key combination free elsewhere.  Matches initial Intent.

- The service menu `.desktop` entries no longer pass `%f` (the right-clicked
  item), so both the right-click menu and the keyboard shortcut now always
  act on the folder currently shown in the active window, not a selected
  item.

- `navigate-sibling.py` only takes `next`/`prev` and always determines the
  current folder via the active Dolphin window's title. Note that Dolphin's
  service-menu framework *automatically appends* the current folder's path
  to the `Exec` command (that is how `Type=Service` menus operate on files),
  so the script accepts and silently ignores any extra path arguments rather
  than rejecting them.

- Fixed erratic behavior when triggered via a Dolphin-local shortcut: a
  held key auto-repeats the action (unlike right-click or a KDE global
  shortcut, which fire once), and rapid back-to-back runs raced Dolphin's
  asynchronous tab/title updates — reading stale titles (hence wrong
  targets) and closing whatever tab happened to sit left of the new one,
  sometimes before the new tab had even appeared. The script now verifies
  every step against the window title: it waits for the new tab to become
  active, closes the old tab by matching its path (not its position), and
  lands back on the target tab. If any check fails it leaves the tabs
  untouched rather than closing the wrong one.

- Right-click context menus can momentarily grab focus so that no Dolphin
  window reports itself active at the instant the script runs; in that case
  the script falls back to the single Dolphin window when there is exactly
  one, so right-click works reliably without ever acting on a background
  window when several are open.

- Changed the service-menu `MimeType` from `inode/directory;` to `all/all;`.
  The directory-only restriction meant the action was hidden from the
  right-click menu *and* disabled as a keyboard shortcut whenever a **file**
  was selected, so navigation silently did nothing until you clicked empty
  space. With `all/all` the action stays enabled regardless of the
  selection; the script still navigates the window's current folder (it
  ignores the appended path), so a selected file has no effect on the
  result.

