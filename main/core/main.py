import os
import sys
import signal
import time
from typing import Dict, Any

# Import configuration
# Add parent directory to path for direct script execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import CONFIG
from CONFIG import *

# Import our modular components
# Add current directory to path for direct script execution
if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

from datatypes import Data
from game.game_monitor import GameMonitor
from ui.overlay import overlay


def signal_handler(sig, frame):
    """Handle Ctrl+C signal."""
    print("\nStopping Discord Rich Presence...")
    if 'monitor' in globals():
        monitor.stop()
    sys.exit(0)


def create_config_dict() -> Dict[str, Any]:
    """Create configuration dictionary from CONFIG module."""
    config_vars = [
        'NUMBER_4P_COORD', 'ACTIVE_CHARACTER_THRESH', 'NAMES_4P_COORD',
        'BOSS_COORD', 'LOCATION_COORD', 'DOMAIN_COORD', 'GAME_MENU_COORD',
        'ALLOWLIST', 'ALLOWLIST2', 'LOC_CONF_THRESH', 'NAME_CONF_THRESH',
        'SLEEP_PER_ITERATION', 'INACTIVE_COOLDOWN', 'PAUSE_STATE_COOLDOWN',
        'OCR_CHARNAMES_ONE_IN', 'OCR_LOC_ONE_IN', 'OCR_BOSS_ONE_IN',
        'DEBUG_MODE', 'USE_GPU', 'OVERLAY_OPACITY', 'OVERLAY_TEXT_COLOR',
        'OVERLAY_BORDER_COLOR', 'OVERLAY_BORDER_WIDTH', 'OCR_REGION_LABELS',
        'MC_AETHER', 'WANDERER_NAME', 'DEBUG_SAVE_IMAGES', 'DEBUG_IMAGES_DIRECTORY',
        'ENABLE_OCR_OVERLAY', 'DEBUG_LOCATION', 'DEBUG_CHARACTER', 'DEBUG_BOSS',
        'DEBUG_DOMAIN', 'DEBUG_GAME_MENU'
    ]

    config = {}
    for var_name in config_vars:
        if hasattr(CONFIG, var_name):
            config[var_name] = getattr(CONFIG, var_name)
        else:
            print(f"Warning: {var_name} not found in CONFIG module")

    return config


def main():
    """Main entry point."""
    print(__doc__)

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize data layer
    print("Initializing data layer...")
    data = Data()

    # Create configuration dictionary
    config = create_config_dict()

    # Initialize and start OCR debugging overlay if enabled
    if config.get('ENABLE_OCR_OVERLAY', False):
        print(f"Initializing OCR Overlay (enabled: {ENABLE_OCR_OVERLAY})")
        try:
            overlay.enabled = True
            overlay.debug_mode = config.get('DEBUG_MODE', False)

            overlay_started = overlay.start()
            if not overlay_started:
                print("Warning: Failed to start overlay")
        except Exception as e:
            print(f"Failed to initialize overlay: {e}")
            if config.get('DEBUG_MODE', False):
                import traceback
                traceback.print_exc()
    else:
        print("OCR Overlay is disabled in config")

    # Create and start game monitor
    print("Starting game monitor...")
    monitor = GameMonitor(data, config)

    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        print("\nCleaning up resources...")
        monitor.stop()

        # Close overlay if running
        if config.get('ENABLE_OCR_OVERLAY', False) and hasattr(overlay, 'overlay_window'):
            try:
                overlay.stop()
            except Exception as e:
                print(f"Error stopping overlay: {e}")


if __name__ == "__main__":
    main()
