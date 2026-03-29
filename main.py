"""
___________________________________________________________________

Genshin Impact Discord Rich Presence v2.6

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

# Ensure script directory is in path for local modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# VERIFY: Must run with embedded Python only
expected_embedded = os.path.join(script_dir, 'python3.13.11_embedded', 'python.exe')
if sys.executable != expected_embedded:
    print("❌ ERROR: This application must run with the embedded Python interpreter.")
    print(f"   Current: {sys.executable}")
    print(f"   Expected: {expected_embedded}")
    print("")
    print("   Please use one of the following launchers:")
    print("   - start_embedded.bat")
    print("   - start_embedded.ps1")
    print("   - python3.13.11_embedded\\python.exe main.py")
    print("")
    input("Press Enter to exit...")
    sys.exit(1)

print(f"✅ Using embedded Python: {sys.executable}")

# Import core modules
from core import (
    # State
    current_activity, game_start_time, current_timer_type,
    gui_callback, shutdown_event, state_lock,
    update_activity, set_active_character, update_character,
    get_current_activity, get_current_characters, get_game_start_time,
    get_current_timer_type, get_last_active_character,
    reset_game_start_time,
    # Character detection
    CharacterRegionManager,
    # Discord RPC
    start_rpc_thread, stop_rpc_thread, is_rpc_alive, join_rpc_thread,
    # Detection loop
    run_detection_iteration, update_coordinates_if_needed,
    detect_characters_with_adaptation,
    RESOLUTION_CHECK_INTERVAL,
)

# Import OCR abstraction layer
from core import ocr_engine

# Import data types and config
from core.datatypes import (
    Activity, ActivityType, Character, Data, DEBUG_MODE,
    USERNAME, MC_AETHER, WANDERER_NAME
)
from CONFIG import (
    USE_GPU, GAME_RESOLUTION,
    SLEEP_PER_ITERATION, PAUSE_STATE_COOLDOWN,
    GENSHIN_WINDOW_CLASS, GENSHIN_WINDOW_NAME, get_dynamic_coordinates,
    OCR_CHARNAMES_ONE_IN, DEBUG_CHARACTER_MODE,
)

from core import ps_helper

# Load shared config from GUI if available
shared_config_path = os.path.join(script_dir, 'shared_config.json')
if os.path.exists(shared_config_path):
    try:
        with open(shared_config_path, 'r') as f:
            shared_config = json.load(f)
            # Update global variables if present in shared config
            for key in ['USERNAME', 'MC_AETHER', 'WANDERER_NAME', 'GAME_RESOLUTION', 'USE_GPU']:
                if key in shared_config:
                    globals()[key] = shared_config[key]
                    print(f"Updated {key} from shared config: {shared_config[key]}")
    except Exception as e:
        print(f"Failed to load shared config: {e}")

# Check environment variables for GPU override (from GUI subprocess)
cuda_visible_devices = os.getenv('CUDA_VISIBLE_DEVICES')
pytorch_cuda_alloc_conf = os.getenv('PYTORCH_CUDA_ALLOC_CONF')

print(f"Environment check - CUDA_VISIBLE_DEVICES: {cuda_visible_devices}")
print(f"Environment check - PYTORCH_CUDA_ALLOC_CONF: {pytorch_cuda_alloc_conf}")
print(f"USE_GPU from CONFIG: {USE_GPU}")

if cuda_visible_devices is not None:
    if cuda_visible_devices == '0':
        USE_GPU = True
        print("GPU acceleration enabled via environment variable")
    elif cuda_visible_devices == '':
        USE_GPU = False
        print("GPU acceleration disabled via environment variable")
    else:
        print(f"CUDA_VISIBLE_DEVICES set to: {cuda_visible_devices}")

print(f"Final USE_GPU setting: {USE_GPU}")

print(__doc__)

# Initialize data
DATA: Data = Data()

# Initialize OCR
print("Initializing OCR.")
reader = ocr_engine.Reader(["en"], gpu=USE_GPU)
print("OCR started.")
print("_______________________________________________________________")

# Initialize character region manager
character_region_manager = CharacterRegionManager(reader)

# Handle command line arguments for manual control
def handle_adaptive_character_commands():
    """Handle manual control commands for the adaptive character system"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "reset_char_positions":
            character_region_manager.reset_to_base_positions()
            print("✅ Character positions reset to base coordinates")
            sys.exit(0)
        elif command == "log_char_status":
            character_region_manager.log_status()
            sys.exit(0)
        elif command == "disable_char_adaptation":
            character_region_manager.adaptation_enabled = False
            print("🔒 Character adaptation disabled")
            sys.exit(0)
        elif command == "enable_char_adaptation":
            character_region_manager.adaptation_enabled = True
            print("🔓 Character adaptation enabled")
            sys.exit(0)
        elif command == "test_char_adaptation":
            print("🧪 Testing character adaptation system...")
            occupied_slots, confidence_scores = character_region_manager.detect_occupied_slots()
            character_region_manager.log_status()
            print(f"🎯 Test Results: Occupied slots: {occupied_slots}")
            print(f"📊 Confidence scores: {[round(c, 2) for c in confidence_scores]}")
            sys.exit(0)

