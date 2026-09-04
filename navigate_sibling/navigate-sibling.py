#!/usr/bin/env python3
"""
Navigate to the next or previous sibling folder of the folder currently
shown in the active Dolphin window, replacing the current tab in-place.

Intended to be bound to a KDE global custom shortcut (System Settings ->
Shortcuts -> Custom Shortcuts -> New -> Global Shortcut -> Command/URL):
for example:
    /home/[USER]/.local/bin/navigate-sibling.py next
    /home/[USER]/.local/bin/navigate-sibling.py prev

With no folder argument, the current folder is read from Dolphin's window
title (requires Dolphin's "Show full path in title bar" setting). Since this
runs as a global shortcut, it only acts when Dolphin is the focused window;
otherwise it does nothing.

Can also be called with an explicit folder path (e.g. from a right-click
service menu passing "%f"):

    navigate-sibling.py next <path>
    navigate-sibling.py prev <path>

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


def find_active_dolphin_window(
    services: list[str], strict: bool = False
) -> tuple[str, str] | None:
    """
    Return the (service, window) pair for the focused Dolphin window,
    searching across *all* running Dolphin processes/services.

    If *strict* is True, only return a window that actually reports itself
    as active; return None otherwise. This matters for global shortcuts,
    which can fire while a different application has focus, so we must not
    silently act on a background Dolphin window.
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

    if strict:
        return None

    # Fall back to the first window if none report active (e.g. triggered
    # from a service menu where Dolphin briefly loses focus).
    return all_windows[0] if all_windows else None


def _is_url_open(service: str, window: str, uri: str) -> bool:
    result = subprocess.run(
        ["qdbus6", service, window, "org.kde.dolphin.MainWindow.isUrlOpen", uri],
        capture_output=True, text=True,
    )
    return result.stdout.strip() == "true"


def get_window_current_folder(service: str, window: str) -> Path | None:
    """
    Return the folder currently shown in *window*, read from its title.
    Requires Dolphin's "Show full path in title bar" setting to be enabled.
    """
    result = subprocess.run(
        [
            "qdbus6", service, window,
            "org.freedesktop.DBus.Properties.Get",
            "org.qtproject.Qt.QWidget", "windowTitle",
        ],
        capture_output=True, text=True,
    )
    title = result.stdout.strip()
    path = Path(title)
    return path if title and path.is_dir() else None


def navigate_in_place(service: str, window: str, target: Path) -> None:
    """Open *target* as a new tab, then close the previously active tab."""
    uri = target.as_uri()
    subprocess.run(
        [
            "qdbus6", service, window,
            "org.kde.dolphin.MainWindow.openDirectories",
            uri, "false",
        ],
        capture_output=True,
    )

    # Wait until the new tab has actually opened before closing the old one,
    # to avoid closing the only remaining tab (and the whole window) if the
    # new tab hasn't appeared yet.
    opened = False
    for _ in range(20):  # up to ~2 seconds
        if _is_url_open(service, window, uri):
            opened = True
            break
        time.sleep(0.1)

    if not opened:
        print("New tab did not open in time; aborting without closing the old tab.", file=sys.stderr)
        return

    subprocess.run(
        ["qdbus6", service, window, "org.kde.KMainWindow.activateAction", "activate_prev_tab"],
        capture_output=True,
    )
    subprocess.run(
        ["qdbus6", service, window, "org.kde.KMainWindow.activateAction", "file_close"],
        capture_output=True,
    )


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
        print(f"Usage: {sys.argv[0]} (next|prev) [folder]", file=sys.stderr)
        sys.exit(1)

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

    service = None
    window = None

    services = find_dolphin_services()

    # Treat a missing or empty/unresolved "%f" argument the same way, since
    # Dolphin may pass an empty string instead of omitting the argument when
    # a shortcut fires with nothing selected.
    given_path = sys.argv[2].strip() if len(sys.argv) >= 3 else ""

    # When triggered without an explicit path (global shortcut), require a
    # genuinely focused Dolphin window so we never act on a background one.
    if services:
        found = find_active_dolphin_window(services, strict=not given_path)
        if found:
            service, window = found

    if not given_path and services and not window:
        print("Dolphin is not focused; ignoring shortcut.", file=sys.stderr)
        sys.exit(0)

    if given_path:
        current = Path(given_path).expanduser().resolve()
    elif service and window:
        # No folder given (e.g. triggered via keyboard shortcut): read the
        # currently displayed folder from the window title.
        current = get_window_current_folder(service, window)
        if current is None:
            print("Could not determine the current folder from the window title.", file=sys.stderr)
            print('Enable Dolphin\'s "Show full path in title bar" setting.', file=sys.stderr)
            sys.exit(1)
    else:
        print("No folder given and no running Dolphin window found.", file=sys.stderr)
        sys.exit(1)

    if not current.is_dir():
        print(f"Not a directory: {current}", file=sys.stderr)
        sys.exit(1)

    target = navigate(direction, current, wrap=False)
    if target is None:
        print(f"No {direction} sibling folder.")
        sys.exit(0)

    print(f"Navigating to: {target}")

    if service and window:
        navigate_in_place(service, window, target)
    else:
        subprocess.Popen(["dolphin", str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
