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
from typing import Optional
from asyncio import new_event_loop, set_event_loop
import threading
import json
import numpy as np

# Ensure script directory is in path for local modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Import OCR abstraction layer instead of direct EasyOCR
import ocr_engine

import pypresence as discord
import ps_helper

from PIL import ImageGrab

from CONFIG import *
from datatypes import *

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

# Data contains csv tables, file watcher, and best text match algorithms.
DATA: Data = Data()

def get_party_info_string():
    """Generate party info string for Discord RPC."""
    party_members = []
    for i, char in enumerate(current_characters[:4], 1):  # Show first 4 characters
        if char != None:
            party_members.append(char.character_display_name)
        else:
            party_members.append(f"Slot {i}")

    return " | ".join(party_members) if party_members else "No party detected"

def capture_and_process_ocr(coord, allowlist, conf_thresh, activity_type, search_func, text_processor=None, debug_key=None):
    """
    Generic function to handle OCR capture, processing, and activity detection.
    :param coord: Coordinate tuple for ImageGrab
    :param allowlist: String for OCR allowlist
    :param conf_thresh: Confidence threshold for text filtering
    :param activity_type: ActivityType enum for detection
    :param search_func: Function to search for activity data (e.g., DATA.search_location)
    :param text_processor: Optional function to process text before searching
    :param debug_key: Optional key for debug prints (e.g., 'LOCATION')
    :return: Detected activity or None
    """
    image = None
    cap = None
    try:
        image = ImageGrab.grab(bbox=coord)
        cap = np.array(image)
    except OSError:
        print("OSError: Cannot capture screen. Try running as admin if this issue persists.")
        time.sleep(1)
        return None
    except Exception as e:
        print(f"Unexpected error during image capture for {activity_type}: {e}")
        time.sleep(1)
        return None

    results = []
    try:
        results = reader.readtext(cap, allowlist=allowlist)
    except Exception as e:
        print(f"OCR Error during {activity_type} recognition: {e}")
        # Cleanup
        del cap
        if image:
            image.close()
        del image
        time.sleep(1)
        return None

    # Cleanup memory
    del cap
    if image:
        image.close()
    del image

    processed_text = " ".join([word.strip() for word in [r[1] for r in results if r[2] > conf_thresh]])
    if debug_key and DEBUG_MODE:
        print(f"{debug_key} OCR: '{processed_text}' (confidence: {[r[2] for r in results if r[2] > conf_thresh]})")

    if text_processor:
        processed_text = text_processor(processed_text)

    if len(processed_text) > 0:
        data = search_func(processed_text)
        if data:
            return data
    return None

# Dynamic coordinate management
current_resolution = None
current_coordinates = None
_last_coordinate_log = None
_last_resolution_check = 0
RESOLUTION_CHECK_INTERVAL = 60  # Check every 60 seconds like GUI
RESOLUTION_CHANGE_THRESHOLD = 10  # 10px threshold for resolution change

# Anti-spam tracking for logs
_last_location_log = None
_last_character_logs = [None, None, None, None]  # One for each character slot
_last_activity_log = None
_last_detection_log = None

