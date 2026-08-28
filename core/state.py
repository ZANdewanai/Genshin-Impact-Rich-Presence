"""Global state management for the Genshin Impact Rich Presence application."""

import os
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable

from core.datatypes import Activity, ActivityType, Character, Location, DEBUG_MODE
from core.log_utils import log as log_ts, should_log as log_should_log
from CONFIG import MAX_PARTY_SLOTS


# =============================================================================
# Threading & Synchronization
# =============================================================================

shutdown_event = threading.Event()
state_lock = threading.RLock()
ocr_lock = threading.Lock()

ocr_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr")


# =============================================================================
# Game State Variables
# =============================================================================

# Current active character (1-indexed, 0 = undetectable/game paused)
current_active_character: int = 0
last_active_character: int = 0  # Remember the last detected active character

# Character data for all party slots (5 in current Genshin).
current_characters: list[Optional[Character]] = [None] * MAX_PARTY_SLOTS

# Flag to track if characters were truly detected this cycle (vs cached from before)
# Initialized to True so first detection cycle works immediately
currently_active_characters_valid: bool = True

# Activity tracking
prev_non_idle_activity: Activity = Activity(ActivityType.LOADING, False)
"""Stores most recent non-idle activity (Loading, Location, Domain, Commissions, World Boss)."""

prev_location: Optional[Location] = None
"""Stores most recently visited location (assumes commissions are here)."""

current_activity: Activity = Activity(ActivityType.LOADING, False)

# Timers
game_start_time: Optional[int] = None
"""Global session timer - tracks total time since gameplay started."""

current_timer_type = "global"
"""Tracks which timer to use: 'global', 'activity', or 'menu'."""

menu_start_time: Optional[int] = None
"""Timer for menu activities - starts when entering menus."""

# Game pause state
game_paused = False
"""True if the game is found to be paused in the previous iteration."""

game_pause_state_cooldown = 0
"""Cooldown before committing pause/unpause state to current_activity."""

game_pause_state_displayed = False
"""Shows the last displayed game pause state (to prevent spam)."""

# Inactive detection
ingame_pause_ocr = False
"""Set to True when genshin is minimized (internal use)."""

inactive_detection_cooldown = 0
"""Limits other detections if some inactive action is detected."""

inactive_detection_mode: Optional[ActivityType] = None
"""What was the inactive activity that was last detected."""

reload_party_flag = False
"""Set to True after party setup screen is detected."""

# Coordinate tracking
current_resolution = None
current_coordinates = None
_last_coordinate_log = None
_last_resolution_check = 0

# Anti-spam tracking for logs
_last_location_log = None
_last_activity_log = None
_last_detection_log = None


# =============================================================================
# GUI Integration
# =============================================================================

# =============================================================================
gui_callback: Optional[Callable] = None
"""Optional callback for GUI notifications on activity changes (set by embedders)."""


# State Accessors (for use with closures in RPC thread)
# =============================================================================


def get_current_activity():
    """Get current activity (for RPC thread)."""
    with state_lock:
        if DEBUG_MODE:
            print(
                f"DEBUG get_current_activity: returning {current_activity} (type={current_activity.activity_type})"
            )
        return current_activity


def get_current_characters():
    """Get current characters (for RPC thread)."""
    with state_lock:
        return current_characters.copy()


def get_game_start_time():
    """Get game start time (for RPC thread)."""
    with state_lock:
        return game_start_time


def get_current_timer_type():
    """Get current timer type (for RPC thread)."""
    with state_lock:
        return current_timer_type


# =============================================================================
# State Updaters
# =============================================================================


def update_activity(activity: Activity):
    """Update current activity thread-safely."""
    global current_activity
    with state_lock:
        current_activity = activity


def update_prev_non_idle_activity(activity: Activity):
    """Update previous non-idle activity thread-safely."""
    global prev_non_idle_activity
    with state_lock:
        prev_non_idle_activity = activity


