"""
core/utils.py
Shared utility functions used across commands.
No business logic here — pure helpers.
"""

import os
from config import FILE_ICONS


def confirm(message: str) -> bool:
    """Prompt the user for y/n confirmation. Returns True for yes."""
    return input(f"{message} (y/n): ").strip().lower() == "y"


def file_icon(filename: str) -> str:
    """Return an emoji icon based on a file's extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if not ext:
        return "📃"
    return FILE_ICONS.get(ext, "📃")


def human_size(path: str) -> str:
    """Return a human-readable file size string (B / KB / MB / GB)."""
    try:
        b = os.path.getsize(path)
        for unit in ("B", "KB", "MB", "GB"):
            if b < 1024:
                return f"{b:.0f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"
    except OSError:
        return "?"


def count_matches(folder: str, exts: tuple, exclude_keyword: str = "") -> list[str]:
    """
    Return filenames in folder whose extensions match `exts`.
    Optionally exclude filenames containing `exclude_keyword`.
    """
    results = []
    try:
        for f in os.listdir(folder):
            if exclude_keyword and exclude_keyword in f.lower():
                continue
            if f.lower().endswith(exts):
                results.append(f)
    except FileNotFoundError:
        pass
    return results