"""
CONFIGURATION FILE

Make sure these coordinates are set up properly before running the script.

See README.md on how to determine coordinates.
"""

USERNAME = "PlayerName"
"""
LEGACY SETTING - Now configured in GUI

For detecting when the main character (Traveler) is being played.

⚠️  IMPORTANT: This setting is now configured in the GUI application.
   Changes made here will be overridden by GUI settings.
   Use the GUI's "Username" field instead.
"""

MC_AETHER = True
"""
LEGACY SETTING - Now configured in GUI

Main character gender setting.
True = Aether (Male), False = Lumine (Female)

⚠️  IMPORTANT: This setting is now configured in the GUI application.
   Changes made here will be overridden by GUI settings.
   Use the GUI's "Main Character" dropdown instead.
"""

WANDERER_NAME = "Wanderer"
"""
LEGACY SETTING - Now configured in GUI

For detecting when Wanderer is active. (Spoiler: You can rename Wanderer)

⚠️  IMPORTANT: This setting is now configured in the GUI application.
   Changes made here will be overridden by GUI settings.
   Use the GUI's "Wanderer Name" field instead.
"""

MANEKIN_NAME = "Manekin"
"""
LEGACY SETTING - Now configured in GUI

For detecting when Wonderland Manekin (male) is active.
Can be renamed in-game.

⚠️  IMPORTANT: This setting is now configured in the GUI application.
   Changes made here will be overridden by GUI settings.
   Use the GUI's "Manekin Name" field instead.
"""

MANEKINA_NAME = "Manekina"
"""
LEGACY SETTING - Now configured in GUI

For detecting when Wonderland Manekina (female) is active.
Can be renamed in-game.

⚠️  IMPORTANT: This setting is now configured in the GUI application.
   Changes made here will be overridden by GUI settings.
   Use the GUI's "Manekina Name" field instead.
"""

GAME_RESOLUTION = 1080
"""
LEGACY SETTING - Now auto-detected

The resolution you're running Genshin at (number corresponds to the
resolution height in pixels).

⚠️  IMPORTANT: This setting is now automatically detected by the script.
   The application will detect your Genshin Impact window size dynamically.
   Manual configuration here is no longer necessary.

NOTE: This setting is rarely needed anymore due to automatic detection.
Only modify if you encounter coordinate detection issues with specific GPU upscaling
configurations (DLDSR/DLSS/NVIDIA Image Sharpening, etc.) or non-standard aspect ratios.

For most users: Leave this setting unchanged - the script will auto-detect correctly.
Advanced users only: If using GPU upscaling that changes the final display resolution,
set this to your monitor's actual resolution, not the game's internal resolution.

Common resolutions (for reference):
720: 1280x720 (720p)
1080: 1920x1080 (1080p)
1440: 2560x1440 (1440p)
2160: 3840x2160 (2160p)
"""

# ______________________________________________________________#
#                                                               #
#                                                               #
#     MANUAL CONFIGURATION OF SCREEN COORDINATES BELOW          #
#                                                               #
#     Only necessary for non-16:9 aspect ratios                 #
#                                                               #
#     Set GAME_RESOLUTION = 0 if using these settings           #
#                                                               #
# ______________________________________________________________#

NUMBER_4P_COORD = [
    (2484, 356, 2514, 386),  # Char 1 - 30x30 box centered at original point
    (2484, 481, 2514, 511),  # Char 2
    (2484, 610, 2514, 640),  # Char 3
    (2484, 735, 2514, 765),  # Char 4
]
"""
List containing bounding box coordinates for character number detection.
Each box should cover the white part of the character number box (1, 2, 3, 4) to the right of the character name.
Format: (top_left_x, top_left_y, bottom_right_x, bottom_right_y)

This is used to determine which character is active and whether the game is paused.
"""

NAMES_4P_COORD = [
    (2166, 320, 2365, 395),  # Character 1
    (2166, 445, 2365, 520),  # Character 2
    (2166, 575, 2365, 650),  # Character 3
    (2166, 705, 2365, 780),  # Character 4
]
"""
Bounding box coordinates of character names in 4-character single player mode.

First list entry --> 1st character, etc...

Each list entry is a tuple representing a rectangle: (top left X, top left Y, bottom right X, bottom right Y)
"""

