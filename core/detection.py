"""Detection loop and game state detection logic."""

import json
import os
import time
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from core import ps_helper
from PIL import ImageGrab
import numpy as np

from core.datatypes import Activity, ActivityType, Character, Data, DEBUG_MODE
from CONFIG import DEBUG_CHARACTER_MODE
from CONFIG import (
    ACTIVE_CHARACTER_THRESH,
    SLEEP_PER_ITERATION,
    OCR_CHARNAMES_ONE_IN,
    OCR_LOC_ONE_IN,
    OCR_BOSS_ONE_IN,
    PAUSE_STATE_COOLDOWN,
    INACTIVE_COOLDOWN,
    NUMBER_4P_COORD,
    LOCATION_COORD,
    BOSS_COORD,
    DOMAIN_COORD,
    PARTY_SETUP_COORD,
    MAP_LOC_COORD,
    ACTIVITY_COORD,
    ALLOWLIST,
    ALLOWLIST2,
    LOC_CONF_THRESH,
    BOSS_CONF_THRESH,
    DOMAIN_CONF_THRESH,
    NAME_CONF_THRESH,
    GENSHIN_WINDOW_CLASS,
    GENSHIN_WINDOW_NAME,
    get_dynamic_coordinates,
)
from core.state import (
    current_active_character,
    last_active_character,
    current_activity,
    prev_non_idle_activity,
    prev_location,
    game_start_time,
    game_paused,
    game_pause_state_cooldown,
    game_pause_state_displayed,
    current_timer_type,
    menu_start_time,
    ingame_pause_ocr,
    inactive_detection_cooldown,
    inactive_detection_mode,
    reload_party_flag,
    current_resolution,
    current_coordinates,
    _last_coordinate_log,
    _last_resolution_check,
    _last_location_log,
    _last_activity_log,
    gui_callback,
    shutdown_event,
    state_lock,
    update_activity,
    set_active_character,
    update_character,
    get_current_characters,
)
import core.state
import core.state as state_module
import core.datatypes as character_datatypes
from core.ocr_utils import capture_and_process_ocr
from core.character_detection import CharacterRegionManager

if TYPE_CHECKING:
    from ocr_engine import Reader


# Resolution monitoring constants
RESOLUTION_CHECK_INTERVAL = 60  # Check every 60 seconds like GUI
RESOLUTION_CHANGE_THRESHOLD = 10  # 10px threshold for resolution change

# Shared config path (defined locally since it's runtime-dependent)
script_dir = Path(__file__).resolve().parent.parent
shared_config_path = script_dir / "shared_config.json"


def search_character_with_custom(DATA, text, custom_username, character_images=None):
    """Search for character, checking custom name first, then database"""
    # First check if text matches custom username (Traveler)
    if custom_username and text.strip().lower() == custom_username.strip().lower():
        # Create a custom character entry with flexible image key
        # Use custom image key if provided, otherwise default to traveler based on MC_AETHER setting
        if character_images and custom_username in character_images:
            image_key = character_images[custom_username]
        else:
            # Default to appropriate traveler image based on MC_AETHER setting
            # Read MC_AETHER from shared config if available, otherwise use CONFIG default
            mc_aether = True  # Default fallback
            try:
                if shared_config_path.exists():
                    with open(shared_config_path, "r") as f:
                        config_data = json.load(f)
                        mc_aether = config_data.get("MC_AETHER", True)
            except Exception:
                pass  # Use default if config read fails

            image_key = "char_aether" if mc_aether else "char_lumine"

        return Character(
            character_display_name=custom_username,
            image_key=image_key,
            search_str=text.lower(),
        )

    # Fall back to database lookup for all other characters
    char_data = DATA.search_character(text)
    if char_data:
        return char_data

    # If no database match, create a generic character entry for unmatched names
    # This maintains backward compatibility for characters not in the database yet
    return Character(
        character_display_name=text,
        image_key="char_unknown",  # Use a default unknown icon
        search_str=text.lower(),
    )


