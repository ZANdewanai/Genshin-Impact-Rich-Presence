#!/usr/bin/env python3
"""
Script to capture and save images of all OCR regions for debugging.
Run this while Genshin Impact is running to see exactly what areas are being OCR'd.

Usage: python tools/capture_ocr_regions.py
"""

import numpy as np
from PIL import ImageGrab, ImageDraw
import os
import sys

# Add parent directory to path to import from core/
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import coordinates from CONFIG (now imports core.ps_helper locally)
from CONFIG import (
    LOCATION_COORD, BOSS_COORD, PARTY_SETUP_COORD, DOMAIN_COORD,
    MAP_LOC_COORD, ACTIVITY_COORD, NAMES_4P_COORD, NUMBER_4P_COORD
)


def capture_and_save_region(coord, name, folder="debug_images"):
    """Capture a screen region and save it as an image."""
    try:
        # Ensure debug folder exists
        os.makedirs(folder, exist_ok=True)
        
        # Capture the region
        if isinstance(coord[0], (list, tuple)):  # Multiple coordinates (like character names)
            for i, single_coord in enumerate(coord):
                img = ImageGrab.grab(bbox=single_coord)
                filename = f"{folder}/{name}_{i+1}.png"
                img.save(filename)
                print(f"Saved: {filename} (size: {img.size})")
        else:  # Single coordinate
            img = ImageGrab.grab(bbox=coord)
            filename = f"{folder}/{name}.png"
            img.save(filename)
            print(f"Saved: {filename} (size: {img.size})")

    except Exception as e:
        print(f"Error capturing {name}: {e}")


def main():
    print("Capturing OCR regions... Make sure Genshin Impact is running!")
    print("=" * 50)

    # Create debug folder if it doesn't exist
    os.makedirs("debug_images", exist_ok=True)

    # Capture all OCR regions
    capture_and_save_region(LOCATION_COORD, "location_ocr_region")
    capture_and_save_region(BOSS_COORD, "boss_ocr_region")
    capture_and_save_region(PARTY_SETUP_COORD, "party_setup_ocr_region")
    capture_and_save_region(DOMAIN_COORD, "domain_ocr_region")
    capture_and_save_region(MAP_LOC_COORD, "map_location_ocr_region")
    capture_and_save_region(ACTIVITY_COORD, "activity_ocr_region")
    capture_and_save_region(NAMES_4P_COORD, "character_names_ocr_region")
    capture_and_save_region(NUMBER_4P_COORD, "character_numbers_ocr_region")

    print("=" * 50)
    print("All OCR regions captured! Check the 'debug_images' folder.")
    print("\nRegion explanations:")
    print("- location_ocr_region.png: Where location names appear (top of screen)")
    print("- boss_ocr_region.png: Where boss names appear during fights")
    print("- party_setup_ocr_region.png: Where 'Party Setup' text appears")
    print("- domain_ocr_region.png: Where domain names appear")
    print("- map_location_ocr_region.png: Where location names appear on the map")
    print("- activity_ocr_region.png: Where activity text appears (above map)")
    print("- character_names_ocr_region_X.png: Where each party member's name appears (4 images)")
    print("- character_numbers_ocr_region_X.png: Where each party member's number appears (4 images)")


if __name__ == "__main__":
    main()
