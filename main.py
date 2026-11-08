"""
___________________________________________________________________

Genshin Impact Discord Rich Presence v3.0

User settings live in shared_config.json (managed by the GUI).
CONFIG.py holds read-only defaults (coordinates, app id, window names).

To exit, press Ctrl+C or close the terminal.
___________________________________________________________________
"""

import sys
import os
import time

# Suppress ONNX Runtime verbose logging (CUDA/DirectML provider warnings)
# Must be set before onnxruntime DLL loads (level 3 = ERROR)
os.environ["ORT_LOGGING_LEVEL"] = "3"

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
        print("   - start_embedded.bat / start_embedded.ps1")
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
    # Discord RPC
    start_rpc_thread,
    stop_rpc_thread,
    join_rpc_thread,
    # Detection loop
    update_coordinates_if_needed,
)

# Import OCR abstraction layer
from core import ocr_engine

# Import data types and config
from core.datatypes import (
    Character,
    Data,
    DEBUG_MODE,
)
from CONFIG import (
    USE_GPU,
    GENSHIN_WINDOW_CLASS,
    GENSHIN_WINDOW_NAME,
)

from core import ps_helper
import core.state

# User-changeable settings (username, traveler, GPU, debug flags...) all come
# from shared_config.json via core.shared_config (mtime-gated, read live).
# CONFIG.py is read-only defaults; nothing is copied or mutated at startup.
# Identity settings are read by core.datatypes._identity_settings() when
# characters.csv is loaded; DEBUG flags self-sync via _ConfigFlag.

print(__doc__)

# Initialize data
DATA: Data = Data()

# Initialize OCR
print("Initializing OCR.")
# GPU preference: shared_config.json (GUI toggle) wins over CONFIG.py default.
from core.shared_config import get_shared_config
use_gpu = bool(get_shared_config().get("USE_GPU", USE_GPU))
reader = ocr_engine.Reader(["en"], gpu=use_gpu)
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
    """Handle graceful shutdown on Ctrl+C or SIGTERM."""
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
    # Force immediate process termination - kills all threads.
    # os._exit bypasses normal cleanup that might hang on daemon threads.
    os._exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("Press Ctrl+C to exit gracefully")

# Resolution re-detection cadence. detection.update_coordinates_if_needed()
# internally rate-limits its window-size polling to
# core.detection.RESOLUTION_CHECK_INTERVAL seconds, so calling it every loop
# iteration is cheap and correct regardless of how long each iteration takes.
RESOLUTION_CHECK_INTERVAL_S = 60.0
_last_resolution_check = 0.0


def update_pause_state():
    """Single owner of core.state.ingame_pause_ocr.

    OCR pauses whenever the Genshin window is missing/minimized OR not in
    the foreground; it resumes only when both are true again.
    """
    window_open = ps_helper.check_process_window_open(
        GENSHIN_WINDOW_CLASS, GENSHIN_WINDOW_NAME
    )
    foreground = ps_helper.check_genshin_is_foreground()
    should_pause = not (window_open and foreground)

    with core.state.state_lock:
        if should_pause and not core.state.ingame_pause_ocr:
            core.state.ingame_pause_ocr = True
            print(
                "GenshinImpact.exe minimized/closed. Pausing OCR."
                if not window_open
                else "GenshinImpact.exe lost focus. Pausing OCR."
            )
        elif not should_pause and core.state.ingame_pause_ocr:
            core.state.ingame_pause_ocr = False
            print("GenshinImpact.exe resumed. Resuming OCR.")


# Main loop
loop_count = 0

while not shutdown_event.is_set():
    # Initialize/update coordinates (internally rate-limited).
    now = time.time()
    if now - _last_resolution_check >= RESOLUTION_CHECK_INTERVAL_S:
        _last_resolution_check = now
        update_coordinates_if_needed()

    # Pause/resume OCR based on window state (checked every iteration; the
    # window queries are cached in ps_helper).
    update_pause_state()

    if core.state.ingame_pause_ocr:
        time.sleep(3)  # Sleep 3 seconds when not in foreground
        loop_count += 1
        continue

    # Run one detection iteration
    try:
        sleep_duration = coordinator.tick()
    except Exception as e:
        print(f"[ERROR] Coordinator error: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sleep_duration = 1.0

    # Write data to shared file for GUI every 10 iterations (approx every 1.5s)
    if loop_count % 10 == 0:
        write_gui_shared_data()

    time.sleep(sleep_duration)
    loop_count += 1
