"""
Game State Detector module for Genshin Impact Rich Presence.

Handles detection of characters, locations, bosses, domains, and game state.
"""

import time
from typing import List, Optional, Tuple
from collections import Counter

from PIL import Image
from ..datatypes import *
from ..ocr.ocr_engine import OCREngine


class GameStateDetector:
    """
    Detects various game states including characters, locations, bosses, and domains.
    """

    def __init__(self, data: Data, ocr_engine: OCREngine,
                 config: dict):
        """
        Initialize game state detector.

        Args:
            data: Game data instance
            ocr_engine: OCR engine instance
            config: Configuration dictionary with coordinates and settings
        """
        self.data = data
        self.ocr_engine = ocr_engine
        self.config = config

        # Extract configuration values
        self.number_4p_coord = config.get('NUMBER_4P_COORD', [])
        self.names_4p_coord = config.get('NAMES_4P_COORD', [])
        self.boss_coord = config.get('BOSS_COORD', [])
        self.location_coord = config.get('LOCATION_COORD', [])
        self.domain_coord = config.get('DOMAIN_COORD', [])
        self.game_menu_coord = config.get('GAME_MENU_COORD', [])

        self.active_character_thresh = config.get('ACTIVE_CHARACTER_THRESH', 0)
        self.allowlist = config.get('ALLOWLIST', '')
        self.allowlist2 = config.get('ALLOWLIST2', '')
        self.loc_conf_thresh = config.get('LOC_CONF_THRESH', 0.7)
        self.name_conf_thresh = config.get('NAME_CONF_THRESH', 0.7)
        self.ocr_charnames_one_in = config.get('OCR_CHARNAMES_ONE_IN', 1)
        self.ocr_boss_one_in = config.get('OCR_BOSS_ONE_IN', 1)
        self.ocr_loc_one_in = config.get('OCR_LOC_ONE_IN', 1)

        # Individual debug flags
        self.debug_location = config.get('DEBUG_LOCATION', False)
        self.debug_character = config.get('DEBUG_CHARACTER', False)
        self.debug_boss = config.get('DEBUG_BOSS', False)
        self.debug_domain = config.get('DEBUG_DOMAIN', False)
        self.debug_game_menu = config.get('DEBUG_GAME_MENU', False)

        # Initialize components
        self.ocr_engine = OCREngine(
            debug_mode=config.get('DEBUG_MODE', False),
            debug_save_images=config.get('DEBUG_SAVE_IMAGES', False),
            debug_images_directory=config.get('DEBUG_IMAGES_DIRECTORY', './debug_images')
        )

        # Set the game_state_detector reference in OCR engine
        self.ocr_engine.game_state_detector = self

    def detect_active_character(self, game_window_rect: Optional[Tuple] = None) -> Tuple[int, List[int]]:
        """
        Detect which character is currently active.

        Args:
            game_window_rect: Game window rectangle
{{ ... }}

        Returns:
            Tuple of (active_character_index, brightness_values)
        """
        charnumber_cap = []
        character_indicator_brightness = [0, 0, 0, 0]  # Initialize with default values

        for i in range(4):
            try:
                # Get the coordinates for this character with bounds checking
                if i < len(self.number_4p_coord):
                    coords = self.number_4p_coord[i]
                    # Convert to tuple if it's not already
                    if not isinstance(coords, (list, tuple)):
                        coords = tuple(coords) if hasattr(coords, '__iter__') else (0, 0, 0, 0)

                    # Ensure we have valid coordinates
                    if len(coords) >= 2:  # At least need x,y coordinates
                        # For single-pixel coordinates, create a small region around it
                        if len(coords) == 2:
                            x, y = coords[0], coords[1]
                            region = (x, y, x+1, y+1)
                        else:
                            region = (coords[0], coords[1], coords[2], coords[3])

                        # Capture the region
                        cap = self.ocr_engine.capture_game_region(region, game_window_rect)
                        if cap is not None:
                            charnumber_cap.append(Image.fromarray(cap))
                            # Calculate brightness for active character detection
                            if len(coords) == 2:  # Single pixel
                                pixel = cap[0, 0] if len(cap.shape) == 3 else cap[0, 0]
                                # Convert to int to avoid overflow warnings when summing uint8 values
                                if len(pixel) >= 3:
                                    character_indicator_brightness[i] = int(pixel[0]) + int(pixel[1]) + int(pixel[2])
                                else:
                                    character_indicator_brightness[i] = int(pixel[0])
                            continue

                # If we get here, something went wrong with the capture
                charnumber_cap.append(None)
                character_indicator_brightness[i] = 0

            except Exception as e:
                if self.ocr_engine.debug_mode:
                    print(f"[DEBUG] Error processing character {i+1}: {str(e)}")
                charnumber_cap.append(None)
                character_indicator_brightness[i] = 0

        # Determine which character is active based on brightness threshold
        active_character = [
            character_index
            for character_index, brightness in enumerate(character_indicator_brightness)
            if brightness < self.active_character_thresh
        ]

        found_active_character = len(active_character) == 1
        active_character_index = active_character[0] + 1 if found_active_character else 0

        return active_character_index, character_indicator_brightness

    def detect_party_members(self, game_window_rect: Optional[Tuple] = None,
                           force_update: bool = False) -> List[Optional[Character]]:
        """
        Detect current party members.

        Args:
            game_window_rect: Game window rectangle
            force_update: Force OCR even if characters already detected

        Returns:
            List of detected characters (4 elements, None if not detected)
        """
        current_characters = [None, None, None, None]

        try:
            charname_cap = []
            for i in range(4):
                # Get the coordinates for this character's name
                coords = self.names_4p_coord[i]
                # Capture the region
                cap = self.ocr_engine.capture_game_region((
                    coords[0], coords[1], coords[2], coords[3]
                ), game_window_rect)
                if cap is not None:
                    charname_cap.append(cap)
                else:
                    charname_cap.append(None)

            # Process each character's name with OCR
            for character_index, img in enumerate(charname_cap):
                if img is None:
                    continue

                try:
                    # Perform OCR on the character name image
                    text = self.ocr_engine.extract_text_from_image(
                        img,
                        config=f'--psm 6 -c tessedit_char_whitelist={self.allowlist}',
                        region_name=f"character_{character_index + 1}"
                    )

                    if text:  # Only process if we got some text
                        char = self.data.search_character(text)
                        if char is not None:
                            current_characters[character_index] = char

                except Exception as e:
                    if self.ocr_engine.debug_mode and self.debug_character:
                        print(f"[DEBUG] Error processing character {character_index + 1} name: {e}")

        except Exception as e:
            if self.ocr_engine.debug_mode and self.debug_character:
                print(f"[DEBUG] Error in detect_party_members: {e}")

        return current_characters

    def detect_location(self, game_window_rect: Optional[Tuple] = None) -> Optional[Location]:
        """
        Detect current location using multi-attempt OCR for reliability.

        Args:
            game_window_rect: Game window rectangle

        Returns:
            Detected location or None if not found
        """
        try:
            # Get the location coordinates
            coords = self.location_coord
            # Capture the region
            loc_cap = self.ocr_engine.capture_game_region((
                coords[0], coords[1], coords[2], coords[3]
            ), game_window_rect)

            if loc_cap is None:
                return None

            # Use PARALLEL OCR processing for much faster text detection
            # Take 6 screenshots rapidly, then process them all in parallel
            location_text = self.ocr_engine.extract_text_from_region_parallel(
                (coords[0], coords[1], coords[2], coords[3]),
                config=f'--psm 7 -c tessedit_char_whitelist={self.allowlist + ","}',
                game_window_rect=game_window_rect,
                num_captures=6  # 6 rapid screenshots
            )

            if location_text and len(location_text.strip()) > 2 and not any(char.isdigit() for char in location_text):
                # Check if this looks like a commission activity
                if "mission accept" in location_text.lower():
                    return None  # This is handled separately as commissions

                # Search for the location in the database
                location = self.data.search_location(location_text, self.loc_conf_thresh)
                if location is not None:
                    if self.ocr_engine.debug_mode and self.debug_location:
                        print(f"[DEBUG] Location OCR: Detected '{location_text}' -> '{location.location_name}'")
                    return location

            return None

        except Exception as e:
            if self.ocr_engine.debug_mode and self.debug_location:
                print(f"[DEBUG] Error in detect_location: {e}")
            return None

    def detect_boss(self, game_window_rect: Optional[Tuple] = None) -> Optional[Boss]:
        """
        Detect current boss.

        Args:
            game_window_rect: Game window rectangle

        Returns:
            Detected boss or None if not found
        """
        try:
            boss_cap = self.ocr_engine.capture_game_region(self.boss_coord, game_window_rect)
            if boss_cap is None:
                return None

            # Extract text using OCR
            boss_text = self.ocr_engine.extract_text_from_image(
                boss_cap,
                config=f'--psm 6 -c tessedit_char_whitelist={self.allowlist}',
                region_name="boss"
            )

            boss_text = self.ocr_engine.clean_ocr_text(boss_text)

            if len(boss_text) > 0:
                boss = self.data.search_boss(boss_text)
                return boss

        except Exception as e:
            if self.ocr_engine.debug_mode and self.debug_boss:
                print(f"[DEBUG] Error in detect_boss: {e}")

        return None

    def detect_game_menu(self, game_window_rect: Optional[Tuple] = None) -> Optional[GameMenu]:
        """
        Detect current game menu.

        Args:
            game_window_rect: Game window rectangle

        Returns:
            Detected game menu or None if not found
        """
        try:
            # Get the game menu coordinates
            coords = self.game_menu_coord
            # Capture the region
            game_menu_cap = self.ocr_engine.capture_game_region((
                coords[0], coords[1], coords[2], coords[3]
            ), game_window_rect)

            if game_menu_cap is None:
                return None

            # Extract text using OCR
            game_menu_text = self.ocr_engine.extract_text_from_image(
                game_menu_cap,
                config=f'--psm 6 -c tessedit_char_whitelist={self.allowlist2}',
                region_name="game_menu"
            )

            game_menu_text = self.ocr_engine.clean_ocr_text(game_menu_text)

            if len(game_menu_text) > 0:
                game_menu = self.data.search_game_menu(game_menu_text)
                return game_menu

        except Exception as e:
            if self.ocr_engine.debug_mode and self.debug_game_menu:
                print(f"[DEBUG] Error in detect_game_menu: {e}")

        return None

    def detect_domain(self, game_window_rect: Optional[Tuple] = None) -> Optional[Domain]:
        """
        Detect current domain using multiple PSM modes for better accuracy.

        Args:
            game_window_rect: Game window rectangle

        Returns:
            Detected domain or None if not found
        """
        try:
            domain_cap = self.ocr_engine.capture_game_region(self.domain_coord, game_window_rect)
            if domain_cap is None:
                return None

            # Try different PSM modes to see which one works best
            domain_texts = []
            for psm in [6, 7, 8, 10, 11]:
                try:
                    # Preprocess the image
                    processed_img = self.ocr_engine.preprocess_image_for_ocr(domain_cap, "domain")

                    # Try with different configurations
                    text = self.ocr_engine.extract_text_from_image(
                        processed_img,
                        config=f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\'\"-.,()[]!? ',
                        preprocess=False,  # Already preprocessed
                        region_name="domain"
                    )

                    if text and len(text) > 2:  # Only consider text with more than 2 characters
                        domain_texts.append((psm, text))
                        if self.ocr_engine.debug_mode and self.debug_domain:
                            print(f"PSM {psm}: {text}")
                except Exception as e:
                    if self.ocr_engine.debug_mode and self.debug_domain:
                        print(f"Error with PSM {psm}: {e}")

            if domain_texts:
                if self.ocr_engine.debug_mode and self.debug_domain:
                    print("\n=== DOMAIN DETECTION DEBUG ===")
                    print(f"Tried PSM modes: {[m for m, _ in domain_texts]}")
                    print(f"OCR Results: {[(m, t) for m, t in domain_texts]}")

                # Use the result with the most non-whitespace characters
                best_psm, best_text = max(domain_texts, key=lambda x: len(x[1].strip()))
                if self.ocr_engine.debug_mode and self.debug_domain:
                    print(f"Best PSM: {best_psm}, Text: {best_text}")

                # Search for domain in the database
                domain = self.data.search_domain(best_text)
                return domain

        except Exception as e:
            if self.ocr_engine.debug_mode and self.debug_domain:
                print(f"Error in domain detection: {e}")

        return None

    def debug_all_detection_methods(self) -> dict:
        """
        Debug method to test all detection methods.

        Returns:
            Dictionary with detection results and analysis
        """
        if not self.ocr_engine.debug_mode:
            print("[DEBUG] Debug mode not enabled")
            return {}

        print(f"\n{'='*60}")
        print("GAME STATE DETECTOR DEBUG - ALL DETECTION METHODS")
        print(f"{'='*60}")

        results = {}

        # Test active character detection
        print(f"\n--- Testing ACTIVE CHARACTER DETECTION ---")
        try:
            active_char, brightness_values = self.detect_active_character()
            print(f"   Active character: {active_char}")
            print(f"   Brightness values: {brightness_values}")
            print(f"   Threshold: {self.active_character_thresh}")

            results["active_character"] = {
                "success": True,
                "active_character": active_char,
                "brightness_values": brightness_values
            }
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results["active_character"] = {"success": False, "error": str(e)}

        # Test party members detection
        print(f"\n--- Testing PARTY MEMBERS DETECTION ---")
        try:
            party_members = self.detect_party_members()
            detected = sum(1 for c in party_members if c is not None)
            print(f"   Detected {detected}/4 characters")

            for i, char in enumerate(party_members):
                if char:
                    print(f"     Character {i+1}: {char.character_display_name}")
                else:
                    print(f"     Character {i+1}: Not detected")

            results["party_members"] = {
                "success": True,
                "detected_count": detected,
                "characters": party_members
            }
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results["party_members"] = {"success": False, "error": str(e)}

        # Test location detection
        print(f"\n--- Testing LOCATION DETECTION ---")
        try:
            location = self.detect_location()
            if location:
                print(f"   Location: {location.location_name}")
                print(f"   Confidence threshold: {self.loc_conf_thresh}")
            else:
                print("   No location detected")

            results["location"] = {
                "success": True,
                "location": location
            }
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results["location"] = {"success": False, "error": str(e)}

        # Test boss detection
        print(f"\n--- Testing BOSS DETECTION ---")
        try:
            boss = self.detect_boss()
            if boss:
                print(f"   Boss: {boss.boss_name}")
            else:
                print("   No boss detected")

            results["boss"] = {
                "success": True,
                "boss": boss
            }
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results["boss"] = {"success": False, "error": str(e)}

        # Test domain detection
        print(f"\n--- Testing DOMAIN DETECTION ---")
        try:
            domain = self.detect_domain()
            if domain:
                print(f"   Domain: {domain.domain_name}")
            else:
                print("   No domain detected")

            results["domain"] = {
                "success": True,
                "domain": domain
            }
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results["domain"] = {"success": False, "error": str(e)}

        # Test game menu detection
        print(f"\n--- Testing GAME MENU DETECTION ---")
        try:
            game_menu = self.detect_game_menu()
            if game_menu:
                print(f"   Game menu: {game_menu.game_menu_name}")
            else:
                print("   No game menu detected")

            results["game_menu"] = {
                "success": True,
                "game_menu": game_menu
            }
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results["game_menu"] = {"success": False, "error": str(e)}

        # Summary
        self._print_detection_summary(results)
        return results

    def _print_detection_summary(self, results: dict):
        """Print a summary of detection results."""
        print(f"\n{'='*60}")
        print("GAME STATE DETECTOR DEBUG SUMMARY")
        print(f"{'='*60}")

        success_count = sum(1 for r in results.values() if r.get("success", False))
        total_tests = len(results)

        print(f"Detection methods tested: {total_tests}")
        print(f"Successful detections: {success_count}")

        # Show details for each test
        print(f"\nResults:")
        for method, result in results.items():
            success = result.get("success", False)
            status = "✅" if success else "❌"
            print(f"  {method.upper()}: {status}")

            if success:
                if method == "active_character":
                    active = result.get("active_character", 0)
                    print(f"    Active character: {active}")
                elif method == "party_members":
                    detected = result.get("detected_count", 0)
                    print(f"    Characters detected: {detected}/4")
                elif method == "location" and result.get("location"):
                    location = result["location"]
                    print(f"    Location: {location.location_name}")
                elif method == "boss" and result.get("boss"):
                    boss = result["boss"]
                    print(f"    Boss: {boss.boss_name}")
                elif method == "domain" and result.get("domain"):
                    domain = result["domain"]
                    print(f"    Domain: {domain.domain_name}")
                elif method == "game_menu" and result.get("game_menu"):
                    game_menu = result["game_menu"]
                    print(f"    Game menu: {game_menu.game_menu_name}")

        print(f"\nOverall: {success_count}/{total_tests} detection methods working")

        if success_count == total_tests:
            print("🎉 All detection methods working correctly!")
        elif success_count >= total_tests // 2:
            print("⚠️  Some detection methods have issues")
        else:
            print("❌ Multiple detection methods failing")

    def debug_specific_detection(self, detection_type: str) -> dict:
        """
        Debug a specific detection method individually.

        Args:
            detection_type: Type of detection to debug ('character', 'location', 'boss', 'domain', 'menu')

        Returns:
            Dictionary with debug results for the specific detection
        """
        if not self.ocr_engine.debug_mode:
            print(f"[DEBUG] Debug mode not enabled - skipping {detection_type} test")
            return {}

        detection_methods = {
            'character': self.detect_active_character,
            'location': self.detect_location,
            'boss': self.detect_boss,
            'domain': self.detect_domain,
            'menu': self.detect_game_menu
        }

        if detection_type not in detection_methods:
            print(f"❌ Unknown detection type: {detection_type}")
            return {"error": f"Unknown detection type: {detection_type}"}

        method = detection_methods[detection_type]

        print(f"\n{'🔍'} DEBUGGING: {detection_type.upper()} DETECTION")
        print(f"{'─'*50}")

        results = {"detection_type": detection_type}

        try:
            if detection_type == 'character':
                # Special handling for character detection
                active_char, brightness_values = method()
                print(f"📊 Active character: {active_char}")
                print(f"📊 Brightness values: {brightness_values}")
                print(f"📊 Threshold: {self.active_character_thresh}")

                results.update({
                    "success": True,
                    "active_character": active_char,
                    "brightness_values": brightness_values,
                    "threshold": self.active_character_thresh
                })

            else:
                # Standard detection
                detected_item = method()
                if detected_item:
                    if detection_type == 'location':
                        print(f"📍 Location: {detected_item.location_name}")
                        print(f"📍 Confidence threshold: {self.loc_conf_thresh}")
                        results.update({
                            "success": True,
                            "location": detected_item.location_name,
                            "confidence_threshold": self.loc_conf_thresh
                        })
                    elif detection_type == 'boss':
                        print(f"👹 Boss: {detected_item.boss_name}")
                        results.update({
                            "success": True,
                            "boss": detected_item.boss_name
                        })
                    elif detection_type == 'domain':
                        print(f"🏛️ Domain: {detected_item.domain_name}")
                        results.update({
                            "success": True,
                            "domain": detected_item.domain_name
                        })
                    elif detection_type == 'menu':
                        print(f"📋 Game menu: {detected_item.game_menu_name}")
                        results.update({
                            "success": True,
                            "game_menu": detected_item.game_menu_name
                        })
                else:
                    print(f"❌ No {detection_type} detected")
                    results.update({
                        "success": False,
                        "error": f"No {detection_type} detected"
                    })

        except Exception as e:
            print(f"❌ Error in {detection_type} detection: {e}")
            results.update({
                "success": False,
                "error": str(e)
            })

        return results

    def debug_detection_comparison(self, detection_types: list = None) -> dict:
        """
        Compare multiple detection methods.

        Args:
            detection_types: List of detection types to compare (optional, defaults to all)

        Returns:
            Dictionary with comparison results
        """
        if detection_types is None:
            detection_types = ['character', 'location', 'boss', 'domain', 'menu']

        if not self.ocr_engine.debug_mode:
            print("[DEBUG] Debug mode not enabled")
            return {}

        print(f"\n{'🔍'} DETECTION COMPARISON DEBUG")
        print(f"{'─'*50}")

        results = {}

        for detection_type in detection_types:
            print(f"\n🔎 Testing: {detection_type}")
            detection_results = self.debug_specific_detection(detection_type)

            if detection_results.get("success", False):
                print(f"   ✅ Success: {detection_results}")
                results[detection_type] = detection_results
            else:
                print(f"   ❌ Failed: {detection_results.get('error', 'Unknown error')}")
                results[detection_type] = detection_results

        # Summary
        successful_detections = sum(1 for r in results.values() if r.get("success", False))
        print(f"\n📊 Summary: {successful_detections}/{len(results)} detection methods working")

        return results


