"""
commands/files.py
All file-level operations: move, sort, rename, find, list folder, undo.
Each function is self-contained and returns nothing — it prints its own output.
"""

import os
import shutil

from config import DESKTOP, DOWNLOADS, FILE_BUCKETS, IMAGE_EXTS
from core.logger import log, log_action, peek_last_action, pop_last_action
from core.utils import confirm, count_matches, file_icon, human_size


# ── Internal: move a batch of files ──────────────────────────────────────────

def _move_files(files: list[str], src_folder: str, dest_folder: str) -> int:
    """Move filenames from src_folder to dest_folder. Returns count moved."""
    os.makedirs(dest_folder, exist_ok=True)
    count = 0
    for f in files:
        src  = os.path.join(src_folder, f)
        dest = os.path.join(dest_folder, f)
        shutil.move(src, dest)
        log(f"Moved {src} → {dest}")
        log_action("move", src, dest)
        count += 1
    return count


# ── Move PDFs ─────────────────────────────────────────────────────────────────

def move_pdfs() -> None:
    files = count_matches(DOWNLOADS, (".pdf",))
    if not files:
        print("📄 No PDFs found in Downloads.")
        return
    if confirm(f"Found {len(files)} PDF(s). Move to Desktop/PDF Files?"):
        n = _move_files(files, DOWNLOADS, os.path.join(DESKTOP, "PDF Files"))
        print(f"📄 Moved {n} PDF(s) to Desktop/PDF Files.")


# ── Move Screenshots ──────────────────────────────────────────────────────────

def move_screenshots() -> None:
    try:
        files = [f for f in os.listdir(DOWNLOADS) if "screenshot" in f.lower()]
    except FileNotFoundError:
        files = []
    if not files:
        print("🖼️  No screenshots found in Downloads.")
        return
    if confirm(f"Found {len(files)} screenshot(s). Move to Desktop/Screenshots?"):
        n = _move_files(files, DOWNLOADS, os.path.join(DESKTOP, "Screenshots"))
        print(f"🖼️  Moved {n} screenshot(s) to Desktop/Screenshots.")


# ── Move Images ───────────────────────────────────────────────────────────────

def move_images() -> None:
    files = count_matches(DOWNLOADS, IMAGE_EXTS, exclude_keyword="screenshot")
    if not files:
        print("🖼️  No images found in Downloads.")
        return
    if confirm(f"Found {len(files)} image(s). Move to Desktop/Images?"):
        n = _move_files(files, DOWNLOADS, os.path.join(DESKTOP, "Images"))
        print(f"🖼️  Moved {n} image(s) to Desktop/Images.")


# ── Sort Downloads ────────────────────────────────────────────────────────────

def sort_downloads() -> None:
    preview: dict[str, list] = {}
    for label, exts in FILE_BUCKETS.items():
        matched = count_matches(DOWNLOADS, exts)
        if matched:
            preview[label] = matched

    if not preview:
        print("🗂️  Nothing to sort in Downloads.")
        return

    print("Files that will be moved:")
    for label, files in preview.items():
        print(f"  → Desktop/{label}/  ({len(files)} file(s))")

    if confirm("Proceed?"):
        total = 0
        for label, files in preview.items():
            total += _move_files(files, DOWNLOADS, os.path.join(DESKTOP, label))
        print(f"🗂️  Sorted {total} file(s) from Downloads.")


# ── Rename File ───────────────────────────────────────────────────────────────

def rename_file(old: str, new: str) -> None:
    old_path = os.path.join(DESKTOP, old)
    new_path = os.path.join(DESKTOP, new)
    if not os.path.exists(old_path):
        print(f"⚠️  File not found on Desktop: {old}")
        return
    os.rename(old_path, new_path)
    log(f"Renamed {old} → {new}")
    log_action("rename", old_path, new_path)
    print(f"✅ Renamed '{old}' to '{new}'.")


# ── Find File ─────────────────────────────────────────────────────────────────

def find_file(filename: str) -> None:
    if not filename:
        print("⚠️  Usage: find file <name>")
        return
    found = []
    for folder in [DESKTOP, DOWNLOADS]:
        for root, _, files in os.walk(folder):
            if filename in files:
                found.append(os.path.join(root, filename))
    if found:
        print(f"🔍 Found {len(found)} match(es):")
        for path in found:
            print(f"  {path}")
    else:
        print(f"🔍 No file named '{filename}' found on Desktop or Downloads.")


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