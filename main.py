"""
___________________________________________________________________

Genshin Impact Discord Rich Presence v3.0

Setup CONFIG.py with the game resolution, username, etc...
before using.

To exit, press Ctrl+C or close the terminal.
___________________________________________________________________
"""

import sys
import os
import json
import time
import threading

# DPI awareness MUST be declared before any window enumeration or screen
# capture. The PyInstaller bootloader manifest (unlike python.exe's) does not
# declare it, so without this Windows reports DPI-virtualized (scaled down)
# window rects on high-DPI displays and every OCR region is misaligned.
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE_V2-ish
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from PIL import ImageGrab

# Windowed exe (pythonw / PyInstaller console=False) has no console and
# sys.stdout/sys.stderr are None - guard before touching them.
if sys.stdout is not None:
    sys.stdout.reconfigure(line_buffering=True)
else:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is not None:
    sys.stderr.reconfigure(line_buffering=True)
else:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# When stdout is a PIPE (engine spawned by the GUI), Python defaults to the
# legacy ANSI codepage - printing OCR'd game text (arrows, accents, CJK)
# raises UnicodeEncodeError which aborts the detection scan mid-result.
# Force UTF-8 so game text survives the trip to the GUI log.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Frozen (PyInstaller exe): __file__ points inside the bundle - base paths
# on the exe's own folder instead. core/, CONFIG.py, data/ etc. live there.
if getattr(sys, "frozen", False):
    script_dir = os.path.dirname(os.path.abspath(sys.executable))
    # Some modules (core/datatypes.py) read data files via CWD-relative
    # paths like "data/bosses.csv" - make that deterministic.
    os.chdir(script_dir)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# VERIFY: Must run with embedded Python only (skip when frozen - the exe
# carries its own interpreter).
if not getattr(sys, "frozen", False):
    expected_embedded = os.path.join(script_dir, "python3.12.8_embedded", "python.exe")
    # Case-insensitive comparison for Windows paths
    if sys.executable.lower() != expected_embedded.lower():
        print("[ERROR] This application must run with the embedded Python interpreter.")
        print(f"   Current: {sys.executable}")
        print(f"   Expected: {expected_embedded}")
        print("")
        print("   Please use the provided launcher:")
        print("   - start.bat")
        print("   - start.ps1")
        print("   - python3.12.8_embedded/python.exe main.py")
        print("")
        input("Press Enter to exit...")
        sys.exit(1)

print(f"[OK] Using interpreter: {sys.executable}")

# Import core modules
from core import (
    shutdown_event,
    get_current_activity,
    get_current_characters,
    get_game_start_time,
    get_current_timer_type,
    get_last_active_character,
    reset_game_start_time,
    write_gui_shared_data,
    shutdown_ocr_executor,
    # Discord RPC
    start_rpc_thread,
    stop_rpc_thread,
    join_rpc_thread,
    # Detection loop
    update_coordinates_if_needed,
    RESOLUTION_CHECK_INTERVAL,
)

# Import OCR abstraction layer
from core import ocr_engine

# Import data types and config
from core.datatypes import (
    Character,
    Data,
    set_config_values,
)
from CONFIG import (
    USE_GPU,
    GENSHIN_WINDOW_CLASS,
    GENSHIN_WINDOW_NAME,
    get_dynamic_coordinates,
    DEBUG_MODE,
    DEBUG_CHARACTER_MODE,
    USERNAME,
    MC_AETHER,
    WANDERER_NAME,
)

# Fallbacks for settings normally supplied via shared_config.json by the GUI
MANEKIN_NAME = "Manekin"
MANEKINA_NAME = "Manekina"
GAME_RESOLUTION = 1080

from core import ps_helper
import core.state

# Load shared config from GUI if available
shared_config_path = os.path.join(script_dir, "shared_config.json")
if os.path.exists(shared_config_path):
    try:
        with open(shared_config_path, "r") as f:
            shared_config = json.load(f)
            # Update global variables if present in shared config
            for key in [
                "USERNAME",
                "MC_AETHER",
                "WANDERER_NAME",
                "MANEKIN_NAME",
                "MANEKINA_NAME",
                "GAME_RESOLUTION",
                "USE_GPU",
            ]:
                if key in shared_config:
                    globals()[key] = shared_config[key]
                    print(f"Updated {key} from shared config: {shared_config[key]}")
    except Exception as e:
        print(f"Failed to load shared config: {e}")

# Set config values in datatypes module to avoid circular dependency
set_config_values(
    debug_mode=DEBUG_MODE,
    debug_character_mode=DEBUG_CHARACTER_MODE,
    mc_aether=MC_AETHER,
    wanderer_name=WANDERER_NAME,
    manekin_name=MANEKIN_NAME,
    manekina_name=MANEKINA_NAME,
    username=USERNAME,
    game_resolution=GAME_RESOLUTION
)

