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
            # Initialize OCR reader for testing
            global reader
            reader = ocr_engine.Reader(["en"], gpu=USE_GPU)
            print("OCR initialized for testing.")
            occupied_slots, confidence_scores = character_region_manager.detect_occupied_slots()
            character_region_manager.log_status()
            print(f"🎯 Test Results: Occupied slots: {occupied_slots}")
            print(f"📊 Confidence scores: {[round(c, 2) for c in confidence_scores]}")
            sys.exit(0)

# Handle startup commands
handle_adaptive_character_commands()

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

def detect_characters_with_adaptation():
    global current_characters

    # Store previous character data before detection
    previous_characters = current_characters.copy()

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
    characters_updated = False
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
                # Validate that the OCR result is a legitimate character from the database
                if char_data.image_key != "char_unknown":
                    # This is a validated character from the database
                    if current_characters[char_idx] != char_data:
                        current_characters[char_idx] = char_data
                        print(f"✅ Detected character {char_idx + 1}: {char_data.character_display_name}")
                        characters_updated = True
                else:
                    # OCR detected text but it doesn't match any known character
                    if DEBUG_MODE:
                        print(f"⚠️ OCR detected '{char_data.character_display_name}' in slot {char_idx + 1}, but no database match found")
                    # Don't update with unknown characters
            else:
                # Only clear if we had a character before and OCR completely failed
                if current_characters[char_idx] is not None:
                    if DEBUG_MODE:
                        print(f"⚠️ Failed to detect character in slot {char_idx + 1}, keeping previous data")
        else:
            # For unoccupied slots, only clear if we don't have a previous character
            # This preserves character data when in menus/party setup
            char_idx = slot_idx  # Fallback to sequential
            if char_idx < 4 and current_characters[char_idx] is None:
                # Only set to None if it wasn't already None
                pass  # Keep existing data

    # If no characters were successfully detected at all, preserve existing data
    if not any(current_characters) and any(previous_characters):
        if DEBUG_MODE:
            print("🔄 No characters detected, preserving previous character data")
        current_characters = previous_characters.copy()
    elif not characters_updated and any(current_characters):
        if DEBUG_MODE:
            print("🔄 Character detection completed, data preserved")

    # Log adaptation summary
    if DEBUG_MODE and any(c != 0 for c in confidence_scores):
        active_slots = [i for i, c in enumerate(confidence_scores) if c > 0]
        print(f"🎯 Active character slots detected: {active_slots}")

def search_character_with_custom(text, custom_username, character_images=None):
    """Search for character, checking custom name first, then database"""
    # First check if text matches custom username (Traveler)
    if custom_username and text.strip().lower() == custom_username.strip().lower():
        # Create a custom character entry with flexible image key
        from datatypes import Character

        # Use custom image key if provided, otherwise default to traveler based on MC_AETHER setting
        if character_images and custom_username in character_images:
            image_key = character_images[custom_username]
        else:
            # Default to appropriate traveler image based on MC_AETHER setting
            # Read MC_AETHER from shared config if available, otherwise use CONFIG default
            mc_aether = True  # Default fallback
            try:
                if os.path.exists(shared_config_path):
                    with open(shared_config_path, 'r') as f:
                        config_data = json.load(f)
                        mc_aether = config_data.get('MC_AETHER', True)
            except Exception:
                pass  # Use default if config read fails

            image_key = "char_aether" if mc_aether else "char_lumine"

        return Character(
            character_display_name=custom_username,
            image_key=image_key,
            search_str=text.lower()
        )

    # Fall back to database lookup for all other characters
    char_data = DATA.search_character(text)
    if char_data:
        return char_data

    # If no database match, create a generic character entry for unmatched names
    # This maintains backward compatibility for characters not in the database yet
    from datatypes import Character
    return Character(
        character_display_name=text,
        image_key="char_unknown",  # Use a default unknown icon
        search_str=text.lower()
    )

