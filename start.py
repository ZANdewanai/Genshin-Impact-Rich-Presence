#!/usr/bin/env python3
"""
Consolidated launcher for Genshin Impact Rich Presence.

Replaces: start_embedded.bat/.ps1, start_gui.bat/.ps1, build.bat, webview_launcher.py, build_dist.py, clear_discord.py

Usage:
  python start.py engine          # Run OCR engine (main.py)
  python start.py gui             # Run GUI (webview_launcher.py)
  python start.py build           # Full PyInstaller build
  python start.py assemble        # Assemble release folder only (--assemble-only)
  python start.py clean           # Clear Discord Rich Presence
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
EMBEDDED_PYTHON = ROOT / "python3.12.8_embedded" / "python.exe"
MAIN_PY = ROOT / "main.py"
WEBVIEW_LAUNCHER = ROOT / "webview_launcher.py"
BUILD_DIST = ROOT / "build_dist.py"
CLEAR_DISCORD = ROOT / "clear_discord.py"


def run_embedded(script: Path, args: list = None, env_vars: dict = None):
    """Run a script with embedded Python."""
    if not EMBEDDED_PYTHON.exists():
        sys.exit(f"Embedded Python not found: {EMBEDDED_PYTHON}")
    cmd = [str(EMBEDDED_PYTHON), str(script)]
    if args:
        cmd.extend(args)
    os.chdir(ROOT)
    env = os.environ.copy()
    # Suppress ONNX Runtime verbose logging for engine
    env.setdefault("ORT_LOGGING_LEVEL", "3")
    if env_vars:
        env.update(env_vars)
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        sys.exit(f"Command failed with exit code {e.returncode}")


def run_current(script: Path, args: list = None):
    """Run a script with current interpreter (dev fallback)."""
    cmd = [sys.executable, str(script)]
    if args:
        cmd.extend(args)
    os.chdir(ROOT)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"Command failed with exit code {e.returncode}")


def cmd_engine(args):
    """Run the OCR detection engine (main.py)."""
    if EMBEDDED_PYTHON.exists():
        run_embedded(MAIN_PY)
    else:
        print("Embedded Python not found, using current interpreter")
        run_current(MAIN_PY)


def cmd_gui(args):
    """Run the Web GUI (webview_launcher.py)."""
    if EMBEDDED_PYTHON.exists():
        run_embedded(WEBVIEW_LAUNCHER)
    else:
        print("Embedded Python not found, using current interpreter")
        run_current(WEBVIEW_LAUNCHER)


def cmd_build(args):
    """Full PyInstaller build + assemble."""
    if EMBEDDED_PYTHON.exists():
        run_embedded(BUILD_DIST)
    else:
        run_current(BUILD_DIST)


def cmd_assemble(args):
    """Assemble release folder only (skip PyInstaller)."""
    if EMBEDDED_PYTHON.exists():
        run_embedded(BUILD_DIST, ["--assemble-only"])
    else:
        run_current(BUILD_DIST, ["--assemble-only"])


def cmd_clean(args):
    """Clear Discord Rich Presence."""
    if EMBEDDED_PYTHON.exists():
        run_embedded(CLEAR_DISCORD)
    else:
        run_current(CLEAR_DISCORD)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Genshin Impact Rich Presence Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("engine", help="Run OCR detection engine (main.py)")
    subparsers.add_parser("gui", help="Run Web GUI (webview_launcher.py)")
    subparsers.add_parser("build", help="Full PyInstaller build + assemble")
    subparsers.add_parser("assemble", help="Assemble release folder only (--assemble-only)")
    subparsers.add_parser("clean", help="Clear Discord Rich Presence")

    args = parser.parse_args()

    commands = {
        "engine": cmd_engine,
        "gui": cmd_gui,
        "build": cmd_build,
        "assemble": cmd_assemble,
        "clean": cmd_clean,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()