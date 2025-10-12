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

# Data contains csv tables, file watcher, and best text match algorithms.
DATA: Data = Data()

# _____________________________________________________________________
# ADAPTIVE CHARACTER DETECTION SYSTEM
# _____________________________________________________________________

class CharacterRegionManager:
    """Manages dynamic character name and number bounding boxes with paired vertical adaptation"""

    def __init__(self):
        # Base character positions (from CONFIG.py) - names and numbers must stay paired
        self.base_name_positions = NAMES_4P_COORD.copy()
        self.base_number_positions = NUMBER_4P_COORD.copy()
        self.current_name_positions = self.base_name_positions.copy()
        self.current_number_positions = self.base_number_positions.copy()

        # Dynamic tracking
        self.occupied_slots = [True, True, True, True]  # Assume all slots occupied initially
        self.slot_confidence = [0.0, 0.0, 0.0, 0.0]
        self.adaptation_history = []
        self.vertical_shifts = [0, 0, 0, 0]  # Track vertical shift for each slot

        # Movement constraints (vertical only, ±30 pixels max)
        self.max_vertical_shift = 30
        self.movement_step = 5
        self.adaptation_enabled = True
        self.needs_redetection = False

    def detect_occupied_slots(self):
        """Determine which character slots are actually occupied with overlap prevention"""
        occupied = []
        confidence_scores = []
        detected_names = set()  # Track detected names to prevent duplicates

        for i, base_coords in enumerate(self.base_name_positions):
            # Try current position first
            success, confidence = self._test_slot_detection(i, self.current_name_positions[i])

            if DEBUG_MODE:
                print(f"🔍 Slot {i} detection: success={success}, confidence={confidence:.3f}")

            if success:
                # Check for duplicate character names
                if not self._would_create_duplicate(success, detected_names):
                    occupied.append(i)
                    confidence_scores.append(confidence)
                    detected_names.add(success)  # Add detected name to prevent duplicates
                    if DEBUG_MODE:
                        print(f"✅ Slot {i} marked as occupied with '{success}'")
                else:
                    # Duplicate detected - mark as empty and try adaptation
                    occupied.append(None)
                    confidence_scores.append(0.0)
                    if DEBUG_MODE:
                        print(f"❌ Slot {i} rejected as duplicate: '{success}' already detected")
                    if self.adaptation_enabled:
                        # Try to find a different position that doesn't create duplicates
                        adaptive_success, adaptive_confidence, best_coords = self._try_adaptive_positions_with_duplicate_prevention(i, base_coords, detected_names)

                        if adaptive_success:
                            self.current_name_positions[i] = best_coords
                            occupied[i] = i  # Update the slot
                            confidence_scores[i] = adaptive_confidence

                            # Log the adaptation
                            self.adaptation_history.append({
                                'slot': i,
                                'original_coords': base_coords,
                                'adapted_coords': best_coords,
                                'timestamp': time.time(),
                                'reason': 'duplicate_prevention'
                            })
            else:
                # Try adaptive positions (vertical shifts only) if adaptation enabled
                if self.adaptation_enabled:
                    adaptive_success, adaptive_confidence, best_coords = self._try_adaptive_positions_with_duplicate_prevention(i, base_coords, detected_names)

                    if adaptive_success:
                        self.current_name_positions[i] = best_coords
                        occupied.append(i)
                        confidence_scores.append(adaptive_confidence)

                        # Log the adaptation
                        self.adaptation_history.append({
                            'slot': i,
                            'original_coords': base_coords,
                            'adapted_coords': best_coords,
                            'timestamp': time.time()
                        })
                    else:
                        occupied.append(None)  # Empty slot
                        confidence_scores.append(0.0)
                else:
                    occupied.append(None)  # Empty slot
                    confidence_scores.append(0.0)

        self.occupied_slots = occupied
        self.slot_confidence = confidence_scores

        # Update global coordinate variables so GUI gets the adapted coordinates
        self._update_global_coordinates()

        return occupied, confidence_scores

    def _would_create_duplicate(self, detected_text, detected_names):
        """Check if detected text would create a duplicate character"""
        return detected_text in detected_names

    def _try_adaptive_positions_with_duplicate_prevention(self, slot_index, base_coords, detected_names):
        """Try vertical position shifts with duplicate prevention"""
        x1, y1, x2, y2 = base_coords
        width = x2 - x1
        height = y2 - y1

        best_result = (False, 0.0, base_coords)

        # Calculate slot boundaries to prevent overlap
        slot_boundaries = self._calculate_slot_boundaries()

        # Try shifting up and down from base position
        for shift in range(-self.max_vertical_shift, self.max_vertical_shift + 1, self.movement_step):
            test_y1 = y1 + shift
            test_y2 = y2 + shift

            # Stay within reasonable bounds (assuming max 2160p resolution)
            if test_y1 < 0 or test_y2 > 2160:
                continue

            # Check for overlap with adjacent slots
            test_coords = (x1, test_y1, x2, test_y2)
            if self._would_overlap_with_adjacent_slots(slot_index, test_coords, slot_boundaries):
                continue

            # Test detection at this position
            temp_success, temp_confidence = self._test_slot_detection(slot_index, test_coords)

            if temp_success:
                # Check if this would create a duplicate
                if not self._would_create_duplicate(temp_success, detected_names):
                    if temp_confidence > best_result[1]:
                        best_result = (True, temp_confidence, test_coords)

        return best_result

    def _update_global_coordinates(self):
        """Update global coordinate variables with adapted positions for GUI"""
        global NAMES_4P_COORD, NUMBER_4P_COORD

        # Update the global coordinate arrays with current adapted positions
        NAMES_4P_COORD = self.current_name_positions.copy()
        NUMBER_4P_COORD = self.current_number_positions.copy()

        # Log the coordinate update for debugging
        if DEBUG_MODE:
            print("📍 Updated global coordinates for GUI:")
            print(f"   NAMES_4P_COORD: {NAMES_4P_COORD}")
            print(f"   NUMBER_4P_COORD: {NUMBER_4P_COORD}")

        # Also update the shared config file that GUI reads
        self._update_gui_shared_config()

    def _update_gui_shared_config(self):
        """Update the shared config file that the GUI reads"""
        try:
            shared_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared_config.json')
            if os.path.exists(shared_config_file):
                with open(shared_config_file, 'r') as f:
                    gui_config = json.load(f)
            else:
                gui_config = {}

            # Update coordinate information for GUI
            gui_config['ADAPTED_NAMES_4P_COORD'] = self.current_name_positions.copy()
            gui_config['ADAPTED_NUMBER_4P_COORD'] = self.current_number_positions.copy()
            gui_config['ADAPTATION_ACTIVE'] = True
            gui_config['ADAPTATION_HISTORY'] = self.adaptation_history.copy()
            gui_config['OCCUPIED_SLOTS'] = self.occupied_slots.copy()

            with open(shared_config_file, 'w') as f:
                json.dump(gui_config, f, indent=4)

            if DEBUG_MODE:
                print("📤 Updated shared config for GUI with adapted coordinates")

        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Error updating shared config: {e}")

    def _test_slot_detection(self, slot_index, coords):
        """Test if a character slot can be detected at given coordinates"""
        try:
            image = ImageGrab.grab(bbox=coords)
            cap = np.array(image)
            results = reader.readtext(cap, allowlist=ALLOWLIST)

            # Look for character-like text
            for result in results:
                if result[2] > NAME_CONF_THRESH:
                    text = result[1].strip()
                    if len(text) > 2 and self._looks_like_character_name(text):
                        if DEBUG_MODE:
                            print(f"🔍 Slot {slot_index} OCR: '{text}' (confidence: {result[2]:.3f})")
                        return text, result[2]  # Return the actual character name text, not True

            # Debug: Log what OCR found but was rejected
            if DEBUG_MODE and results:
                rejected_texts = []
                for result in results:
                    if result[2] > 0.1:  # Log results with at least 10% confidence
                        text = result[1].strip()
                        if len(text) > 1:
                            rejected_texts.append(f"'{text}'({result[2]:.3f})")
                if rejected_texts:
                    print(f"🔍 Slot {slot_index} OCR rejected: {', '.join(rejected_texts)}")

            return False, 0.0

        except Exception as e:
            if DEBUG_MODE:
                print(f"🔍 Slot {slot_index} OCR error: {e}")
            return False, 0.0

    def _try_adaptive_positions(self, slot_index, base_coords):
        """Try vertical position shifts for a character slot with overlap prevention"""
        x1, y1, x2, y2 = base_coords
        width = x2 - x1
        height = y2 - y1

        best_result = (False, 0.0, base_coords)

        # Calculate slot boundaries to prevent overlap
        slot_boundaries = self._calculate_slot_boundaries()

        # Try shifting up and down from base position
        for shift in range(-self.max_vertical_shift, self.max_vertical_shift + 1, self.movement_step):
            test_y1 = y1 + shift
            test_y2 = y2 + shift

            # Stay within reasonable bounds (assuming max 2160p resolution)
            if test_y1 < 0 or test_y2 > 2160:
                continue

            # Check for overlap with adjacent slots
            test_coords = (x1, test_y1, x2, test_y2)
            if self._would_overlap_with_adjacent_slots(slot_index, test_coords, slot_boundaries):
                continue

            success, confidence = self._test_slot_detection(slot_index, test_coords)

            if success and confidence > best_result[1]:
                best_result = (True, confidence, test_coords)

        return best_result

    def _calculate_slot_boundaries(self):
        """Calculate the safe boundaries for each character slot to prevent overlap"""
        boundaries = []

        for i in range(4):
            if i == 0:
                # First slot - only lower boundary
                upper_bound = -float('inf')
                lower_bound = self.base_name_positions[1][1] - 10  # 10px buffer from next slot
            elif i == 3:
                # Last slot - only upper boundary
                upper_bound = self.base_name_positions[2][1] + 10  # 10px buffer from previous slot
                lower_bound = float('inf')
            else:
                # Middle slots - both boundaries
                upper_bound = self.base_name_positions[i-1][1] + 10
                lower_bound = self.base_name_positions[i+1][1] - 10

            boundaries.append((upper_bound, lower_bound))

        return boundaries

    def _would_overlap_with_adjacent_slots(self, slot_index, test_coords, slot_boundaries):
        """Check if test coordinates would overlap with adjacent slots"""
        test_y1, test_y2 = test_coords[1], test_coords[3]

        # Check against adjacent slots only
        for i in [slot_index - 1, slot_index + 1]:
            if 0 <= i < 4:
                upper_bound, lower_bound = slot_boundaries[i]

                # Check if this slot would encroach on adjacent slot's territory
                if slot_index < i:  # We're checking against a lower slot
                    if test_y2 > lower_bound:  # Would overlap with lower slot
                        return True
                else:  # We're checking against an upper slot
                    if test_y1 < upper_bound:  # Would overlap with upper slot
                        return True

        return False

    def _looks_like_character_name(self, text):
        """Check if text resembles a Genshin character name"""
        # Simple heuristics - can be expanded
        if len(text) < 2 or len(text) > 30:
            return False

        # Should contain letters and possibly spaces or apostrophes
        import re
        if not re.match(r"^[A-Za-z\s']+$", text):
            return False

        # Should not be common UI words
        ui_words = ['menu', 'party', 'setup', 'exit', 'close', 'ok', 'cancel', 'select', 'change', 'ready', 'waiting', 'use', 'item', 'equip']
        if text.lower() in ui_words:
            return False

        return True

    def get_active_coordinates(self):
        """Get coordinates only for occupied slots"""
        coords = []
        for i, occupied in enumerate(self.occupied_slots):
            if occupied is not None:
                coords.append(self.current_name_positions[i])
        return coords

    def get_adaptive_number_coordinates(self):
        """Get number coordinates that stay paired with adapted name positions"""
        # Apply the same vertical shifts to number positions as name positions
        adaptive_coords = []
        for i in range(4):
            base_x, base_y = self.base_number_positions[i]
            # Apply the same vertical shift as the corresponding name position
            name_coords = self.current_name_positions[i]
            name_base_coords = self.base_name_positions[i]

            # Calculate vertical shift from name position adaptation
            name_shift = name_coords[1] - name_base_coords[1]
            adaptive_y = base_y + name_shift

            adaptive_coords.append((base_x, adaptive_y))

        return adaptive_coords

    def reset_to_base_positions(self):
        """Reset all positions to original coordinates"""
        self.current_name_positions = self.base_name_positions.copy()
        self.current_number_positions = self.base_number_positions.copy()
        self.occupied_slots = [True, True, True, True]
        self.slot_confidence = [0.0, 0.0, 0.0, 0.0]
        self.adaptation_history.clear()
        print("🔄 Reset character positions to base coordinates")

    def log_status(self):
        """Log current adaptation status for debugging"""
        if not DEBUG_MODE:
            return

        print("🔍 Character Adaptation Status:")
        occupied_indices = [i for i, slot in enumerate(self.occupied_slots) if slot is not None]
        print(f"   Occupied slots: {occupied_indices}")
        print(f"   Confidence scores: {[round(c, 2) for c in self.slot_confidence]}")
        print(f"   Adaptations made: {len(self.adaptation_history)}")

        if self.adaptation_history:
            latest = self.adaptation_history[-1]
            print(f"   Latest adaptation: Slot {latest['slot']} at {time.time() - latest['timestamp']:.1f}s ago")

        # Show current coordinate values for GUI verification
        print("📍 Current Coordinates (what GUI receives):")
        print(f"   Name positions: {self.current_name_positions}")
        print(f"   Number positions: {self.current_number_positions}")
        print(f"   Base name positions: {self.base_name_positions}")
        print(f"   Base number positions: {self.base_number_positions}")

        # Show vertical shifts
        shifts = []
        for i in range(4):
            name_shift = self.current_name_positions[i][1] - self.base_name_positions[i][1]
            number_shift = self.current_number_positions[i][1] - self.base_number_positions[i][1]
            shifts.append(f"Slot{i}: name={name_shift}px, number={number_shift}px")

        print(f"   Vertical shifts: {shifts}")