BOSS_COORD = (700, 20, 1960, 80)
"""
Bounding box coordinates for weekly/world boss name.

(top left X, top left Y, bottom right X, bottom right Y)
"""

LOCATION_COORD = (702, 240, 1838, 345)
"""
Bounding box coordinates for location/"commission accepted" popup

(top left X, top left Y, bottom right X, bottom right Y)
"""

"""
NOTE: Scanning domains/party setup/map location will only occur if active 
      characters cannot be found to conserve processing power.
      If neither domain, active character, nor party setup detected,
      then assume game is paused. Lower detection rate.
"""

MAP_LOC_COORD = (1980, 140, 2520, 260)

# New activity detection region above map location (for additional immersion)
ACTIVITY_COORD = (1880, 20, 2440, 80)

DOMAIN_COORD = (1680, 160, 2420, 260)
"""
Bounding box coordinates for selected domain name.

(top left X, top left Y, bottom right X, bottom right Y)
"""

PARTY_SETUP_COORD = (0, 20, 900, 100)
"""
Bounding box for "Party Setup" text.

(top left X, top left Y, bottom right X, bottom right Y)
"""
# ______________________________________________________________#
#                                                               #
#                                                               #
#                                                               #
#                                                               #
#                                                               #
#     ADVANCED SETTINGS BELOW                                   #
#                                                               #
#     DO NOT TOUCH UNLESS YOU KNOW WHAT YOU'RE DOING            #
#                                                               #
#                                                               #
#                                                               #
#                                                               #
#                                                               #
# ______________________________________________________________#


SLEEP_PER_ITERATION = 0.14
"""
How many seconds to sleep per iteration.

Decrease if location popups are being missed by the OCR detector.

Increase if the script is causing the game to lag.
"""

USE_GPU = True
"""
Try both True and False to see which one runs better.

On a laptop with Ryzen 7 4800H and RTX 2060, CPU causes the game to lag,
GPU works slightly better, but has about 1 minute, once-off 'warm-up' time 
for the OCR inference model to figure out how to work while the game is running.
"""


ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'- "
ALLOWLIST2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890- "
"""
Text characters whitelist to limit OCR results.

Ensure that text chars for place/character/boss/domain names are in this list.
"""

NAME_CONF_THRESH = 0.6
"""
How confident the OCR should be before accepting a character name.

(NOTE: This doesn't need to be too high, as incorrect names will be checked against the database)
"""

LOC_CONF_THRESH = 0.5
"""
How confident the OCR should be before accepting a location name.

(NOTE: This doesn't need to be too high, as incorrect names will be checked against the database)
"""

BOSS_CONF_THRESH = 0.5
"""
How confident the OCR should be before accepting a boss name.

(NOTE: This doesn't need to be too high, as incorrect names will be checked against the database)
"""

DOMAIN_CONF_THRESH = 0.5
"""
How confident the OCR should be before accepting a domain name.

(NOTE: This doesn't need to be too high, as incorrect names will be checked against the database)
"""

INACTIVE_COOLDOWN = 5
"""
For this many iterations after the last time any non-active activity is detected
(e.g. party setup, domain, map), do not scan any other non-active activities.

Prevents misreads/save CPU.
"""

PAUSE_STATE_COOLDOWN = 2
"""
The game pause state must remain consistent for this many iterations before current activity
is updated. This is to prevent misreads.
"""

ACTIVE_CHARACTER_THRESH = 240 * 3
"""
The brightness of the character number pixel should be lower than this value to signify an active character.

This works out of the box, but if in-game gamma/brightness is drastically changed, this value may need to be
adjusted accordingly. (Estimate: 245 for max brightness, 230 for min brightness)

Lower values = more sensitive detection (more likely to detect characters as active)
Higher values = less sensitive detection (less likely to detect characters as active)
"""

