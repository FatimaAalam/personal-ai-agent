"""
tests/test_watch_mode.py

Unit tests for the watch_mode module.
Run with:  python -m pytest tests/test_watch_mode.py -v
"""

import time
import threading
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_log():
    """Return a simple callable that records calls."""
    messages = []
    def log(msg):
        messages.append(msg)
    log.messages = messages
    return log


# ── Tests ────────────────────────────────────────────────────────────────────

class TestWatchModeUnavailable:
    """Behaviour when watchdog is not installed."""

    def test_start_returns_install_hint(self, tmp_path):
        with patch("commands.watch_mode.WATCHDOG_AVAILABLE", False):
            # Re-import to pick up the patch
            import importlib
            import commands.watch_mode as wm
            importlib.reload(wm)
            wm.WATCHDOG_AVAILABLE = False

            result = wm.start_watch(MagicMock(), make_log(), tmp_path)
            assert "pip install watchdog" in result
            assert wm.is_active() is False


class TestWatchModeLifecycle:
    """Start / stop / status cycle."""

    def test_start_sets_active_flag(self, tmp_path):
        import commands.watch_mode as wm
        if not wm.WATCHDOG_AVAILABLE:
            import pytest; pytest.skip("watchdog not installed")

        log = make_log()
        sort = MagicMock()

        msg = wm.start_watch(sort, log, tmp_path)
        assert wm.is_active() is True
        assert "Watch mode ON" in msg

        wm.stop_watch(log)   # cleanup

    def test_stop_clears_active_flag(self, tmp_path):
        import commands.watch_mode as wm
        if not wm.WATCHDOG_AVAILABLE:
            import pytest; pytest.skip("watchdog not installed")

        log = make_log()
        sort = MagicMock()

        wm.start_watch(sort, log, tmp_path)
        msg = wm.stop_watch(log)

        assert wm.is_active() is False
        assert "OFF" in msg

    def test_double_start_is_idempotent(self, tmp_path):
        import commands.watch_mode as wm
        if not wm.WATCHDOG_AVAILABLE:
            import pytest; pytest.skip("watchdog not installed")

        log = make_log()
        sort = MagicMock()

        wm.start_watch(sort, log, tmp_path)
        msg2 = wm.start_watch(sort, log, tmp_path)   # second call
        assert "already running" in msg2
        assert wm.is_active() is True

        wm.stop_watch(log)

    def test_stop_when_not_running(self):
        import commands.watch_mode as wm
        # Ensure stopped state
        import commands.watch_mode as wm
        if wm.is_active():
            wm.stop_watch(make_log())

        msg = wm.stop_watch(make_log())
        assert "not running" in msg

    def test_missing_directory(self, tmp_path):
        import commands.watch_mode as wm
        if not wm.WATCHDOG_AVAILABLE:
            import pytest; pytest.skip("watchdog not installed")

        ghost = tmp_path / "does_not_exist"
        msg = wm.start_watch(MagicMock(), make_log(), ghost)
        assert "not found" in msg
        assert wm.is_active() is False


class TestDownloadsHandler:
    """Handler filtering and debounce logic."""

    def test_sort_called_on_new_file(self, tmp_path):
        import commands.watch_mode as wm
        if not wm.WATCHDOG_AVAILABLE:
            import pytest; pytest.skip("watchdog not installed")

        from watchdog.events import FileCreatedEvent

        sort = MagicMock()
        log  = make_log()
        handler = wm.DownloadsHandler(sort, log, tmp_path)

        # Create a real file so the handler can verify it exists
        new_file = tmp_path / "document.pdf"
        new_file.touch()

        event = FileCreatedEvent(str(new_file))
        handler.on_created(event)

        # Give the settle thread time to fire
        time.sleep(1.0)
        sort.assert_called_once()

    def test_temp_files_are_ignored(self, tmp_path):
        import commands.watch_mode as wm
        if not wm.WATCHDOG_AVAILABLE:
            import pytest; pytest.skip("watchdog not installed")

        from watchdog.events import FileCreatedEvent

        sort = MagicMock()
        log  = make_log()
        handler = wm.DownloadsHandler(sort, log, tmp_path)

        for name in (".DS_Store", "file.crdownload", "download.part", ".hidden"):
            event = FileCreatedEvent(str(tmp_path / name))
            handler.on_created(event)

        time.sleep(0.8)
        sort.assert_not_called()

    def test_directory_events_are_ignored(self, tmp_path):
        import commands.watch_mode as wm
        if not wm.WATCHDOG_AVAILABLE:
            import pytest; pytest.skip("watchdog not installed")

        from watchdog.events import DirCreatedEvent

        sort = MagicMock()
        log  = make_log()
        handler = wm.DownloadsHandler(sort, log, tmp_path)

        event = DirCreatedEvent(str(tmp_path / "new_folder"))
        handler.on_created(event)

        time.sleep(0.8)
        sort.assert_not_called()