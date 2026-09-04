# navigate_sibling

Go to the next/previous sibling folder of the folder currently shown in the
active Dolphin window, replacing the current tab in place. Skips hidden
folders and stops at the first/last sibling.

## Requirements

- `qdbus6` (ships with Plasma/KDE)
- Dolphin's **"Show full path in title bar"** setting enabled — required
  when invoked with no folder argument (global shortcut use), since the
  current folder is read from the window title. `install.sh` enables this
  for you automatically.

## Install

```sh
./install.sh
```

Copies `navigate-sibling.py` to `~/.local/bin/` and enables Dolphin's
full-path title bar setting. Since this tool is mainly meant to be used via
a keyboard Global Shortcut, `install.sh` will ask whether you also want the
**Go to Next/Previous Sibling Folder** right-click service menus installed
into `~/.local/share/kio/servicemenus/` (optional).

## Usage

**Dolphin right-click menu:** right-click a folder and choose **Go to Next
Sibling Folder** / **Go to Previous Sibling Folder**.

**Global shortcut (recommended for quick navigation):** `install.sh` does not
do this part for you — set it up yourself in System Settings → Shortcuts →
Custom Shortcuts:

1. Click **Edit** → **New** → **Global Shortcut** → **Command/URL**, and
   choose **+ Add New Command or Script** (do this twice, once for next and
   once for previous).
2. In the **Trigger** tab, set the key combination you want (e.g. Meta+Right
   for next, Meta+Left for previous).
3. In the **Action** tab, enter the full path to the script plus `next` or
   `prev`, e.g.:

   ```
   "/home/[USER]/.local/bin/navigate-sibling.py" next
   ```

   ```
   "/home/[USER]/.local/bin/navigate-sibling.py" prev
   ```

   Replace `[USER]` with your own username (the same value `install.sh` used
   when patching the `.desktop` files).

With no path argument it acts on whichever Dolphin window is currently
focused; it does nothing if Dolphin isn't the active window.
