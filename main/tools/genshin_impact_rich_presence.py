#!/usr/bin/env python3
"""
Genshin Impact Rich Presence - Single Executable Version
Combines GUI and OCR functionality into one bundle
"""

import sys
import os
import threading
import subprocess
import time

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    """Main entry point for the bundled application"""
    print("Genshin Impact Rich Presence")
    print("=" * 40)
    print("Starting application...")

    try:
        # Import and run the GUI
        from GenshinImpactRichPresence_GUI import GenshinRichPresenceApp

        # Create and run the GUI
        app = GenshinRichPresenceApp()
        app.mainloop()

    except Exception as e:
        print(f"Error starting application: {e}")
        print("Press Enter to exit...")
        try:
            input()
        except:
            time.sleep(3)
        sys.exit(1)

if __name__ == "__main__":
    main()
