"""
commands/fileops.py
Basic file operations: create_file, delete_file.

create_file  — creates a file (and its parent folder if needed) on Desktop.
delete_file  — moves a file to the macOS Trash via send2trash (reversible).
               Falls back to a permanent os.remove() if send2trash is missing,
               but warns the user first.

Parsing is handled in agent.py; these functions receive clean arguments.

Requires:  pip install send2trash
"""

import os

try:
    from send2trash import send2trash
    TRASH_AVAILABLE = True
except ImportError:
    TRASH_AVAILABLE = False

from config import DESKTOP
from core.logger import log, log_action
from core.utils import confirm


# ── Create File ───────────────────────────────────────────────────────────────

def create_file(filename: str, folder: str | None = None) -> None:
    """
    Create an empty file on Desktop, optionally inside a sub-folder.
    If the sub-folder doesn't exist it is created automatically.

    Parameters
    ----------
    filename : str   e.g. "notes.txt"
    folder   : str   e.g. "study"  (a Desktop sub-folder name, or None)
    """
    if not filename:
        print("⚠️  Usage: create file <name> [in folder <folder>]")
        return

    # ── Resolve destination ───────────────────────────────────────────────────
    if folder:
        dir_path  = os.path.join(DESKTOP, folder)
        file_path = os.path.join(dir_path, filename)
    else:
        dir_path  = DESKTOP
        file_path = os.path.join(DESKTOP, filename)

    # ── Guard: already exists ─────────────────────────────────────────────────
    if os.path.exists(file_path):
        print(f"⚠️  File already exists: {file_path}")
        return

    # ── Auto-create folder if needed ──────────────────────────────────────────
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        log(f"Auto-created folder: {dir_path}")
        log_action("create_folder", dir_path, "")
        print(f"📁 Folder '{folder}' didn't exist — created it.")

    # ── Create the file ───────────────────────────────────────────────────────
    with open(file_path, "w") as f:
        pass   # empty file

    log(f"Created file: {file_path}")
    log_action("create_file", file_path, "")

    if folder:
        print(f"✅ Created '{filename}' in Desktop/{folder}/")
    else:
        print(f"✅ Created '{filename}' on Desktop.")


# ── Delete File ───────────────────────────────────────────────────────────────

def delete_file(filename: str, folder: str | None = None) -> None:
    """
    Move a file to the macOS Trash (reversible — same as Cmd+Delete in Finder).
    Uses send2trash if available; warns and asks for explicit consent before
    falling back to permanent deletion if the library is missing.

    Parameters
    ----------
    filename : str   e.g. "notes.txt"
    folder   : str   e.g. "study"  (a Desktop sub-folder name, or None)
    """
    if not filename:
        print("⚠️  Usage: delete file <name> [in folder <folder>]")
        return

    # ── Resolve path ──────────────────────────────────────────────────────────
    if folder:
        file_path = os.path.join(DESKTOP, folder, filename)
    else:
        file_path = os.path.join(DESKTOP, filename)

    display = f"Desktop/{folder}/{filename}" if folder else f"Desktop/{filename}"

    # ── Guard: doesn't exist ──────────────────────────────────────────────────
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {display}")
        return

    # ── Guard: is a directory ─────────────────────────────────────────────────
    if os.path.isdir(file_path):
        print(f"⚠️  '{filename}' is a folder, not a file. Use 'delete empty folders' instead.")
        return

    # ── send2trash not installed — warn before doing anything permanent ────────
    if not TRASH_AVAILABLE:
        print("⚠️  send2trash is not installed — Trash support unavailable.")
        print("   Run:  pip install send2trash")
        print("   This would be a PERMANENT delete with no recovery.\n")
        if not confirm(f"Permanently delete '{display}' with NO undo?"):
            print("Cancelled. Install send2trash for safe Trash support.")
            return
        try:
            os.remove(file_path)
            log(f"Permanently deleted file: {file_path}")
            print(f"🗑️  Permanently deleted '{filename}'. (Install send2trash to use Trash instead.)")
        except OSError as e:
            print(f"⚠️  Could not delete file: {e}")
        return

    # ── Normal path: move to Trash ────────────────────────────────────────────
    if not confirm(f"Move '{display}' to Trash? (You can recover it from Finder → Trash)"):
        print("Cancelled.")
        return

    try:
        send2trash(file_path)
        log(f"Moved to Trash: {file_path}")
        log_action("trash_file", file_path, "")
        print(f"🗑️  Moved '{filename}' to Trash.")
        print(f"   To recover: open Finder → Trash → right-click → Put Back.")
    except Exception as e:
        print(f"⚠️  Could not move to Trash: {e}")