OCR_CHARNAMES_ONE_IN = 10
"""Process character name every N loops - FAST DETECTION for responsive character switching"""
OCR_LOC_ONE_IN = 5
"""Process location every N loops - BALANCED FREQUENCY for responsiveness vs performance"""
OCR_BOSS_ONE_IN = 30
"""Process boss name every N loops"""
OCR_DOMAIN_ONE_IN = 30
"""Process domain name every N loops"""
OCR_ENGINE = "rapidocr"
"""
OCR engine to use for text recognition.

RapidOCR is used - it works for detecting Genshin Impact game text and is lightweight.
Uses ONNX Runtime for fast, lightweight text recognition.

Set via environment variable: GENSHIN_OCR_ENGINE=rapidocr
"""

# ----------------------------------------------------------------------------------------------------------

DISC_APP_ID = "944346292568596500"
"""
Discord Application ID for this project's Discord Rich Presence app
(owned and managed by ZANdewanai).
"""

# URL-based asset loading - bypasses Discord's 300 asset limit
USE_URL_ASSETS = True
"""
Enable to use external URLs for images instead of Discord-uploaded assets.
This bypasses Discord's 300 asset limit by hot-loading images from a CDN/hosted location.

When enabled, image keys from CSV files (e.g., 'char_aether', 'boss_anemo_hypostasis')
will be converted to full URLs by prepending ASSET_BASE_URL.

⚠️  IMPORTANT: Discord only supports URLs that:
   - Start with https://
   - Point to a direct image file (jpg, png, etc.)
   - Are publicly accessible without authentication
   - Have proper CORS headers (for Discord client to fetch)

Example: Set ASSET_BASE_URL to a GitHub raw content URL or your own CDN.
"""

# External asset URL configuration
# Can be overridden via environment variable GENSHIN_ASSET_BASE_URL
# Example: Set to your fork's URL if you fork this repository
import os
ASSET_BASE_URL = os.environ.get("GENSHIN_ASSET_BASE_URL", 
    "https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/refs/heads/main/resources/assets/images/")
"""
Base URL for external image assets when USE_URL_ASSETS is True.

The image key from CSV files will be appended to this URL.

To use your own fork or CDN, set the GENSHIN_ASSET_BASE_URL environment variable
or modify the URL above to point to your asset repository.

Examples:
- GitHub (branch): "https://raw.githubusercontent.com/username/repo/refs/heads/main/resources/assets/images/characters/"
- GitHub (tag): "https://raw.githubusercontent.com/username/repo/refs/tags/v1.0.0/assets/"
- Self-hosted CDN: "https://cdn.yoursite.com/genshin-rpc/"
- Imgur (direct links): "https://i.imgur.com/"

Note: For GitHub, use the 'raw.githubusercontent.com' domain for direct file access.
Format: https://raw.githubusercontent.com/USER/REPO/refs/heads/BRANCH/PATH/

The image keys in CSV files (char_aether, boss_anemo_hypostasis, etc.) will be
appended with '.png' extension automatically.

Example full URL construction:
  ASSET_BASE_URL + "char_aether" + ".png"
  = "https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/refs/heads/main/resources/assets/images/characters/char_aether.png"
"""

GENSHIN_WINDOW_NAME = "Genshin Impact"
"""
The exact window caption (window name) of GenshinImpact.exe.

In the future, this may change, so here's how to find it:
- Open task manager list of processes
- Right click the table header, turn on 'PID'
- Download & open WinSpy++, click 'More >>' (bottom right button)
- Open the folder with the same Process ID (PID) as GenshinImpact.exe
- Find the window entry with the window class "UnityWndClass" and the window caption
  "Genshin Impact"

Note that if NVIDIA Freestyle (game filter) is enabled, there will also be
a window with the same window caption, but with the "DXGIWatchdogThreadWindow" class,
hence, it's important to filter out the exact class & window caption.
"""

