"""
CONFIGURATION FILE

Core settings for Genshin Impact Rich Presence.
Coordinates are auto-detected from the game window at runtime.
See data/party_layouts.csv and data/region_coords.csv for base coordinates.
"""

import os
import csv
from pathlib import Path

# Advanced detection tuning
SLEEP_PER_ITERATION = 0.14  # seconds per loop iteration

USE_GPU = True  # GPU acceleration for OCR (requires onnxruntime-directml)


ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'- "
ALLOWLIST2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890- "
# OCR character whitelists

NAME_CONF_THRESH = 0.6
LOC_CONF_THRESH = 0.5
BOSS_CONF_THRESH = 0.5
DOMAIN_CONF_THRESH = 0.5
# OCR confidence thresholds for name/location/boss/domain

INACTIVE_COOLDOWN = 5  # iterations to skip non-active scans after last detection
PAUSE_STATE_COOLDOWN = 2  # iterations before confirming pause state
ACTIVE_CHARACTER_THRESH = 240 * 3  # brightness threshold for active character detection

OCR_CHARNAMES_ONE_IN = 10  # process character names every N loops
OCR_LOC_ONE_IN = 5       # process location every N loops
OCR_BOSS_ONE_IN = 30     # process boss name every N loops
OCR_DOMAIN_ONE_IN = 30   # process domain name every N loops
OCR_ENGINE = "rapidocr"  # OCR engine: rapidocr

# ----------------------------------------------------------------------------------------------------------

DISC_APP_ID = "944346292568596500"  # Discord Application ID

# URL-based asset loading - bypasses Discord's 300 asset limit
USE_URL_ASSETS = True
ASSET_BASE_URL = os.environ.get("GENSHIN_ASSET_BASE_URL",
    "https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/refs/heads/main/resources/assets/images/")
# Base URL for external image assets (characters/, bosses/, domains/, locations/, ui/)

GENSHIN_WINDOW_NAME = "Genshin Impact"  # Window caption for GenshinImpact.exe
GENSHIN_WINDOW_CLASS = "UnityWndClass"  # Window class for GenshinImpact.exe

DEBUG_MODE = False  # Print debug messages
DEBUG_CHARACTER_MODE = False  # Print character detection debug messages
DEBUG_SAVE_IMAGES = False  # Save debug screenshots to debug_cache/
DEBUG_STATIC_IMAGE = False  # Use static image for debugging
DEBUG_STATIC_IMAGE_PATH = r"debug_images\debug_image.jpg"  # Static screenshot path

# Base coordinates for 2560x1440 resolution (1440p)
BASE_RESOLUTION_WIDTH = 2560
BASE_RESOLUTION_HEIGHT = 1440
MAX_PARTY_SLOTS = 5

# Data file paths (relative to this file)
_DATA_DIR = Path(__file__).parent / "data"
_PARTY_LAYOUTS_CSV = _DATA_DIR / "party_layouts.csv"
_REGION_COORDS_CSV = _DATA_DIR / "region_coords.csv"


