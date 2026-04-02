"""Adaptive character detection system."""

import json
import os
import re
import time
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import ImageGrab

from core.datatypes import ActivityType, Character, DEBUG_MODE
from CONFIG import DEBUG_CHARACTER_MODE
from CONFIG import NAMES_4P_COORD, NUMBER_4P_COORD, ALLOWLIST, NAME_CONF_THRESH

# Shared config path (defined locally since it's runtime-dependent)
script_dir = Path(__file__).resolve().parent.parent
shared_config_path = script_dir / "shared_config.json"

from core import ps_helper
from core.ocr_utils import capture_and_process_ocr


class CharacterRegionManager:
    """Manages dynamic character name and number bounding boxes with paired vertical adaptation."""

    def __init__(self, reader):
        self.reader = reader

        # Load coordinates from shared_config.json first, fallback to CONFIG.py
        script_dir = Path(__file__).resolve().parent.parent
        shared_config_file = script_dir / "shared_config.json"

        try:
            if shared_config_file.exists():
                with open(shared_config_file, "r") as f:
                    config = json.load(f)
                    # Use adapted coordinates if available, otherwise fallback
                    if (
                        "ADAPTED_NAMES_4P_COORD" in config
                        and "ADAPTED_NUMBER_4P_COORD" in config
                    ):
                        self.base_name_positions = [
                            tuple(c) for c in config["ADAPTED_NAMES_4P_COORD"]
                        ]
                        self.base_number_positions = [
                            tuple(c) for c in config["ADAPTED_NUMBER_4P_COORD"]
                        ]
                    else:
                        self.base_name_positions = list(NAMES_4P_COORD)
                        self.base_number_positions = list(NUMBER_4P_COORD)
            else:
                self.base_name_positions = list(NAMES_4P_COORD)
                self.base_number_positions = list(NUMBER_4P_COORD)
        except (OSError, RuntimeError, ValueError) as e:
            if DEBUG_MODE:
                print(f"⚠️ Error loading shared config: {e}, using CONFIG.py")
            self.base_name_positions = list(NAMES_4P_COORD)
            self.base_number_positions = list(NUMBER_4P_COORD)

        self.current_name_positions = self.base_name_positions.copy()
        self.current_number_positions = self.base_number_positions.copy()

        # Dynamic tracking
        self.occupied_slots = [
            True,
            True,
            True,
            True,
        ]  # Assume all slots occupied initially
        self.slot_confidence = [0.0, 0.0, 0.0, 0.0]
        self.adaptation_history = []
        self.vertical_shifts = [0, 0, 0, 0]  # Track vertical shift for each slot

        # Movement constraints (vertical only, ±30 pixels max)
        self.max_vertical_shift = 30
        self.movement_step = 5
        self.adaptation_enabled = True
        self.needs_redetection = False

    def init_from_coordinates(self):
        """Reset positions to base coordinates after screen resolution change."""
        self.current_name_positions = self.base_name_positions.copy()
        self.current_number_positions = self.base_number_positions.copy()
        self.vertical_shifts = [0, 0, 0, 0]
        self.needs_redetection = True

    def detect_occupied_slots(self):
        """Determine which character slots are actually occupied with overlap prevention"""
        occupied = []
        confidence_scores = []
        detected_names = set()  # Track detected names to prevent duplicates

        for i, base_coords in enumerate(self.base_name_positions):
            # Try current position first
            success, confidence = self._test_slot_detection(
                i, self.current_name_positions[i]
            )

            if DEBUG_MODE and DEBUG_CHARACTER_MODE:
                print(
                    f"🔍 Slot {i} detection: success={success}, confidence={confidence:.3f}"
                )

            if success:
                # Enhanced duplicate and fragment detection
                full_detected_names = list(
                    detected_names
                )  # Convert to list for fragment checking

                # Check if this is a fragment of another character's name
                if self._is_text_fragment(success, full_detected_names):
                    if DEBUG_MODE:
                        print(
                            f"❌ Slot {i} rejected as fragment: '{success}' appears to be part of another character name"
                        )
                    occupied.append(None)
                    confidence_scores.append(0.0)
                elif not self._would_create_duplicate(success, detected_names):
                    occupied.append(i)
                    confidence_scores.append(confidence)
                    detected_names.add(
                        success
                    )  # Add detected name to prevent duplicates
                    if DEBUG_MODE:
                        print(f"✅ Slot {i} marked as occupied with '{success}'")
                else:
                    # Duplicate detected - mark as empty and try adaptation
                    occupied.append(None)
                    confidence_scores.append(0.0)
                    if DEBUG_MODE:
                        print(
                            f"❌ Slot {i} rejected as duplicate: '{success}' already detected"
                        )
                    if self.adaptation_enabled:
                        # Try to find a different position that doesn't create duplicates
                        adaptive_success, adaptive_confidence, best_coords = (
                            self._try_adaptive_positions_with_duplicate_prevention(
                                i, base_coords, detected_names
                            )
                        )

                        if adaptive_success:
                            self.current_name_positions[i] = best_coords
                            occupied[i] = i  # Update the slot
                            confidence_scores[i] = adaptive_confidence

                            # Log the adaptation
                            self.adaptation_history.append(
                                {
                                    "slot": i,
                                    "original_coords": base_coords,
                                    "adapted_coords": best_coords,
                                    "timestamp": time.time(),
                                    "reason": "duplicate_prevention",
                                }
                            )
            else:
                # Try adaptive positions (vertical shifts only) if adaptation enabled
                if self.adaptation_enabled:
                    adaptive_success, adaptive_confidence, best_coords = (
                        self._try_adaptive_positions_with_duplicate_prevention(
                            i, base_coords, detected_names
                        )
                    )

                    if adaptive_success:
                        self.current_name_positions[i] = best_coords
                        occupied.append(i)
                        confidence_scores.append(adaptive_confidence)

                        # Log the adaptation
                        self.adaptation_history.append(
                            {
                                "slot": i,
                                "original_coords": base_coords,
                                "adapted_coords": best_coords,
                                "timestamp": time.time(),
                            }
                        )
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

    def _is_text_fragment(self, text, full_detected_names):
        """Check if detected text is likely a fragment of another character's name"""
        if not text or len(text) < 2:
            return True

        # Check if this text appears as a substring in any full detected name
        for full_name in full_detected_names:
            if text.lower() in full_name.lower() and text.lower() != full_name.lower():
                return True

        return False

    def _try_adaptive_positions_with_duplicate_prevention(
        self, slot_index, base_coords, detected_names
    ):
        """Try vertical position shifts with duplicate prevention"""
        x1, y1, x2, y2 = base_coords

        best_result = (False, 0.0, base_coords)

        # Calculate slot boundaries to prevent overlap
        slot_boundaries = self._calculate_slot_boundaries()

        # Try shifting up and down from base position
        for shift in range(
            -self.max_vertical_shift, self.max_vertical_shift + 1, self.movement_step
        ):
            test_y1 = y1 + shift
            test_y2 = y2 + shift

            # Stay within screen bounds
            screen_height = ps_helper.get_screen_resolution()[1]
            if test_y1 < 0 or test_y2 > screen_height:
                continue

            # Check for overlap with adjacent slots
            test_coords = (x1, test_y1, x2, test_y2)
            if self._would_overlap_with_adjacent_slots(
                slot_index, test_coords, slot_boundaries
            ):
                continue

            # Test detection at this position
            temp_success, temp_confidence = self._test_slot_detection(
                slot_index, test_coords
            )

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
            shared_config_file = (
                Path(__file__).resolve().parent.parent / "shared_config.json"
            )
            if shared_config_file.exists():
                with open(shared_config_file, "r") as f:
                    gui_config = json.load(f)
            else:
                gui_config = {}

            # Update coordinate information for GUI
            gui_config["ADAPTED_NAMES_4P_COORD"] = self.current_name_positions.copy()
            gui_config["ADAPTED_NUMBER_4P_COORD"] = self.current_number_positions.copy()
            gui_config["ADAPTATION_ACTIVE"] = True
            gui_config["ADAPTATION_HISTORY"] = self.adaptation_history.copy()
            gui_config["OCCUPIED_SLOTS"] = self.occupied_slots.copy()

            with open(shared_config_file, "w") as f:
                json.dump(gui_config, f, indent=4)

            if DEBUG_MODE:
                print("📤 Updated shared config for GUI with adapted coordinates")

        except (OSError, RuntimeError) as e:
            if DEBUG_MODE:
                print(f"❌ Error updating shared config: {e}")

    def _test_slot_detection(self, slot_index, coords):
        """Test if a character slot can be detected at given coordinates"""
        try:
            # Log capture coordinates and verify against overlay
            if DEBUG_MODE:
                print(f"📸 Capturing slot {slot_index} at coords: {coords}")
            image = ImageGrab.grab(bbox=coords)
            cap = np.array(image)
            image.close()
            results = self.reader.readtext(cap, allowlist=ALLOWLIST)

            # Look for character-like text
            for result in results:
                if result[2] > NAME_CONF_THRESH:
                    text = result[1].strip()
                    if len(text) > 2 and self._looks_like_character_name(text):
                        if DEBUG_MODE:
                            print(
                                f"🔍 Slot {slot_index} OCR: '{text}' (confidence: {result[2]:.3f})"
                            )
                        return text, result[
                            2
                        ]  # Return the actual character name text, not True

            # Debug: Log what OCR found but was rejected
            if DEBUG_MODE and results:
                rejected_texts = []
                for result in results:
                    if result[2] > 0.1:  # Log results with at least 10% confidence
                        text = result[1].strip()
                        if len(text) > 1:
                            rejected_texts.append(f"'{text}'({result[2]:.3f})")
                if rejected_texts:
                    print(
                        f"🔍 Slot {slot_index} OCR rejected: {', '.join(rejected_texts)}"
                    )

            return False, 0.0

        except (OSError, RuntimeError) as e:
            if DEBUG_MODE:
                print(f"🔍 Slot {slot_index} OCR error: {e}")
            return False, 0.0

    def _calculate_slot_boundaries(self):
        """Calculate the safe boundaries for each character slot to prevent overlap"""
        boundaries = []

        for i in range(4):
            if i == 0:
                # First slot - only lower boundary
                upper_bound = -float("inf")
                lower_bound = (
                    self.base_name_positions[1][1] - 10
                )  # 10px buffer from next slot
            elif i == 3:
                # Last slot - only upper boundary
                upper_bound = (
                    self.base_name_positions[2][1] + 10
                )  # 10px buffer from previous slot
                lower_bound = float("inf")
            else:
                # Middle slots - both boundaries
                upper_bound = self.base_name_positions[i - 1][1] + 10
                lower_bound = self.base_name_positions[i + 1][1] - 10

            boundaries.append((upper_bound, lower_bound))

        return boundaries

    def _would_overlap_with_adjacent_slots(
        self, slot_index, test_coords, slot_boundaries
    ):
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
        if not re.match(r"^[A-Za-z\s']+$", text):
            return False

        # Should not be common UI words
        ui_words = [
            "menu",
            "party",
            "setup",
            "exit",
            "close",
            "ok",
            "cancel",
            "select",
            "change",
            "ready",
            "waiting",
            "use",
            "item",
            "equip",
        ]
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
            x1, y1, x2, y2 = self.base_number_positions[i]

            # Apply the same vertical shift as the corresponding name position
            name_coords = self.current_name_positions[i]
            name_base_coords = self.base_name_positions[i]

            # Calculate vertical shift from name position adaptation
            name_shift = name_coords[1] - name_base_coords[1]
            adaptive_y1 = y1 + name_shift
            adaptive_y2 = y2 + name_shift

            adaptive_coords.append((x1, adaptive_y1, x2, adaptive_y2))

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
        occupied_indices = [
            i for i, slot in enumerate(self.occupied_slots) if slot is not None
        ]
        print(f"   Occupied slots: {occupied_indices}")
        print(f"   Confidence scores: {[round(c, 2) for c in self.slot_confidence]}")
        print(f"   Adaptations made: {len(self.adaptation_history)}")

        if self.adaptation_history:
            latest = self.adaptation_history[-1]
            print(
                f"   Latest adaptation: Slot {latest['slot']} at {time.time() - latest['timestamp']:.1f}s ago"
            )

        # Show current coordinate values for GUI verification
        print("📍 Current Coordinates (what GUI receives):")
        print(f"   Name positions: {self.current_name_positions}")
        print(f"   Number positions: {self.current_number_positions}")
        print(f"   Base name positions: {self.base_name_positions}")
        print(f"   Base number positions: {self.base_number_positions}")

        # Show vertical shifts
        shifts = []
        for i in range(4):
            name_shift = (
                self.current_name_positions[i][1] - self.base_name_positions[i][1]
            )
            number_shift = (
                self.current_number_positions[i][1] - self.base_number_positions[i][1]
            )
            shifts.append(f"Slot{i}: name={name_shift}px, number={number_shift}px")

        print(f"   Vertical shifts: {shifts}")
