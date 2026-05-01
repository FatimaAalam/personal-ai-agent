"""
commands/files.py
All file-level operations: move, sort, rename, find, list folder, undo.
Each function is self-contained and returns nothing — it prints its own output.
"""
 
import os
import shutil
import hashlib
from collections import defaultdict
 
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
 
 
# ── Duplicate Finder ──────────────────────────────────────────────────────────
 
# Path segments — if ANY of these appear anywhere in a file's absolute path,
# that file is treated as a system/app file and is never touched.
_PROTECTED_PATH_SEGMENTS = (
    "/Applications/",
    ".app/Contents/",
    ".app/Frameworks/",
    ".app/Resources/",
    "/Frameworks/",
    "/node_modules/",
    "/.git/",
    "/Contents/",
    "/Resources/",
    "/Plugins/",
    "/Helpers/",
    "/SharedSupport/",
)
 
# File extensions that are part of how software works — never safe to delete
# as duplicates even if they appear in user folders.
_PROTECTED_EXTENSIONS = {
    ".pak", ".wasm", ".woff", ".woff2",
    ".dylib", ".so", ".a", ".o",
    ".plist", ".nib", ".lproj",
    ".strings", ".compiled",
    ".car",                          # compiled asset catalog
    ".metallib",                     # Metal shader library
}
 
# Exact filenames that are always protected regardless of location
_PROTECTED_FILENAMES = {
    "PkgInfo", "Info.plist", "CodeResources",
    "LICENSE", "LICENSE.md", "LICENSE.txt",
    "NOTICE", "NOTICE.md", "NOTICE.txt",
    "SECURITY.md", "PRIVACY", "PRIVACY.md",
    "package.json", "package-lock.json",
    "yarn.lock", "Cargo.lock", "Gemfile.lock",
}
 
 
def _is_protected(path: str) -> bool:
    """
    Return True if a file should never be touched by the duplicate finder.
    Checks path segments, file extension, and exact filename.
    """
    # Check dangerous path segments
    for segment in _PROTECTED_PATH_SEGMENTS:
        if segment in path:
            return True
 
    fname = os.path.basename(path)
    ext   = os.path.splitext(fname)[1].lower()
 
    # Check protected extensions
    if ext in _PROTECTED_EXTENSIONS:
        return True
 
    # Check protected exact filenames (case-sensitive — these are real names)
    if fname in _PROTECTED_FILENAMES:
        return True
 
    return False
 
 