def calculate_keyword_match_score(ocr_words, location_match, region_word):
    """
    Calculate how well OCR keywords match against a location database entry.
    Returns a score between 0.0 and 1.0 based on keyword overlap and relevance.
    """
    score = 0.0

    # Get location details for comparison
    location_name = location_match.location_name.lower() if hasattr(location_match, 'location_name') else ""
    subregion = location_match.subarea.lower() if hasattr(location_match, 'subarea') else ""
    region = location_match.country.lower() if hasattr(location_match, 'country') else ""
    match_term = location_match.search_str.lower() if hasattr(location_match, 'search_str') else ""

    # Prepare OCR words for comparison (remove punctuation, convert to lowercase)
    clean_ocr_words = [word.strip('.,!?').lower() for word in ocr_words if len(word.strip('.,!?')) > 1]

    # Score 1: Direct keyword matches with location name
    name_matches = 0
    for ocr_word in clean_ocr_words:
        if (len(ocr_word) > 2 and
            (ocr_word in location_name or
             location_name in ocr_word or
             any(ocr_word in part or part in ocr_word for part in location_name.split()))):
            name_matches += 1

    if name_matches > 0:
        score += min(0.4, name_matches * 0.2)  # Up to 40% for name matches

    # Score 2: Match term overlap (this is the key - CSV match column)
    if match_term:
        match_words = match_term.split()
        match_overlap = sum(1 for ocr_word in clean_ocr_words
                          for match_word in match_words
                          if (len(ocr_word) > 2 and len(match_word) > 2 and
                              (ocr_word == match_word or
                               ocr_word in match_word or
                               match_word in ocr_word)))
        if match_overlap > 0:
            score += min(0.5, match_overlap * 0.25)  # Up to 50% for match term overlap

    # Score 3: Region confirmation
    if region and region_word.lower() in region:
        score += 0.2  # 20% bonus for correct region

    # Score 4: Subregion relevance
    if subregion:
        subregion_matches = sum(1 for ocr_word in clean_ocr_words
                              if len(ocr_word) > 2 and ocr_word in subregion)
        if subregion_matches > 0:
            score += min(0.1, subregion_matches * 0.05)  # Up to 10% for subregion

    return max(0.0, min(1.0, score))