def detect_characters_with_adaptation(reader, DATA, character_region_manager):
    """Detect characters using adaptive slot detection."""
    # Store previous character data before detection using thread-safe accessor
    previous_characters = get_current_characters()

    # Detect which slots are occupied
    occupied_slots, confidence_scores = character_region_manager.detect_occupied_slots()

    # Get custom character name and image mappings from shared config
    custom_username = None
    character_images = {}  # Maps character names to image keys
    try:
        if shared_config_path.exists():
            with open(shared_config_path, "r") as f:
                shared_config = json.load(f)
                custom_username = shared_config.get("USERNAME")

                # Hot-swap custom character names (GUI can change these live)
                for cfg_key in ("WANDERER_NAME", "MANEKIN_NAME", "MANEKINA_NAME"):
                    val = shared_config.get(cfg_key)
                    if isinstance(val, str) and val.strip() and val != getattr(
                        character_datatypes, cfg_key, None
                    ):
                        setattr(character_datatypes, cfg_key, val.strip())

                # Support flexible character image mapping
                if "CHARACTER_IMAGES" in shared_config:
                    character_images = shared_config["CHARACTER_IMAGES"]
                else:
                    # Legacy support for MC_AETHER setting
                    mc_aether = shared_config.get("MC_AETHER", True)
                    traveler_image = "char_aether" if mc_aether else "char_lumine"
                    if custom_username:
                        character_images[custom_username] = traveler_image

    except (OSError, RuntimeError, ValueError) as e:
        if DEBUG_MODE:
            print(f"[WARNING] Config read error: {e}")
        # Continue with defaults - non-critical error

    # Update character data for occupied slots
    characters_updated = False
    detected_char_count = sum(1 for slot in occupied_slots if slot is not None)
    found_valid_characters_this_cycle = False

    for slot_idx, char_idx in enumerate(occupied_slots):
        if char_idx is not None:
            coords = character_region_manager.current_name_positions[char_idx]

            # Use existing OCR logic with adapted coordinates
            char_data = capture_and_process_ocr(
                reader,
                coords,
                ALLOWLIST,
                NAME_CONF_THRESH,
                ActivityType.LOCATION,  # Placeholder
                lambda text: search_character_with_custom(
                    DATA, text, custom_username, character_images
                ),
                debug_key=f"CHAR_ADAPT_{char_idx}",
            )

            if char_data:
                # Validate that the OCR result is a legitimate character from the database
                if char_data.image_key != "char_unknown":
                    # This is a validated character from the database
                    found_valid_characters_this_cycle = True
                    if DEBUG_MODE and DEBUG_CHARACTER_MODE:
                        char_names = [
                            char.character_display_name if char else None
                            for char in previous_characters
                        ]
                        print(
                            f"[DEBUG] current_characters before JSON write: {char_names}"
                        )
                    if previous_characters[char_idx] != char_data:
                        print(f"[DEBUG] About to call update_character for slot {char_idx} with {char_data.character_display_name}")
                        update_character(char_idx, char_data)
                        print(
                            f"[OK] Detected character {char_idx + 1}: {char_data.character_display_name}"
                        )
                        characters_updated = True
                else:
                    # OCR detected text but it doesn't match any known character
                    if DEBUG_MODE:
                        print(
                            f"[WARNING] OCR detected '{char_data.character_display_name}' in slot {char_idx + 1}, but no database match found"
                        )
                    # Don't update with unknown characters - keep cached if exists
            else:
                # Only clear if we had a character before and OCR completely failed
                if previous_characters[char_idx] is not None:
                    if DEBUG_MODE:
                        print(
                            f"[WARNING] Failed to detect character in slot {char_idx + 1}, keeping previous data"
                        )
        else:
            # Don't clear unoccupied slots - preserve previously detected characters
            # OCR may temporarily fail to detect a character even if they're still in the party
            # Only clear when we have strong evidence the party configuration actually changed
            pass

    # If no characters were successfully detected at all, mark cache as invalid
    # This allows map location detection to run when no valid characters present
    if DEBUG_MODE:
        print(
            f"DEBUG: found_valid_characters_this_cycle={found_valid_characters_this_cycle}, current_characters={previous_characters}"
        )
    if not found_valid_characters_this_cycle:
        with state_lock:
            state_module.currently_active_characters_valid = False
        if any(previous_characters):
            if DEBUG_MODE:
                print(
                    "[REFRESH] No valid characters detected this cycle, marking cache invalid for map detection"
                )
    elif found_valid_characters_this_cycle:
        with state_lock:
            state_module.currently_active_characters_valid = True
        if DEBUG_MODE:
            print("[REFRESH] Valid characters detected this cycle, marking as active")

    # Log adaptation summary
    if DEBUG_MODE and any(c != 0 for c in confidence_scores):
        active_slots = [
            i for i, char in enumerate(core.state.current_characters) if char is not None
        ]
        print(f"[ACTIVE] Active character slots detected: {active_slots}")