GENSHIN_WINDOW_CLASS = "UnityWndClass"
"""
The exact window class name of GenshinImpact.exe.

In the future, this may change, so here's how to find it:
- Open task manager list of processes
- Right click the table header, turn on 'PID'
- Download & open WinSpy++, click 'More >>' (bottom right button)
- Open the folder with the same Process ID (PID) as GenshinImpact.exe
- Find the window entry with the window class "UnityWndClass" and the window caption
  "Genshin Impact"

Note that if NVIDIA Freestyle (game filter) is enabled, there will also be
a window with the same window caption, but with the "DXGIWatchdogThreadWindow" class,
hence, it's important to filter out the exact class & window caption.
"""

DEBUG_MODE = True
"""
Set to true to print debug messages.
"""

DEBUG_CHARACTER_MODE = True
"""
Set to true to print character detection debug messages.
Disable to reduce console spam from character detection.
"""

DEBUG_STATIC_IMAGE = False
"""
Set to true to enable static image debug mode.

When enabled, CharSensor will grab its name/number regions from the image
specified by DEBUG_STATIC_IMAGE_PATH instead of the live screen. Useful for
validating OCR/coordinate calibration against a known capture.
"""

DEBUG_STATIC_IMAGE_PATH = r"debug_images\debug_image.jpg"
"""
Path to the static screenshot used when DEBUG_STATIC_IMAGE is True.

The image must be the same resolution as the configured game resolution so
the region coordinates line up (the 2560x1440 coordinates are used as-is).
"""

# Base coordinates for 2560x1440 resolution (1440p)
BASE_RESOLUTION_WIDTH = 2560
BASE_RESOLUTION_HEIGHT = 1440

# Store original coordinates before scaling
# Character number regions now use full bounding boxes (x1, y1, x2, y2) for more robust detection

# CANONICAL PARTY HUD COORDINATES
# Each party size (1P through 5P) has its own coordinate set
# Calibrated from debug_party_N_slots.jpg via calibrate_party_layouts.py
# (stored in sensor_data/party_layouts.json)

# Party 1 (single character - trial/solo)
BASE_NAMES_1P_COORD = [
    (2115, 515, 2380, 600),
]

BASE_NUMBER_1P_COORD = [
    (2450, 545, 2480, 575),
]

# Party 2
BASE_NAMES_2P_COORD = [
    (2115, 395, 2380, 480),
    (2115, 595, 2380, 635),
]

BASE_NUMBER_2P_COORD = [
    (2450, 425, 2480, 455),
    (2450, 600, 2480, 630),
]

# Party 3
BASE_NAMES_3P_COORD = [
    (2115, 375, 2380, 445),
    (2115, 495, 2380, 565),
    (2115, 585, 2380, 685),
]

BASE_NUMBER_3P_COORD = [
    (2450, 400, 2480, 420),
    (2450, 520, 2480, 550),
    (2450, 630, 2480, 660),
]

# Party 4
BASE_NAMES_4P_COORD = [
    (2115, 305, 2380, 375),
    (2115, 465, 2380, 565),
    (2115, 575, 2380, 615),
    (2115, 725, 2380, 795),
]

BASE_NUMBER_4P_COORD = [
    (2450, 335, 2480, 355),
    (2450, 500, 2480, 530),
    (2450, 610, 2480, 640),
    (2450, 755, 2480, 785),
]

# Party 5 (full party)
BASE_NAMES_5P_COORD = [
    (2115, 275, 2380, 315),
    (2115, 385, 2380, 425),
    (2115, 515, 2380, 555),
    (2115, 665, 2380, 735),
    (2115, 755, 2380, 795),
]

BASE_NUMBER_5P_COORD = [
    (2450, 290, 2480, 300),
    (2450, 400, 2480, 420),
    (2450, 530, 2480, 550),
    (2450, 690, 2480, 710),
    (2450, 770, 2480, 780),
]

MAX_PARTY_SLOTS = 5

BASE_ACTIVITY_COORD = (1880, 20, 2436, 77)
BASE_BOSS_COORD = (680, 10, 2005, 110)
BASE_DOMAIN_COORD = (1680, 160, 2416, 257)
BASE_PARTY_SETUP_COORD = (0, 20, 896, 97)
BASE_LOCATION_COORD = (701, 240, 1834, 342)
BASE_MAP_LOC_COORD = (1980, 140, 2516, 257)


