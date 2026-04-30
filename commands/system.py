"""
commands/system.py
System-level commands: opening applications, future OS interactions.
"""

import subprocess


def open_vscode() -> None:
    """Open Visual Studio Code (macOS)."""
    try:
        subprocess.run(["open", "-a", "Visual Studio Code"], check=True)
        print("💻 Opening VS Code...")
    except subprocess.CalledProcessError:
        print("⚠️  Could not open VS Code. Is it installed?")
    except FileNotFoundError:
        print("⚠️  'open' command not found. Are you on macOS?")


def open_app(app_name: str) -> None:
    """Generic app opener for macOS. Usage: open app <App Name>"""
    if not app_name:
        print("⚠️  Usage: open app <name>")
        return
    try:
        subprocess.run(["open", "-a", app_name], check=True)
        print(f"🚀 Opening {app_name}...")
    except subprocess.CalledProcessError:
        print(f"⚠️  Could not open '{app_name}'. Is it installed?")