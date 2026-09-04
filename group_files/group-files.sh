#!/usr/bin/env bash
# Move selected files into a new folder, prompting for the folder name via kdialog.

set -euo pipefail

if [[ $# -eq 0 ]]; then
    exit 0
fi

# All selected files should be in the same directory; use the first one's parent.
first="$1"
if [[ -d "$first" ]]; then
    target_dir="$first"
else
    target_dir="$(dirname "$first")"
fi

cd "$target_dir" || exit 1

# Prompt for folder name via kdialog.
default_name="Group"
name=$(kdialog --title "Group Files" --inputbox "Enter folder name:" "$default_name" 2>/dev/null || true)

# User cancelled or closed the dialog.
if [[ -z "$name" ]]; then
    exit 0
fi

# Sanitize the name (remove slashes).
name="${name//\/}"

# If the name already exists, increment it.
base="$name"
counter=1
while [[ -e "$name" ]]; do
    printf -v name "%s_%02d" "$base" "$counter"
    ((counter++)) || true
done

mkdir "$name"

moved=0
for path in "$@"; do
    # Only move files (not directories) and skip the group folder itself.
    if [[ -f "$path" ]]; then
        mv -n "$path" "$name/"
        ((moved++)) || true
    fi
done

echo "Moved $moved file(s) into: $target_dir/$name"
