import os
import shutil
import subprocess
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
DESKTOP   = os.path.expanduser("~/Desktop")
DOWNLOADS = os.path.expanduser("~/Downloads")
LOG_FILE  = os.path.join(DESKTOP, "agent_log.txt")

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(action: str) -> None:
    """Append a timestamped action to the log file."""
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} | {action}\n")

def confirm(message: str) -> bool:
    """Ask the user y/n and return True for yes."""
    return input(f"{message} (y/n): ").strip().lower() == "y"

def count_matches(folder: str, exts, exclude_keyword: str = "") -> list:
    """Return list of filenames in folder that match extensions (and optional exclusion)."""
    results = []
    for f in os.listdir(folder):
        if exclude_keyword and exclude_keyword in f.lower():
            continue
        if f.lower().endswith(exts):
            results.append(f)
    return results

def move_files(files: list, src_folder: str, dest_folder: str) -> int:
    """Move a list of filenames from src_folder to dest_folder. Returns count moved."""
    os.makedirs(dest_folder, exist_ok=True)
    count = 0
    for f in files:
        src  = os.path.join(src_folder, f)
        dest = os.path.join(dest_folder, f)
        shutil.move(src, dest)
        log(f"Moved {src} → {dest}")
        count += 1
    return count

# ── Main loop ─────────────────────────────────────────────────────────────────
print("Agent started... type 'goodbye' to exit")
print("Type 'help' to see all commands.\n")

