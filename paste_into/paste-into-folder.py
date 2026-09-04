#!/usr/bin/env python3
"""
Paste the clipboard's cut/copied files into the folder currently selected
in the active Dolphin window, without navigating into it.

Intended to be bound to a KDE global custom shortcut (System Settings ->
Shortcuts -> Custom Shortcuts -> New -> Global Shortcut -> Command/URL),
e.g. bound to Ctrl+Alt+V:
    /home/[USER]/.local/bin/paste-into-folder.py

Requires exactly one folder to be selected in the active Dolphin view, and
something previously cut/copied onto the clipboard (e.g. via Ctrl+X). Since
this runs as a global shortcut, it only acts when Dolphin is the focused
window; otherwise it does nothing.
"""

import re
import subprocess
import sys


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
    """Return the (service, window) pair for the focused Dolphin window,
    searching across all running Dolphin processes/services."""
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

    return None


def main() -> None:
    services = find_dolphin_services()
    if not services:
        print("No running Dolphin instance found.", file=sys.stderr)
        sys.exit(1)

    # Global shortcuts can fire while a different application has focus, so
    # only act on a window that actually reports itself as active.
    found = find_active_dolphin_window(services)
    if not found:
        print("Dolphin is not focused; ignoring shortcut.", file=sys.stderr)
        sys.exit(0)
    service, window = found

    subprocess.run(
        ["qdbus6", service, window, "org.kde.dolphin.MainWindow.pasteIntoFolder"],
        capture_output=True,
    )


if __name__ == "__main__":
    main()