def update_coordinates_if_needed():
    """
    Checks if Genshin window resolution has changed and updates coordinates accordingly.
    Called both for initialization and continuous monitoring.
    """
    global current_resolution, current_coordinates, _last_coordinate_log, _last_resolution_check
    global NUMBER_4P_COORD, NAMES_4P_COORD, BOSS_COORD, LOCATION_COORD
    global MAP_LOC_COORD, ACTIVITY_COORD, DOMAIN_COORD, PARTY_SETUP_COORD

    try:
        current_time = time.time()

        # Check if we need to monitor for resolution changes (every RESOLUTION_CHECK_INTERVAL seconds)
        if current_resolution is not None and (current_time - _last_resolution_check) >= RESOLUTION_CHECK_INTERVAL:
            _last_resolution_check = current_time

            # Get current window size
            window_rect = ps_helper.get_genshin_window_rect()
            if window_rect:
                current_window_size = (window_rect[2] - window_rect[0], window_rect[3] - window_rect[1])  # width, height

                # Check if resolution changed significantly
                if abs(current_window_size[1] - current_resolution[1]) > RESOLUTION_CHANGE_THRESHOLD:
                    if DEBUG_MODE:
                        print(f"Detected resolution change: {current_resolution[0]}x{current_resolution[1]} -> {current_window_size[0]}x{current_window_size[1]}")

                    # Force re-detection of coordinates
                    current_resolution = None  # Reset to trigger re-initialization below

        # Initialize or re-initialize coordinates if needed
        if current_resolution is None:
            new_coordinates, new_resolution = get_dynamic_coordinates()

            # Only update if we actually got new coordinates
            if new_coordinates and new_resolution:
                current_resolution = new_resolution
                current_coordinates = new_coordinates

                # Update global coordinate variables
                NUMBER_4P_COORD = new_coordinates['NUMBER_4P_COORD']
                NAMES_4P_COORD = new_coordinates['NAMES_4P_COORD']
                BOSS_COORD = new_coordinates['BOSS_COORD']
                LOCATION_COORD = new_coordinates['LOCATION_COORD']
                MAP_LOC_COORD = new_coordinates['MAP_LOC_COORD']
                ACTIVITY_COORD = new_coordinates['ACTIVITY_COORD']
                DOMAIN_COORD = new_coordinates['DOMAIN_COORD']
                PARTY_SETUP_COORD = new_coordinates['PARTY_SETUP_COORD']

                resolution_log = f"{'Updated' if _last_resolution_check > 0 else 'Initialized'} coordinates for resolution: {new_resolution[0]}x{new_resolution[1]}"
                if resolution_log != _last_coordinate_log:
                    print(resolution_log)
                    _last_coordinate_log = resolution_log

                return True

    except Exception as e:
        if DEBUG_MODE:
            print(f"Error {'updating' if current_resolution else 'initializing'} coordinates: {e}")

    return False

current_active_character = 0  # 1-indexed. 0 is undetectable/game paused.
last_active_character = 0  # Remember the last detected active character

# TODO: Support variable number of characters.
current_characters: list[Character] = [None, None, None, None]

prev_non_idle_activity: Activity = Activity(ActivityType.LOADING, False)
"""
Stores most recent non-idle activity.

Non-idle activities are:
- Loading (assumes travelling in unknown location)
- Location
- Domain
- Commissions
- World Boss
"""

prev_location: Optional[Location] = None
"""
Stores most recently visited location (assumes commissions are here).
"""

current_activity: Activity = Activity(ActivityType.LOADING, False)

game_start_time: Optional[int] = None
"""
Global session timer - tracks total time since gameplay started
"""

current_timer_type = "global"
"""
Tracks which timer should be used for Rich Presence:
- "global": Use game_start_time (total session time)
- "activity": Use current_activity.start_time (activity-specific time)
- "menu": Use a menu-specific timer
"""

menu_start_time: Optional[int] = None
"""
Timer for menu activities - starts when entering menus, returns to global when exiting
"""

game_paused = False
"""
True if the game is found to be paused in the previous iteration

(May not be accurate. Commit pause/resume state if game_pause_state_cooldown == 0)
"""

game_pause_state_cooldown = 0
"""
Only commit game paused/unpaused to `current_activity` if game_pause_state_cooldown == 0.

This value gets set to `CONFIG.PAUSE_STATE_COOLDOWN` when game is detected as paused/unpaused.
"""

game_pause_state_displayed = False
"""
Shows the last displayed game pause state.
(Needed to prevent spamming console with the same game paused/resumed message).
"""

inactive_detection_cooldown = 0
"""
In non-active charcter detection mode, limit other detections if some inactive action is detected.

(Inactive refers to no active characters detectable, e.g. party setup/domain name/map teleporter location)

This value gets set to `CONFIG.INACTIVE_COOLDOWN` when party setup screen is detected,
and decremented each iteration.

Reduces CPU and prevent incorrect domain detection.
"""

inactive_detection_mode: Optional[ActivityType] = None
"""
What was the inactive activity that was last detected.
"""

