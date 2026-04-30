"""
core/logger.py
Handles all logging for the agent.

Two separate logs:
  - agent_log.txt         Human-readable diary (timestamped plain text)
  - agent_actions.json    Machine-readable undo stack (structured JSON)
"""

import json
from datetime import datetime

from config import LOG_FILE, ACTIONS_FILE


# ── Human-readable log ────────────────────────────────────────────────────────

def log(action: str) -> None:
    """Append a timestamped line to the human-readable log file."""
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} | {action}\n")


# ── Structured undo log ───────────────────────────────────────────────────────

def log_action(action_type: str, original_path: str, destination_path: str = None) -> None:
    """
    Append a structured entry to agent_actions.json for undo support.

    Entry schema:
        {
            "action":           "move" | "rename" | "create_folder",
            "original_path":    "/absolute/path/before",
            "destination_path": "/absolute/path/after",   # None for creates
            "timestamp":        "2025-01-01T12:00:00.000"
        }
    """
    entry = {
        "action":           action_type,
        "original_path":    original_path,
        "destination_path": destination_path,
        "timestamp":        datetime.now().isoformat(),
    }

    actions = _load_actions()
    actions.append(entry)
    _save_actions(actions)


def pop_last_action() -> dict | None:
    """
    Remove and return the last action from the undo stack.
    Returns None if the stack is empty or corrupted.
    """
    actions = _load_actions()
    if not actions:
        return None
    last = actions.pop()
    _save_actions(actions)
    return last


def peek_last_action() -> dict | None:
    """Return the last action without removing it."""
    actions = _load_actions()
    return actions[-1] if actions else None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_actions() -> list:
    try:
        with open(ACTIONS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_actions(actions: list) -> None:
    with open(ACTIONS_FILE, "w") as f:
        json.dump(actions, f, indent=2)