# utils

Standalone helper scripts. Nothing here is installed by an `install.sh` —
run them directly from this folder as needed.

- **convert_folder_svg.py** – Converts a `folder.svg` in this directory into
  a `folder.png` (512px wide by default), using `cairosvg`. If `folder.png`
  already exists it's renamed to `folder_old_001.png` (incrementing) instead
  of being overwritten. Useful for producing a custom
  `script_files/folder.png` template for `generate_folder_thumbnails` — see
  that tool's README for the full workflow.

  Requirements: `cairosvg` – `pip install cairosvg` or
  `sudo pacman -S python-cairosvg`.

  ```sh
  ./convert_folder_svg.py
  ```
