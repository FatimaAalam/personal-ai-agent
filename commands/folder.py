"""
commands/folder.py
Folder-level operations: create folder, create project scaffold, delete empty folders.
"""
import os
from config import DESKTOP, DOWNLOADS, PROTECTED_FOLDERS
from core.logger import log, log_action
from core.utils import confirm

# ── Location resolver ──────────────────────────────────────────────────────────
_LOCATION_MAP = {
    "desktop":   DESKTOP,
    "downloads": DOWNLOADS,
}

def _resolve_location(location: str) -> str:
    """
    Turn a location string ('downloads', 'desktop') into an absolute path.
    Falls back to Desktop for anything unrecognised.
    """
    return _LOCATION_MAP.get(location.lower().strip(), DESKTOP)

# ── Create Folder ─────────────────────────────────────────────────────────────
def create_folder(name: str, location: str = "desktop", preview: bool = False) -> None:
    if not name:
        print("⚠️  Please provide a folder name.")
        return
    base = _resolve_location(location)
    path = os.path.join(base, name)
    if preview:
        print(f"  [preview] Would create folder: {path}")
        return
    if os.path.exists(path):
        print(f"⚠️  Folder already exists: {name}")
        return
    os.mkdir(path)
    log(f"Created folder: {path}")
    log_action("create_folder", path)
    print(f"✅ Created folder '{name}' in {location}")

# ── Create Project Scaffold ───────────────────────────────────────────────────
def create_project(name: str, preview: bool = False) -> None:
    if not name:
        print("⚠️  Usage: create project <name>")
        return
    base = os.path.join(DESKTOP, name)
    sub_folders = ["src", "tests", "docs", "assets"]
    if preview:
        print(f"  [preview] Would create project: {base}/")
        for folder in sub_folders:
            print(f"  [preview]   {folder}/")
        print(f"  [preview]   src/main.py")
        print(f"  [preview]   README.md")
        return
    for folder in sub_folders:
        os.makedirs(os.path.join(base, folder), exist_ok=True)
    main_py = os.path.join(base, "src", "main.py")
    with open(main_py, "w") as f:
        f.write(
            f"# {name}\n\n"
            "def main():\n"
            "    pass\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
    readme = os.path.join(base, "README.md")
    with open(readme, "w") as f:
        f.write(f"# {name}\n\n> Project description here.\n\n## Setup\n\n## Usage\n")
    log(f"Created project: {base}")
    print(f"🚀 Project '{name}' created:")
    for folder in sub_folders:
        print(f"   📁 {folder}/")
    print(f"   📄 src/main.py")
    print(f"   📄 README.md")

# ── Delete Empty Folders ──────────────────────────────────────────────────────
def delete_empty_folders(preview: bool = False) -> None:
    empty = []
    for root, dirs, files in os.walk(DESKTOP, topdown=False):
        if root == DESKTOP:
            continue
        if any(p in root.lower() for p in PROTECTED_FOLDERS):
            continue
        if not dirs and not files:
            empty.append(root)
    if not empty:
        print("✅ No empty folders found on Desktop.")
        return
    print(f"Found {len(empty)} empty folder(s):")
    for folder in empty:
        print(f"  {folder}")
    if preview:
        print("\n👁 Preview mode — no folders were deleted.")
        return
    if confirm("Delete them all?"):
        for folder in empty:
            os.rmdir(folder)
            log(f"Deleted empty folder: {folder}")
        print(f"🗑️  Deleted {len(empty)} empty folder(s).")