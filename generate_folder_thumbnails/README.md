# generate_folder_thumbnails

Dolphin right-click menu that generates a custom folder icon by compositing
the first image (or video frame) found inside a folder onto a folder
template, recursively for every subfolder.  When possible, we use the frame at
the 50% mark.

## Requirements

- `Pillow` – `install.sh` installs this automatically via `pacman` if
  available, otherwise install it yourself with `pip install Pillow` or
  `sudo pacman -S python-pillow`.
- `ffmpeg` (optional) – only needed to generate icons from video files;
  without it, folders containing only videos are skipped.

## Install

```sh
./install.sh
```

Copies `generate_folder_thumails.py` and `script_files/` to `~/.local/bin/`,
and installs the two service menus (`Generate Folder Thumbnail` and
`Refresh Folder Thumbnail`) into `~/.local/share/kio/servicemenus/`.

## Usage

Right-click a folder in Dolphin and choose **Generate Folder Thumbnail** to
create icons for that folder and every subfolder that doesn't already have
one, or **Refresh Folder Thumbnail** to regenerate them even if they exist.

Can also be run directly:

```sh
generate_folder_thumails.py [--refresh] <folder> [<folder> ...]
```

## Customizing the image placement

The composited image is placed inside a defined rectangle on top of the
folder template, controlled by `CONTENT_BOX` near the top of
`generate_folder_thumails.py`:

```python
CONTENT_BOX = (15, 67, 240, 208)    # (left, upper, right, lower)
CORNER_RADIUS = 18
```

Edit these pixel coordinates (relative to the 256x256 `script_files/folder.png`
template) to move or resize where the cover image sits on the folder icon.

For quick tweaking, edit the installed copy directly at
`~/.local/bin/generate_folder_thumails.py`, run
the script on a test folder, and repeat until it looks right.

## Using your own folder template

`script_files/folder.png` is the blank folder icon that images are
composited onto (referenced by `script_files/directory.txt`'s `Icon=` line).
To use your own:

1. Drop your own `folder.svg` into `utils/` provided with this Repo.
2. Run `utils/convert_folder_svg.py` to render it to a `folder.png`.
3. Copy the resulting PNG over `folder.png`: if you haven't installed yet,
   copy it into this repo's `script_files/folder.png` and run `install.sh`;
   if you've already installed, copy it directly over
   `~/.local/bin/script_files/folder.png` instead — no need to reinstall.
4. In the .py script, Update `CONTENT_BOX` and 'CORNER_RADIUS' to match where the "page" area sits in your new
   template, then re-run `install.sh`.