def _load_party_layouts():
    """Load party area bounding box from CSV. Returns (x1, y1, x2, y2) for the single party area."""
    try:
        with open(_PARTY_LAYOUTS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["region"] == "party_area":
                    return (
                        int(row["x1"]), int(row["y1"]),
                        int(row["x2"]), int(row["y2"])
                    )
    except Exception as e:
        if DEBUG_MODE:
            print(f"Warning: Could not load party_layouts.csv: {e}")
    # Fallback to default coordinates
    return (2115, 275, 2380, 795)


def _load_region_coords():
    """Load non-party region coordinates from CSV. Returns dict[region_name] = (x1, y1, x2, y2)."""
    coords = {}
    try:
        with open(_REGION_COORDS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                coords[row["region"].upper() + "_COORD"] = (
                    int(row["x1"]), int(row["y1"]),
                    int(row["x2"]), int(row["y2"])
                )
    except Exception as e:
        if DEBUG_MODE:
            print(f"Warning: Could not load region_coords.csv: {e}")
    return coords


# Load base coordinates at module import
BASE_PARTY_AREA = _load_party_layouts()
BASE_REGION_COORDS = _load_region_coords()

# Single party area bounding box (for CharSensor)
BASE_PARTY_AREA_COORD = BASE_PARTY_AREA

BASE_ACTIVITY_COORD = BASE_REGION_COORDS.get("ACTIVITY_COORD", (1880, 20, 2436, 77))
BASE_BOSS_COORD = BASE_REGION_COORDS.get("BOSS_COORD", (680, 10, 2005, 110))
BASE_DOMAIN_COORD = BASE_REGION_COORDS.get("DOMAIN_COORD", (1680, 160, 2416, 257))
BASE_PARTY_SETUP_COORD = BASE_REGION_COORDS.get("PARTY_SETUP_COORD", (0, 20, 896, 97))
BASE_LOCATION_COORD = BASE_REGION_COORDS.get("LOCATION_COORD", (701, 240, 1834, 342))
BASE_MAP_LOC_COORD = BASE_REGION_COORDS.get("MAP_LOC_COORD", (1980, 140, 2516, 257))

# Module-level coordinate variables (initialized to base, updated by get_dynamic_coordinates)
PARTY_AREA_COORD = BASE_PARTY_AREA
BOSS_COORD = BASE_BOSS_COORD
LOCATION_COORD = BASE_LOCATION_COORD
MAP_LOC_COORD = BASE_MAP_LOC_COORD
ACTIVITY_COORD = BASE_ACTIVITY_COORD
DOMAIN_COORD = BASE_DOMAIN_COORD
PARTY_SETUP_COORD = BASE_PARTY_SETUP_COORD

DETECTED_RESOLUTION = (BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT)
# Screen-space origin (left, top) of the Genshin client area. Base coords are
# window-relative; OCR capture (ImageGrab) uses absolute screen coords, so
# every published coordinate below already has this offset baked in.
WINDOW_ORIGIN = (0, 0)


def _base_coords_dict():
    return {
        "PARTY_AREA_COORD": BASE_PARTY_AREA,
        "BOSS_COORD": BASE_BOSS_COORD,
        "LOCATION_COORD": BASE_LOCATION_COORD,
        "MAP_LOC_COORD": BASE_MAP_LOC_COORD,
        "ACTIVITY_COORD": BASE_ACTIVITY_COORD,
        "DOMAIN_COORD": BASE_DOMAIN_COORD,
        "PARTY_SETUP_COORD": BASE_PARTY_SETUP_COORD,
    }


def get_dynamic_coordinates():
    """
    Detects the actual Genshin Impact client area and returns scaled,
    screen-absolute coordinates (base coords scaled to the client size and
    offset by the client origin). Updates module-level coordinate variables.
    """
    global PARTY_AREA_COORD, BOSS_COORD, LOCATION_COORD, MAP_LOC_COORD
    global ACTIVITY_COORD, DOMAIN_COORD, PARTY_SETUP_COORD, DETECTED_RESOLUTION
    global WINDOW_ORIGIN

    # Minimum reasonable window size for Genshin (width, height)
    MIN_WINDOW_SIZE = (800, 600)

    # Import ps_helper to avoid circular import with core.detection
    from core import ps_helper

    try:
        # Get the actual Genshin client-area dimensions + screen origin
        client = ps_helper.get_genshin_client_rect()
        if client:
            origin_x, origin_y, actual_width, actual_height = client

            if actual_width < MIN_WINDOW_SIZE[0] or actual_height < MIN_WINDOW_SIZE[1]:
                if DEBUG_MODE:
                    print(
                        f"Detected window too small ({actual_width}x{actual_height}), using base coordinates"
                    )
                WINDOW_ORIGIN = (0, 0)
                return _base_coords_dict(), (BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT)

            if DEBUG_MODE:
                print(
                    f"Detected Genshin client area: {actual_width}x{actual_height} "
                    f"at ({origin_x},{origin_y})"
                )

            scale_x = actual_width / BASE_RESOLUTION_WIDTH
            scale_y = actual_height / BASE_RESOLUTION_HEIGHT

            def scaled(coord):
                return (
                    round(coord[0] * scale_x) + origin_x,
                    round(coord[1] * scale_y) + origin_y,
                    round(coord[2] * scale_x) + origin_x,
                    round(coord[3] * scale_y) + origin_y,
                )

            PARTY_AREA_COORD = scaled(BASE_PARTY_AREA)
            BOSS_COORD = scaled(BASE_BOSS_COORD)
            LOCATION_COORD = scaled(BASE_LOCATION_COORD)
            MAP_LOC_COORD = scaled(BASE_MAP_LOC_COORD)
            ACTIVITY_COORD = scaled(BASE_ACTIVITY_COORD)
            DOMAIN_COORD = scaled(BASE_DOMAIN_COORD)
            PARTY_SETUP_COORD = scaled(BASE_PARTY_SETUP_COORD)
            DETECTED_RESOLUTION = (actual_width, actual_height)
            WINDOW_ORIGIN = (origin_x, origin_y)

            return {
                "PARTY_AREA_COORD": PARTY_AREA_COORD,
                "BOSS_COORD": BOSS_COORD,
                "LOCATION_COORD": LOCATION_COORD,
                "MAP_LOC_COORD": MAP_LOC_COORD,
                "ACTIVITY_COORD": ACTIVITY_COORD,
                "DOMAIN_COORD": DOMAIN_COORD,
                "PARTY_SETUP_COORD": PARTY_SETUP_COORD,
            }, (actual_width, actual_height)
        else:
            if DEBUG_MODE:
                print("Could not detect Genshin window, using base coordinates")
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error detecting window size: {e}")

    # Fallback to base coordinates if detection fails
    WINDOW_ORIGIN = (0, 0)
    coords = _base_coords_dict()
    PARTY_AREA_COORD = coords["PARTY_AREA_COORD"]
    BOSS_COORD = coords["BOSS_COORD"]
    LOCATION_COORD = coords["LOCATION_COORD"]
    MAP_LOC_COORD = coords["MAP_LOC_COORD"]
    ACTIVITY_COORD = coords["ACTIVITY_COORD"]
    DOMAIN_COORD = coords["DOMAIN_COORD"]
    PARTY_SETUP_COORD = coords["PARTY_SETUP_COORD"]
    DETECTED_RESOLUTION = (BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT)

    return coords, DETECTED_RESOLUTION


def reload_coordinate_data():
    """Re-read party_layouts.csv / region_coords.csv and recompute coords.

    Called by the coordinator when the CSVs' mtimes change (hot reload).
    """
    global BASE_PARTY_AREA, BASE_PARTY_AREA_COORD, BASE_REGION_COORDS
    global BASE_ACTIVITY_COORD, BASE_BOSS_COORD, BASE_DOMAIN_COORD
    global BASE_PARTY_SETUP_COORD, BASE_LOCATION_COORD, BASE_MAP_LOC_COORD

    BASE_PARTY_AREA = _load_party_layouts()
    BASE_PARTY_AREA_COORD = BASE_PARTY_AREA
    BASE_REGION_COORDS = _load_region_coords()
    BASE_ACTIVITY_COORD = BASE_REGION_COORDS.get("ACTIVITY_COORD", BASE_ACTIVITY_COORD)
    BASE_BOSS_COORD = BASE_REGION_COORDS.get("BOSS_COORD", BASE_BOSS_COORD)
    BASE_DOMAIN_COORD = BASE_REGION_COORDS.get("DOMAIN_COORD", BASE_DOMAIN_COORD)
    BASE_PARTY_SETUP_COORD = BASE_REGION_COORDS.get("PARTY_SETUP_COORD", BASE_PARTY_SETUP_COORD)
    BASE_LOCATION_COORD = BASE_REGION_COORDS.get("LOCATION_COORD", BASE_LOCATION_COORD)
    BASE_MAP_LOC_COORD = BASE_REGION_COORDS.get("MAP_LOC_COORD", BASE_MAP_LOC_COORD)
    if DEBUG_MODE:
        print("Reloaded coordinate CSVs")
    get_dynamic_coordinates()


# Initialize coordinates on import
get_dynamic_coordinates()