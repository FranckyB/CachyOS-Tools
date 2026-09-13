#!/usr/bin/env python3
"""
Move every item from the folder currently shown in the active Dolphin window
into its parent folder, then replace the current tab with the parent folder.

Intended to be bound to a keyboard shortcut inside Dolphin itself (Settings
-> Configure Keyboard Shortcuts -> assign a key to the "Move Contents Up"
service-menu action installed by install.sh), rather than a KDE global
shortcut. That way the key combination is only grabbed while Dolphin has
focus, and other applications never lose access to it. It can also still be
run manually:

    /home/[USER]/.local/bin/move-up.py

The current folder is read from the focused Dolphin window's title
(requires Dolphin's "Show full path in title bar" setting). The action
ignores any selected files and always operates on the folder currently shown
in the active tab.
"""

import fcntl
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

LOCK_PATH = "/tmp/move-up.lock"


@dataclass
class ProgressDialog:
    service: str
    path: str


def open_progress_dialog(message: str) -> ProgressDialog | None:
    """Open a non-blocking progress dialog when kdialog is available."""
    if shutil.which("kdialog") is None:
        return None

    result = subprocess.run(
        ["kdialog", "--title", "Move Contents Up", "--progressbar", message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return None

    dialog = ProgressDialog(parts[0], parts[1])
    qdbus_progress(dialog, "showCancelButton", "false")
    qdbus_progress(dialog, "setLabelText", message)
    return dialog


def qdbus_progress(dialog: ProgressDialog, method: str, *args: str) -> bool:
    """Call a method on the progress dialog, ignoring best-effort failures."""
    result = subprocess.run(
        ["qdbus6", dialog.service, dialog.path, method, *args],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def update_progress_dialog(dialog: ProgressDialog | None, message: str) -> None:
    if dialog is None:
        return
    qdbus_progress(dialog, "setLabelText", message)


def close_progress_dialog(dialog: ProgressDialog | None) -> None:
    if dialog is None:
        return
    qdbus_progress(dialog, "close")


def find_dolphin_services() -> list[str]:
    """Return all org.kde.dolphin-<pid> D-Bus service names."""
    result = subprocess.run(["qdbus6"], capture_output=True, text=True)
    return [
        line.strip() for line in result.stdout.splitlines()
        if re.fullmatch(r"org\.kde\.dolphin-\d+", line.strip())
    ]


def find_active_dolphin_window(services: list[str]) -> tuple[str, str] | None:
    """Return the focused Dolphin window, or the only window if unambiguous."""
    all_windows: list[tuple[str, str]] = []
    for service in services:
        result = subprocess.run(
            ["qdbus6", service], capture_output=True, text=True
        )
        windows = [
            line.strip() for line in result.stdout.splitlines()
            if re.fullmatch(r"/dolphin/Dolphin_\d+", line.strip())
        ]

        for window in windows:
            check = subprocess.run(
                ["qdbus6", service, window, "org.kde.dolphin.MainWindow.isActiveWindow"],
                capture_output=True, text=True,
            )
            if check.stdout.strip() == "true":
                return service, window
            all_windows.append((service, window))

    if len(all_windows) == 1:
        return all_windows[0]
    return None


def _current_title(service: str, window: str) -> str:
    result = subprocess.run(
        [
            "qdbus6", service, window,
            "org.freedesktop.DBus.Properties.Get",
            "org.qtproject.Qt.QWidget", "windowTitle",
        ],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def get_window_current_folder(service: str, window: str) -> Path | None:
    """Return the local folder currently shown in the window title."""
    title = _current_title(service, window)
    if not title or "://" in title or ":" in title.split("/")[0]:
        return None
    path = Path(title).expanduser()
    if not path.is_absolute():
        return None
    try:
        path = path.resolve()
    except OSError:
        return None
    return path if path.is_dir() else None


def _settled_title(service: str, window: str, timeout: float = 0.6) -> str:
    deadline = time.monotonic() + timeout
    last = _current_title(service, window)
    while time.monotonic() < deadline:
        time.sleep(0.04)
        current = _current_title(service, window)
        if current == last:
            return current
        last = current
    return last


def _activate(service: str, window: str, action: str) -> None:
    subprocess.run(
        ["qdbus6", service, window, "org.kde.KMainWindow.activateAction", action],
        capture_output=True,
    )


def refresh_current_view(service: str, window: str) -> None:
    """Ask Dolphin to redraw the current view."""
    _activate(service, window, "view_redisplay")


def select_item_in_dolphin(item: Path) -> None:
    """Ask the session file manager to reveal and select an item."""
    subprocess.run(
        [
            "qdbus6",
            "org.freedesktop.FileManager1",
            "/org/freedesktop/FileManager1",
            "org.freedesktop.FileManager1.ShowItems",
            item.as_uri(),
            "",
        ],
        capture_output=True,
    )


def replace_tab_with_parent(service: str, window: str, old: Path, parent: Path) -> None:
    """Open parent in a new tab, close the tab showing old, and end on parent."""
    old_title = str(old)
    parent_title = str(parent)

    subprocess.run(
        [
            "qdbus6", service, window,
            "org.kde.dolphin.MainWindow.openDirectories",
            parent.as_uri(), "false",
        ],
        capture_output=True,
    )

    deadline = time.monotonic() + 2.0
    while _current_title(service, window) != parent_title:
        if time.monotonic() > deadline:
            print("Parent tab did not become active; leaving tabs untouched.", file=sys.stderr)
            return
        time.sleep(0.05)

    for _ in range(50):
        _activate(service, window, "activate_prev_tab")
        title = _settled_title(service, window)
        if title == old_title:
            _activate(service, window, "file_close")
            break
        if title == parent_title:
            break

    for _ in range(50):
        if _settled_title(service, window) == parent_title:
            break
        _activate(service, window, "activate_next_tab")


def path_exists(path: Path) -> bool:
    """Return True for existing paths, including symlinks."""
    return path.exists() or path.is_symlink()


def remove_existing_path(path: Path) -> None:
    """Remove a destination path so a source can overwrite it."""
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    raise OSError(f"Unsupported destination type: {path}")


def move_with_overwrite(source: Path, destination: Path) -> None:
    """Move source onto destination, merging directories and overwriting conflicts."""
    if source.is_symlink() or source.is_file():
        if path_exists(destination):
            remove_existing_path(destination)
        shutil.move(str(source), str(destination))
        return

    if source.is_dir():
        if destination.is_dir() and not destination.is_symlink():
            for child in list(source.iterdir()):
                move_with_overwrite(child, destination / child.name)
            source.rmdir()
            return

        if path_exists(destination):
            remove_existing_path(destination)
        shutil.move(str(source), str(destination))
        return

    raise OSError(f"Unsupported source type: {source}")


def move_children_to_parent(current: Path, parent: Path) -> int:
    """Move all direct children from current into parent, overwriting on conflict."""
    children = list(current.iterdir())

    moved = 0
    for child in children:
        move_with_overwrite(child, parent / child.name)
        moved += 1
    return moved


def trash_empty_folder(path: Path) -> bool:
    """Move an empty folder to trash when gio is available."""
    result = subprocess.run(
        ["gio", "trash", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True

    message = result.stderr.strip() or result.stdout.strip() or "unknown gio error"
    print(f"Could not move empty folder to trash: {message}", file=sys.stderr)
    return False


def main() -> None:
    lock_file = open(LOCK_PATH, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Another move-up.py is already running; ignoring this trigger.", file=sys.stderr)
        sys.exit(1)

    services = find_dolphin_services()
    found = find_active_dolphin_window(services) if services else None
    if not found:
        print("Dolphin is not focused; ignoring shortcut.", file=sys.stderr)
        sys.exit(0)
    service, window = found

    current = get_window_current_folder(service, window)
    if current is None:
        print("Could not determine the current folder from the window title.", file=sys.stderr)
        print('Enable Dolphin\'s "Show full path in title bar" setting.', file=sys.stderr)
        sys.exit(1)

    parent = current.parent
    if parent == current:
        print("Cannot move contents up from the filesystem root.", file=sys.stderr)
        sys.exit(1)

    dialog = open_progress_dialog(f"Moving contents of {current.name} up to {parent.name or parent}")
    try:
        try:
            update_progress_dialog(dialog, f"Moving contents of {current.name} up to {parent.name or parent}...")
            moved = move_children_to_parent(current, parent)
        except OSError as exc:
            print(f"Move failed: {exc}", file=sys.stderr)
            update_progress_dialog(dialog, "Move failed")
            sys.exit(1)

        trashed = False
        should_replace_tab = False
        try:
            if not any(current.iterdir()):
                should_replace_tab = True
        except OSError as exc:
            print(f"Moved {moved} item(s), but could not inspect {current}: {exc}", file=sys.stderr)

        print(f"Moved {moved} item(s) into: {parent}")

        if should_replace_tab:
            update_progress_dialog(dialog, f"Opening {parent.name or parent} and sending {current.name} to trash...")
            replace_tab_with_parent(service, window, current, parent)
            trashed = trash_empty_folder(current)
            if not trashed and current.exists():
                select_item_in_dolphin(current)
        else:
            update_progress_dialog(dialog, f"Moved {moved} item(s) into {parent.name or parent}")
            refresh_current_view(service, window)

        if trashed:
            print(f"Moved empty folder to trash: {current}")
        else:
            print(f"Folder left in place: {current}")
    finally:
        close_progress_dialog(dialog)


if __name__ == "__main__":
    main()