def update_coordinates_if_needed(character_region_manager=None):
    """
    Checks if Genshin window resolution has changed and updates coordinates accordingly.
    Called both for initialization and for continuous monitoring.
    """
    global NUMBER_4P_COORD, NAMES_4P_COORD, BOSS_COORD, LOCATION_COORD
    global MAP_LOC_COORD, ACTIVITY_COORD, DOMAIN_COORD, PARTY_SETUP_COORD

    try:
        current_time = time.time()

        # Check if we need to monitor for resolution changes (every RESOLUTION_CHECK_INTERVAL seconds)
        if (
            state_module.current_resolution is not None
            and (current_time - state_module._last_resolution_check) >= RESOLUTION_CHECK_INTERVAL
        ):
            state_module._last_resolution_check = current_time

            # Get current window size
            window_rect = ps_helper.get_genshin_window_rect()
            if window_rect:
                current_window_size = (
                    window_rect[2] - window_rect[0],
                    window_rect[3] - window_rect[1],
                )  # width, height

                # Check if resolution changed significantly
                if (
                    abs(current_window_size[1] - state_module.current_resolution[1])
                    > RESOLUTION_CHANGE_THRESHOLD
                ):
                    if DEBUG_MODE:
                        print(
                            f"Detected resolution change: {state_module.current_resolution[0]}x{state_module.current_resolution[1]} -> {current_window_size[0]}x{current_window_size[1]}"
                        )

                    # Force re-detection of coordinates
                    state_module.current_resolution = (
                        None  # Reset to trigger re-initialization below
                    )
            else:
                state_module.current_resolution = None

        # Initialize or re-initialize coordinates if needed
        if state_module.current_resolution is None:
            new_coordinates, new_resolution = get_dynamic_coordinates()

            # Only update if we actually got new coordinates
            if new_coordinates and new_resolution:
                state_module.current_resolution = new_resolution
                state_module.current_coordinates = new_coordinates

                # Update global coordinate variables
                NUMBER_4P_COORD = new_coordinates["NUMBER_4P_COORD"]
                NAMES_4P_COORD = new_coordinates["NAMES_4P_COORD"]
                BOSS_COORD = new_coordinates["BOSS_COORD"]
                LOCATION_COORD = new_coordinates["LOCATION_COORD"]
                MAP_LOC_COORD = new_coordinates["MAP_LOC_COORD"]
                ACTIVITY_COORD = new_coordinates["ACTIVITY_COORD"]
                DOMAIN_COORD = new_coordinates["DOMAIN_COORD"]
                PARTY_SETUP_COORD = new_coordinates["PARTY_SETUP_COORD"]

                # Reset character region manager with new coordinates
                if character_region_manager and hasattr(
                    character_region_manager, "init_from_coordinates"
                ):
                    character_region_manager.init_from_coordinates()

                resolution_log = f"{'Updated' if state_module._last_resolution_check > 0 else 'Initialized'} coordinates for resolution: {new_resolution[0]}x{new_resolution[1]}"
                if resolution_log != state_module._last_coordinate_log:
                    print(resolution_log)
                    state_module._last_coordinate_log = resolution_log

                return True

    except (OSError, RuntimeError, ValueError) as e:
        if DEBUG_MODE:
            print(
                f"Error {'updating' if state_module.current_resolution else 'initializing'} coordinates: {e}"
            )

    return False


def _get_current_search_str():
    """Safely extract search_str from current_activity."""
    current = state_module.current_activity
    if (
        hasattr(current, "activity_data")
        and current.activity_data is not None
        and hasattr(current.activity_data, "search_str")
    ):
        return current.activity_data.search_str
    return None


