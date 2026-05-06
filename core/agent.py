"""
core/agent.py  —  Command router (Phase 2: hybrid AI + string matching)

Flow for every user input:
  1. Try ai/brain.py → Ollama parses intent into a known command key.
  2. If Ollama returns a valid command  → route it directly (no string matching).
  3. If Ollama returns None (offline / unknown) → fall back to string matching.
  4. If neither matches → "I didn't understand that."

The prompt shows [🤖 AI] when Ollama is reachable, [⚡ local] when falling back.
"""

import os
from pathlib import Path

import config
from core.logger  import log, log_action, peek_last_action
from core.utils   import confirm

from commands.files    import move_pdfs, move_images, move_screenshots, sort_downloads, rename_file
from commands.history  import list_folder, undo_last
from commands.finder   import find_file, find_duplicates
from commands.fileops  import create_file, delete_file
from commands.folder  import create_folder, create_project, delete_empty_folders
from commands.system   import open_vscode, open_app
from commands.watch_mode import start_watch, stop_watch, is_active

# ── AI brain (Phase 2) ────────────────────────────────────────────────────────
from ai.brain import parse_intent, COMMAND_MAP

# ── Help text ─────────────────────────────────────────────────────────────────
HELP_TEXT = """
╔══════════════════════════════════════════════════════╗
║            Personal AI Agent  —  Commands            ║
╠══════════════════════════════════════════════════════╣
║  FILE COMMANDS                                       ║
║  list desktop / list downloads / list <path>         ║
║  move pdf / move images / move screenshots           ║
║  sort downloads                                      ║
║  rename file <old> to <new>                          ║
║  find file <name>                                    ║
║  find duplicates                                     ║
║  undo                                                ║
║                                                      ║
║  FOLDER COMMANDS                                     ║
║  create folder named <name>                          ║
║  create project <name>                               ║
║  delete empty folders                                ║
║                                                      ║
║  SYSTEM COMMANDS                                     ║
║  open vscode                                         ║
║  open app <name>                                     ║
║                                                      ║
║  WATCH MODE                                          ║
║  watch on  /  watch off  /  watch status             ║
║                                                      ║
║  OTHER                                               ║
║  help                                                ║
║  goodbye                                             ║
║                                                      ║
║  TIP: Prefix any command with --preview to dry-run.  ║
║  TIP: You can now speak naturally! The AI brain      ║
║       understands plain English.                     ║
╚══════════════════════════════════════════════════════╝
"""

# ── Intent → handler dispatch ─────────────────────────────────────────────────

def _dispatch(command: str, args: dict, preview: bool) -> bool:
    """
    Route a parsed intent to the correct handler.
    Returns True if a handler was found, False otherwise.
    """
    c = command  # shorthand

    if c == "list_folder":
        folder = args.get("folder", "downloads")
        list_folder(folder)

    elif c == "undo":
        undo_last()

    elif c == "move_pdfs":
        move_pdfs(preview=preview)

    elif c == "move_images":
        move_images(preview=preview)

    elif c == "move_screenshots":
        move_screenshots(preview=preview)

    elif c == "sort_downloads":
        sort_downloads(preview=preview)

    elif c == "rename_file":
        old = args.get("old", "")
        new = args.get("new", "")
        if not old or not new:
            print("⚠️  I need both the old name and the new name.")
            return True
        rename_file(old, new, preview=preview)

    elif c == "find_file":
        name = args.get("name", "")
        if not name:
            print("⚠️  What file should I search for?")
            return True
        find_file(name)

    elif c == "find_duplicates":
        find_duplicates()

    elif c == "create_folder":
        name     = args.get("name", "")
        location = args.get("location", "desktop")
        if not name:
            print("⚠️  What should I name the folder?")
            return True
        create_folder(name, location=location, preview=preview)

    elif c == "create_project":
        name = args.get("name", "")
        if not name:
            print("⚠️  What should I name the project?")
            return True
        create_project(name, preview=preview)

    elif c == "create_file":
        name   = args.get("name", "")
        folder = args.get("folder", None)
        if not name:
            print("⚠️  What should I name the file?")
            return True
        create_file(name, folder)

    elif c == "delete_file":
        name   = args.get("name", "")
        folder = args.get("folder", None)
        if not name:
            print("⚠️  Which file should I delete?")
            return True
        delete_file(name, folder)

    elif c == "delete_empty_folders":
        delete_empty_folders(preview=preview)

    elif c == "open_vscode":
        open_vscode()

    elif c == "open_app":
        name = args.get("name", "")
        if not name:
            print("⚠️  Which app should I open?")
            return True
        open_app(name)

    elif c == "watch_on":
        print(start_watch(sort_downloads, log, Path(config.DOWNLOADS)))

    elif c == "watch_off":
        print(stop_watch(log))

    elif c == "watch_status":
        status = "active 👁" if is_active() else "inactive"
        print(f"Watch mode is {status}.")

    elif c == "help":
        print(HELP_TEXT)

    elif c == "goodbye":
        print("Goodbye! 👋")
        return "exit"

    else:
        return False

    return True