reload_party_flag = False
"""
Set to True after party setup screen is detected.

Forces character names to be reloaded once active gameplay is detected.
"""

# GUI callback for compatibility with GUI version
gui_callback = None
"""
Callback function for GUI notifications when activities change.
Set to None if running without GUI.
"""

# Global variables for GUI communication
gui_shared_state = {
    'current_activity': None,
    'current_active_character': 0,
    'current_characters': [None, None, None, None],
    'game_start_time': None,
    'pause_ocr': False
}

def get_gui_state():
    """Get current state for GUI"""
    return {
        'current_activity': current_activity,
        'current_active_character': current_active_character,
        'current_characters': current_characters,
        'game_start_time': game_start_time,
        'pause_ocr': pause_ocr
    }

def main_loop():
    """Main loop function that can be called by GUI"""
    global loop_count
    shared_file = os.getenv('GUI_SHARED_DATA_FILE')
    if shared_file:
        try:
            data_to_write = {
                'timestamp': time.time(),
                'current_activity': current_activity,
                'current_characters': current_characters,
                'game_start_time': game_start_time,
                'pause_ocr': pause_ocr
            }
            with open(shared_file, 'w') as f:
                json.dump(data_to_write, f, default=str)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error writing to shared file: {e}")

    # Break if we need to stop (for testing)
    if not getattr(gui_callback, '_running', True):
        return

    # Update GUI shared state
    gui_shared_state.update({
        'current_activity': current_activity,
        'current_active_character': current_active_character,
        'current_characters': current_characters,
        'game_start_time': game_start_time,
        'pause_ocr': pause_ocr
    })

    # Call GUI callback if set
    if gui_callback:
        try:
            gui_callback(current_activity)
        except Exception as e:
            if DEBUG_MODE:
                print(f"GUI callback error: {e}")

    # Sleep for a short time to prevent busy waiting
    time.sleep(0.1)

#
#  RPC-SETUP
#                                                                    
rpc_event_loop = new_event_loop()