handle_adaptive_character_commands()

# Print adaptive system status
print("🎯 Character Adaptive OCR System Status:")
print(f"   Adaptation enabled: {character_region_manager.adaptation_enabled}")
print(f"   Max vertical shift: {character_region_manager.max_vertical_shift}px")
print(f"   Movement step: {character_region_manager.movement_step}px")
print(f"   Base coordinates: {character_region_manager.base_name_positions}")
print("✅ Adaptive character detection system initialized!")
print("💡 Use command line arguments to control the system:")
print("   python main.py reset_char_positions")
print("   python main.py log_char_status")
print("   python main.py disable_char_adaptation")
print("   python main.py enable_char_adaptation")
print("   python main.py test_char_adaptation")
print("_______________________________________________________________")

# Reset game timer on startup for fresh session
reset_game_start_time()

# Start Discord RPC thread
start_rpc_thread(
    get_current_activity,
    get_current_characters,
    get_game_start_time,
    get_current_timer_type,
    get_last_active_character
)


# Register signal handlers for graceful shutdown
import signal

def signal_handler(signum, frame):
    """Handle graceful shutdown on Ctrl+C or SIGTERM - kills entire process immediately"""
    print(f"\nReceived signal {signum}, terminating process...")
    shutdown_event.set()
    # Clear Discord presence before killing process
    try:
        stop_rpc_thread()
        join_rpc_thread(timeout=1.0)
    except:
        pass
    # Force immediate process termination - kills all threads
    # Use _exit to bypass normal cleanup that might hang on daemon threads
    import os
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("Press Ctrl+C to exit gracefully")

# Window monitoring thread
ps_window_thread_instance: threading.Thread = None


def update_genshin_open_status():
    """Update pause_ocr status based on Genshin window state."""
    from core.state import ingame_pause_ocr
    window_open = ps_helper.check_process_window_open(GENSHIN_WINDOW_CLASS, GENSHIN_WINDOW_NAME)
    genshin_active = ps_helper.check_genshin_is_foreground()

    if window_open and genshin_active and ingame_pause_ocr:
        ingame_pause_ocr = False
        print("GenshinImpact.exe resumed. Resuming OCR.")
    elif (not window_open or not genshin_active) and not ingame_pause_ocr:
        ingame_pause_ocr = True
        if not window_open:
            print("GenshinImpact.exe minimized/closed. Pausing OCR.")
        else:
            print("GenshinImpact.exe lost focus. Pausing OCR.")


# Main loop
loop_count = 0

