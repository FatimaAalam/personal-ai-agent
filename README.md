# Personal AI Agent

A local Python based automation agent that helps manage files, folders, and desktop workflows directly from your laptop.

This project is built for personal productivity and system automation. Instead of manually organizing files, creating folders, opening tools, and managing project structures, the agent performs tasks using simple natural language style commands.

The goal is to evolve this from a rule based assistant into a full local AI powered desktop agent using Ollama and local LLM integration.
## Features
### Current Features
- Create folders on Desktop
- Move PDF files automatically
- Move images to organized folders
- Move screenshots separately
- Open Visual Studio Code
- Create full project structure
- Rename files
- Find files in Desktop and Downloads
- Delete empty folders
- Preview mode before execution
- Confirmation before bulk file operations
- Action history log for tracking changes
  
### Example Commands
- move pdf --> &emsp; &emsp;Move PDFs from Downloads → Desktop/PDF Files
- move images -->      &emsp;       &emsp;         Move images from Downloads → Desktop/Images
-  move screenshots -->      &emsp;    &emsp;       Move screenshots from Downloads → Desktop/Screenshots
- sort downloads -->      &emsp;    &emsp;        Sort PDFs + images from Downloads into Desktop folders
- create folder named <name> -->  &emsp; &emsp;     Create a folder on Desktop
- create project <name> -->    &emsp; &emsp;         Create a project scaffold on Desktop
- rename file <old> to <new> --> &emsp; &emsp;      Rename a file on Desktop
- find file <filename> -->      &emsp; &emsp;     Search Desktop and Downloads for a file
- delete empty folders -->   &emsp; &emsp;           Remove empty folders from Desktop
- open vscode -->          &emsp; &emsp;             Open Visual Studio Code
- preview <command> -->     &emsp; &emsp;         Show what a command would do without running it
- goodbye -->        &emsp; &emsp;                  Exit the agent

## Tech Stack
- Python 3
- os
- shutil
- subprocess
- datetime

## Future Integration:

- Ollama
- Llama 3
- Local AI decision engine
- Voice command support

## Project Structure
```
personal-ai-agent/
│
├──  agent.py
├──  README.md
└──  agent_log.txt
```
## Why This Project

This project is designed to solve real daily workflow problems while improving practical Python, automation, DevOps thinking, and local AI system design.

It focuses on building something useful instead of only tutorial based projects.
## Author

Built by Fatima Aalam

Software Engineer | Automation | DevOps | AI Systems
