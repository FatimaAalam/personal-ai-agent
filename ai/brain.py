"""
ai/brain.py  —  Phase 2: Ollama AI Brain

Sends user input to a local Ollama model and gets back a structured
intent (command name + optional args). If Ollama is offline or returns
something unrecognised, returns None so the caller can fall back to
string matching.

Public API
----------
parse_intent(user_input: str) -> dict | None
    Returns {"command": "<command_key>", "args": {...}} or None.
"""

import json
import urllib.request
import urllib.error

# ── Ollama config ──────────────────────────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:latest"
TIMEOUT      = 30   # seconds — needed for cold start

# ── The master command map ─────────────────────────────────────────────────────
COMMAND_MAP = {
    "list_folder":           "list files in a folder (desktop, downloads, or a path)",
    "undo":                  "undo the last action",
    "move_pdfs":             "move PDF files to a PDF folder",
    "move_images":           "move image files to an Images folder",
    "move_screenshots":      "move screenshots to a Screenshots folder",
    "sort_downloads":        "sort / organise the downloads folder",
    "rename_file":           "rename a file (needs old name and new name)",
    "find_file":             "find / search for a file by name",
    "find_duplicates":       "find duplicate files",
    "create_folder":         "create a new folder with a given name, optionally in a location (desktop or downloads)",
    "create_project":        "create a project scaffold folder with a given name",
    "delete_empty_folders":  "delete empty folders",
    "open_vscode":           "open VS Code",
    "open_app":              "open an application by name",
    "watch_on":              "start watch mode (auto-sort downloads in background)",
    "watch_off":             "stop watch mode",
    "watch_status":          "check if watch mode is active",
    "help":                  "show help / list all commands",
    "goodbye":               "exit / quit the agent",
}

# ── System prompt ──────────────────────────────────────────────────────────────
_COMMAND_LIST = "\n".join(
    f'  "{k}": {v}' for k, v in COMMAND_MAP.items()
)

SYSTEM_PROMPT = f"""You are the intent parser for a personal AI file-management agent.
Your ONLY job is to map natural-language user input to one of the known commands below.

Known commands (key: description):
{_COMMAND_LIST}

Rules:
1. Respond with a single JSON object — nothing else.
2. Format: {{"command": "<key>", "args": {{}}}}
3. For rename_file, include args: {{"old": "<old name>", "new": "<new name>"}}
4. For find_file, include args: {{"name": "<filename>"}}
5. For create_folder, include args: {{"name": "<folder name>", "location": "<desktop|downloads>"}}
   — default location is "desktop" if not mentioned. If the user says "in downloads" or "in my downloads", set location to "downloads".
6. For create_project, include args: {{"name": "<folder name>"}}
7. For open_app, include args: {{"name": "<app name>"}}
8. For list_folder, include args: {{"folder": "<desktop|downloads|path>"}} — default "downloads" if unspecified.
9. If the input doesn't match any command, respond exactly: {{"command": null, "args": {{}}}}
10. Never explain. Never add markdown fences. Output raw JSON only.
"""

# ── Public function ────────────────────────────────────────────────────────────

def parse_intent(user_input: str) -> dict | None:
    """
    Ask Ollama to parse the user's intent.

    Returns a dict like {"command": "sort_downloads", "args": {}}
    or None if Ollama is offline, times out, or returns an unrecognised command.
    """
    payload = json.dumps({
        "model":    OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_input},
        ],
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read())
            raw  = body["message"]["content"].strip()

        # Strip accidental markdown fences (```json … ```)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)

        command = parsed.get("command")
        if command is None or command not in COMMAND_MAP:
            return None          # Ollama said it doesn't know — fall back

        return {
            "command": command,
            "args":    parsed.get("args", {}),
        }

    except (urllib.error.URLError, TimeoutError, OSError,
            json.JSONDecodeError, KeyError, Exception):
        return None