def discord_rpc_loop():
    set_event_loop(rpc_event_loop)
    rpc: discord.Presence = None

    def init_discord_rpc():
        nonlocal rpc

        printed_wait = False
        while True:
            try:
                rpc = discord.Presence(DISC_APP_ID)
                rpc.connect()
                print("Connected to Discord Client!")
                break
            except discord.exceptions.DiscordNotFound:
                if not printed_wait:
                    printed_wait = True
                    print("Waiting for discord to start...")
                time.sleep(2.5)
            except Exception as e:
                print("Unknown error while attempting to initialize discord RPC:")
                print(e)
                time.sleep(2.5)

    previous_update = None
    """
    Contains previous parameters dict sent to rpc update function.

    Only update rpc if data is different.
    """

    updated_now = False

    while True:
        if rpc == None:
            init_discord_rpc()  # Waits for discord to open (Blocking)

        params = current_activity.to_update_params_dict()

        # Handle special markers for dynamic content
        if params.get("state") == "LOCATION_PARTY_INFO":
            # Replace with current party information
            params["state"] = f"Party: {get_party_info_string()}"
        elif params.get("state") == "MAP_PARTY_INFO":
            # Handle map location party info
            params["state"] = f"Party: {get_party_info_string()}"
        elif "PARTY_INFO_MARKER" in params.get("state", ""):
            # Handle party info marker in other activity types
            if params.get("state") == "PARTY_INFO_MARKER":
                params["state"] = f"Party: {get_party_info_string()}"
            else:
                params["state"] = params["state"].replace(" | PARTY_INFO_MARKER", f" | Party: {get_party_info_string()}")

        # Handle location details with region info for LOCATION and MAP_LOCATION activities
        if (current_activity.activity_type in [ActivityType.LOCATION, ActivityType.MAP_LOCATION]
            and current_activity.activity_data is not None
            and hasattr(current_activity.activity_data, 'subarea')
            and hasattr(current_activity.activity_data, 'country')):

            location = current_activity.activity_data
            region_info = []

            if location.subarea:
                region_info.append(location.subarea)
            if location.country:
                region_info.append(location.country)

            if region_info:
                current_details = params.get("details", "")
                combined_details = f"{current_details} ({', '.join(region_info)})"

                # Check if the combined details would be too long
                if len(combined_details) > 128:
                    # Use shortened details and put full info in tooltip
                    # Shorten to fit within reasonable limits for main text
                    base_text = "Exploring" if current_activity.activity_type == ActivityType.LOCATION else "Thinking of traveling to"
                    max_location_length = 128 - len(f"{base_text} ") - len(f" ({', '.join(region_info[:1])}...)") - 10  # Leave room for region

                    if max_location_length > 20:  # Only shorten if we can keep a reasonable amount
                        shortened_location = location.location_name[:max_location_length] + "..."
                        params["details"] = f"{base_text} {shortened_location}"
                    else:
                        # If location name is extremely long, use just the base activity
                        params["details"] = base_text

                    # Put only region/subregion info in the tooltip (large_text)
                if region_info:
                        region_text = ', '.join(region_info)

                        # Update or set the large_text for tooltip
                        if "large_text" not in params:
                            params["large_text"] = region_text
                        else:
                            # If large_text already exists, append to it
                            existing_text = params.get("large_text", "")
                            if existing_text and "Domain" not in existing_text and "Trounce" not in existing_text:
                                params["large_text"] = f"{existing_text} | {region_text}"
                            else:
                                params["large_text"] = region_text
            else:
                # If it fits within 128 characters, use the combined details
                params["details"] = combined_details

        # Smart timer selection based on activity type
        if current_timer_type == "global" and game_start_time != None:
            params["start"] = game_start_time
        elif current_timer_type == "activity":
            params["start"] = current_activity.start_time
        elif current_timer_type == "menu" and menu_start_time != None:
            params["start"] = menu_start_time
        elif game_start_time != None:
            params["start"] = game_start_time  # fallback to global

        if last_active_character != 0:
            c = current_characters[last_active_character - 1]
            if c != None:
                params["small_image"] = c.image_key
                params["small_text"] = f"playing {c.character_display_name}"

        if previous_update != params:
            try:
                # print(f'updated rpc: {params}')
                rpc.update(**params)
                previous_update = params
                updated_now = True
            except discord.exceptions.InvalidID:
                # Discord closed mid game. Need to create a new Presence client connection instance.
                rpc.close()
                rpc = None
                continue
            except Exception as e:
                print("Error updating Discord RPC:")
                print(e)
        else:
            updated_now = False

        if updated_now:
            # Rate limit for UpdateActivity RPC is 5 updates / 20 seconds.
            time.sleep(5)
        else:
            # If no update sent, it's safe to increase refresh rate to check for changes in current activity.
            time.sleep(1)


rpc_thread = threading.Thread(daemon=True, target=discord_rpc_loop)
rpc_thread.start()


"""

PRIMARY LOOP
                                                                                                      
"""

print("Initializing OCR.")
reader = ocr_engine.Reader(["en"], gpu=USE_GPU)
print("OCR started.")
print("_______________________________________________________________")

pause_ocr = False
"""
Set to true when genshin is minimized.
"""

ps_window_thread_instance: threading.Thread = None


def update_genshin_open_status():
    global pause_ocr

    window_open = ps_helper.check_process_window_open(GENSHIN_WINDOW_CLASS, GENSHIN_WINDOW_NAME)
    genshin_active = ps_helper.check_genshin_is_foreground()

    if window_open and genshin_active and pause_ocr:
        pause_ocr = False
        print("GenshinImpact.exe resumed. Resuming OCR.")
    elif (not window_open or not genshin_active) and not pause_ocr:
        pause_ocr = True
        if not window_open:
            print("GenshinImpact.exe minimized/closed. Pausing OCR.")
        else:
            print("GenshinImpact.exe lost focus. Pausing OCR.")


loop_count = 0

