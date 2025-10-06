#!/usr/bin/env python3
"""
Genshin Impact Rich Presence Launcher
A professional launcher that starts the GUI application
"""

import sys
import os
import subprocess
import platform
import time

def check_python():
    """Check if Python is available and working"""
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[OK] Python found: {version}")
            return True
        else:
            print("[ERROR] Python check failed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print(f"[ERROR] Python error: {e}")
        return False

def check_gui_script():
    """Check if the GUI script exists"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gui_script = os.path.join(script_dir, "GenshinImpactRichPresence_GUI.py")

    if os.path.exists(gui_script):
        print("[OK] GUI script found")
        return gui_script
    else:
        print(f"[ERROR] GUI script not found: {gui_script}")
        return None

def launch_gui(gui_script):
    """Launch the GUI application"""
    try:
        print("Launching Genshin Impact Rich Presence...")
        # Launch the GUI and wait for it to complete
        result = subprocess.run([sys.executable, gui_script])
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n[INFO] Launcher interrupted by user")
        return True
    except Exception as e:
        print(f"[ERROR] Error launching GUI: {e}")
        return False

def show_error_and_exit(message):
    """Show error message and exit"""
    print(f"\n[ERROR] {message}")
    print("\nPlease ensure:")
    print("- Python 3.13+ is installed")
    print("- All dependencies are installed (run install.py)")
    print("- All files are in the same directory")
    print("\nAlternatively, use the installer which handles everything automatically.")
    print("\nPress Enter to exit...")
    time.sleep(3)  # Give user time to read the message
    sys.exit(1)

def main():
    """Main launcher function"""
    print("Genshin Impact Rich Presence Launcher")
    print("=" * 50)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print("-" * 50)

    # Check Python
    if not check_python():
        show_error_and_exit("Python is not installed or not working properly.")

    # Check GUI script
    gui_script = check_gui_script()
    if not gui_script:
        show_error_and_exit("GUI script is missing.")

    print()
    # Launch GUI
    if launch_gui(gui_script):
        print("\n[SUCCESS] Application closed successfully")
    else:
        print("\n[ERROR] Application exited with error")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[CRITICAL] Unexpected error: {e}")
        print("Press Enter to exit...")
        time.sleep(3)  # Give user time to read the message
        sys.exit(1)