def get_dynamic_coordinates():
    """
    Detects the actual Genshin Impact window size and returns scaled coordinates.

    Returns:
        tuple: (scaled_coords_dict, detected_resolution)
        where scaled_coords_dict contains all coordinate arrays scaled to actual window size
    """
    # Minimum reasonable window size for Genshin (width, height)
    MIN_WINDOW_SIZE = (800, 600)

    # Party size -> (names, numbers) base coordinate sets, canonical 1P-5P
    party_sets = {
        1: (BASE_NAMES_1P_COORD, BASE_NUMBER_1P_COORD),
        2: (BASE_NAMES_2P_COORD, BASE_NUMBER_2P_COORD),
        3: (BASE_NAMES_3P_COORD, BASE_NUMBER_3P_COORD),
        4: (BASE_NAMES_4P_COORD, BASE_NUMBER_4P_COORD),
        5: (BASE_NAMES_5P_COORD, BASE_NUMBER_5P_COORD),
    }

    def scaled_party_sets(scale_x, scale_y):
        """Return resolution-scaled per-party-size coordinate dict."""
        out = {}
        for size, (names, numbers) in party_sets.items():
            out[f"NAMES_{size}P_COORD"] = [
                (
                    round(x1 * scale_x), round(y1 * scale_y),
                    round(x2 * scale_x), round(y2 * scale_y),
                )
                for (x1, y1, x2, y2) in names
            ]
            out[f"NUMBER_{size}P_COORD"] = [
                (
                    round(x1 * scale_x), round(y1 * scale_y),
                    round(x2 * scale_x), round(y2 * scale_y),
                )
                for (x1, y1, x2, y2) in numbers
            ]
        return out

    try:
        # Get the actual Genshin window dimensions
        from core import ps_helper

        window_rect = ps_helper.get_genshin_window_rect()
        if window_rect:
            actual_width = window_rect[2] - window_rect[0]  # right - left
            actual_height = window_rect[3] - window_rect[1]  # bottom - top

            # Validate window size - must be at least minimum size
            if actual_width < MIN_WINDOW_SIZE[0] or actual_height < MIN_WINDOW_SIZE[1]:
                if DEBUG_MODE:
                    print(
                        f"Detected window too small ({actual_width}x{actual_height}), using base coordinates"
                    )
                return {
                    **scaled_party_sets(1.0, 1.0),
                    "BOSS_COORD": BASE_BOSS_COORD,
                    "LOCATION_COORD": BASE_LOCATION_COORD,
                    "MAP_LOC_COORD": BASE_MAP_LOC_COORD,
                    "ACTIVITY_COORD": BASE_ACTIVITY_COORD,
                    "DOMAIN_COORD": BASE_DOMAIN_COORD,
                    "PARTY_SETUP_COORD": BASE_PARTY_SETUP_COORD,
                }, (BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT)

            if DEBUG_MODE:
                print(f"Detected Genshin window size: {actual_width}x{actual_height}")

            # Calculate scaling factors
            scale_x = actual_width / BASE_RESOLUTION_WIDTH
            scale_y = actual_height / BASE_RESOLUTION_HEIGHT

            # Scale all coordinate arrays (canonical 1P-5P party sets +
            # the non-party regions)
            scaled_coords = {
                **scaled_party_sets(scale_x, scale_y),
                "BOSS_COORD": (
                    round(BASE_BOSS_COORD[0] * scale_x),
                    round(BASE_BOSS_COORD[1] * scale_y),
                    round(BASE_BOSS_COORD[2] * scale_x),
                    round(BASE_BOSS_COORD[3] * scale_y),
                ),
                "LOCATION_COORD": (
                    round(BASE_LOCATION_COORD[0] * scale_x),
                    round(BASE_LOCATION_COORD[1] * scale_y),
                    round(BASE_LOCATION_COORD[2] * scale_x),
                    round(BASE_LOCATION_COORD[3] * scale_y),
                ),
                "MAP_LOC_COORD": (
                    round(BASE_MAP_LOC_COORD[0] * scale_x),
                    round(BASE_MAP_LOC_COORD[1] * scale_y),
                    round(BASE_MAP_LOC_COORD[2] * scale_x),
                    round(BASE_MAP_LOC_COORD[3] * scale_y),
                ),
                "ACTIVITY_COORD": (
                    round(BASE_ACTIVITY_COORD[0] * scale_x),
                    round(BASE_ACTIVITY_COORD[1] * scale_y),
                    round(BASE_ACTIVITY_COORD[2] * scale_x),
                    round(BASE_ACTIVITY_COORD[3] * scale_y),
                ),
                "DOMAIN_COORD": (
                    round(BASE_DOMAIN_COORD[0] * scale_x),
                    round(BASE_DOMAIN_COORD[1] * scale_y),
                    round(BASE_DOMAIN_COORD[2] * scale_x),
                    round(BASE_DOMAIN_COORD[3] * scale_y),
                ),
                "PARTY_SETUP_COORD": (
                    round(BASE_PARTY_SETUP_COORD[0] * scale_x),
                    round(BASE_PARTY_SETUP_COORD[1] * scale_y),
                    round(BASE_PARTY_SETUP_COORD[2] * scale_x),
                    round(BASE_PARTY_SETUP_COORD[3] * scale_y),
                ),
            }

            return scaled_coords, (actual_width, actual_height)
        else:
            if DEBUG_MODE:
                print("Could not detect Genshin window, using base coordinates")
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error detecting window size: {e}")

    # Fallback to base coordinates if detection fails
    return {
        **scaled_party_sets(1.0, 1.0),
        "BOSS_COORD": BASE_BOSS_COORD,
        "LOCATION_COORD": BASE_LOCATION_COORD,
        "MAP_LOC_COORD": BASE_MAP_LOC_COORD,
        "ACTIVITY_COORD": BASE_ACTIVITY_COORD,
        "DOMAIN_COORD": BASE_DOMAIN_COORD,
        "PARTY_SETUP_COORD": BASE_PARTY_SETUP_COORD,
    }, (BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT)