while True:
    # Initialize/update coordinates on first run and periodically check for resolution changes
    if loop_count == 0 or loop_count % (RESOLUTION_CHECK_INTERVAL * 10) == 0:  # Check every ~10 minutes (60*10 seconds)
        update_coordinates_if_needed()

    if pause_ocr:
        # When Genshin is minimized/closed, sleep much longer to reduce CPU usage
        time.sleep(3)  # Sleep 3 seconds when completely minimized

        # Check window status less frequently when inactive
        if loop_count % 3 == 0:  # Check every 3 iterations when paused
            if (
                ps_window_thread_instance == None
                or not ps_window_thread_instance.is_alive()
            ):
                ps_window_thread_instance = threading.Thread(
                    target=update_genshin_open_status,
                    daemon=True,
                )
                ps_window_thread_instance.start()
        continue

    try:
        charnumber_cap = [
            ImageGrab.grab(
                bbox=(
                    NUMBER_4P_COORD[i][0],
                    NUMBER_4P_COORD[i][1],
                    NUMBER_4P_COORD[i][0] + 1,
                    NUMBER_4P_COORD[i][1] + 1,
                )
            ).getpixel((0, 0))
            for i in range(4)
        ]
    except OSError:
        print(
            "OSError: Cannot capture screen. Try running as admin if this issue persists."
        )
        time.sleep(1)
        continue

    charnumber_brightness = [sum(rgb) for rgb in charnumber_cap]
    active_character = [
        idx
        for idx, bri in enumerate(charnumber_brightness)
        if bri < ACTIVE_CHARACTER_THRESH
    ]
    found_active_character = len(active_character) == 1

    # Dynamic sleep timing based on game state for better CPU efficiency
    if not found_active_character:
        # In menus or party setup - use medium sleep time
        dynamic_sleep = 0.5  # 500ms when in menus (vs 140ms when actively playing)
    else:
        # Actively playing - use normal fast timing
        dynamic_sleep = SLEEP_PER_ITERATION  # 140ms when actively playing

    if found_active_character and active_character[0] + 1 != current_active_character:
        if current_activity.activity_type == ActivityType.LOADING:
            current_activity.activity_data = True

        current_active_character = active_character[0] + 1
        last_active_character = current_active_character  # Remember the last active character
        if current_characters[current_active_character - 1] != None:
            print(
                f'Switched active character to "{current_characters[current_active_character - 1].character_display_name}"'
            )
            # Notify GUI of character change
            if gui_callback:
                try:
                    gui_callback(current_activity)
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"GUI callback error: {e}")

    if not found_active_character:
        # Only reset current_active_character during actual loading, not when in menus
        if current_activity.activity_type == ActivityType.LOADING:
            current_active_character = 0

        if loop_count % 8 == 0 and (
            ps_window_thread_instance == None
            or not ps_window_thread_instance.is_alive()
        ):
            ps_window_thread_instance = threading.Thread(
                target=update_genshin_open_status,
                daemon=True,
            )
            ps_window_thread_instance.start()

    # Initialize curr_game_paused - will be set to False if active character found
    curr_game_paused = True

    if found_active_character:
        curr_game_paused = False  # Active character found, so game is not paused
        inactive_detection_cooldown = 0  # reset anti-domain read cooldown
        inactive_detection_mode = None  # reset inactive detection mode

        if current_activity.is_idle():
            # Restore previous activity once an active character is detected.
            current_activity = prev_non_idle_activity

    # _____________________________________________________________________
    #
    # CAPTURE PARTY MEMBERS
    # _____________________________________________________________________

    if (
        loop_count % OCR_CHARNAMES_ONE_IN == 0
        or len([a for a in current_characters if a == None]) > 0
        or reload_party_flag
    ):
        reload_party_flag = False

        for character_index in range(4):
            char_data = capture_and_process_ocr(
                NAMES_4P_COORD[character_index],
                ALLOWLIST,
                NAME_CONF_THRESH,
                ActivityType.LOCATION,  # Placeholder, not used for characters
                lambda text: DATA.search_character(text),
                debug_key='CHARNAME'
            )
            if char_data and (current_characters[character_index] == None or char_data != current_characters[character_index]):
                current_characters[character_index] = char_data
                char_log = f"Detected character {character_index + 1}: {char_data.character_display_name}"
                if char_log != _last_character_logs[character_index]:
                    print(char_log)
                    _last_character_logs[character_index] = char_log

        # _____________________________________________________________________
        #
        # CAPTURE LOCATION
        # _____________________________________________________________________

        if loop_count % OCR_LOC_ONE_IN == 0:
            def loc_text_processor(text):
                if "mission accept" in text.lower():
                    return "COMMISSION"
                return text

            loc_data = capture_and_process_ocr(
                LOCATION_COORD,
                ALLOWLIST,
                LOC_CONF_THRESH,
                ActivityType.LOCATION,
                lambda text: DATA.search_location(text) if text != "COMMISSION" else None,
                text_processor=loc_text_processor,
                debug_key='LOCATION'
            )
            if loc_data:
                if loc_data == "COMMISSION":
                    if current_activity.activity_type != ActivityType.COMMISSION:
                        current_activity = Activity(ActivityType.COMMISSION, prev_location)
                        commission_log = "Detected doing commissions"
                        if commission_log != _last_activity_log:
                            print(commission_log)
                            _last_activity_log = commission_log
                            if gui_callback:
                                try:
                                    gui_callback(current_activity)
                                except Exception as e:
                                    if DEBUG_MODE:
                                        print(f"GUI callback error: {e}")
                else:
                    location = loc_data
                    if (
                        current_activity.activity_type != ActivityType.LOCATION
                        or current_activity.activity_data.search_str != location.search_str
                    ):
                        current_activity = Activity(ActivityType.LOCATION, location)
                        prev_location = location
                        location_log = f"Detected location: {location.location_name}"
                        if location_log != _last_location_log:
                            print(location_log)
                            _last_location_log = location_log
                            if gui_callback:
                                try:
                                    gui_callback(current_activity)
                                except Exception as e:
                                    if DEBUG_MODE:
                                        print(f"GUI callback error: {e}")

        # _____________________________________________________________________
        #
        # CAPTURE BOSS
        # _____________________________________________________________________

        if loop_count % OCR_BOSS_ONE_IN == 0:
            boss_data = capture_and_process_ocr(
                BOSS_COORD,
                ALLOWLIST,
                LOC_CONF_THRESH,
                ActivityType.WORLD_BOSS,
                DATA.search_boss,
                debug_key='BOSS'
            )
            if boss_data and (
                current_activity.activity_type != ActivityType.WORLD_BOSS
                or current_activity.activity_data.search_str != boss_data.search_str
            ):
                current_activity = Activity(ActivityType.WORLD_BOSS, boss_data)
                current_timer_type = "activity"  # Boss fights use activity-specific timer
                boss_log = f"Detected boss: {boss_data.boss_name}"
                if boss_log != _last_activity_log:
                    print(boss_log)
                    _last_activity_log = boss_log
                    if gui_callback:
                        try:
                            gui_callback(current_activity)
                        except Exception as e:
                            if DEBUG_MODE:
                                print(f"GUI callback error: {e}")

    # Check if we should run inactive detections (party setup, domain, map location, etc.)
    # This runs when no active character is found OR when we want to check for map location
    should_check_inactive = not found_active_character or (
        found_active_character and
        inactive_detection_cooldown == 0 and
        inactive_detection_mode == ActivityType.MAP_LOCATION
    )

    if should_check_inactive:
        curr_game_paused = True  # Set False later if domain/party setup detected.

        if inactive_detection_cooldown > 0:
            inactive_detection_cooldown -= 1

        # _____________________________________________________________________
        #
        # CAPTURE PARTY SETUP/OTHER TEXT
        # _____________________________________________________________________

        if (
            inactive_detection_cooldown == 0
            or inactive_detection_mode == ActivityType.PARTY_SETUP
        ):
            party_data = capture_and_process_ocr(
                PARTY_SETUP_COORD,
                ALLOWLIST,
                LOC_CONF_THRESH,
                ActivityType.PARTY_SETUP,
                lambda text: "party setup" in text.lower(),
                debug_key='PARTY_SETUP'
            )
            if party_data:
                curr_game_paused = False
                inactive_detection_cooldown = INACTIVE_COOLDOWN
                inactive_detection_mode = ActivityType.PARTY_SETUP
                if current_activity.activity_type != ActivityType.PARTY_SETUP:
                    current_activity = Activity(ActivityType.PARTY_SETUP, prev_non_idle_activity)
                    reload_party_flag = True
                    print(f"Entered Party Setup")
                    if gui_callback:
                        try:
                            gui_callback(current_activity)
                        except Exception as e:
                            if DEBUG_MODE:
                                print(f"GUI callback error: {e}")

        # _____________________________________________________________________
        #
        # CAPTURE DOMAIN
        # _____________________________________________________________________

        if (
            inactive_detection_cooldown == 0
            or inactive_detection_mode == ActivityType.DOMAIN
        ):
            domain_data = capture_and_process_ocr(
                DOMAIN_COORD,
                ALLOWLIST,
                LOC_CONF_THRESH,
                ActivityType.DOMAIN,
                DATA.search_domain,
                debug_key='DOMAIN'
            )
            if domain_data and (
                current_activity.activity_type != ActivityType.DOMAIN
                or current_activity.activity_data.search_str != domain_data.search_str
            ):
                curr_game_paused = False
                inactive_detection_cooldown = INACTIVE_COOLDOWN
                inactive_detection_mode = ActivityType.DOMAIN
                current_activity = Activity(ActivityType.DOMAIN, domain_data)
                current_timer_type = "activity"  # Domains use activity-specific timer
                domain_log = f"Detected domain: {current_activity.activity_data.domain_name}"
                if domain_log != _last_activity_log:
                    print(domain_log)
                    _last_activity_log = domain_log
                    if gui_callback:
                        try:
                            gui_callback(current_activity)
                        except Exception as e:
                            if DEBUG_MODE:
                                print(f"GUI callback error: {e}")

        # _____________________________________________________________________
        #
        # CAPTURE GAMEMENU
        # _____________________________________________________________________

        if (
            inactive_detection_cooldown == 0
            or inactive_detection_mode == ActivityType.GAMEMENU
        ):
            gamemenu_data = capture_and_process_ocr(
                PARTY_SETUP_COORD,  # Note: Uses PARTY_SETUP_COORD for gamemenu
                ALLOWLIST2,
                LOC_CONF_THRESH,
                ActivityType.GAMEMENU,
                DATA.search_gamemenu,
                debug_key='GAMEMENU'
            )
            if gamemenu_data and (
                current_activity.activity_type != ActivityType.GAMEMENU
                or current_activity.activity_data.search_str != gamemenu_data.search_str
            ):
                current_activity = Activity(ActivityType.GAMEMENU, gamemenu_data)
                current_timer_type = "menu"  # Activity region menus use menu timer
                menu_start_time = time.time()  # Start menu timer
                curr_game_paused = False
                inactive_detection_cooldown = INACTIVE_COOLDOWN
                inactive_detection_mode = ActivityType.GAMEMENU
                activity_log = f"Detected gamemenu activity: {gamemenu_data.gamemenu_name}"
                if activity_log != _last_activity_log:
                    print(activity_log)
                    _last_activity_log = activity_log

        # _____________________________________________________________________
        #
        # CAPTURE ACTIVITY
        # _____________________________________________________________________

        if (
            inactive_detection_cooldown == 0
            or inactive_detection_mode == ActivityType.LOCATION
        ):
            activity_data = capture_and_process_ocr(
                ACTIVITY_COORD,
                ALLOWLIST,
                LOC_CONF_THRESH,
                ActivityType.GAMEMENU,  # Can detect gamemenu here too
                DATA.search_gamemenu,
                debug_key='ACTIVITY'
            )
            if activity_data and (
                current_activity.activity_type != ActivityType.GAMEMENU
                or current_activity.activity_data.search_str != activity_data.search_str
            ):
                current_activity = Activity(ActivityType.GAMEMENU, activity_data)
                current_timer_type = "menu"  # Activity region menus use menu timer
                menu_start_time = time.time()  # Start menu timer
                curr_game_paused = False
                inactive_detection_cooldown = INACTIVE_COOLDOWN
                inactive_detection_mode = ActivityType.GAMEMENU
                activity_log = f"Detected gamemenu activity: {activity_data.gamemenu_name}"
                if activity_log != _last_activity_log:
                    print(activity_log)
                    _last_activity_log = activity_log

        # _____________________________________________________________________
        #
        # CAPTURE MAP LOCATION
        # _____________________________________________________________________

        if (
            inactive_detection_cooldown == 0
            or inactive_detection_mode == ActivityType.MAP_LOCATION
        ) and not found_active_character:  # Only check map location when no active character (saves CPU)
            def map_text_processor(text):
                comma_idx = text.find(",")
                if comma_idx != -1:
                    text = text[:comma_idx]
                return text

            map_loc_data = capture_and_process_ocr(
                MAP_LOC_COORD,
                ALLOWLIST + ",",  # Include comma for city name omission
                LOC_CONF_THRESH,
                ActivityType.MAP_LOCATION,
                DATA.search_location,
                text_processor=map_text_processor,
                debug_key='MAP_LOC'
            )
            if map_loc_data and (
                current_activity.activity_type != ActivityType.MAP_LOCATION
                or current_activity.activity_data.search_str != map_loc_data.search_str
            ):
                current_activity = Activity(ActivityType.MAP_LOCATION, map_loc_data)
                prev_location = map_loc_data
                curr_game_paused = False
                inactive_detection_cooldown = INACTIVE_COOLDOWN
                inactive_detection_mode = ActivityType.MAP_LOCATION
                map_location_log = f"Thinking of traveling to: {map_loc_data.location_name}"
                if map_location_log != _last_location_log:
                    print(map_location_log)
                    _last_location_log = map_location_log

        time.sleep(0.1)  # Inactive mode doesn't require high refresh rate.

    if game_pause_state_cooldown > 0:
        game_pause_state_cooldown -= 1

    if curr_game_paused != game_paused:
        game_pause_state_cooldown = PAUSE_STATE_COOLDOWN
        game_paused = curr_game_paused
    elif (
        game_pause_state_cooldown == 0
        and curr_game_paused != game_pause_state_displayed
    ):
        if curr_game_paused:
            current_activity = Activity(ActivityType.PAUSED, prev_non_idle_activity)
            print("Game paused.")
        else:
            print("Game resumed.")

        game_pause_state_displayed = curr_game_paused

    if not current_activity.is_idle():
        prev_non_idle_activity = current_activity

    if (
        current_activity.activity_type != ActivityType.LOADING
        or current_activity.activity_data
    ) and game_start_time == None:
        game_start_time = time.time()

