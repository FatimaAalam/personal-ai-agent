"""
core/agent.py
The main command router. Reads user input, dispatches to the right command.
Adding a new command = one elif block + one import. Nothing else changes.
"""
from commands.files   import (find_file, find_duplicates, list_folder,
                               move_images, move_pdfs, move_screenshots,
                               sort_downloads, rename_file, undo_last)
from commands.folder  import create_folder, create_project, delete_empty_folders
from commands.system  import open_app, open_vscode
from commands.watch_mode import start_watch, stop_watch, is_active
from core.logger      import log
from pathlib          import Path
import config

HELP_TEXT = """
╔══════════════════════════════════════════════════════════╗
║              Personal AI Agent — Commands                ║
╠══════════════════════════════════════════════════════════╣
║  FILE OPERATIONS                                         ║
║    move pdf                  Downloads → Desktop/PDF Files║
║    move images               Downloads → Desktop/Images  ║
║    move screenshots          Downloads → Desktop/Screenshots║
║    sort downloads            Auto-sort all Downloads     ║
║    rename file <old> to <new>                            ║
║    find file <filename>      Search Desktop + Downloads  ║
║    find duplicates           Find identical files        ║
║    list desktop              List everything on Desktop  ║
║    list downloads            List everything in Downloads ║
║    list <folder name>        List a Desktop sub-folder   ║
║    undo                      Reverse last action         ║
╠══════════════════════════════════════════════════════════╣
║  FOLDER OPERATIONS                                       ║
║    create folder named <name>                            ║
║    create project <name>     Full scaffold (src/tests/…) ║
║    delete empty folders      Clean up Desktop            ║
╠══════════════════════════════════════════════════════════╣
║  SYSTEM                                                  ║
║    open vscode                                           ║
║    open app <name>           Open any macOS app          ║
╠══════════════════════════════════════════════════════════╣
║  WATCH MODE                                              ║
║    watch on                  Auto-sort Downloads on drop ║
║    watch off                 Stop background watcher     ║
║    watch status              Show watcher state          ║
╠══════════════════════════════════════════════════════════╣
║  OTHER                                                   ║
║    --preview <command>       Dry-run without executing   ║
║    help                      Show this menu              ║
║    goodbye                   Exit                        ║
╚══════════════════════════════════════════════════════════╝
"""

def run() -> None:
    """Start the agent input loop."""
    print("🤖 Personal AI Agent started. Type 'help' for commands, 'goodbye' to exit.\n")

    while True:
        try:
            watch_badge = " [👁 watching]" if is_active() else ""
            raw = input(f">>{watch_badge} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        command = raw.lower()

        # ── Preview mode ──────────────────────────────────────────────────────
        if command.startswith("--preview"):
            inner = command.replace("--preview", "").strip()
            print(f"[PREVIEW] Would execute: '{inner}'")

        # ── Help ──────────────────────────────────────────────────────────────
        elif command == "help":
            print(HELP_TEXT)

        # ── Exit ──────────────────────────────────────────────────────────────
        elif command == "goodbye":
            print("👋 Goodbye! Shutting down...")
            break

        # ── Watch mode ────────────────────────────────────────────────────────
        elif command in ("watch on", "watch start", "start watch"):
            print(start_watch(sort_downloads, log, Path(config.DOWNLOADS)))

        elif command in ("watch off", "watch stop", "stop watch"):
            print(stop_watch(log))

        elif command in ("watch status", "watch"):
            if is_active():
                print(f"👁  Watch mode is ACTIVE — monitoring {config.DOWNLOADS}")
            else:
                print("💤  Watch mode is OFF.  Type  watch on  to start.")

        # ── List folder ───────────────────────────────────────────────────────
        elif command.startswith("list "):
            target = raw[5:].strip()          # preserve original casing
            list_folder(target)

        # ── Undo ──────────────────────────────────────────────────────────────
        elif command == "undo":
            undo_last()

        # ── Move PDFs ─────────────────────────────────────────────────────────
        elif "move pdf" in command:
            move_pdfs()

        # ── Move Screenshots (before move images — order matters) ─────────────
        elif "move screenshots" in command:
            move_screenshots()

        # ── Move Images ───────────────────────────────────────────────────────
        elif "move images" in command:
            move_images()

        # ── Sort Downloads ────────────────────────────────────────────────────
        elif "sort downloads" in command:
            sort_downloads()

        # ── Rename File ───────────────────────────────────────────────────────
        elif "rename file" in command:
            parts = command.replace("rename file", "").strip().split(" to ")
            if len(parts) != 2:
                print("⚠️  Usage: rename file <old name> to <new name>")
            else:
                rename_file(parts[0].strip(), parts[1].strip())

        # ── Find File ─────────────────────────────────────────────────────────
        elif command.startswith("find file"):
            filename = raw[9:].strip()
            find_file(filename)

        # ── Find Duplicates ───────────────────────────────────────────────────
        elif "find duplicates" in command or "find duplicate" in command:
            find_duplicates()

        # ── Delete Empty Folders ──────────────────────────────────────────────
        elif "delete empty folders" in command:
            delete_empty_folders()

        # ── Create Folder ─────────────────────────────────────────────────────
        elif "create folder named" in command:
            name = raw.lower().replace("create folder named", "").strip()
            create_folder(name)

        # ── Create Project ────────────────────────────────────────────────────
        elif command.startswith("create project"):
            name = raw[14:].strip()
            create_project(name)

        # ── Open VS Code ──────────────────────────────────────────────────────
        elif "open vscode" in command or "open vs code" in command:
            open_vscode()

        # ── Open App (generic) ────────────────────────────────────────────────
        elif command.startswith("open app"):
            app_name = raw[8:].strip()
            open_app(app_name)

        # ── Unknown ───────────────────────────────────────────────────────────
        else:
            print("❓ Unknown command. Type 'help' to see all commands.")