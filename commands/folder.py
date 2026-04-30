"""
commands/folders.py
Folder-level operations: create folder, create project scaffold, delete empty folders.
"""

import os

from config import DESKTOP, PROTECTED_FOLDERS
from core.logger import log, log_action
from core.utils import confirm


# ── Create Folder ─────────────────────────────────────────────────────────────

def create_folder(name: str) -> None:
    if not name:
        print("⚠️  Please provide a folder name.")
        return
    path = os.path.join(DESKTOP, name)
    if os.path.exists(path):
        print(f"⚠️  Folder already exists: {name}")
        return
    os.mkdir(path)
    log(f"Created folder: {path}")
    log_action("create_folder", path)
    print(f"✅ Created folder: {name}")


# ── Create Project Scaffold ───────────────────────────────────────────────────

def create_project(name: str) -> None:
    if not name:
        print("⚠️  Usage: create project <name>")
        return

    base = os.path.join(DESKTOP, name)
    sub_folders = ["src", "tests", "docs", "assets"]

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

def delete_empty_folders() -> None:
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

    if confirm("Delete them all?"):
        for folder in empty:
            os.rmdir(folder)
            log(f"Deleted empty folder: {folder}")
            # Intentionally NOT added to undo log — nothing to restore
        print(f"🗑️  Deleted {len(empty)} empty folder(s).")