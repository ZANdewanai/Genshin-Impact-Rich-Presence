"""Global state management for the Genshin Impact Rich Presence application."""
import threading
from typing import Optional, Callable

from core.datatypes import Activity, ActivityType, Character, Location, DEBUG_MODE


# =============================================================================
# Threading & Synchronization
# =============================================================================

shutdown_event = threading.Event()
state_lock = threading.Lock()
ocr_lock = threading.Lock()


# =============================================================================
# Game State Variables
# =============================================================================

# Current active character (1-indexed, 0 = undetectable/game paused)
current_active_character: int = 0
last_active_character: int = 0  # Remember the last detected active character

# Character data for all 4 party slots
current_characters: list[Optional[Character]] = [None, None, None, None]

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

# Character cache management
_no_active_character_counter = 0
"""Counter for consecutive iterations without an active character."""

# Coordinate tracking
current_resolution = None
current_coordinates = None
_last_coordinate_log = None
_last_resolution_check = 0

# Anti-spam tracking for logs
_last_location_log = None
_last_character_logs = [None, None, None, None]  # One for each character slot
_last_activity_log = None
_last_detection_log = None


# =============================================================================
# GUI Integration
# =============================================================================

gui_callback: Optional[Callable] = None
"""Callback function for GUI notifications when activities change. Set to None if running without GUI."""

# Global variables for GUI communication
_gui_shared_state = {
    'current_activity': None,
    'current_active_character': 0,
    'current_characters': [None, None, None, None],
    'game_start_time': None,
    'pause_ocr': False
}
_gui_state_lock = threading.Lock()


def get_gui_shared_state():
    """Get current GUI state - thread-safe"""
    with _gui_state_lock:
        return _gui_shared_state.copy()


def set_gui_shared_state(key, value):
    """Set GUI state value - thread-safe"""
    with _gui_state_lock:
        _gui_shared_state[key] = value


def get_gui_state():
    """Get current state for GUI"""
    with state_lock:
        return {
            'current_activity': current_activity,
            'current_active_character': current_active_character,
            'current_characters': current_characters,
            'game_start_time': game_start_time,
            'pause_ocr': ingame_pause_ocr
        }


# =============================================================================
# State Accessors (for use with closures in RPC thread)
# =============================================================================

def get_current_activity():
    """Get current activity (for RPC thread)."""
    with state_lock:
        if DEBUG_MODE:
            print(f"DEBUG get_current_activity: returning {current_activity} (type={current_activity.activity_type})")
        return current_activity


def get_current_characters():
    """Get current characters (for RPC thread)."""
    with state_lock:
        # Return the actual list so RPC thread sees updates
        return current_characters


def get_game_start_time():
    """Get game start time (for RPC thread)."""
    with state_lock:
        return game_start_time


def get_current_timer_type():
    """Get current timer type (for RPC thread)."""
    with state_lock:
        return current_timer_type


def get_last_active_character():
    """Get last active character (for RPC thread)."""
    with state_lock:
        return last_active_character


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


def clear_all_characters():
    """Clear all character data."""
    global current_characters
    with state_lock:
        current_characters = [None, None, None, None]


def reset_game_start_time():
    """Reset the game start timer."""
    global game_start_time
    import time
    with state_lock:
        game_start_time = time.time()