def process_map_text(text, data_instance):
    """Process map location OCR text to extract location candidates."""
    if not text or not text.strip():
        return ""

    # Handle text duplication issue - remove repeated patterns
    cleaned_text = " ".join(text.replace("\n", " ").split())

    # Remove duplicated substrings
    words = cleaned_text.split()
    if (
        len(words) > 10
    ):  # Only process if we have a lot of words (indicating possible duplication)
        result_words = []
        i = 0
        while i < len(words):
            current_word = words[i]
            found_repetition = False
            for length in range(
                min(8, len(words) - i - 1), 2, -1
            ):  # Try different sequence lengths
                if i + length * 2 <= len(words):
                    seq1 = " ".join(words[i : i + length])
                    seq2 = " ".join(words[i + length : i + length * 2])
                    if (
                        seq1 == seq2 and len(seq1) > 10
                    ):  # Only remove substantial repetitions
                        if DEBUG_MODE:
                            print(
                                f"[FILTER] MAP_LOC: Found repetition, removing duplicate sequence: '{seq1}'"
                            )
                        i += length * 2  # Skip both occurrences
                        found_repetition = True
                        break
            if not found_repetition:
                result_words.append(current_word)
                i += 1
        if result_words:
            cleaned_text = " ".join(result_words)
        else:
            cleaned_text = " ".join(
                words
            )  # Fallback to original if deduplication fails

    # Split into words for better processing
    words = cleaned_text.split()
    if not words:
        return ""

    # Filter out only the most obvious OCR artifacts
    filtered_words = []
    skip_words = {
        "d",
        "that",
        "are",
        "of",
        "the",
        "and",
        "or",
        "but",
        "with",
        "for",
        "from",
        "this",
        "these",
        "those",
        "menu",
        "exit",
        "close",
        "ok",
        "cancel",
        "select",
        "ready",
        "waiting",
        "s",
        "t",
        "re",
        "ve",
        "ll",
        "m",
        "n",  # Common OCR fragments
    }

    # Keep location-related words for pattern reconstruction
    location_context_words = {"town", "city", "village"}

    for word in words:
        word_lower = word.lower()
        # Skip very short words, common artifacts, and UI words
        if (
            len(word) < 2
            or word_lower in skip_words
            or word.isdigit()
            or (
                len(word) <= 3
                and not word[0].isupper()
                and word_lower not in location_context_words
            )
        ):
            continue
        # Clean up words that end with comma but are otherwise good
        clean_word = word.rstrip(",") if word.endswith(",") and len(word) > 3 else word
        if len(clean_word) >= 2:
            filtered_words.append(clean_word)

    if not filtered_words:
        return ""

    # Try multiple candidate extractions and validate against database
    candidates = []

    # Pattern 1: Look for proper noun combinations (capitalized words)
    proper_nouns = [
        word for word in filtered_words if word[0].isupper() and len(word) > 2
    ]

    if len(proper_nouns) >= 2:
        # Try combinations of 2-3 proper nouns
        for i in range(len(proper_nouns) - 1):
            for j in range(i + 1, min(i + 3, len(proper_nouns))):
                combination = " ".join(proper_nouns[i : j + 1])
                if 5 < len(combination) < 50:  # Reasonable length for location name
                    candidates.append(combination)

    # Pattern 2: Try mixed case word combinations
    if len(filtered_words) >= 2:
        # Try 2-word combinations
        for i in range(len(filtered_words) - 1):
            combination = f"{filtered_words[i]} {filtered_words[i + 1]}"
            if 5 < len(combination) < 40:
                candidates.append(combination)

        # Try 3-word combinations if available
        if len(filtered_words) >= 3:
            for i in range(len(filtered_words) - 2):
                combination = f"{filtered_words[i]} {filtered_words[i + 1]} {filtered_words[i + 2]}"
                if 5 < len(combination) < 50:
                    candidates.append(combination)

    # Pattern 3: Single proper nouns
    for word in proper_nouns:
        if 3 < len(word) < 30:
            candidates.append(word)

    # Pattern 4: Single filtered words
    for word in filtered_words:
        if 3 < len(word) < 30:
            candidates.append(word)

    # Cross-check each candidate against the locations database
    for candidate in candidates:
        # Try exact match first
        location_match = data_instance.search_location(candidate)
        if location_match:
            if DEBUG_MODE:
                print(
                    f"[OK] MAP_LOC: Found database match for '{candidate}' -> '{location_match.location_name}'"
                )
            return candidate

        # Try partial matches with database entries
        for word in candidate.split():
            if len(word) > 3:  # Only try meaningful words
                location_match = data_instance.search_location(word)
                if location_match:
                    if DEBUG_MODE:
                        print(
                            f"[OK] MAP_LOC: Found partial database match for '{word}' in '{candidate}' -> '{location_match.location_name}'"
                        )
                    return candidate

    # No valid location found
    if DEBUG_MODE:
        print(
            f"[ERROR] MAP_LOC: No database matches found for any candidates from '{cleaned_text}'"
        )
        print(f"[ERROR] MAP_LOC: Tried candidates: {candidates}")
    # Return cleaned text instead of empty string to allow search_func to try fuzzy matching
    return cleaned_text


