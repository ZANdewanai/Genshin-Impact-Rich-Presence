"""
CONFIGURATION FILE

Make sure these coordinates are set up properly before running the script.

See README.md on how to determine coordinates.
"""

import ps_helper

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
    (2484, 356),  # Char 1
    (2484, 481),  # Char 2
    (2484, 610),  # Char 3
    (2484, 735),  # Char 4
]
"""
List containing coordinates of single pixels. 
Each pixel should be the white part of the character number box (1, 2, 3, 4) to the right of the character name.

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
OCR_ENGINE = "easyocr"
"""
OCR engine to use for text recognition.

Only EasyOCR is supported - it actually works for detecting Genshin Impact game text.
PaddleOCR and Tesseract were tested but don't work for game UI text detection.

Set via environment variable: GENSHIN_OCR_ENGINE=easyocr
"""

# ----------------------------------------------------------------------------------------------------------

DISC_APP_ID = "944346292568596500"
"""
Discord Application ID of euwbah's genshin-rpc discord app.
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

DEBUG_CHARACTER_MODE = False
"""
Set to true to print character detection debug messages.
Disable to reduce console spam from character detection.
"""

# Base coordinates for 2560x1440 resolution (1440p)
BASE_RESOLUTION_WIDTH = 2560
BASE_RESOLUTION_HEIGHT = 1440

# Store original coordinates before scaling
BASE_NUMBER_4P_COORD = [
    (2484, 356),  # Char 1
    (2484, 481),  # Char 2
    (2484, 610),  # Char 3
    (2484, 735),  # Char 4
]

BASE_NAMES_4P_COORD = [
    (2166, 320, 2365, 395),
    (2166, 445, 2365, 520),
    (2166, 575, 2365, 650),
    (2166, 705, 2365, 780),
]

BASE_BOSS_COORD = (700, 20, 1960, 80)
BASE_LOCATION_COORD = (702, 240, 1838, 345)
BASE_MAP_LOC_COORD = (1980, 140, 2520, 260)
BASE_ACTIVITY_COORD = (1880, 20, 2440, 80)
BASE_DOMAIN_COORD = (1680, 160, 2420, 260)
BASE_PARTY_SETUP_COORD = (0, 20, 900, 100)

def get_dynamic_coordinates():
    """
    Detects the actual Genshin Impact window size and returns scaled coordinates.

    Returns:
        tuple: (scaled_coords_dict, detected_resolution)
        where scaled_coords_dict contains all coordinate arrays scaled to actual window size
    """
    try:
        # Get the actual Genshin window dimensions
        window_rect = ps_helper.get_genshin_window_rect()
        if window_rect:
            actual_width = window_rect[2] - window_rect[0]  # right - left
            actual_height = window_rect[3] - window_rect[1]  # bottom - top

            if DEBUG_MODE:
                print(f"Detected Genshin window size: {actual_width}x{actual_height}")

            # Calculate scaling factors
            scale_x = actual_width / BASE_RESOLUTION_WIDTH
            scale_y = actual_height / BASE_RESOLUTION_HEIGHT

            # Scale all coordinate arrays
            scaled_coords = {
                'NUMBER_4P_COORD': [
                    (round(x * scale_x), round(y * scale_y))
                    for x, y in BASE_NUMBER_4P_COORD
                ],
                'NAMES_4P_COORD': [
                    tuple(round(px * scale_x) for px in name_bbox)
                    for name_bbox in BASE_NAMES_4P_COORD
                ],
                'BOSS_COORD': tuple(round(px * scale_x) for px in BASE_BOSS_COORD),
                'LOCATION_COORD': tuple(round(px * scale_x) for px in BASE_LOCATION_COORD),
                'MAP_LOC_COORD': tuple(round(px * scale_x) for px in BASE_MAP_LOC_COORD),
                'ACTIVITY_COORD': tuple(round(px * scale_x) for px in BASE_ACTIVITY_COORD),
                'DOMAIN_COORD': tuple(round(px * scale_x) for px in BASE_DOMAIN_COORD),
                'PARTY_SETUP_COORD': tuple(round(px * scale_x) for px in BASE_PARTY_SETUP_COORD),
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
        'NUMBER_4P_COORD': BASE_NUMBER_4P_COORD,
        'NAMES_4P_COORD': BASE_NAMES_4P_COORD,
        'BOSS_COORD': BASE_BOSS_COORD,
        'LOCATION_COORD': BASE_LOCATION_COORD,
        'MAP_LOC_COORD': BASE_MAP_LOC_COORD,
        'ACTIVITY_COORD': BASE_ACTIVITY_COORD,
        'DOMAIN_COORD': BASE_DOMAIN_COORD,
        'PARTY_SETUP_COORD': BASE_PARTY_SETUP_COORD,
    }, (BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT)

# Initialize coordinates on import
DYNAMIC_COORDINATES, DETECTED_RESOLUTION = get_dynamic_coordinates()

# Make coordinates available globally
NUMBER_4P_COORD = DYNAMIC_COORDINATES['NUMBER_4P_COORD']
NAMES_4P_COORD = DYNAMIC_COORDINATES['NAMES_4P_COORD']
BOSS_COORD = DYNAMIC_COORDINATES['BOSS_COORD']
LOCATION_COORD = DYNAMIC_COORDINATES['LOCATION_COORD']
MAP_LOC_COORD = DYNAMIC_COORDINATES['MAP_LOC_COORD']
ACTIVITY_COORD = DYNAMIC_COORDINATES['ACTIVITY_COORD']
DOMAIN_COORD = DYNAMIC_COORDINATES['DOMAIN_COORD']
PARTY_SETUP_COORD = DYNAMIC_COORDINATES['PARTY_SETUP_COORD']
    
if __name__ == "__main__":
    print("This is a config file. It is not meant to be run.")
