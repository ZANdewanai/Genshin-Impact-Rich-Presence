#!/usr/bin/env python3
"""
Genshin Impact Rich Presence - Distribution Build Script

Produces builds/GenshinRichPresence/ : a fully self-contained, windowless
distribution (no embedded Python folder, no console windows):

  GenshinRichPresence.exe   GUI (pywebview), ApplicationIcon.ico
  RichPresenceEngine.exe    OCR engine spawned by the GUI, Distributors icon
  _internal/                shared bundled runtimes for both exes
  core/, gui/dist/, data/, sensor_data/, CONFIG.py

Usage:
  python3.12.8_embedded\\python.exe build_dist.py          # full build
  python3.12.8_embedded\\python.exe build_dist.py --assemble-only
      # skip PyInstaller, just re-assemble from builds/ output
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
PYTHON = PROJECT_ROOT / "python3.12.8_embedded" / "python.exe"
BUILDS = PROJECT_ROOT / "builds"
RELEASE = BUILDS / "GenshinRichPresence"

SPECS = ["GenshinRichPresence.spec", "RichPresenceEngine.spec"]

COPY_DIRS = ["core", "data", "sensor_data"]
# NOTE: shared_config.json is deliberately NOT shipped. It's generated with
# placeholder defaults on first GUI launch (_ensure_shared_config in
# gui/api.py) - shipping a real one would preset someone's username.
COPY_FILES = ["CONFIG.py", "requirements.txt"]


def run_pyinstaller() -> None:
    print("\n[1/3] Running PyInstaller...")
    for spec in SPECS:
        print(f"  Building {spec} ...")
        cmd = [str(PYTHON), "-m", "PyInstaller", spec,
               "--noconfirm", "--distpath", str(BUILDS)]
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            sys.exit(f"PyInstaller failed for {spec} - see output above.")


def assemble() -> None:
    print("\n[2/3] Assembling release folder:", RELEASE.name)
    RELEASE.mkdir(parents=True, exist_ok=True)

    # Merge both exe outputs into one folder; they share _internal.
    for spec in SPECS:
        out = (BUILDS / Path(spec).stem).resolve()
        if not (out / f"{out.name}.exe").exists():
            sys.exit(f"Missing build output: {out} (run without --assemble-only)")
        if out == RELEASE.resolve():
            continue  # GUI output IS the release folder - nothing to merge
        shutil.copytree(out, RELEASE, dirs_exist_ok=True)
        print(f"  Merged: {out.name}/")

    # App code & data as plain files next to the exes
    for d in COPY_DIRS:
        src = PROJECT_ROOT / d
        if src.exists():
            shutil.copytree(src, RELEASE / d, dirs_exist_ok=True)
            print(f"  Copied: {d}/")
    for f in COPY_FILES:
        src = PROJECT_ROOT / f
        if src.exists():
            shutil.copy2(src, RELEASE / f)
            print(f"  Copied: {f}")

    gui_dist = PROJECT_ROOT / "gui" / "dist"
    if gui_dist.exists():
        # Clean first: hashed asset names change every build, so merging
        # would otherwise accumulate stale bundles forever.
        target = RELEASE / "gui" / "dist"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(gui_dist, target)
        print("  Copied: gui/dist/")


def report() -> None:
    total = sum(f.stat().st_size for f in RELEASE.rglob("*") if f.is_file())
    print(f"\n[3/3] Done! {RELEASE}")
    print(f"Total size: {total / 1024 / 1024:.0f} MB")
    print("Distribute the whole GenshinRichPresence folder.")
    print("Users launch: GenshinRichPresence.exe")


if __name__ == "__main__":
    assemble_only = "--assemble-only" in sys.argv
    if not assemble_only:
        run_pyinstaller()
    assemble()
    report()
