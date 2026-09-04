# CachyOS-Tools
A grab bag of different tools and service menus I've made for myself.

Each tool folder (except `utils/`) has its own `install.sh` that copies the
script into `~/.local/bin/` and, if it has one, its `.desktop` service menu
into `~/.local/share/kio/servicemenus/` (patching the `[USER]` placeholder
with your username). Run it from inside the folder:

```sh
cd generate_folder_thumbnails && ./install.sh
```

## Tools

- **generate_folder_thumbnails** – Dolphin right-click menu to generate/refresh a folder thumbnails from their contents. You can use your own folder icon and set the image position by modifying the script.  Convert SVG to PNG script is provided in utils
See its [README](generate_folder_thumbnails/README.md).

- **group_files** – Dolphin right-click menu to group selected files into a new subfolder. 
See its [README](group_files/README.md).

- **navigate_sibling** – Go to the next/previous sibling folder. Can works as a Dolphin right-click menu, but is meant to be bound to KDE Global Shortcuts (see `navigate-sibling.py`'s docstring for the commands to use).  `install.sh` also enables Dolphin's "Show full path in title bar" setting, which the script relies on.
See its [README](navigate_sibling/README.md).

- **paste_into** – Paste clipboard files into the folder selected in the active Dolphin window. Bind using KDE Global Shortcut
  yourself (see `paste-into-folder.py`'s docstring). 
  See its [README](paste_into/README.md).
  
- **utils** – Standalone helper scripts, no need to installed. 
See its [README](utils/README.md).