# ── String-match fallback ─────────────────────────────────────────────────────

def _string_match(raw: str, preview: bool):
    """
    Original Phase 1 string matching — only runs when Ollama returns None.
    Returns (command_key, args_dict) or (None, None).
    """
    t = raw.lower().strip()

    if t in ("goodbye", "bye", "exit", "quit"):
        return "goodbye", {}
    if t == "help":
        return "help", {}
    if t in ("undo", "undo last"):
        return "undo", {}
    if t.startswith("list"):
        parts = t.split()
        folder = parts[1] if len(parts) > 1 else "downloads"
        return "list_folder", {"folder": folder}
    if t in ("move pdf", "move pdfs"):
        return "move_pdfs", {}
    if t in ("move images", "move image"):
        return "move_images", {}
    if t in ("move screenshots", "move screenshot"):
        return "move_screenshots", {}
    if t in ("sort downloads", "sort download"):
        return "sort_downloads", {}
    if t.startswith("rename file "):
        rest = raw[len("rename file "):].strip()
        if " to " in rest:
            old, new = rest.split(" to ", 1)
            return "rename_file", {"old": old.strip(), "new": new.strip()}
    if t.startswith("find file "):
        name = raw[len("find file "):].strip()
        return "find_file", {"name": name}
    if t in ("find duplicates", "find duplicate"):
        return "find_duplicates", {}
    if t.startswith("create file "):
        rest   = raw[len("create file "):].strip()
        folder = None
        if " in folder " in rest:
            name, folder = rest.split(" in folder ", 1)
        else:
            name = rest
        return "create_file", {"name": name.strip(), "folder": folder}
    if t.startswith("delete file "):
        rest   = raw[len("delete file "):].strip()
        folder = None
        if " in folder " in rest:
            name, folder = rest.split(" in folder ", 1)
        else:
            name = rest
        return "delete_file", {"name": name.strip(), "folder": folder}
    if t.startswith("create folder named "):
        rest     = raw[len("create folder named "):].strip()
        location = "desktop"
        if " in " in rest:
            name, location = rest.split(" in ", 1)
            location = location.strip()
        else:
            name = rest
        return "create_folder", {"name": name.strip(), "location": location}
    if t.startswith("create project "):
        name = raw[len("create project "):].strip()
        return "create_project", {"name": name}
    if t in ("delete empty folders", "delete empty"):
        return "delete_empty_folders", {}
    if t in ("open vscode", "vscode"):
        return "open_vscode", {}
    if t.startswith("open app "):
        name = raw[len("open app "):].strip()
        return "open_app", {"name": name}
    if t in ("watch on", "watch start", "start watch"):
        return "watch_on", {}
    if t in ("watch off", "watch stop", "stop watch"):
        return "watch_off", {}
    if t in ("watch", "watch status"):
        return "watch_status", {}

    return None, None


# ── Main loop ─────────────────────────────────────────────────────────────────

def run():
    print("🤖 Personal AI Agent ready. Type 'help' for commands.\n")

    while True:
        # Build prompt badge
        watch_badge = " [👁 watching]" if is_active() else ""
        try:
            raw = input(f">>{watch_badge} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye! 👋")
            break

        if not raw:
            continue

        # ── --preview flag ────────────────────────────────────────────────────
        preview = False
        if raw.startswith("--preview "):
            preview = True
            raw = raw[len("--preview "):].strip()

        # ── AI brain (Phase 2) ────────────────────────────────────────────────
        intent = parse_intent(raw)

        if intent:
            mode_badge = "[🤖 AI]"
            command    = intent["command"]
            args       = intent["args"]
        else:
            # Fallback: Phase 1 string matching
            mode_badge     = "[⚡ local]"
            command, args  = _string_match(raw, preview)

        # ── Dispatch ──────────────────────────────────────────────────────────
        if command:
            if preview:
                print(f"  {mode_badge} 👁 Preview mode — no changes will be made.")
            else:
                print(f"  {mode_badge}")

            result = _dispatch(command, args, preview)

            if result == "exit":
                break
            if result is False:
                print("⚠️  Hmm, I recognised the command but couldn't handle it.")
        else:
            print(
                "❓ I didn't understand that. "
                "Type 'help' to see all commands, or try rephrasing."
            )