while True:
    raw     = input(">> ").strip()
    command = raw.lower()

    if not command:
        continue

    # ── PREVIEW MODE ──────────────────────────────────────────────────────────
    if command.startswith("--preview"):
        inner = command.replace("--preview", "").strip()
        print(f"[PREVIEW] Would execute: '{inner}'")
        continue

    # ── HELP ──────────────────────────────────────────────────────────────────
    elif command == "help":
        print("""
Available commands:
  move pdf                          Move PDFs from Downloads → Desktop/PDF Files
  move images                       Move images from Downloads → Desktop/Images
  move screenshots                  Move screenshots from Downloads → Desktop/Screenshots
  sort downloads                    Sort PDFs + images from Downloads into Desktop folders
  create folder named <name>        Create a folder on Desktop
  create project <name>             Create a project scaffold on Desktop
  rename file <old> to <new>        Rename a file on Desktop
  find file <filename>              Search Desktop and Downloads for a file
  delete empty folders              Remove empty folders from Desktop
  open vscode                       Open Visual Studio Code
  --preview <command>               Show what a command would do without running it
  goodbye                           Exit the agent
""")

    # ── EXIT ──────────────────────────────────────────────────────────────────
    elif command == "goodbye":
        print("Goodbye! Shutting down...")
        break

    # ── CREATE FOLDER ─────────────────────────────────────────────────────────
    elif "create folder named" in command:
        name = command.replace("create folder named", "").strip()
        if not name:
            print("⚠️  Please provide a folder name.")
        else:
            path = os.path.join(DESKTOP, name)
            if not os.path.exists(path):
                os.mkdir(path)
                log(f"Created folder: {path}")
                print(f"✅ Created folder: {name}")
            else:
                print("⚠️  Folder already exists.")

    # ── MOVE PDFs ─────────────────────────────────────────────────────────────
    elif "move pdf" in command:
        files = count_matches(DOWNLOADS, ".pdf")
        if not files:
            print("📄 No PDFs found in Downloads.")
        elif confirm(f"Found {len(files)} PDF(s). Move them to Desktop/PDF Files?"):
            n = move_files(files, DOWNLOADS, os.path.join(DESKTOP, "PDF Files"))
            print(f"📄 Moved {n} PDF(s) to Desktop/PDF Files.")

    # ── MOVE SCREENSHOTS (must come before move images) ───────────────────────
    elif "move screenshots" in command:
        files = [f for f in os.listdir(DOWNLOADS) if "screenshot" in f.lower()]
        if not files:
            print("🖼️  No screenshots found in Downloads.")
        elif confirm(f"Found {len(files)} screenshot(s). Move to Desktop/Screenshots?"):
            n = move_files(files, DOWNLOADS, os.path.join(DESKTOP, "Screenshots"))
            print(f"🖼️  Moved {n} screenshot(s) to Desktop/Screenshots.")

    # ── MOVE IMAGES ───────────────────────────────────────────────────────────
    elif "move images" in command:
        files = count_matches(DOWNLOADS, (".png", ".jpg", ".jpeg", ".webp", ".gif"),
                              exclude_keyword="screenshot")
        if not files:
            print("🖼️  No images found in Downloads.")
        elif confirm(f"Found {len(files)} image(s). Move to Desktop/Images?"):
            n = move_files(files, DOWNLOADS, os.path.join(DESKTOP, "Images"))
            print(f"🖼️  Moved {n} image(s) to Desktop/Images.")

    # ── SORT DOWNLOADS ────────────────────────────────────────────────────────
    elif "sort downloads" in command:
        buckets = {
            "PDF Files": (".pdf",),
            "Images":    (".png", ".jpg", ".jpeg", ".webp", ".gif"),
            "Videos":    (".mp4", ".mov", ".avi", ".mkv"),
            "Archives":  (".zip", ".rar", ".tar", ".gz"),
            "Docs":      (".doc", ".docx", ".txt", ".xlsx", ".pptx"),
        }
        preview = {}
        for label, exts in buckets.items():
            matched = count_matches(DOWNLOADS, exts)
            if matched:
                preview[label] = matched

        if not preview:
            print("🗂️  Nothing to sort in Downloads.")
        else:
            print("Files that will be moved:")
            for label, files in preview.items():
                print(f"  → Desktop/{label}/  ({len(files)} file(s))")
            if confirm("Proceed?"):
                total = 0
                for label, files in preview.items():
                    total += move_files(files, DOWNLOADS, os.path.join(DESKTOP, label))
                print(f"🗂️  Sorted {total} file(s) from Downloads.")

    # ── RENAME FILE ───────────────────────────────────────────────────────────
    elif "rename file" in command:
        parts = command.replace("rename file", "").strip().split(" to ")
        if len(parts) != 2:
            print("⚠️  Usage: rename file <old name> to <new name>")
        else:
            old, new = parts[0].strip(), parts[1].strip()
            old_path = os.path.join(DESKTOP, old)
            new_path = os.path.join(DESKTOP, new)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                log(f"Renamed {old} → {new}")
                print(f"✅ Renamed '{old}' to '{new}'.")
            else:
                print(f"⚠️  File not found on Desktop: {old}")

    # ── DELETE EMPTY FOLDERS ──────────────────────────────────────────────────
    elif "delete empty folders" in command:
        PROTECTED = ["github", ".git"]  # add more names here if needed
        empty = []
        for root, dirs, files in os.walk(DESKTOP, topdown=False):
            if root == DESKTOP:
                continue  # never delete the Desktop itself
            if any(p in root.lower() for p in PROTECTED):
                continue  # skip GitHub and .git folders
            if not dirs and not files:
                empty.append(root)

        if not empty:
            print("✅ No empty folders found.")
        else:
            print(f"Found {len(empty)} empty folder(s):")
            for folder in empty:
                print(f"  {folder}")
            if confirm("Delete them all?"):
                for folder in empty:
                    os.rmdir(folder)
                    log(f"Deleted empty folder: {folder}")
                print(f"🗑️  Deleted {len(empty)} empty folder(s).")

    # ── FIND FILE ─────────────────────────────────────────────────────────────
    elif "find file" in command:
        filename = command.replace("find file", "").strip()
        if not filename:
            print("⚠️  Please provide a filename. Usage: find file <name>")
        else:
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
                print(f"🔍 No file named '{filename}' found.")

    # ── CREATE PROJECT ────────────────────────────────────────────────────────
    elif "create project" in command:
        name = command.replace("create project", "").strip()
        if not name:
            print("⚠️  Usage: create project <name>")
        else:
            base = os.path.join(DESKTOP, name)
            for folder in ["src", "tests", "docs", "assets"]:
                os.makedirs(os.path.join(base, folder), exist_ok=True)
            main_py = os.path.join(base, "src", "main.py")
            with open(main_py, "w") as f:
                f.write(f"# {name}\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n")
            log(f"Created project: {base}")
            print(f"🚀 Project '{name}' created: src/, tests/, docs/, assets/, src/main.py")

    # ── OPEN VS CODE ──────────────────────────────────────────────────────────
    elif "open vscode" in command or "open vs code" in command:
        try:
            subprocess.run(["open", "-a", "Visual Studio Code"], check=True)
            print("💻 Opening VS Code...")
        except subprocess.CalledProcessError:
            print("⚠️  Could not open VS Code. Is it installed?")

    # ── UNKNOWN ───────────────────────────────────────────────────────────────
    else:
        print("❓ Command not recognized. Type 'help' to see all commands.")