# Initialize the character region manager
character_region_manager = CharacterRegionManager()

def handle_adaptive_character_commands():
    """Handle manual control commands for the adaptive character system"""
    import sys

    # Check for command line arguments for manual control
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

# Handle startup commands
handle_adaptive_character_commands()

def detect_characters_with_adaptation():
    """Enhanced character detection with vertical adaptation"""
    global current_characters

    # Detect which slots are occupied
    occupied_slots, confidence_scores = character_region_manager.detect_occupied_slots()

    # Get custom character name and image mappings from shared config
    custom_username = None
    character_images = {}  # Maps character names to image keys
    try:
        shared_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared_config.json')
        if os.path.exists(shared_config_path):
            with open(shared_config_path, 'r') as f:
                shared_config = json.load(f)
                custom_username = shared_config.get('USERNAME')

                # Support flexible character image mapping
                if 'CHARACTER_IMAGES' in shared_config:
                    character_images = shared_config['CHARACTER_IMAGES']
                else:
                    # Legacy support for MC_AETHER setting
                    mc_aether = shared_config.get('MC_AETHER', True)
                    traveler_image = "char_aether" if mc_aether else "char_lumine"
                    if custom_username:
                        character_images[custom_username] = traveler_image

    except Exception:
        pass  # Silently handle config read errors

    # Update character data for occupied slots
    for slot_idx, char_idx in enumerate(occupied_slots):
        if char_idx is not None:
            coords = character_region_manager.current_name_positions[char_idx]

            # Use existing OCR logic with adapted coordinates
            char_data = capture_and_process_ocr(
                coords,
                ALLOWLIST,
                NAME_CONF_THRESH,
                ActivityType.LOCATION,  # Placeholder
                lambda text: search_character_with_custom(text, custom_username, character_images),
                debug_key=f'CHAR_ADAPT_{char_idx}'
            )

            if char_data:
                if current_characters[char_idx] != char_data:
                    current_characters[char_idx] = char_data
                    print(f"✅ Detected character {char_idx + 1}: {char_data.character_display_name}")
            else:
                current_characters[char_idx] = None
        else:
            # Mark empty slots as None
            char_idx = slot_idx  # Fallback to sequential
            if char_idx < 4:
                current_characters[char_idx] = None

    # Log adaptation summary
    if DEBUG_MODE and any(c != 0 for c in confidence_scores):
        active_slots = [i for i, c in enumerate(confidence_scores) if c > 0]
        print(f"🎯 Active character slots detected: {active_slots}")

