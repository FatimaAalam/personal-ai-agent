"""
config.py
All paths, constants, and settings for the agent.
API keys and secrets go in .env — never here.
"""

import os
# from dotenv import load_dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

load_dotenv()

# ── Core Paths ────────────────────────────────────────────────────────────────
DESKTOP   = os.path.expanduser("~/Desktop")
DOWNLOADS = os.path.expanduser("~/Downloads")

# ── Data / Log Paths ──────────────────────────────────────────────────────────
DATA_DIR     = os.path.join(os.path.dirname(__file__), "data")
LOG_FILE     = os.path.join(DATA_DIR, "agent_log.txt")
ACTIONS_FILE = os.path.join(DATA_DIR, "agent_actions.json")

# ── File Type Buckets (used by sort + move commands) ─────────────────────────
FILE_BUCKETS: dict[str, tuple] = {
    "PDF Files": (".pdf",),
    "Images":    (".png", ".jpg", ".jpeg", ".webp", ".gif"),
    "Videos":    (".mp4", ".mov", ".avi", ".mkv"),
    "Archives":  (".zip", ".rar", ".tar", ".gz"),
    "Docs":      (".doc", ".docx", ".txt", ".xlsx", ".pptx"),
}

IMAGE_EXTS = FILE_BUCKETS["Images"]

# ── Protected Folder Names (never deleted) ────────────────────────────────────
PROTECTED_FOLDERS = ["github", ".git"]

# ── File Icon Map ─────────────────────────────────────────────────────────────
FILE_ICONS: dict[str, str] = {
    "pdf":  "📄",
    "png":  "🖼️",  "jpg": "🖼️", "jpeg": "🖼️", "gif": "🖼️", "webp": "🖼️",
    "mp4":  "🎬",  "mov": "🎬", "avi":  "🎬", "mkv":  "🎬",
    "zip":  "📦",  "rar": "📦", "tar":  "📦", "gz":   "📦",
    "doc":  "📝",  "docx":"📝", "txt":  "📝", "xlsx": "📝", "pptx": "📝",
    "py":   "🐍",
    "js":   "📜",  "ts":  "📜",
    "json": "🗂️",
    "html": "🌐",  "css": "🌐",
}

# ── Ensure data/ directory exists at import time ──────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)