# Initialize coordinates on import
DYNAMIC_COORDINATES, DETECTED_RESOLUTION = get_dynamic_coordinates()

# Make coordinates available globally
NAMES_1P_COORD = DYNAMIC_COORDINATES["NAMES_1P_COORD"]
NUMBER_1P_COORD = DYNAMIC_COORDINATES["NUMBER_1P_COORD"]
NAMES_2P_COORD = DYNAMIC_COORDINATES["NAMES_2P_COORD"]
NUMBER_2P_COORD = DYNAMIC_COORDINATES["NUMBER_2P_COORD"]
NAMES_3P_COORD = DYNAMIC_COORDINATES["NAMES_3P_COORD"]
NUMBER_3P_COORD = DYNAMIC_COORDINATES["NUMBER_3P_COORD"]
NAMES_4P_COORD = DYNAMIC_COORDINATES["NAMES_4P_COORD"]
NUMBER_4P_COORD = DYNAMIC_COORDINATES["NUMBER_4P_COORD"]
NAMES_5P_COORD = DYNAMIC_COORDINATES["NAMES_5P_COORD"]
NUMBER_5P_COORD = DYNAMIC_COORDINATES["NUMBER_5P_COORD"]
BOSS_COORD = DYNAMIC_COORDINATES["BOSS_COORD"]
LOCATION_COORD = DYNAMIC_COORDINATES["LOCATION_COORD"]
MAP_LOC_COORD = DYNAMIC_COORDINATES["MAP_LOC_COORD"]
ACTIVITY_COORD = DYNAMIC_COORDINATES["ACTIVITY_COORD"]
DOMAIN_COORD = DYNAMIC_COORDINATES["DOMAIN_COORD"]
PARTY_SETUP_COORD = DYNAMIC_COORDINATES["PARTY_SETUP_COORD"]

if __name__ == "__main__":
    print("This is a config file. It is not meant to be run.")