# Write data to shared file for GUI if environment variable is set
    shared_file = os.getenv('GUI_SHARED_DATA_FILE')
    if shared_file:
        try:
            # Convert Activity object to dict for JSON serialization
            activity_dict = None
            if current_activity:
                # Convert activity_data to serializable format
                activity_data_serialized = None
                if current_activity.activity_data:
                    if hasattr(current_activity.activity_data, '__dict__'):
                        # It's a dataclass/object with attributes - convert to dict
                        activity_data_dict = {}
                        for key, value in current_activity.activity_data.__dict__.items():
                            # Handle enum values
                            if hasattr(value, 'value'):
                                activity_data_dict[key] = value.value
                            elif hasattr(value, 'name'):
                                activity_data_dict[key] = value.name
                            else:
                                activity_data_dict[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value
                        activity_data_serialized = activity_data_dict
                    else:
                        # It's a primitive type
                        activity_data_serialized = current_activity.activity_data

                # Handle activity_type enum
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
                        'search_str': char.search_str
                    })
                else:
                    characters_dict.append(None)

            data_to_write = {
                'timestamp': time.time(),
                'current_activity': activity_dict,
                'current_characters': characters_dict,
                'current_active_character': current_active_character,
                'game_start_time': game_start_time,
                'pause_ocr': pause_ocr
            }
            with open(shared_file, 'w') as f:
                json.dump(data_to_write, f)
            if DEBUG_MODE:
                print(f"✅ Wrote shared data to {shared_file}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Error writing to shared file: {e}")
    
    time.sleep(dynamic_sleep)  # Use dynamic sleep timing based on game state