def search_character_with_custom(text, custom_username, character_images=None):
    """Search for character, checking custom name first, then database"""
    # First check if text matches custom username
    if custom_username and text.strip().lower() == custom_username.strip().lower():
        # Create a custom character entry with flexible image key
        from datatypes import Character

        # Use custom image key if provided, otherwise default to traveler
        if character_images and custom_username in character_images:
            image_key = character_images[custom_username]
        else:
            # Default to traveler image based on legacy MC_AETHER setting
            image_key = "char_aether"  # Default fallback

        return Character(
            character_display_name=custom_username,
            image_key=image_key,
            search_str=text.lower()
        )

    # Fall back to database lookup
    return DATA.search_character(text)

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
        # Use adaptive number coordinates that stay paired with name positions
        adaptive_number_coords = character_region_manager.get_adaptive_number_coordinates()
        charnumber_cap = [
            ImageGrab.grab(
                bbox=(
                    adaptive_number_coords[i][0],
                    adaptive_number_coords[i][1],
                    adaptive_number_coords[i][0] + 1,
                    adaptive_number_coords[i][1] + 1,
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

    # Debug: Log brightness values to see what's happening
    if DEBUG_MODE and loop_count % 50 == 0:  # Log every 5 seconds
        print(f"🔍 Active Character Debug - Brightness: {charnumber_brightness}")
        print(f"🔍 Active Character Debug - Threshold: {ACTIVE_CHARACTER_THRESH}")
        print(f"🔍 Active Character Debug - Adaptive Coords: {character_region_manager.get_adaptive_number_coordinates()}")

    active_character = [
        idx
        for idx, bri in enumerate(charnumber_brightness)
        if bri < ACTIVE_CHARACTER_THRESH
    ]
    found_active_character = len(active_character) == 1

    # Debug: Log active character detection results
    if DEBUG_MODE and loop_count % 50 == 0:  # Log every 5 seconds
        print(f"🔍 Active Character Detection: found={found_active_character}, candidates={active_character}")

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
    # CAPTURE PARTY MEMBERS (ADAPTIVE)
    # _____________________________________________________________________

    if (
        loop_count % OCR_CHARNAMES_ONE_IN == 0
        or len([a for a in current_characters if a == None]) > 0
        or reload_party_flag
        or character_region_manager.needs_redetection
    ):
        reload_party_flag = False
        character_region_manager.needs_redetection = False

        # Use adaptive character detection
        detect_characters_with_adaptation()

        # Log adaptation status periodically for debugging
        if loop_count % 300 == 0:  # Every 5 minutes
            character_region_manager.log_status()

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
                'pause_ocr': pause_ocr,
                # Include adapted coordinates in the frequently updated file
                'adapted_coordinates': {
                    'ADAPTED_NAMES_4P_COORD': character_region_manager.current_name_positions.copy(),
                    'ADAPTED_NUMBER_4P_COORD': character_region_manager.current_number_positions.copy(),
                    'ADAPTATION_ACTIVE': character_region_manager.adaptation_enabled,
                    'OCCUPIED_SLOTS': character_region_manager.occupied_slots.copy()
                }
            }
            with open(shared_file, 'w') as f:
                json.dump(data_to_write, f)
            if DEBUG_MODE:
                print(f"✅ Wrote shared data to {shared_file}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Error writing to shared file: {e}")
    
    time.sleep(dynamic_sleep)  # Use dynamic sleep timing based on game state