def _file_hash(path: str, chunk_size: int = 65536) -> str | None:
    """
    Return the MD5 hash of a file's contents.
    Reads in chunks so large files don't blow up memory.
    Returns None if the file can't be read.
    """
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None
 
 
def find_duplicates() -> None:
    """
    Scan Desktop and Downloads recursively.
    Group files by MD5 hash — identical hash = identical content.
    Show each duplicate cluster and offer to delete all but the oldest copy.
 
    Safety: protected paths, extensions, and filenames are never included.
 
    Strategy (two-pass for speed):
      Pass 1 — group files by size. Files with unique sizes can't be duplicates.
      Pass 2 — hash only the size-matched candidates. Eliminates most I/O.
    """
    scan_folders = [DESKTOP, DOWNLOADS]
 
    print("🔍 Scanning Desktop and Downloads for duplicates...")
 
    # ── Pass 1: collect files, group by size — skip anything protected ─────────
    size_map: dict[int, list[str]] = defaultdict(list)
    skipped_count = 0
 
    for folder in scan_folders:
        for root, dirs, files in os.walk(folder):
            # Prune entire protected directories from the walk — don't descend
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".")
                and not _is_protected(os.path.join(root, d) + "/")
            ]
            for fname in files:
                if fname.startswith("."):
                    continue
                fpath = os.path.join(root, fname)
                if _is_protected(fpath):
                    skipped_count += 1
                    continue
                try:
                    size = os.path.getsize(fpath)
                    if size > 0:               # ignore empty files
                        size_map[size].append(fpath)
                except OSError:
                    continue
 
    if skipped_count:
        print(f"   🛡️  Skipped {skipped_count} protected system/app file(s).")
 
    # Only keep sizes that appear more than once — these are candidates
    candidates = [paths for paths in size_map.values() if len(paths) > 1]
 
    if not candidates:
        print("✅ No duplicate files found.")
        return
 
    # ── Pass 2: hash the candidates, group by hash ────────────────────────────
    hash_map: dict[str, list[str]] = defaultdict(list)
 
    total_candidates = sum(len(p) for p in candidates)
    print(f"   Found {total_candidates} size-matched file(s), hashing...")
 
    for paths in candidates:
        for path in paths:
            h = _file_hash(path)
            if h:
                hash_map[h].append(path)
 
    # Only keep hashes with more than one file = confirmed duplicates
    duplicate_groups = [paths for paths in hash_map.values() if len(paths) > 1]
 
    if not duplicate_groups:
        print("✅ No duplicate files found.")
        return
 
    # ── Report ────────────────────────────────────────────────────────────────
    total_dupes  = sum(len(g) - 1 for g in duplicate_groups)
    wasted_bytes = sum(
        os.path.getsize(p) * (len(g) - 1)
        for g in duplicate_groups
        for p in g[:1]
    )
 
    print(f"\n🗂️  Found {len(duplicate_groups)} duplicate group(s) — "
          f"{total_dupes} extra file(s) wasting {human_size_bytes(wasted_bytes)}.\n")
    print("  For each group, choose which copy to KEEP. The rest will be deleted.\n")
    print("  Commands per group:")
    print("    Enter a number (1, 2, …)  → keep that file, delete the others")
    print("    s                         → skip this group, delete nothing")
    print("    q                         → quit immediately, delete nothing\n")
    print("  " + "─" * 60)
 
    files_to_delete: list[str] = []
 
    for i, group in enumerate(duplicate_groups, 1):
        # Default sort: oldest first (index 0) — shown as suggestion
        group_sorted = sorted(group, key=lambda p: os.path.getmtime(p))
 
        print(f"\n  Group {i} of {len(duplicate_groups)}  "
              f"({len(group)} identical files, {human_size(group_sorted[0])} each)\n")
 
        for idx, path in enumerate(group_sorted, 1):
            # Show a hint next to the oldest copy
            hint = "  ← oldest" if idx == 1 else ""
            print(f"    [{idx}]  {path}{hint}")
 
        print()
 
        # ── Get user choice for this group ────────────────────────────────────
        while True:
            raw_choice = input(f"  Keep which copy? [1-{len(group_sorted)} / s=skip / q=quit]: ").strip().lower()
 
            if raw_choice == "q":
                print("\n  Quit — no files were deleted.")
                return
 
            if raw_choice == "s":
                print("  ⏭️  Skipped.")
                break
 
            if raw_choice.isdigit():
                choice = int(raw_choice)
                if 1 <= choice <= len(group_sorted):
                    keeper    = group_sorted[choice - 1]
                    to_delete = [p for p in group_sorted if p != keeper]
                    print(f"  ✅ Keeping : {keeper}")
                    for p in to_delete:
                        print(f"  🗑️  Will delete: {p}")
                    files_to_delete.extend(to_delete)
                    break
                else:
                    print(f"  ⚠️  Please enter a number between 1 and {len(group_sorted)}.")
            else:
                print(f"  ⚠️  Invalid input. Enter a number, 's' to skip, or 'q' to quit.")
 
    # ── Nothing selected ─────────────────────────────────────────────────────
    if not files_to_delete:
        print("\n✅ No files marked for deletion.")
        return
 
    # ── Final safety check before deleting ───────────────────────────────────
    # Re-verify every path right before deletion — catches anything that slipped
    # through or changed location between scan and now.
    safe_to_delete = []
    blocked        = []
    for path in files_to_delete:
        if _is_protected(path):
            blocked.append(path)
        else:
            safe_to_delete.append(path)
 
    if blocked:
        print(f"\n  🛡️  {len(blocked)} file(s) blocked by safety check (not deleted):")
        for p in blocked:
            print(f"       {p}")
 
    if not safe_to_delete:
        print("\n✅ Nothing to delete after safety checks.")
        return
 
    # ── Final confirmation ────────────────────────────────────────────────────
    print(f"\n  Summary: {len(safe_to_delete)} file(s) will be permanently deleted.\n")
    for path in safe_to_delete:
        print(f"    🗑️  {path}")
 
    print()
    if confirm(f"Confirm — permanently delete these {len(safe_to_delete)} file(s)?"):
        deleted = 0
        for path in safe_to_delete:
            try:
                os.remove(path)
                log(f"Deleted duplicate: {path}")
                deleted += 1
            except OSError as e:
                print(f"  ⚠️  Could not delete {path}: {e}")
        print(f"\n🗑️  Done. Deleted {deleted} file(s).")
    else:
        print("Cancelled. No files were deleted.")
 
 
def human_size_bytes(b: int) -> str:
    """Same as human_size() but accepts raw bytes directly (not a path)."""
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.0f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
 
 
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
 
