#!/usr/bin/env python3
"""
Navigate to the next or previous sibling folder of the folder currently
shown in the active Dolphin window, replacing the current tab in-place.

Intended to be bound to a keyboard shortcut *inside Dolphin itself* (Settings
-> Configure Keyboard Shortcuts -> assign a key to the "Go to Next/Previous
Sibling Folder" service-menu action installed by install.sh), rather than a
KDE global shortcut. That way the key combination is only grabbed while
Dolphin has focus, and other applications never lose access to it. It can
also still be run manually:

    /home/[USER]/.local/bin/navigate-sibling.py next
    /home/[USER]/.local/bin/navigate-sibling.py prev

The current folder is read from the focused Dolphin window's title
(requires Dolphin's "Show full path in title bar" setting). If Dolphin
isn't focused, it does nothing.

Stops at the first/last sibling. Skips hidden folders.
"""

import fcntl
import re
import subprocess
import sys
import time
from pathlib import Path

LOCK_PATH = "/tmp/navigate-sibling.lock"


def find_dolphin_services() -> list[str]:
    """Return all org.kde.dolphin-<pid> D-Bus service names.

    There is one service per running Dolphin *process*, so with more than
    one Dolphin window open at once (each its own process) there can be
    several of these; all of them must be checked for the active window.
    """
    result = subprocess.run(["qdbus6"], capture_output=True, text=True)
    return [
        line.strip() for line in result.stdout.splitlines()
        if re.fullmatch(r"org\.kde\.dolphin-\d+", line.strip())
    ]


def find_active_dolphin_window(services: list[str]) -> tuple[str, str] | None:
    """
    Return the (service, window) pair for the focused Dolphin window,
    searching across *all* running Dolphin processes/services.

    A right-click context menu can momentarily grab focus so that no window
    reports itself active at the instant the script runs; in that case, if
    there is exactly *one* Dolphin window overall, fall back to it. That is
    unambiguous, so we still never act on a background window when several
    are open. Returns None when there is no clear single candidate.
    """
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

    # No window claims to be active (e.g. context-menu focus grab). Only
    # fall back when there is a single Dolphin window, so the target is
    # unambiguous.
    if len(all_windows) == 1:
        return all_windows[0]
    return None


def _is_url_open(service: str, window: str, uri: str) -> bool:
    result = subprocess.run(
        ["qdbus6", service, window, "org.kde.dolphin.MainWindow.isUrlOpen", uri],
        capture_output=True, text=True,
    )
    return result.stdout.strip() == "true"


def _current_title(service: str, window: str) -> str:
    """Return the window's current title (the active tab's full path)."""
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
    """
    Return the folder currently shown in *window*, read from its title.
    Requires Dolphin's "Show full path in title bar" setting to be enabled.
    """
    title = _current_title(service, window)
    path = Path(title)
    return path if title and path.is_dir() else None


def _settled_title(service: str, window: str, timeout: float = 0.6) -> str:
    """Return the title once it stops changing.

    Tab switches update the title asynchronously, so right after an action
    the title can lag one step behind; polling until two consecutive reads
    agree avoids acting on a stale value.
    """
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


def navigate_in_place(service: str, window: str, old: Path, target: Path) -> None:
    """Open *target* in a new tab, then close the tab showing *old*.

    Every step is verified against the window title instead of assuming tab
    positions. This matters because a Dolphin-local shortcut auto-repeats
    while the key is held: rapid back-to-back runs otherwise race Dolphin's
    asynchronous tab/title updates, reading stale titles (wrong target) and
    closing whatever tab happens to sit left of the new one before the new
    tab has even appeared.
    """
    old_title = str(old)
    target_title = str(target)
    uri = target.as_uri()

    subprocess.run(
        [
            "qdbus6", service, window,
            "org.kde.dolphin.MainWindow.openDirectories",
            uri, "false",
        ],
        capture_output=True,
    )

    # Wait until the new tab is open *and active* (title shows the target).
    # If that never happens, leave all tabs untouched rather than risk
    # closing the wrong one.
    deadline = time.monotonic() + 2.0
    while _current_title(service, window) != target_title:
        if time.monotonic() > deadline:
            print("New tab did not become active; leaving tabs untouched.", file=sys.stderr)
            return
        time.sleep(0.05)

    # Close the old tab: cycle left until the tab showing *old* is active,
    # then close it. Stop if we wrap back to the target without finding it.
    for _ in range(50):
        _activate(service, window, "activate_prev_tab")
        title = _settled_title(service, window)
        if title == old_title:
            _activate(service, window, "file_close")
            break
        if title == target_title:
            break  # wrapped all the way around; old tab is already gone

    # Make sure we end back on the target tab.
    for _ in range(50):
        if _settled_title(service, window) == target_title:
            break
        _activate(service, window, "activate_next_tab")


def get_sibling_folders(path: Path) -> list[Path]:
    """Return sorted non-hidden sibling folders of *path*."""
    parent = path.parent
    if parent == path:
        return []

    siblings = [
        entry for entry in parent.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    ]
    return sorted(siblings, key=lambda p: p.name.lower())


def navigate(direction: str, current_path: Path, wrap: bool = False) -> Path | None:
    """Return the next/previous sibling folder, or None if at the boundary."""
    siblings = get_sibling_folders(current_path)
    if current_path not in siblings:
        return None

    index = siblings.index(current_path)
    if direction == "next":
        target = index + 1
        if target >= len(siblings):
            if wrap:
                target = 0
            else:
                return None
    elif direction == "prev":
        target = index - 1
        if target < 0:
            if wrap:
                target = len(siblings) - 1
            else:
                return None
    else:
        return None

    return siblings[target]


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} (next|prev)", file=sys.stderr)
        sys.exit(1)

    # Dolphin's service-menu framework automatically appends the current /
    # selected folder path to the Exec command (that is how Type=Service
    # menus operate on files). We always act on the active window's folder
    # instead, so those extra path arguments are accepted and ignored.
    # Refuse to run if another invocation is already in progress, since
    # overlapping runs can race the tab open/close sequence and end up
    # closing the wrong tab (or the whole window).
    lock_file = open(LOCK_PATH, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Another navigate-sibling.py is already running; ignoring this trigger.", file=sys.stderr)
        sys.exit(1)

    direction = sys.argv[1].lower()
    if direction in ("previous", "prev"):
        direction = "prev"
    elif direction == "next":
        pass
    else:
        print(f"Invalid direction: {direction}", file=sys.stderr)
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

    if not current.is_dir():
        print(f"Not a directory: {current}", file=sys.stderr)
        sys.exit(1)

    target = navigate(direction, current, wrap=False)
    if target is None:
        print(f"No {direction} sibling folder.")
        sys.exit(0)

    print(f"Navigating to: {target}")
    navigate_in_place(service, window, current, target)


if __name__ == "__main__":
    main()
