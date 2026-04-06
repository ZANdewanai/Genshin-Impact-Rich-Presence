#!/usr/bin/env python3
"""
Genshin Impact Rich Presence - Build Script
Creates a release build with GUI and backend
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
RELEASE_DIR = PROJECT_ROOT / "builds" / "release"


def clean_release():
    """Clean the release directory"""
    if RELEASE_DIR.exists():
        print(f"Cleaning {RELEASE_DIR}...")
        shutil.rmtree(RELEASE_DIR)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)


def copy_file(src, dst):
    """Copy a single file"""
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  Copied: {Path(src).name}")


def copy_dir(src, dst):
    """Copy a directory"""
    if os.path.exists(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"  Copied: {Path(src).name}/")


def build_release():
    """Build the release package"""
    print("\n" + "=" * 50)
    print("Building Release Package")
    print("=" * 50)

    # Essential Python files
    print("\n1. Copying Python files...")
    copy_file(PROJECT_ROOT / "main.py", RELEASE_DIR)
    copy_file(PROJECT_ROOT / "CONFIG.py", RELEASE_DIR)
    copy_file(PROJECT_ROOT / "clear_discord.py", RELEASE_DIR)
    copy_file(PROJECT_ROOT / "gui_launcher.py", RELEASE_DIR)
    copy_file(PROJECT_ROOT / "shared_config.json", RELEASE_DIR)
    copy_file(PROJECT_ROOT / "gui_config.json", RELEASE_DIR)

    # Directories
    print("\n2. Copying directories...")
    copy_dir(PROJECT_ROOT / "gui", RELEASE_DIR / "gui")
    copy_dir(PROJECT_ROOT / "core", RELEASE_DIR / "core")
    copy_dir(PROJECT_ROOT / "icons", RELEASE_DIR / "icons")
    copy_dir(
        PROJECT_ROOT / "python3.13.11_embedded", RELEASE_DIR / "python3.13.11_embedded"
    )

    # Create launcher batch file
    print("\n3. Creating launcher...")
    launcher = """@echo off
cd /d "%~dp0"
python3.13.11_embedded\\python.exe gui_launcher.py
pause
"""
    with open(RELEASE_DIR / "start.bat", "w") as f:
        f.write(launcher)

    print("\n" + "=" * 50)
    print("Build complete!")
    print(f"Location: {RELEASE_DIR}")
    print("\nTo run: double-click start.bat")
    print("=" * 50)


if __name__ == "__main__":
    build_release()
