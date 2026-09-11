#!/usr/bin/env python3
"""
Linux Folder Icon Creator

For each folder under a source path that contains images, generate a custom
folder icon by compositing the first image onto a folder template, then save
it as .folder.png and drop a .directory entry so Dolphin displays it.

Image selection / propagation follows the same idea as the original Windows
Thumbnail_Creator scripts: a folder uses its own first image if available,
otherwise it can inherit an image from a subfolder.

Requires: Pillow
    pip install Pillow
    # sudo pacman -S python-pillow

"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw
except ImportError as exc:
    raise SystemExit(
        "Pillow is required but not installed.\n"
        "Install it with:\n"
        "  pip install Pillow\n"
        "or your distro's package manager (e.g. sudo pacman -S python-pillow)."
    ) from exc


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The .directory file used as a template; it is copied unchanged into every
# folder that gets an icon.
DESKTOP_TEMPLATE_NAME = "script_files/directory.txt"
DESKTOP_TEMPLATE_ICON = "script_files/folder.png"

# Name of the generated icon file. It must match the Icon= line in the
# .directory template (e.g. Icon=./.folder.png).
OUTPUT_ICON_NAME = ".folder.png"

# Prefer these base names when choosing a folder cover source.
# First match in this list wins regardless of image extension; anything else
# falls back to alphabetical order.
PREFERRED_IMAGE_NAMES = [
    "fanart",
    "landscape",
    "poster",
]

# Image extensions to consider as folder cover sources.
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")

# Video extensions to consider as folder cover sources when no image is found.
VIDEO_EXTENSIONS = (
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".ts", ".mts", ".m2ts",
)

# If True, empty folders that contain subfolders with images will also get a
# folder icon using the nearest subfolder's image.
PROPAGATE_FROM_SUBFOLDERS = True

# Minimum file size (in bytes) for a media file to be considered a valid
# folder-icon source. Guards against corrupt/truncated files that are
# technically present but too small to be a real photo or video frame.
MIN_MEDIA_FILE_SIZE = 20480

# Content area inside the folder template (in pixels).
# The folder template is 256 x 256 px; this rectangle is centered on the
# folder "page" and the source image is zoomed/cropped to fill it completely.
CONTENT_BOX = (15, 67, 240, 208)   # (left, upper, right, lower)

# Adjust how rounded should the corners be
CORNER_RADIUS = 18

# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def get_content_box(template_path: str | Path) -> tuple[int, int, int, int]:
    """
    Return the hardcoded content rectangle (left, upper, right, lower) in pixels.
    """
    return CONTENT_BOX


def fill_box_with_image(
    source: Image.Image,
    box_width: int,
    box_height: int,
    corner_radius: int = CORNER_RADIUS,
) -> Image.Image:
    """
    Resize and crop *source* so it completely fills the box while preserving
    aspect ratio, then apply rounded corners so it matches the folder page.
    The image is centered before cropping so no white/empty bars remain.
    """
    src_w, src_h = source.size

    # Choose the scale that makes the source cover the entire box.
    scale = max(box_width / src_w, box_height / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))

    resized = source.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Center-crop to the exact target size.
    crop_left = (new_w - box_width) // 2
    crop_upper = (new_h - box_height) // 2
    crop_right = crop_left + box_width
    crop_lower = crop_upper + box_height

    content = resized.crop((crop_left, crop_upper, crop_right, crop_lower))

    # Apply rounded corners via a supersampled anti-aliased alpha mask.
    scale = 4
    big_w = box_width * scale
    big_h = box_height * scale
    big_mask = Image.new("L", (big_w, big_h), 0)
    big_draw = ImageDraw.Draw(big_mask)
    big_draw.rounded_rectangle(
        (0, 0, big_w, big_h),
        radius=corner_radius * scale,
        fill=255,
    )
    mask = big_mask.resize((box_width, box_height), Image.Resampling.LANCZOS)

    # Apply the mask to the content's alpha channel, preserving RGB colors.
    if content.mode != "RGBA":
        content = content.convert("RGBA")
    r, g, b, a = content.split()
    a = ImageChops.multiply(a, mask)
    content.putalpha(a)

    return content


def compose_folder_icon(
    template_path: str | Path,
    source_image_path: str | Path,
    output_path: str | Path,
) -> None:
    """
    Create .folder.png: composite source_image onto template inside content_box.
    """
    template = Image.open(template_path).convert("RGBA")
    content_box = get_content_box(template_path)

    source = Image.open(source_image_path).convert("RGBA")

    box_width = content_box[2] - content_box[0]
    box_height = content_box[3] - content_box[1]

    content = fill_box_with_image(source, box_width, box_height)

    result = template.copy()
    result.paste(content, (content_box[0], content_box[1]), content)
    result.save(output_path, "PNG")


# ---------------------------------------------------------------------------
# Folder processing
# ---------------------------------------------------------------------------

def get_video_duration(video_path: Path) -> float | None:
    """
    Return the duration of *video_path* in seconds using ffprobe, or None.

    Tries the container-level duration first, then falls back to the video
    stream's own duration. Some containers (certain .ts/.m2ts/.mkv files in
    particular) don't report a duration at the format level, which would
    otherwise silently fall back to grabbing a frame near the very start.
    """
    if shutil.which("ffprobe") is None:
        return None

    probes = [
        ["-show_entries", "format=duration"],
        ["-select_streams", "v:0", "-show_entries", "stream=duration"],
    ]
    for probe_args in probes:
        cmd = [
            "ffprobe",
            "-hide_banner",
            "-loglevel", "error",
            *probe_args,
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            if duration > 0:
                return duration
        except (subprocess.CalledProcessError, ValueError):
            continue
    return None


def extract_video_thumbnail(video_path: Path, output_path: Path) -> bool:
    """
    Extract a single thumbnail frame from *video_path* using ffmpeg and save
    it as a PNG at *output_path*. Uses the middle frame when the duration can
    be determined, otherwise falls back to 1 second in. Returns True on success.
    """
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found; cannot generate thumbnail from video.")
        return False

    duration = get_video_duration(video_path)
    seek_seconds = duration / 2 if duration else 1.0
    print(
        f"Seeking {video_path.name} to {seek_seconds:.1f}s"
        f" ({'50% mark, duration=' + format(duration, '.1f') + 's' if duration else 'duration unknown, defaulting to 1s'})"
    )

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-ss", str(seek_seconds),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        "-y",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path.is_file()
    except subprocess.CalledProcessError as exc:
        print(f"ffmpeg failed for {video_path}: {exc}")
        return False


def all_files_with_extensions(
    folder: Path,
    extensions: tuple[str, ...],
    ignore_name: str | None = OUTPUT_ICON_NAME,
) -> list[Path]:
    """
    Return all files in *folder* matching one of *extensions*, sorted
    by configured preference first, then case-insensitively by name.
    """
    results: list[Path] = []
    try:
        preferred_name_ranks = {
            name.casefold(): index for index, name in enumerate(PREFERRED_IMAGE_NAMES)
        }

        def sort_key(path: Path) -> tuple[int, str]:
            preferred_rank = preferred_name_ranks.get(
                path.stem.casefold(),
                len(preferred_name_ranks),
            )
            return preferred_rank, path.name.casefold()

        entries = sorted(folder.iterdir(), key=sort_key)
        for entry in entries:
            if not entry.is_file():
                continue
            if entry.name.lower().endswith(extensions):
                if ignore_name and entry.name == ignore_name:
                    continue
                results.append(entry)
    except PermissionError:
        pass
    return results


def is_usable_media_file(path: Path, *, log_skip: bool = False) -> bool:
    """
    Return True when *path* exists and is large enough to be worth trying.
    """
    try:
        if path.stat().st_size < MIN_MEDIA_FILE_SIZE:
            if log_skip:
                print(f"Skipping too-small file (likely corrupt): {path}")
            return False
    except OSError:
        return False
    return True


def media_sources_in(folder: Path) -> list[Path]:
    """
    Return candidate media files inside *folder*: images first (preferred),
    then videos, each sorted alphabetically. Used to fall back to another
    file if the first candidate turns out to be unreadable/corrupt.
    """
    images = all_files_with_extensions(folder, IMAGE_EXTENSIONS)
    videos = all_files_with_extensions(folder, VIDEO_EXTENSIONS, ignore_name=None)
    return images + videos


def first_media_source_in(folder: Path) -> Path | None:
    """
    Return the first image file inside *folder*, or the first video file if
    no image is found. Returns the *original* media path, not an extracted
    thumbnail. Returns None if neither exists.
    """
    for source in media_sources_in(folder):
        if is_usable_media_file(source):
            return source
    return None


def is_video_file(path: Path) -> bool:
    """Return True if *path* has a video extension."""
    return path.name.lower().endswith(VIDEO_EXTENSIONS)


def _walk_sorted_bottom_up(source: Path) -> list[Path]:
    """
    Return all directories under *source*, sorted alphabetically and ordered
    deepest-first so parents are processed after their children.
    """
    entries: list[tuple[Path, list[str]]] = []
    for root, dirs, _files in os.walk(source, topdown=True):
        dirs[:] = sorted(
            (d for d in dirs if not d.startswith(".")), key=str.casefold
        )
        entries.append((Path(root), dirs))

    # Reverse so deepest directories are processed first.
    return [root for root, _dirs in reversed(entries)]


def process_tree(
    source: Path,
    template_path: Path,
    desktop_template_path: Path,
    refresh: bool = False   
) -> None:
    """
    Walk bottom-up so subfolder images can propagate to empty parents.
    """
    # source_image_for[folder] = original media path used for that folder's icon
    source_image_for: dict[Path, Path] = {}

    for root_path in _walk_sorted_bottom_up(source):
        dirs = sorted(
            (d.name for d in root_path.iterdir()
             if d.is_dir() and not d.name.startswith(".")),
            key=str.casefold,
        )

        own_source = first_media_source_in(root_path)
        inherited_from: Path | None = None

        if own_source:
            source_media = own_source
        elif PROPAGATE_FROM_SUBFOLDERS:
            # Use the first subfolder (already sorted) that got an icon.
            source_media = None
            for d in dirs:
                sub = root_path / d
                if sub in source_image_for:
                    source_media = source_image_for[sub]
                    inherited_from = sub
                    break
        else:
            source_media = None

        if source_media:
            icon_path = root_path / OUTPUT_ICON_NAME
            desktop_path = root_path / ".directory"

            if (
                not refresh
                and icon_path.is_file()
                and desktop_path.is_file()
            ):
                print(f"Skipped {root_path} (existing icon/desktop)")
                source_image_for[root_path] = source_media
                continue

            if inherited_from is not None:
                # Reuse the already-generated icon from the subfolder.
                inherited_icon = inherited_from / OUTPUT_ICON_NAME
                if inherited_icon.is_file():
                    shutil.copy2(inherited_icon, icon_path)
                    shutil.copy2(desktop_template_path, desktop_path)
                    print(f"Created {icon_path} (copied from {inherited_icon})")
                    source_image_for[root_path] = source_media
                    continue

            # Try each own candidate in turn (falling back to the next one if
            # a file turns out to be missing/unreadable/corrupt), unless we're
            # reusing an inherited source that isn't backed by its own icon.
            candidates = (
                media_sources_in(root_path) if inherited_from is None else [source_media]
            )

            created = False
            for candidate in candidates:
                if not is_usable_media_file(candidate, log_skip=True):
                    continue

                # If the source is a video, extract a temporary thumbnail frame.
                temp_thumb: Path | None = None
                if is_video_file(candidate):
                    temp_thumb = root_path / ".video_thumb_tmp.png"
                    if not extract_video_thumbnail(candidate, temp_thumb):
                        continue
                    source_image = temp_thumb
                else:
                    source_image = candidate

                if not source_image.is_file():
                    print(f"Source file not found, skipping: {source_image}")
                    continue

                try:
                    compose_folder_icon(template_path, source_image, icon_path)
                except (OSError, Image.UnidentifiedImageError) as exc:
                    print(f"Could not read {candidate} ({exc}); trying another file.")
                    if temp_thumb is not None:
                        try:
                            temp_thumb.unlink()
                        except OSError:
                            pass
                    continue

                shutil.copy2(desktop_template_path, desktop_path)
                print(f"Created {icon_path}")

                # Clean up temporary video frame thumbnails safely.
                if temp_thumb is not None:
                    try:
                        temp_thumb.unlink()
                    except OSError:
                        pass

                source_image_for[root_path] = candidate
                created = True
                break

            if not created:
                print(f"No usable media found for {root_path}; skipping icon.")


def main() -> None:
    script_dir = Path(__file__).parent.resolve()

    # A leading/trailing "--refresh" flag forces regeneration of icons that
    # already exist, instead of skipping folders that already have one.
    args = sys.argv[1:]
    refresh = "--refresh" in args
    if refresh:
        args = [a for a in args if a != "--refresh"]

    # Accept one or more folder paths from the command line (e.g. multiple
    # folders selected in a service menu), otherwise prompt for a single one.
    if args:
        sources = args
    else:
        sources = [input("Enter the source directory: ").strip()]

    template_path = script_dir / DESKTOP_TEMPLATE_ICON
    if not template_path.is_file():
        print(f"Bundled folder template not found: {template_path}")
        return

    desktop_template_path = script_dir / DESKTOP_TEMPLATE_NAME
    if not desktop_template_path.is_file():
        print(f"Bundled .directory template not found: {desktop_template_path}")
        return

    for source in sources:
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_dir():
            print(f"Not a valid directory: {source}")
            continue

        print(f"Processing {source_path}")
        process_tree(source_path, template_path, desktop_template_path, refresh=refresh)

    print("Done.")


if __name__ == "__main__":
    main()