print(__doc__)

# Initialize data
DATA: Data = Data()

# Initialize OCR
print("Initializing OCR.")
reader = ocr_engine.Reader(["en"], gpu=USE_GPU)
print("OCR started.")
print("_______________________________________________________________")

# Initialize sensor coordinator
from core.coordinator import SensorCoordinator

coordinator = SensorCoordinator(reader, DATA)
print("[OK] Sensor worker architecture enabled "
      "(CharSensor / LocationSensor / MenuSensor)")

# Reset game timer on startup for fresh session
reset_game_start_time()

# Start sensor workers if enabled
if coordinator is not None:
    coordinator.start()


# Start Discord RPC thread
start_rpc_thread(
    get_current_activity,
    get_current_characters,
    get_game_start_time,
    get_current_timer_type,
    get_last_active_character,
)


# Register signal handlers for graceful shutdown
import signal


def signal_handler(signum, frame):
    """Handle graceful shutdown on Ctrl+C or SIGTERM - kills entire process immediately"""
    print(f"\nReceived signal {signum}, terminating process...")
    shutdown_event.set()
    if coordinator is not None:
        try:
            coordinator.stop()
        except Exception as e:
            print(f"Warning: Error stopping sensors: {e}")
    # Clear Discord presence before killing process
    try:
        stop_rpc_thread()
        join_rpc_thread(timeout=1.0)
    except (OSError, RuntimeError) as e:
        print(f"Warning: Error during shutdown: {e}")
    try:
        shutdown_ocr_executor()
    except (OSError, RuntimeError) as e:
        print(f"Warning: Error during OCR executor shutdown: {e}")
    # Force immediate process termination - kills all threads
    # Use _exit to bypass normal cleanup that might hang on daemon threads
    os._exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("Press Ctrl+C to exit gracefully")

# Window monitoring thread
ps_window_thread_instance: threading.Thread = None


def update_genshin_open_status():
    """Update pause_ocr status based on Genshin window state."""
    window_open = ps_helper.check_process_window_open(
        GENSHIN_WINDOW_CLASS, GENSHIN_WINDOW_NAME
    )
    genshin_active = ps_helper.check_genshin_is_foreground()

    with core.state.state_lock:
        if window_open and genshin_active and core.state.ingame_pause_ocr:
            core.state.ingame_pause_ocr = False
            print("GenshinImpact.exe resumed. Resuming OCR.")
        elif (
            not window_open or not genshin_active
        ) and not core.state.ingame_pause_ocr:
            core.state.ingame_pause_ocr = True
            if not window_open:
                print("GenshinImpact.exe minimized/closed. Pausing OCR.")
            else:
                print("GenshinImpact.exe lost focus. Pausing OCR.")


# Main loop
loop_count = 0

while not shutdown_event.is_set():
    # Initialize/update coordinates on first run and periodically check for resolution changes
    if (
        loop_count == 0 or loop_count % (RESOLUTION_CHECK_INTERVAL * 10) == 0
    ):  # Check every ~10 minutes
        update_coordinates_if_needed()

    # Check if Genshin is in foreground
    if not ps_helper.check_genshin_is_foreground():
        with core.state.state_lock:
            if not core.state.ingame_pause_ocr:
                core.state.ingame_pause_ocr = True
                print("GenshinImpact.exe lost focus. Pausing OCR.")

        time.sleep(3)  # Sleep 3 seconds when not in foreground

        # Check window status less frequently when inactive
        if loop_count % 3 == 0:  # Check every 3 iterations when paused
            if (
                ps_window_thread_instance is None
                or not ps_window_thread_instance.is_alive()
            ):
                ps_window_thread_instance = threading.Thread(
                    target=update_genshin_open_status,
                    daemon=True,
                )
                ps_window_thread_instance.start()
        loop_count += 1
        continue

    # Update pause_ocr status if Genshin is back in foreground
    with core.state.state_lock:
        if core.state.ingame_pause_ocr:
            core.state.ingame_pause_ocr = False
            print("GenshinImpact.exe resumed. Resuming OCR.")

    # Run one detection iteration
    try:
        sleep_duration = coordinator.tick()
    except Exception as e:
        print(f"[ERROR] Coordinator error: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sleep_duration = 1.0

    # Write data to shared file for GUI every 10 iterations (approx every 1.5 seconds)
    if loop_count % 10 == 0:
        write_gui_shared_data()


    time.sleep(sleep_duration)
    loop_count += 1
