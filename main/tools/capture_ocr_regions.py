#!/usr/bin/env python3
"""
Script to capture and save images of all OCR regions for debugging.
Run this while Genshin Impact is running to see exactly what areas are being OCR'd.
"""

import numpy as np
from PIL import ImageGrab, ImageDraw
import os

# Import config to get coordinates
from CONFIG import *

def capture_and_save_region(coord, name, folder="debug_images"):
    """Capture a screen region and save it as an image."""
    try:
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
    capture_and_save_region(GAME_MENU_COORD, "game_menu_ocr_region")
    capture_and_save_region(DOMAIN_COORD, "domain_ocr_region")
    capture_and_save_region(MAP_LOC_COORD, "map_location_ocr_region")
    capture_and_save_region(NAMES_4P_COORD, "character_names_ocr_region")

    print("=" * 50)
    print("All OCR regions captured! Check the 'debug_images' folder.")
    print("\nRegion explanations:")
    print("- location_ocr_region.png: Where location names appear (top of screen)")
    print("- boss_ocr_region.png: Where boss names appear during fights")
    print("- gamemenu_ocr_region.png: Where 'Game Menu' text appears")
    print("- domain_ocr_region.png: Where domain names appear")
    print("- map_location_ocr_region.png: Where location names appear on the map")
    print("- character_names_ocr_region_X.png: Where each party member's name appears (4 images)")

if __name__ == "__main__":
    main()
