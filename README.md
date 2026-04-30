# 🤖 Personal AI Agent

A modular, extensible personal assistant that runs entirely from your terminal with zero recurring cost.

> Built in phases: file automation today, voice + AI brain + Gmail/Calendar/Telegram/GitHub coming next.

---

## Features

### ✅ Phase 1 — File & Folder Automation (complete)
- **List folder** — `list desktop` / `list downloads` / `list <any folder>` with icons and file sizes
- **Move files** — PDFs, images, screenshots from Downloads to organized Desktop folders
- **Sort downloads** — auto-bucket everything by type in one command
- **Rename & Find** — rename files on Desktop, deep-search across Desktop + Downloads
- **Create folder / project** — instant project scaffold with `src/`, `tests/`, `docs/`, `assets/`, `README.md`
- **Delete empty folders** — clean up safely, skips protected dirs
- **Undo system** — reverses the last action using a structured JSON log (not just a diary)

### 🔜 Coming Phases
- **Phase 2** — Ollama AI brain (local LLM, zero cost, intent parsing)
- **Phase 3** — Voice commands (speech-to-text input + text-to-speech output)
- **Phase 4** — Gmail + Google Calendar integration
- **Phase 5** — Telegram bot interface
- **Phase 6** — GitHub integration (repos, issues, PRs)

---

## Project Structure

```
personal-ai-agent/
├── main.py                  # Entry point
├── config.py                # All paths and constants
│
├── core/
│   ├── agent.py             # Command router (the main loop)
│   ├── logger.py            # Human log + structured undo log
│   └── utils.py             # Shared helpers (confirm, icons, sizes)
│
├── commands/
│   ├── files.py             # move, sort, rename, find, list, undo
│   ├── folders.py           # create folder/project, delete empty
│   └── system.py            # open apps
│
├── integrations/            # (future) Gmail, Calendar, Telegram, GitHub
├── ai/                      # (future) Ollama brain
├── tests/
│
├── data/                    # Runtime logs — gitignored
│   ├── agent_log.txt        # Human-readable diary
│   └── agent_actions.json   # Machine-readable undo stack
│
├── .env.example             # Secret keys template
├── .gitignore
└── requirements.txt
```

---

## Setup

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/personal-ai-agent.git
cd personal-ai-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env template
cp .env.example .env

# 5. Run
python main.py
```

---

## Commands

| Command | What it does |
|---|---|
| `list desktop` | Show everything on Desktop with icons + sizes |
| `list downloads` | Show everything in Downloads |
| `list <folder>` | Show contents of any Desktop sub-folder |
| `undo` | Reverse the last move/rename/create |
| `move pdf` | Move PDFs from Downloads → Desktop/PDF Files |
| `move images` | Move images (excl. screenshots) → Desktop/Images |
| `move screenshots` | Move screenshots → Desktop/Screenshots |
| `sort downloads` | Auto-sort all Downloads into type folders |
| `rename file <old> to <new>` | Rename a file on Desktop |
| `find file <name>` | Search Desktop + Downloads recursively |
| `create folder named <name>` | Create a folder on Desktop |
| `create project <name>` | Full project scaffold |
| `delete empty folders` | Remove empty folders from Desktop |
| `open vscode` | Open VS Code |
| `open app <name>` | Open any macOS application |
| `--preview <command>` | Dry-run without executing |
| `help` | Show all commands |
| `goodbye` | Exit |

---

## How Undo Works

Every reversible action writes a structured JSON entry to `data/agent_actions.json`:

```json
{
  "action": "move",
  "original_path": "/Users/you/Downloads/report.pdf",
  "destination_path": "/Users/you/Desktop/PDF Files/report.pdf",
  "timestamp": "2025-01-01T12:00:00.123"
}
```

`undo` pops the last entry, reverses the file operation, and saves the stack back — so you can undo multiple times in sequence.

---

## Design Principles

- **Zero cost** — no paid APIs, no subscriptions. Ollama runs locally.
- **Modular** — each feature is its own file. Adding a new command = one import + one elif.
- **Safe** — every destructive action asks for confirmation. Undo is always available.
- **Portfolio-ready** — clean structure, typed functions, documented modules.

---

## License

MIT
## Author

Built by Fatima Aalam

Software Engineer | Automation | DevOps | AI Systems
