"""
commands/watch_mode.py

Background file watcher for the personal AI agent.
Uses watchdog to monitor the Downloads folder and auto-sort
new files the moment they appear — no command needed.

Runs on a daemon thread so the main command loop stays responsive.
"""

import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

# Watchdog imports — guarded so the rest of the agent still runs
# if the user hasn't installed watchdog yet.
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


# ── Shared state ────────────────────────────────────────────────────────────

_observer: Optional[Any] = None              # watchdog Observer thread
_watch_active = False                         # public flag — read by agent.py
_lock = threading.Lock()                      # guards _observer + _watch_active


def is_active() -> bool:
    """Return True if watch mode is currently running."""
    return _watch_active


# ── Event handler ────────────────────────────────────────────────────────────

class DownloadsHandler(FileSystemEventHandler):
    """
    Reacts to file-system events inside the watched folder.

    Only 'created' events are handled — modifications and deletions
    are ignored to avoid double-sorting or acting on temp files.
    A 0.5-second settle delay lets the OS finish writing the file
    before we touch it.
    """

    def __init__(self, sort_func, log_func, watch_dir: Path):
        super().__init__()
        self.sort_func = sort_func        # e.g. sort_downloads() from files.py
        self.log_func  = log_func         # log() from logger.py
        self.watch_dir = watch_dir
        self._pending: dict[str, float] = {}   # path → scheduled trigger time
        self._timer_lock = threading.Lock()

    # watchdog calls this on every CREATE event (files AND dirs)
    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)

        # Skip hidden/temp files (e.g. .crdownload, .part, .DS_Store)
        if src.name.startswith(".") or src.suffix in {".crdownload", ".part", ".tmp"}:
            return

        # Debounce: wait 0.5s after the last event for this path
        with self._timer_lock:
            self._pending[str(src)] = time.monotonic() + 0.5

        # Spin up a one-shot checker
        t = threading.Thread(target=self._settle_and_sort, args=(str(src),), daemon=True)
        t.start()

    def _settle_and_sort(self, path_str: str):
        """Wait for the file to stop being written, then sort."""
        while True:
            time.sleep(0.1)
            with self._timer_lock:
                trigger_at = self._pending.get(path_str)
            if trigger_at is None:
                return                          # cancelled
            if time.monotonic() >= trigger_at:
                with self._timer_lock:
                    self._pending.pop(path_str, None)
                break

        src = Path(path_str)
        if not src.exists():
            return

        self.log_func(
            f"[👁 Watch] New file detected: {src.name} — auto-sorting Downloads…"
        )

        try:
            # Re-use the existing sort logic; it already logs its own actions.
            self.sort_func()
        except Exception as exc:
            self.log_func(f"[👁 Watch] Sort error: {exc}")


# ── Public API ───────────────────────────────────────────────────────────────

def start_watch(sort_func, log_func, watch_dir: Path) -> str:
    """
    Start the background observer.

    Parameters
    ----------
    sort_func : callable
        The existing sort_downloads() function from commands/files.py.
    log_func  : callable
        The existing log() function from core/logger.py.
    watch_dir : Path
        Directory to monitor (typically ~/Downloads).

    Returns
    -------
    str  — message to display to the user.
    """
    global _observer, _watch_active

    if not WATCHDOG_AVAILABLE:
        return (
            "❌  watchdog is not installed.\n"
            "   Run:  pip install watchdog\n"
            "   Then restart the agent and try again."
        )

    with _lock:
        if _watch_active:
            return f"👁  Watch mode is already running on {watch_dir}"

        if not watch_dir.exists():
            return f"❌  Watch directory not found: {watch_dir}"

        handler  = DownloadsHandler(sort_func, log_func, watch_dir)
        observer = Observer()
        observer.schedule(handler, str(watch_dir), recursive=False)
        observer.daemon = True          # dies automatically when main process exits
        observer.start()

        _observer    = observer
        _watch_active = True

    log_func(f"[👁 Watch] Started monitoring {watch_dir}")
    return (
        f"👁  Watch mode ON — monitoring {watch_dir}\n"
        f"   New files will be sorted automatically.\n"
        f"   Type  watch off  to stop."
    )


def stop_watch(log_func) -> str:
    """
    Stop the background observer.

    Parameters
    ----------
    log_func : callable
        The existing log() function from core/logger.py.

    Returns
    -------
    str  — message to display to the user.
    """
    global _observer, _watch_active

    with _lock:
        if not _watch_active:
            return "ℹ️  Watch mode is not running."

        if _observer is not None:
            _observer.stop()
            _observer.join(timeout=3)   # wait up to 3s for clean shutdown
            _observer = None

        _watch_active = False

    log_func("[👁 Watch] Stopped.")
    return "🛑  Watch mode OFF — auto-sort stopped."