def run_detection_iteration(reader, DATA, character_region_manager, loop_count):
    """Run one iteration of the detection loop."""
    global _last_location_log, _last_activity_log

    # Check if Genshin is in foreground before doing any OCR operations
    if not ps_helper.check_genshin_is_foreground():
        if not state_module.ingame_pause_ocr:
            state_module.ingame_pause_ocr = True
            print("GenshinImpact.exe lost focus. Pausing OCR.")
        return 3.0  # Return sleep duration

    # Update pause_ocr status if Genshin is back in foreground
    if state_module.ingame_pause_ocr:
        state_module.ingame_pause_ocr = False
        print("GenshinImpact.exe resumed. Resuming OCR.")

    # Use adaptive number coordinates that stay paired with name positions
    adaptive_number_coords = character_region_manager.get_adaptive_number_coordinates()
    charnumber_brightness = []
    for i in range(4):
        coords = adaptive_number_coords[i]
        x1, y1, x2, y2 = coords
        # Capture full 30x30 box for brightness analysis
        image = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        try:
            # Convert to numpy array and compute mean brightness across all
            # channels. Using mean (not max) so the darker background of the
            # active character's number box lowers the average. Multiply by 3
            # to scale into the same 0-765 range as sum-of-RGB used elsewhere.
            img_array = np.array(image)
            mean_brightness = int(img_array.mean() * 3)
        finally:
            image.close()
        charnumber_brightness.append(mean_brightness)
        # Explicitly free memory
        del img_array

    # Debug: Log brightness values to see what's happening
    if (
        DEBUG_MODE and DEBUG_CHARACTER_MODE and loop_count % 50 == 0
    ):  # Log every 5 seconds
        adaptive_coords = character_region_manager.get_adaptive_number_coordinates()
        coord_strs = []
        for c in adaptive_coords:
            cx = (c[0] + c[2]) // 2
            cy = (c[1] + c[3]) // 2
            coord_strs.append(f"({cx},{cy})")
        print(f"[DEBUG] Active Character Debug - Brightness: {charnumber_brightness}")
        print(f"[DEBUG] Active Character Debug - Threshold: {ACTIVE_CHARACTER_THRESH}")
        print(f"[DEBUG] Active Character Debug - Adaptive Centers: {coord_strs}")

    # Find the slot with minimum brightness (active character has darker background)
    min_brightness = min(charnumber_brightness)
    active_character = None
    if min_brightness < ACTIVE_CHARACTER_THRESH:
        active_character = charnumber_brightness.index(min_brightness)
        found_active_character = True
    else:
        found_active_character = False

    # Debug: Log every detection to diagnose issues
    if DEBUG_MODE:
        adaptive_coords = character_region_manager.get_adaptive_number_coordinates()
        # Show center points for readability
        coord_strs = []
        for c in adaptive_coords:
            cx = (c[0] + c[2]) // 2
            cy = (c[1] + c[3]) // 2
            coord_strs.append(f"({cx},{cy})")
        print(
            f"[DEBUG] Brightness: {charnumber_brightness} | Centers: {coord_strs} | Min: {min_brightness} | Thresh: {ACTIVE_CHARACTER_THRESH} | Active slot: {active_character} | Found: {found_active_character}"
        )

    # Dynamic sleep timing based on game state for better CPU efficiency
    if not found_active_character:
        # In menus or party setup - use medium sleep time
        dynamic_sleep = 0.5  # 500ms when in menus
    else:
        # Actively playing - use normal fast timing
        dynamic_sleep = SLEEP_PER_ITERATION  # 140ms when actively playing

    with state_lock:
        _active_char_matches = (
            found_active_character and active_character + 1 != state_module.current_active_character
        )
        _is_loading = state_module.current_activity.activity_type == ActivityType.LOADING
        _is_gamemenu = state_module.current_activity.activity_type == ActivityType.GAMEMENU

    # DEBUG: Log active character detection state
    if DEBUG_MODE:
        print(f"[DEBUG] Active char detection: found={found_active_character}, active_slot={active_character}, current_active={state_module.current_active_character}, activity={state_module.current_activity.activity_type}, is_idle={state_module.current_activity.is_idle()}")

    if _active_char_matches:
        if _is_loading:
            # Signal that we've loaded
            pass  # Handled below
        elif _is_gamemenu:
            # Don't switch active character during gamemenu/cutscene
            pass
        else:
            new_char_idx = active_character + 1
            set_active_character(new_char_idx)
            # Use thread-safe accessor for current_characters
            chars = get_current_characters()
            c = chars[new_char_idx - 1]
            if c is not None:
                # Only print if we haven't already printed for this character
                if not hasattr(run_detection_iteration, "_last_printed_char"):
                    run_detection_iteration._last_printed_char = None
                if (
                    run_detection_iteration._last_printed_char
                    != c.character_display_name
                ):
                    print(f'Switched active character to "{c.character_display_name}"')
                    run_detection_iteration._last_printed_char = (
                        c.character_display_name
                    )

    # Initialize curr_game_paused - will be set to False if active character found
    curr_game_paused = True

    if found_active_character:
        curr_game_paused = False  # Active character found, so game is not paused
        with state_lock:
            state_module.inactive_detection_cooldown = 0  # reset anti-domain read cooldown
            state_module.inactive_detection_mode = None  # reset inactive detection mode

        with state_lock:
            _is_idle = state_module.current_activity.is_idle()
        if _is_idle:
            # Restore previous activity once an active character is detected.
            with state_lock:
                state_module.current_activity = state_module.prev_non_idle_activity
                if DEBUG_MODE:
                    print(f"[DEBUG] Restored prev_non_idle_activity: {state_module.current_activity.activity_type}")

    # CAPTURE PARTY MEMBERS (ADAPTIVE)
    should_detect_characters = False

    with state_lock:
        _has_missing_chars = len([a for a in core.state.current_characters if a is None]) > 0

    if state_module.reload_party_flag:
        with state_lock:
            state_module.reload_party_flag = False
        should_detect_characters = True
    elif _has_missing_chars:
        # Only run if we have missing characters AND it's the right timing
        should_detect_characters = loop_count % OCR_CHARNAMES_ONE_IN == 0
    elif character_region_manager.needs_redetection:
        # Only run intelligent redetection at specific intervals
        should_detect_characters = loop_count % OCR_CHARNAMES_ONE_IN == 0
        character_region_manager.needs_redetection = (
            False  # Reset immediately after use
        )
    elif loop_count % OCR_CHARNAMES_ONE_IN == 0:
        # Normal scheduled character detection
        should_detect_characters = True

    if should_detect_characters:
        detect_characters_with_adaptation(reader, DATA, character_region_manager)

        # Log adaptation status periodically for debugging
        if loop_count % 300 == 0:  # Every 5 minutes
            character_region_manager.log_status()

        # Update found_active_character based on validated database matches
        # If no valid characters found in database, treat as not having active characters
        with state_lock:
            if not state_module.currently_active_characters_valid:
                found_active_character = False
                if DEBUG_MODE:
                    print(
                        f"[INFO] No valid database characters detected this cycle, treating as no active characters (using cached display)"
                    )
            else:
                if DEBUG_MODE:
                    print(
                        f"[OK] Valid characters active this cycle, active character detection enabled"
                    )

        # If we have valid characters detected (party is formed) but activity is still LOADING,
        # set to "Exploring Teyvat" (LOCATION with None data) until location detection finds a specific location
        with state_lock:
            has_valid_party = state_module.currently_active_characters_valid and any(c is not None for c in core.state.current_characters)
            if has_valid_party and state_module.current_activity.activity_type == ActivityType.LOADING:
                new_activity = Activity(ActivityType.LOCATION, None)
                update_activity(new_activity)
                print(f"[DEBUG] FORCE: Set activity to 'Exploring Teyvat' (party detected, no specific location yet)")
                print(f"[DEBUG] FORCE: Party members: {[c.character_display_name if c else 'Empty' for c in core.state.current_characters]}")
                if DEBUG_MODE:
                    print(f"[OK] Set activity to 'Exploring Teyvat' (party detected, no specific location yet)")
                    print(f"[DEBUG] Party members: {[c.character_display_name if c else 'Empty' for c in core.state.current_characters]}")

        # CAPTURE LOCATION
        if loop_count % OCR_LOC_ONE_IN == 0:
            print(f"[OCR] Running location detection...")

            def loc_text_processor(text):
                if "mission accept" in text.lower():
                    return "COMMISSION"
                return text

            loc_data = capture_and_process_ocr(
                reader,
                LOCATION_COORD,
                ALLOWLIST,
                LOC_CONF_THRESH,
                ActivityType.LOCATION,
                lambda text: (
                    DATA.search_location(text) if text != "COMMISSION" else None
                ),
                text_processor=loc_text_processor,
                debug_key="LOCATION",
            )
            
            if loc_data:
                print(f"[OK] Detected location: {loc_data.location_name}")
            else:
                print(f"[OCR] Location detection: No match found")
            if loc_data:
                if loc_data == "COMMISSION":
                    if state_module.current_activity.activity_type != ActivityType.COMMISSION:
                        new_activity = Activity(ActivityType.COMMISSION, state_module.prev_location)
                        update_activity(new_activity)
                        commission_log = "Detected doing commissions"
                        if commission_log != _last_activity_log:
                            print(commission_log)
                            _last_activity_log = commission_log
                            if gui_callback:
                                try:
                                    gui_callback(new_activity)
                                except (RuntimeError, TypeError) as e:
                                    if DEBUG_MODE:
                                        print(f"GUI callback error: {e}")
                else:
                    location = loc_data
                    should_update_location = False
                    with state_lock:
                        if (
                            state_module.current_activity.activity_type != ActivityType.LOCATION
                            or _get_current_search_str() != location.search_str
                        ):
                            should_update_location = True

                    if should_update_location:
                        new_activity = Activity(ActivityType.LOCATION, location)
                        update_activity(new_activity)
                        with state_lock:
                            state_module.prev_location = location
                        location_log = f"Detected location: {location.location_name}"
                        if location_log != _last_location_log:
                            print(location_log)
                            _last_location_log = location_log
                            if gui_callback:
                                try:
                                    gui_callback(new_activity)
                                except (RuntimeError, TypeError) as e:
                                    if DEBUG_MODE:
                                        print(f"GUI callback error: {e}")

        # CAPTURE BOSS
        if loop_count % OCR_BOSS_ONE_IN == 0:
            boss_data = capture_and_process_ocr(
                reader,
                BOSS_COORD,
                ALLOWLIST,
                BOSS_CONF_THRESH,
                ActivityType.WORLD_BOSS,
                DATA.search_boss,
                debug_key="BOSS",
            )
            if boss_data:
                should_update_boss = False
                with state_lock:
                    if (
                        state_module.current_activity.activity_type != ActivityType.WORLD_BOSS
                        or _get_current_search_str() != boss_data.search_str
                    ):
                        should_update_boss = True

                if should_update_boss:
                    new_activity = Activity(ActivityType.WORLD_BOSS, boss_data)
                    update_activity(new_activity)
                    with state_lock:
                        state_module.current_timer_type = (
                            "activity"  # Boss fights use activity-specific timer
                        )
                    boss_log = f"Detected boss: {boss_data.boss_name}"
                    if boss_log != _last_activity_log:
                        print(boss_log)
                        _last_activity_log = boss_log
                        if gui_callback:
                            try:
                                gui_callback(new_activity)
                            except Exception as e:
                                if DEBUG_MODE:
                                    print(f"GUI callback error: {e}")

    # Check if we should run inactive detections
    with state_lock:
        _inactive_cooldown = state_module.inactive_detection_cooldown
        _inactive_mode = state_module.inactive_detection_mode

    should_check_inactive = not found_active_character or (
        found_active_character
        and _inactive_cooldown == 0
        and _inactive_mode == ActivityType.MAP_LOCATION
    )

    if should_check_inactive:
        curr_game_paused = True  # Set False later if domain/party setup detected.

        with state_lock:
            if state_module.inactive_detection_cooldown > 0:
                state_module.inactive_detection_cooldown -= 1

        # CAPTURE PARTY SETUP/OTHER TEXT
        if _inactive_cooldown == 0 or _inactive_mode == ActivityType.PARTY_SETUP:
            party_data = capture_and_process_ocr(
                reader,
                PARTY_SETUP_COORD,
                ALLOWLIST,
                LOC_CONF_THRESH,
                ActivityType.PARTY_SETUP,
                lambda text: "party setup" in text.lower(),
                debug_key="PARTY_SETUP",
            )
            if party_data:
                curr_game_paused = False
                with state_lock:
                    state_module.inactive_detection_cooldown = INACTIVE_COOLDOWN
                    state_module.inactive_detection_mode = ActivityType.PARTY_SETUP
                should_update_party = False
                with state_lock:
                    if state_module.current_activity.activity_type != ActivityType.PARTY_SETUP:
                        should_update_party = True
                if should_update_party:
                    new_activity = Activity(
                        ActivityType.PARTY_SETUP, state_module.prev_non_idle_activity
                    )
                    update_activity(new_activity)
                    with state_lock:
                        state_module.reload_party_flag = True
                    print("Entered Party Setup")
                    if gui_callback:
                        try:
                            gui_callback(new_activity)
                        except Exception as e:
                            if DEBUG_MODE:
                                print(f"GUI callback error: {e}")

        # CAPTURE DOMAIN
        if _inactive_cooldown == 0 or _inactive_mode == ActivityType.DOMAIN:
            domain_data = capture_and_process_ocr(
                reader,
                DOMAIN_COORD,
                ALLOWLIST,
                DOMAIN_CONF_THRESH,
                ActivityType.DOMAIN,
                DATA.search_domain,
                debug_key="DOMAIN",
            )
            if domain_data:
                should_update_domain = False
                with state_lock:
                    if (
                        state_module.current_activity.activity_type != ActivityType.DOMAIN
                        or _get_current_search_str() != domain_data.search_str
                    ):
                        should_update_domain = True

                if should_update_domain:
                    new_activity = Activity(ActivityType.DOMAIN, domain_data)
                    update_activity(new_activity)
                    with state_lock:
                        state_module.current_timer_type = (
                            "activity"  # Domains use activity-specific timer
                        )
                    domain_log = (
                        f"Detected domain: {new_activity.activity_data.domain_name}"
                    )
                    if domain_log != _last_activity_log:
                        print(domain_log)
                        _last_activity_log = domain_log
                        if gui_callback:
                            try:
                                gui_callback(new_activity)
                            except Exception as e:
                                if DEBUG_MODE:
                                    print(f"GUI callback error: {e}")

        # CAPTURE GAMEMENU
        if _inactive_cooldown == 0 or _inactive_mode == ActivityType.GAMEMENU:
            print(f"[OCR] Running gamemenu detection...")
            try:
                gamemenu_data = capture_and_process_ocr(
                    reader,
                    PARTY_SETUP_COORD,  # Note: Uses PARTY_SETUP_COORD for gamemenu
                    ALLOWLIST2,
                    LOC_CONF_THRESH,
                    ActivityType.GAMEMENU,
                    DATA.search_gamemenu,
                    debug_key="GAMEMENU",
                )
                if gamemenu_data:
                    print(f"[OK] Detected gamemenu: {gamemenu_data.gamemenu_name}")
                    should_update_gamemenu = False
                    with state_lock:
                        if (
                            state_module.current_activity.activity_type != ActivityType.GAMEMENU
                            or _get_current_search_str() != gamemenu_data.search_str
                        ):
                            should_update_gamemenu = True

                    if should_update_gamemenu:
                        new_activity = Activity(ActivityType.GAMEMENU, gamemenu_data)
                        update_activity(new_activity)
                        with state_lock:
                            state_module.current_timer_type = (
                                "menu"  # Activity region menus use menu timer
                            )
                            state_module.menu_start_time = time.time()  # Start menu timer
                        curr_game_paused = False
                        with state_lock:
                            state_module.inactive_detection_cooldown = INACTIVE_COOLDOWN
                            state_module.inactive_detection_mode = ActivityType.GAMEMENU
                else:
                    print(f"[OCR] Gamemenu detection: No match found")
            except (OSError, RuntimeError) as e:
                print(f"[ERROR] Error processing GAMEMENU detection: {e}")
                if DEBUG_MODE:
                    import traceback

                    traceback.print_exc()

        # CAPTURE MAP LOCATION
        if (
            _inactive_cooldown == 0 or _inactive_mode == ActivityType.MAP_LOCATION
        ) and not found_active_character:
            if DEBUG_MODE:
                print("DEBUG: About to capture MAP_LOC...")
            map_loc_data = capture_and_process_ocr(
                reader,
                MAP_LOC_COORD,
                ALLOWLIST + ",",  # Include comma for city name omission
                LOC_CONF_THRESH,
                ActivityType.MAP_LOCATION,
                DATA.search_location,
                text_processor=lambda text: process_map_text(text, DATA),
                debug_key="MAP_LOC",
            )
            if DEBUG_MODE:
                print(f"DEBUG: MAP_LOC capture returned: {map_loc_data}")
            if map_loc_data:
                if DEBUG_MODE:
                    print(
                        f"DEBUG: About to update activity with MAP_LOC: {map_loc_data.location_name}"
                    )
                # Check if we need to update (outside lock to avoid nested locking)
                should_update = False
                with state_lock:
                    if (
                        state_module.current_activity.activity_type != ActivityType.MAP_LOCATION
                        or _get_current_search_str() != map_loc_data.search_str
                    ):
                        should_update = True

                if should_update:
                    new_activity = Activity(ActivityType.MAP_LOCATION, map_loc_data)
                    if DEBUG_MODE:
                        print(f"DEBUG: Created new activity: {new_activity}")
                    update_activity(new_activity)
                    if DEBUG_MODE:
                        print("DEBUG: Activity updated successfully")
                    with state_lock:
                        state_module.prev_location = map_loc_data
                    curr_game_paused = False
                    with state_lock:
                        state_module.inactive_detection_cooldown = INACTIVE_COOLDOWN
                        state_module.inactive_detection_mode = ActivityType.MAP_LOCATION

                    # Format location with subregion and region information
                    location_parts = []
                    if map_loc_data.location_name:
                        location_parts.append(map_loc_data.location_name)
                    if hasattr(map_loc_data, "subarea") and map_loc_data.subarea:
                        location_parts.append(map_loc_data.subarea)
                    if hasattr(map_loc_data, "country") and map_loc_data.country:
                        location_parts.append(map_loc_data.country)

                    full_location_name = (
                        ", ".join(location_parts)
                        if location_parts
                        else map_loc_data.location_name
                    )
                    map_location_log = f"Thinking of traveling to: {full_location_name}"
                    if map_location_log != _last_location_log:
                        print(map_location_log)
                        _last_location_log = map_location_log

        return 0.1  # Inactive mode sleep

    # Update pause state
    should_pause = False
    should_resume = False
    with state_lock:
        if state_module.game_pause_state_cooldown > 0:
            state_module.game_pause_state_cooldown -= 1

        if curr_game_paused != state_module.game_paused:
            state_module.game_pause_state_cooldown = PAUSE_STATE_COOLDOWN
            state_module.game_paused = curr_game_paused
        elif (
            state_module.game_pause_state_cooldown == 0
            and curr_game_paused != state_module.game_pause_state_displayed
        ):
            if curr_game_paused:
                should_pause = True
            else:
                should_resume = True
            state_module.game_pause_state_displayed = curr_game_paused

    if should_pause:
        new_activity = Activity(ActivityType.PAUSED, state_module.prev_non_idle_activity)
        update_activity(new_activity)
        print("Game paused.")
    elif should_resume:
        print("Game resumed.")

    # Update prev_non_idle_activity if needed
    with state_lock:
        if not state_module.current_activity.is_idle():
            state_module.prev_non_idle_activity = state_module.current_activity

    # Start game timer if needed
    with state_lock:
        if state_module.game_start_time is None:
            state_module.game_start_time = time.time()

    return dynamic_sleep