while not shutdown_event.is_set():
    # Initialize/update coordinates on first run and periodically check for resolution changes
    if loop_count == 0 or loop_count % (RESOLUTION_CHECK_INTERVAL * 10) == 0:  # Check every ~10 minutes
        update_coordinates_if_needed()

    # Check if Genshin is in foreground
    if not ps_helper.check_genshin_is_foreground():
        from core.state import ingame_pause_ocr
        if not ingame_pause_ocr:
            ingame_pause_ocr = True
            print("GenshinImpact.exe lost focus. Pausing OCR.")

        time.sleep(3)  # Sleep 3 seconds when not in foreground

        # Check window status less frequently when inactive
        if loop_count % 3 == 0:  # Check every 3 iterations when paused
            if ps_window_thread_instance is None or not ps_window_thread_instance.is_alive():
                ps_window_thread_instance = threading.Thread(
                    target=update_genshin_open_status,
                    daemon=True,
                )
                ps_window_thread_instance.start()
        loop_count += 1
        continue

    # Update pause_ocr status if Genshin is back in foreground
    from core.state import ingame_pause_ocr
    if ingame_pause_ocr:
        ingame_pause_ocr = False
        print("GenshinImpact.exe resumed. Resuming OCR.")

    # Run one detection iteration
    try:
        sleep_duration = run_detection_iteration(reader, DATA, character_region_manager, loop_count)
    except Exception as e:
        print(f"❌ Error in detection iteration: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sleep_duration = 1.0  # Use longer sleep on error to avoid spamming

    # Write data to shared file for GUI if environment variable is set
    shared_file = os.getenv('GUI_SHARED_DATA_FILE')
    if shared_file:
        try:
            from core.state import current_characters, current_active_character, ingame_pause_ocr

            # Convert Activity object to dict for JSON serialization
            activity_dict = None
            if current_activity:
                activity_data_serialized = None
                if current_activity.activity_data:
                    if hasattr(current_activity.activity_data, '__dict__'):
                        activity_data_dict = {}
                        for key, value in current_activity.activity_data.__dict__.items():
                            if hasattr(value, 'value'):
                                activity_data_dict[key] = value.value
                            elif hasattr(value, 'name'):
                                activity_data_dict[key] = value.name
                            else:
                                activity_data_dict[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value
                        activity_data_serialized = activity_data_dict
                    else:
                        activity_data_serialized = current_activity.activity_data

                activity_type_value = None
                if hasattr(current_activity.activity_type, 'value'):
                    activity_type_value = current_activity.activity_type.value
                elif hasattr(current_activity.activity_type, 'name'):
                    activity_type_value = current_activity.activity_type.name
                else:
                    activity_type_value = str(current_activity.activity_type)

                activity_dict = {
                    'activity_type': activity_type_value,
                    'activity_data': activity_data_serialized
                }

            # Convert Character objects to dicts
            characters_dict = []
            for char in current_characters:
                if char:
                    characters_dict.append({
                        'character_display_name': char.character_display_name,
                        'image_key': char.image_key,
                    })

            data_to_write = {
                'timestamp': time.time(),
                'current_activity': activity_dict,
                'current_characters': characters_dict,
                'current_active_character': current_active_character,
                'game_start_time': game_start_time,
                'pause_ocr': ingame_pause_ocr,
                'adapted_coordinates': {
                    'ADAPTED_NAMES_4P_COORD': character_region_manager.current_name_positions.copy(),
                    'ADAPTED_NUMBER_4P_COORD': character_region_manager.current_number_positions.copy(),
                    'ADAPTATION_ACTIVE': character_region_manager.adaptation_enabled,
                    'OCCUPIED_SLOTS': character_region_manager.occupied_slots.copy()
                }
            }
            with open(shared_file, 'w') as f:
                json.dump(data_to_write, f, default=str)

            if DEBUG_MODE:
                print(f"✅ Wrote shared data to {shared_file}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Error writing to shared file: {e}")

    time.sleep(sleep_duration)
    loop_count += 1
