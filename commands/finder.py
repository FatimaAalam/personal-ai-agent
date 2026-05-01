"""
commands/finder.py
Search operations: find_file, find_duplicates.
find_duplicates uses a two-pass approach (size → hash) with safety
guards so it never touches system or app files.
"""

import os
import hashlib
from collections import defaultdict

from config import DESKTOP, DOWNLOADS
from core.logger import log
from core.utils import confirm, human_size


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


# ── Duplicate Finder internals ────────────────────────────────────────────────

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
    ".car",        # compiled asset catalog
    ".metallib",   # Metal shader library
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
    """Return True if a file should never be touched by the duplicate finder."""
    if any(seg in path for seg in _PROTECTED_PATH_SEGMENTS):
        return True
    _, ext = os.path.splitext(path)
    if ext.lower() in _PROTECTED_EXTENSIONS:
        return True
    if os.path.basename(path) in _PROTECTED_FILENAMES:
        return True
    return False


def _file_hash(path: str) -> str | None:
    """Return MD5 hex digest of a file, or None on read error."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _human_size_bytes(b: int) -> str:
    """Convert raw byte count to a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.0f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


# ── Find Duplicates ───────────────────────────────────────────────────────────

def find_duplicates() -> None:
    scan_folders = [DESKTOP, DOWNLOADS]

    print("🔍 Scanning Desktop and Downloads for duplicates...")

    # ── Pass 1: collect files, group by size ──────────────────────────────────
    size_map: dict[int, list[str]] = defaultdict(list)
    skipped_count = 0

    for folder in scan_folders:
        for root, dirs, files in os.walk(folder):
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
                    if size > 0:
                        size_map[size].append(fpath)
                except OSError:
                    continue

    if skipped_count:
        print(f"   🛡️  Skipped {skipped_count} protected system/app file(s).")

    candidates = [paths for paths in size_map.values() if len(paths) > 1]

    if not candidates:
        print("✅ No duplicate files found.")
        return

    # ── Pass 2: hash candidates, group by hash ────────────────────────────────
    hash_map: dict[str, list[str]] = defaultdict(list)
    total_candidates = sum(len(p) for p in candidates)
    print(f"   Found {total_candidates} size-matched file(s), hashing...")

    for paths in candidates:
        for path in paths:
            h = _file_hash(path)
            if h:
                hash_map[h].append(path)

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
          f"{total_dupes} extra file(s) wasting {_human_size_bytes(wasted_bytes)}.\n")
    print("  For each group, choose which copy to KEEP. The rest will be deleted.\n")
    print("  Commands per group:")
    print("    Enter a number (1, 2, …)  → keep that file, delete the others")
    print("    s                         → skip this group, delete nothing")
    print("    q                         → quit immediately, delete nothing\n")
    print("  " + "─" * 60)

    files_to_delete: list[str] = []

    for i, group in enumerate(duplicate_groups, 1):
        group_sorted = sorted(group, key=lambda p: os.path.getmtime(p))

        print(f"\n  Group {i} of {len(duplicate_groups)}  "
              f"({len(group)} identical files, {human_size(group_sorted[0])} each)\n")

        for idx, path in enumerate(group_sorted, 1):
            hint = "  ← oldest" if idx == 1 else ""
            print(f"    [{idx}]  {path}{hint}")

        print()

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
                print("  ⚠️  Invalid input. Enter a number, 's' to skip, or 'q' to quit.")

    if not files_to_delete:
        print("\n✅ No files marked for deletion.")
        return

    # ── Final safety re-check ─────────────────────────────────────────────────
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