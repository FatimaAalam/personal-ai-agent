"""
tests/test_brain.py  —  Unit tests for ai/brain.py (Phase 2)

Tests are split into two groups:
  1. Pure logic tests  — no network needed (mocked urllib)
  2. Live smoke test   — skipped automatically if Ollama is not running

Run with:
    python3 -m pytest tests/test_brain.py -v
"""

import json
import sys
import unittest
from unittest.mock import patch, MagicMock

# Make sure the project root is on the path when running from any directory
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.brain import parse_intent, COMMAND_MAP


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mock_ollama_response(command: str, args: dict = None):
    """Build a fake urllib response that returns a valid Ollama JSON body."""
    args = args or {}
    content = json.dumps({"command": command, "args": args})
    body = json.dumps({
        "message": {"content": content}
    }).encode()

    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__  = MagicMock(return_value=False)
    return mock_resp


def _mock_ollama_null():
    """Fake response when Ollama says it doesn't know the command."""
    body = json.dumps({
        "message": {"content": '{"command": null, "args": {}}'}
    }).encode()

    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__  = MagicMock(return_value=False)
    return mock_resp


# ── Test suite ─────────────────────────────────────────────────────────────────

class TestBrainParsing(unittest.TestCase):
    """Tests that mock the network — always run, no Ollama needed."""

    # ── Happy-path: well-known commands ───────────────────────────────────────

    @patch("urllib.request.urlopen")
    def test_sort_downloads(self, mock_urlopen):
        mock_urlopen.return_value = _mock_ollama_response("sort_downloads")
        result = parse_intent("sort my downloads folder")
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "sort_downloads")

    @patch("urllib.request.urlopen")
    def test_rename_file_with_args(self, mock_urlopen):
        mock_urlopen.return_value = _mock_ollama_response(
            "rename_file", {"old": "report.pdf", "new": "q4_report.pdf"}
        )
        result = parse_intent("rename report.pdf to q4_report.pdf")
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "rename_file")
        self.assertEqual(result["args"]["old"], "report.pdf")
        self.assertEqual(result["args"]["new"], "q4_report.pdf")

    @patch("urllib.request.urlopen")
    def test_find_file_with_args(self, mock_urlopen):
        mock_urlopen.return_value = _mock_ollama_response(
            "find_file", {"name": "resume.pdf"}
        )
        result = parse_intent("where is resume.pdf")
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "find_file")
        self.assertEqual(result["args"]["name"], "resume.pdf")

    @patch("urllib.request.urlopen")
    def test_watch_on(self, mock_urlopen):
        mock_urlopen.return_value = _mock_ollama_response("watch_on")
        result = parse_intent("start watching downloads")
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "watch_on")

    @patch("urllib.request.urlopen")
    def test_create_project(self, mock_urlopen):
        mock_urlopen.return_value = _mock_ollama_response(
            "create_project", {"name": "portfolio"}
        )
        result = parse_intent("create a new project called portfolio")
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "create_project")

    # ── Fallback cases ────────────────────────────────────────────────────────

    @patch("urllib.request.urlopen")
    def test_unknown_command_returns_none(self, mock_urlopen):
        """Ollama returns null command → parse_intent returns None."""
        mock_urlopen.return_value = _mock_ollama_null()
        result = parse_intent("what is the meaning of life")
        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_unrecognised_command_key_returns_none(self, mock_urlopen):
        """Ollama hallucinates a command not in COMMAND_MAP → None."""
        mock_urlopen.return_value = _mock_ollama_response("fly_to_moon")
        result = parse_intent("fly me to the moon")
        self.assertIsNone(result)

    @patch("urllib.request.urlopen", side_effect=Exception("connection refused"))
    def test_ollama_offline_returns_none(self, _):
        """Network error → silent None (triggers fallback in agent.py)."""
        result = parse_intent("sort downloads")
        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_markdown_fences_stripped(self, mock_urlopen):
        """Model sometimes wraps JSON in ```json fences — must still parse."""
        body = json.dumps({
            "message": {
                "content": "```json\n{\"command\": \"undo\", \"args\": {}}\n```"
            }
        }).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__  = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = parse_intent("undo that")
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "undo")

    # ── Sanity-check COMMAND_MAP ──────────────────────────────────────────────

    def test_command_map_not_empty(self):
        self.assertGreater(len(COMMAND_MAP), 0)

    def test_all_command_map_keys_are_strings(self):
        for k in COMMAND_MAP:
            self.assertIsInstance(k, str)


# ── Live smoke test (skipped if Ollama is offline) ────────────────────────────

class TestBrainLive(unittest.TestCase):
    """
    These tests actually call Ollama.
    Automatically skipped when Ollama is not running on localhost:11434.
    Run manually to verify the real model behaviour.
    """

    @classmethod
    def setUpClass(cls):
        import urllib.request, urllib.error
        try:
            urllib.request.urlopen("http://localhost:11434", timeout=2)
            cls.ollama_available = True
        except Exception:
            cls.ollama_available = False

    def _skip_if_offline(self):
        if not self.ollama_available:
            self.skipTest("Ollama not running — skipping live test")

    def test_live_sort_downloads(self):
        self._skip_if_offline()
        result = parse_intent("sort my downloads folder please")
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "sort_downloads")

    def test_live_natural_language_undo(self):
        self._skip_if_offline()
        result = parse_intent("oops, undo what you just did")
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "undo")

    def test_live_gibberish_returns_none(self):
        self._skip_if_offline()
        result = parse_intent("xkqzmw flurbinator 999")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()