def set_active_character(idx: int):
    """Set the current active character index."""
    global current_active_character, last_active_character
    with state_lock:
        current_active_character = idx
        last_active_character = idx
        if DEBUG_MODE:
            print(f"DEBUG set_active_character: set to {idx}")


def get_last_active_character():
    """Get the last active character index."""
    with state_lock:
        if DEBUG_MODE:
            print(f"DEBUG get_last_active_character: returning {last_active_character}")
        return last_active_character


def update_character(slot_idx: int, character: Optional[Character]):
    """Update a character at a specific slot."""
    global current_characters
    with state_lock:
        if 0 <= slot_idx < len(current_characters):
            current_characters[slot_idx] = character
            if DEBUG_MODE:
                print(f"DEBUG update_character: slot {slot_idx} set to {character.character_display_name if character else 'None'}")
                print(f"DEBUG current_characters after update: {[c.character_display_name if c else 'None' for c in current_characters]}")


def clear_all_characters():
    """Clear all character data."""
    global current_characters
    with state_lock:
        current_characters = [None] * MAX_PARTY_SLOTS


def reset_game_start_time():
    """Reset the game start timer."""
    global game_start_time
    import time

    with state_lock:
        game_start_time = time.time()


def shutdown_ocr_executor():
    """Shutdown the OCR thread pool executor."""
    global ocr_executor
    if ocr_executor is not None:
        ocr_executor.shutdown(wait=False)
        ocr_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr")


# =============================================================================
# GUI Shared Data File
# =============================================================================

def _get_shared_data_path():
    """Get path to GUI shared data file."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "gui_shared_data.json"
    )


def write_gui_shared_data():
    """Write current state to shared data file for GUI."""
    try:
        data = {
            "active_characters": [],
            "location": "Unknown",
            "activity": "None",
            "active_character_index": 0,  # 0-indexed, -1 if none
            "timestamp": None,
        }

        with state_lock:
            # Get active characters with image keys
            chars = []
            char_image_keys = []
            for char in current_characters:
                if char is not None:
                    chars.append(char.character_display_name)
                    char_image_keys.append(char.image_key)
            data["active_characters"] = chars if chars else ["None"]
            data["active_character_image_keys"] = char_image_keys if char_image_keys else [""]

            if DEBUG_MODE and log_should_log("gui_data", 30.0):
                log_ts(f"DEBUG write_gui_shared_data: current_characters = {[c.character_display_name if c else 'None' for c in current_characters]}")
                log_ts(f"DEBUG write_gui_shared_data: active_characters = {data['active_characters']}")
            
            # Get active character index (convert from 1-indexed to 0-indexed)
            if current_active_character > 0:
                data["active_character_index"] = current_active_character - 1
            else:
                data["active_character_index"] = -1
            
            # Get location from current activity
            if current_activity and current_activity.activity_type == ActivityType.LOCATION and current_activity.activity_data:
                data["location"] = current_activity.activity_data.location_name
            elif prev_location:
                data["location"] = prev_location.location_name
            
            # Get activity description
            if current_activity:
                # Use activity type name
                data["activity"] = current_activity.activity_type.name.replace("_", " ").title()
            else:
                data["activity"] = "Unknown"
            
            data["timestamp"] = game_start_time
        
        if DEBUG_MODE and log_should_log("gui_final", 30.0):
            log_ts(f"DEBUG write_gui_shared_data: Final data = {data}")
        
        # Write to file atomically (write to temp file, then rename)
        shared_path = _get_shared_data_path()
        temp_path = shared_path + ".tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)
            if DEBUG_MODE:
                print(f"DEBUG write_gui_shared_data: Wrote to {shared_path}")
            # Atomic rename on Windows
            if os.path.exists(shared_path):
                os.replace(temp_path, shared_path)
            else:
                os.rename(temp_path, shared_path)
        except Exception as e:
            # Clean up temp file if something went wrong
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass  # Best effort cleanup
            raise
            
    except Exception as e:
        if DEBUG_MODE:
            print(f"DEBUG: Failed to write shared data: {e}")