def calculate_location_confidence(subregion_word, region_word, original_text, pattern):
    """
    Calculate confidence score for how well a location pattern matches the OCR text.
    Returns a value between 0.0 and 1.0 where 1.0 is perfect confidence.
    """
    confidence = 0.0
    original_lower = original_text.lower()

    # Base confidence: Both words appear in the original text
    if subregion_word.lower() in original_lower and region_word.lower() in original_lower:
        confidence += 0.4

        # Bonus: Words appear close to each other (within 15 words)
        subregion_positions = []
        region_positions = []

        words = original_text.split()
        for i, word in enumerate(words):
            if subregion_word.lower() in word.lower():
                subregion_positions.append(i)
            if region_word.lower() in word.lower():
                region_positions.append(i)

        # Check if any subregion and region appear close together
        for sub_pos in subregion_positions:
            for reg_pos in region_positions:
                distance = abs(sub_pos - reg_pos)
                if distance <= 15:  # Within reasonable proximity
                    proximity_bonus = max(0, (15 - distance) / 15) * 0.3
                    confidence += proximity_bonus

        # Bonus: Pattern matches expected format
        if ', ' in pattern:  # Proper "Subregion, Region" format
            confidence += 0.2
        elif pattern.count(' ') <= 2:  # Simple format
            confidence += 0.1

        # Bonus: Subregion and region words are distinct and meaningful
        if (len(subregion_word) > 3 and len(region_word) > 3 and
            subregion_word.lower() != region_word.lower()):
            confidence += 0.2

    return max(0.0, min(1.0, confidence))

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

        # No truncation needed - Discord allows up to 128 characters for details,
        # and our formatted location names are well under this limit

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
    found_active_character = len(active_character) >= 1  # Allow multiple active indicators

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

        # Intelligent character redetection when active character detection fails
        # Only trigger when there's evidence of character changes or after cooldown
        if loop_count % 15 == 0:  # Reduced frequency - every 15 loops (about 2 seconds)
            # Check if we have a significant change in brightness patterns that suggests character switching
            brightness_change_threshold = 50  # Minimum brightness change to suggest character switch

            # Compare current brightness with previous reading (if available)
            if hasattr(character_region_manager, '_last_brightness_check'):
                prev_brightness = character_region_manager._last_brightness_check
                current_brightness = charnumber_brightness

                # Calculate total brightness change across all slots
                total_brightness_change = sum(abs(current - prev) for current, prev in zip(current_brightness, prev_brightness))

                if total_brightness_change > brightness_change_threshold:
                    if DEBUG_MODE:
                        print(f"🔄 Detected significant brightness change ({total_brightness_change}), triggering character redetection")
                    character_region_manager.needs_redetection = True
                elif loop_count % 60 == 0:  # Fallback: every 60 loops (about 8-9 seconds) if no changes detected
                    if DEBUG_MODE:
                        print("🔄 Periodic character redetection check (fallback)")
                    character_region_manager.needs_redetection = True
            else:
                # First time - store current brightness and trigger initial redetection
                character_region_manager._last_brightness_check = charnumber_brightness
                if DEBUG_MODE:
                    print("🔄 Initial brightness check, triggering character redetection")
                character_region_manager.needs_redetection = True

            # Update stored brightness for next comparison
            character_region_manager._last_brightness_check = charnumber_brightness

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

    # More restrictive character detection conditions to reduce OCR overhead
    should_detect_characters = False

    if reload_party_flag:
        should_detect_characters = True
        reload_party_flag = False
    elif len([a for a in current_characters if a == None]) > 0:
        # Only run if we have missing characters AND it's the right timing
        should_detect_characters = loop_count % OCR_CHARNAMES_ONE_IN == 0
    elif character_region_manager.needs_redetection:
        # Only run intelligent redetection at specific intervals
        should_detect_characters = loop_count % OCR_CHARNAMES_ONE_IN == 0
        character_region_manager.needs_redetection = False  # Reset immediately after use
    elif loop_count % OCR_CHARNAMES_ONE_IN == 0:
        # Normal scheduled character detection (every 10 loops)
        should_detect_characters = True

    if should_detect_characters:
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
            def map_text_processor(text, data_instance=DATA):
                if not text or not text.strip():
                    return ""

                # Handle text duplication issue - remove repeated patterns
                cleaned_text = ' '.join(text.replace('\n', ' ').split())

                # Remove duplicated substrings (like "Nasha Nod-Krai d devices that are s" appearing twice)
                words = cleaned_text.split()
                if len(words) > 10:  # Only process if we have a lot of words (indicating possible duplication)
                    # Find and remove repeated sequences
                    result_words = []
                    i = 0
                    while i < len(words):
                        current_word = words[i]
                        # Check if this word starts a repeated sequence
                        found_repetition = False
                        for length in range(min(8, len(words) - i - 1), 2, -1):  # Try different sequence lengths
                            if i + length * 2 <= len(words):
                                seq1 = ' '.join(words[i:i + length])
                                seq2 = ' '.join(words[i + length:i + length * 2])
                                if seq1 == seq2 and len(seq1) > 10:  # Only remove substantial repetitions
                                    if DEBUG_MODE:
                                        print(f"🔄 MAP_LOC: Found repetition, removing duplicate sequence: '{seq1}'")
                                    i += length * 2  # Skip both occurrences
                                    found_repetition = True
                                    break
                        if not found_repetition:
                            result_words.append(current_word)
                            i += 1
                    if result_words:
                        cleaned_text = ' '.join(result_words)
                    else:
                        cleaned_text = ' '.join(words)  # Fallback to original if deduplication fails

                # Split into words for better processing
                words = cleaned_text.split()
                if not words:
                    return ""

                # Filter out only the most obvious OCR artifacts
                filtered_words = []
                skip_words = {
                    'd', 'devices', 'that', 'are', 'scattered', 'of', 'the',
                    'and', 'or', 'but', 'with', 'for', 'from', 'this', 'these', 'those',
                    'menu', 'exit', 'close', 'ok', 'cancel', 'select', 'ready', 'waiting',
                    's', 't', 're', 've', 'll', 'm', 'n'  # Common OCR fragments
                }

                # Keep location-related words for pattern reconstruction
                location_context_words = {'town', 'city', 'village'}

                for word in words:
                    word_lower = word.lower()
                    # Skip very short words, common artifacts, and UI words
                    if (len(word) < 2 or
                        word_lower in skip_words or
                        word.isdigit() or
                        (len(word) <= 3 and not word[0].isupper() and word_lower not in location_context_words)):  # Keep "town", "city" etc.
                        continue
                    # Clean up words that end with comma but are otherwise good
                    clean_word = word.rstrip(',') if word.endswith(',') and len(word) > 3 else word
                    if len(clean_word) >= 2:
                        filtered_words.append(clean_word)

                if not filtered_words:
                    return ""

                # Try multiple candidate extractions and validate against database
                candidates = []

                # Pattern 1: Look for proper noun combinations (capitalized words)
                proper_nouns = [word for word in filtered_words if word[0].isupper() and len(word) > 2]

                if len(proper_nouns) >= 2:
                    # Try combinations of 2-3 proper nouns
                    for i in range(len(proper_nouns) - 1):
                        for j in range(i + 1, min(i + 3, len(proper_nouns))):
                            combination = ' '.join(proper_nouns[i:j+1])
                            if 5 < len(combination) < 50:  # Reasonable length for location name
                                candidates.append(combination)

                # Pattern 2: Try mixed case word combinations
                if len(filtered_words) >= 2:
                    # Try 2-word combinations
                    for i in range(len(filtered_words) - 1):
                        combination = f"{filtered_words[i]} {filtered_words[i+1]}"
                        if 5 < len(combination) < 40:
                            candidates.append(combination)

                    # Try 3-word combinations if available
                    if len(filtered_words) >= 3:
                        for i in range(len(filtered_words) - 2):
                            combination = f"{filtered_words[i]} {filtered_words[i+1]} {filtered_words[i+2]}"
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
                            print(f"✅ MAP_LOC: Found database match for '{candidate}' -> '{location_match.location_name}'")
                        return candidate

                    # Try partial matches with database entries
                    for word in candidate.split():
                        if len(word) > 3:  # Only try meaningful words
                            location_match = data_instance.search_location(word)
                            if location_match:
                                if DEBUG_MODE:
                                    print(f"✅ MAP_LOC: Found partial database match for '{word}' in '{candidate}' -> '{location_match.location_name}'")
                                return candidate

                # Systematic keyword matching approach
                # Step 1: First identify potential regions from the garbled text
                potential_regions = []
                for word in proper_nouns:
                    if len(word) > 3:  # Regions are typically longer words
                        region_match = data_instance.search_location(word)
                        if region_match:
                            potential_regions.append((word, region_match))

                # Step 2: If we found regions, cache ALL locations for those regions
                if potential_regions:
                    for region_word, region_match in potential_regions:
                        if DEBUG_MODE:
                            print(f"🔍 MAP_LOC: Found region '{region_word}', caching all locations for this region...")

                        # Get the original uncleaned text to extract ALL keywords
                        original_words = cleaned_text.split()

                        # Cache all locations that belong to this region
                        region_locations = []
                        # We need to search through the data to find locations in this region
                        # Since we don't have a direct method, we'll use a broad search approach

                        # Step 3: Extract ALL words from the original OCR text (no filtering)
                        all_ocr_words = [word.strip(',') for word in original_words if len(word.strip(',')) > 1]

                        if DEBUG_MODE:
                            print(f"🔍 MAP_LOC: Extracted keywords from OCR: {all_ocr_words}")

                        # Step 4: Try to find the best matching location by keyword overlap
                        best_match = None
                        best_score = 0
                        best_pattern = None

                        # Get all possible location match terms for this region
                        # We'll search for locations and filter by region
                        for test_word in all_ocr_words:
                            if len(test_word) > 2:
                                # Try the word as a potential location match term
                                location_match = data_instance.search_location(test_word.lower())

                                if location_match:
                                    # Check if this location belongs to our region
                                    if (hasattr(location_match, 'country') and
                                        location_match.country and
                                        region_word.lower() in location_match.country.lower()):

                                        # Calculate match score based on keyword overlap
                                        match_score = calculate_keyword_match_score(all_ocr_words, location_match, region_word)

                                        if match_score > best_score and match_score > 0.3:  # 30% minimum score
                                            best_match = location_match
                                            best_score = match_score
                                            best_pattern = test_word.lower()

                                            if DEBUG_MODE:
                                                print(f"🎯 MAP_LOC: Found potential match '{test_word.lower()}' -> '{location_match.location_name}' (score: {match_score:.2f})")

                        # Step 5: Return the best match if it meets our criteria
                        if best_match and best_score > 0.4:  # 40% confidence threshold
                            if DEBUG_MODE:
                                print(f"✅ MAP_LOC: Selected best match '{best_pattern}' -> '{best_match.location_name}' (score: {best_score:.2f})")
                            return best_pattern

                # Fallback: Try the original region/subregion approach for cleaner text
                if len(proper_nouns) >= 2:
                    # Try different combinations where later words might be regions and earlier words subregions
                    for region_candidate in proper_nouns:
                        for subregion_candidate in proper_nouns:
                            if region_candidate != subregion_candidate:
                                # Try "Subregion Region" format (common OCR concatenation)
                                combined_candidate = f"{subregion_candidate} {region_candidate}"
                                if len(combined_candidate) < 50:
                                    location_match = data_instance.search_location(combined_candidate)
                                    if location_match:
                                        if DEBUG_MODE:
                                            print(f"✅ MAP_LOC: Found region/subregion match for '{combined_candidate}' -> '{location_match.location_name}'")
                                        return combined_candidate

                                # Try "Subregion, Region" format (proper format)
                                proper_format = f"{subregion_candidate}, {region_candidate}"
                                if len(proper_format) < 60:
                                    location_match = data_instance.search_location(proper_format)
                                    if location_match:
                                        if DEBUG_MODE:
                                            print(f"✅ MAP_LOC: Found proper format match for '{proper_format}' -> '{location_match.location_name}'")
                                        return proper_format

                # If no database matches found, try one more approach with original text
                # but only if it contains proper nouns and isn't just artifacts
                original_words = cleaned_text.split()
                original_proper_nouns = [word for word in original_words if word[0].isupper() and len(word) > 2]

                for word in original_proper_nouns:
                    if 3 < len(word) < 30:
                        # Last chance - check if this single word matches database
                        location_match = data_instance.search_location(word)
                        if location_match:
                            if DEBUG_MODE:
                                print(f"✅ MAP_LOC: Found final database match for '{word}' -> '{location_match.location_name}'")
                            return word

                # No valid location found in database
                if DEBUG_MODE:
                    print(f"❌ MAP_LOC: No database matches found for any candidates from '{cleaned_text}'")
                    print(f"❌ MAP_LOC: Tried candidates: {candidates}")
                return ""

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

                # Format location with subregion and region information
                location_parts = []
                if map_loc_data.location_name:
                    location_parts.append(map_loc_data.location_name)
                if hasattr(map_loc_data, 'subarea') and map_loc_data.subarea:
                    location_parts.append(map_loc_data.subarea)
                if hasattr(map_loc_data, 'country') and map_loc_data.country:
                    location_parts.append(map_loc_data.country)

                full_location_name = ", ".join(location_parts) if location_parts else map_loc_data.location_name
                map_location_log = f"Thinking of traveling to: {full_location_name}"
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

            # Debug: Log current_characters before writing
            if DEBUG_MODE:
                char_names = [char.character_display_name if char else None for char in current_characters]
                print(f"🔍 DEBUG: current_characters before JSON write: {char_names}")

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
