"""
commands/history.py
History and navigation: undo_last, list_folder.
undo_last reverses the most recent logged action.
list_folder displays folder contents with icons and sizes.
"""

import os
import shutil

from config import DESKTOP, DOWNLOADS
from core.logger import log, peek_last_action, pop_last_action
from core.utils import confirm, file_icon, human_size


# ── List Folder ───────────────────────────────────────────────────────────────

def list_folder(target: str) -> None:
    """
    List contents of a folder one level deep with icons and sizes.
    target: 'desktop' | 'downloads' | any Desktop sub-folder name
    """
    keyword = target.lower().strip()
    if keyword in ("desktop", ""):
        folder_path, label = DESKTOP, "Desktop"
    elif keyword == "downloads":
        folder_path, label = DOWNLOADS, "Downloads"
    else:
        folder_path = os.path.join(DESKTOP, target)
        label       = f"Desktop/{target}"

    if not os.path.isdir(folder_path):
        print(f"⚠️  Folder not found: {folder_path}")
        return

    try:
        entries = sorted(os.listdir(folder_path))
    except PermissionError:
        print(f"⚠️  Permission denied: {folder_path}")
        return

    if not entries:
        print(f"📂 '{label}' is empty.")
        return

    folders = [e for e in entries if os.path.isdir(os.path.join(folder_path, e))]
    files   = [e for e in entries if os.path.isfile(os.path.join(folder_path, e))]

    print(f"\n📂 {label}  ({len(folders)} folder(s), {len(files)} file(s))\n")

    if folders:
        print("  ── Folders ──")
        for d in folders:
            try:
                sub_count = len(os.listdir(os.path.join(folder_path, d)))
            except PermissionError:
                sub_count = "?"
            print(f"    📁  {d}/  ({sub_count} item(s))")

    if files:
        print("  ── Files ──")
        for fname in files:
            fpath = os.path.join(folder_path, fname)
            print(f"    {file_icon(fname)}  {fname}  [{human_size(fpath)}]")

    print()


# ── Undo ──────────────────────────────────────────────────────────────────────

def undo_last() -> None:
    """Read the undo stack and reverse the most recent reversible action."""
    last = peek_last_action()
    if not last:
        print("↩️  Nothing to undo — action log is empty.")
        return

    action_type = last["action"]
    orig        = last["original_path"]
    dest        = last["destination_path"]
    ts          = last["timestamp"]

    print(f"\n  Last action  : {action_type}")
    print(f"  Recorded at  : {ts}")
    print(f"  Original path: {orig}")
    if dest:
        print(f"  Moved to     : {dest}")

    # ── Reverse: move / rename ────────────────────────────────────────────────
    if action_type in ("move", "rename"):
        if not os.path.exists(dest):
            print(f"⚠️  File no longer exists at: {dest}")
            return
        if not confirm(f"\nUndo this {action_type}?"):
            print("Cancelled.")
            return
        os.makedirs(os.path.dirname(orig), exist_ok=True)
        shutil.move(dest, orig)
        log(f"Undid {action_type}: {dest} → {orig}")
        pop_last_action()
        print(f"✅ Undone. '{os.path.basename(dest)}' restored to:\n   {orig}")

    # ── Reverse: create_folder ────────────────────────────────────────────────
    elif action_type == "create_folder":
        if not os.path.exists(orig):
            print(f"⚠️  Folder no longer exists: {orig}")
            return
        if os.listdir(orig):
            print(f"⚠️  Cannot undo — folder is not empty: {orig}")
            return
        if not confirm("Undo folder creation (delete it)?"):
            print("Cancelled.")
            return
        os.rmdir(orig)
        log(f"Undid create_folder: removed {orig}")
        pop_last_action()
        print(f"✅ Folder removed: {orig}")

    else:
        print(f"↩️  '{action_type}' cannot be automatically undone.")