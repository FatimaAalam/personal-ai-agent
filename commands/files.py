"""
commands/files.py
Move and sort operations: move_pdfs, move_images, move_screenshots,
sort_downloads, rename_file.
Each function is self-contained and prints its own output.
"""
 
import os
import shutil
 
from config import DESKTOP, DOWNLOADS, FILE_BUCKETS, IMAGE_EXTS
from core.logger import log, log_action
from core.utils import confirm, count_matches
 
 
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
 



