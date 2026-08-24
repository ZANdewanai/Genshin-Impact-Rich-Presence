#!/usr/bin/env python3
"""
Genshin Impact Rich Presence - Distribution Build Script
Creates a clean distribution package without excess files
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist_rapidocr_v3"


def clean_dist():
    """Clean the distribution directory"""
    if DIST_DIR.exists():
        print(f"Cleaning {DIST_DIR}...")
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def copy_file(src, dst):
    """Copy a single file"""
    if os.path.exists(src):
        # Ensure dst is a file path, not a directory
        if dst.is_dir():
            dst = dst / Path(src).name
        shutil.copy2(src, dst)
        print(f"  Copied: {Path(src).name}")
    else:
        print(f"  Skipped (not found): {Path(src).name}")


def copy_dir(src, dst, exclude_patterns=None):
    """Copy a directory with optional exclusions"""
    if os.path.exists(src):
        if exclude_patterns:
            shutil.copytree(src, dst, 
                           ignore=shutil.ignore_patterns(*exclude_patterns),
                           dirs_exist_ok=True)
        else:
            shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"  Copied: {Path(src).name}/")
    else:
        print(f"  Skipped (not found): {Path(src).name}/")


def build_distribution():
    """Build the distribution package"""
    print("\n" + "=" * 50)
    print("Building Distribution Package")
    print("=" * 50)
    
    # Clean and create dist directory first (skip if locked)
    try:
        clean_dist()
    except PermissionError:
        print("Warning: Could not clean dist directory (files in use). Continuing...")
        if not DIST_DIR.exists():
            DIST_DIR.mkdir(parents=True, exist_ok=True)

    # Essential Python files
    print("\n1. Copying Python files...")
    copy_file(PROJECT_ROOT / "main.py", DIST_DIR / "main.py")
    copy_file(PROJECT_ROOT / "CONFIG.py", DIST_DIR / "CONFIG.py")
    copy_file(PROJECT_ROOT / "clear_discord.py", DIST_DIR / "clear_discord.py")
    copy_file(PROJECT_ROOT / "webview_launcher.py", DIST_DIR / "webview_launcher.py")
    copy_file(PROJECT_ROOT / "README.md", DIST_DIR / "README.md")
    copy_file(PROJECT_ROOT / "LICENSE", DIST_DIR / "LICENSE")
    copy_file(PROJECT_ROOT / "requirements.txt", DIST_DIR / "requirements.txt")

    # Directories (including embedded Python for portable distribution)
    print("\n2. Copying directories...")
    copy_dir(PROJECT_ROOT / "gui" / "dist", DIST_DIR / "gui" / "dist")
    copy_dir(PROJECT_ROOT / "core", DIST_DIR / "core")
    copy_dir(PROJECT_ROOT / "data", DIST_DIR / "data")
    copy_dir(PROJECT_ROOT / "resources", DIST_DIR / "resources")
    copy_dir(PROJECT_ROOT / "icons", DIST_DIR / "icons")
    # Copy embedded Python (will clean up heavy packages after)
    copy_dir(PROJECT_ROOT / "python3.12.8_embedded", DIST_DIR / "python3.12.8_embedded")
    

    # Create launcher scripts
    print("\n3. Creating launcher scripts...")
    
    # Simple batch launcher using embedded Python
    batch_launcher = """@echo off
cd /d "%~dp0"
python3.12.8_embedded\\python.exe webview_launcher.py
"""
    with open(DIST_DIR / "start.bat", "w") as f:
        f.write(batch_launcher)
    print("  Created: start.bat")

    # PowerShell launcher
    ps_launcher = """$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
& ".\\python3.12.8_embedded\\python.exe" webview_launcher.py
"""
    with open(DIST_DIR / "start.ps1", "w") as f:
        f.write(ps_launcher)
    print("  Created: start.ps1")

    # Create version info file
    version_info = f"""Genshin Impact Rich Presence v3.0
Portable Distribution Build (RapidOCR)

This is a portable, ready-to-use distribution with everything included:
- Embedded Python 3.12.8
- RapidOCR (ONNX Runtime) for text recognition
- All dependencies pre-installed
- GUI application
- Character/location data
- Configuration files

Size: ~500-600 MB

To run: double-click start.bat

For questions or issues, visit:
https://github.com/ZANdewanai/Genshin-Impact-Rich-Presence
"""
    with open(DIST_DIR / "VERSION.txt", "w") as f:
        f.write(version_info)
    print("  Created: VERSION.txt")

    print("\n" + "=" * 50)
    print("Portable distribution build complete!")
    print(f"Location: {DIST_DIR}")
    print("\nTo run the application: double-click start.bat")
    print("=" * 50)


if __name__ == "__main__":
    build_distribution()
