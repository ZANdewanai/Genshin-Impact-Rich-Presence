"""
CONFIGURATION FILE

Make sure these coordinates are set up properly before running the script.

See README.md on how to determine coordinates.
"""

USERNAME = "ZANdewanai"
"""
For detecting when MC is being played. 
"""

MC_AETHER = True
"""
If main character is Aether, set this to True.
If main character is Lumine, set this to False.
"""

WANDERER_NAME = "a"
"""
For detecting when Wanderer is active. (Spoiler: You can rename wanderer)
"""

GAME_RESOLUTION = 1080
"""
The resolution you're running genshin at (number corresponds to the
resolution height in pixels).

NOTE: If you're using DLDSR/DLSS/NVIDIA Image Sharpening or any other
GPU configuration that performs image upscaling or oversampling
(not counting the built-in AMD FSR2 anti-aliasing mode),
you'll need to set this to the final output resolution that your
screen will display. E.g. 75% resolution with NVIDIA Image Sharpening
will still result in an image with the same resolution as your monitor,
so you should use the monitor resolution instead of the in-game resolution.

This quick setting only works if you're running the game in fullscreen at a 16:9
aspect ratio. Otherwise, you'll need to set this number to 0 and
manually set the screen coordinates below.

Some common resolutions (any other number is supported):

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
    (2166, 320, 2365, 395),
    (2166, 445, 2365, 520),
    (2166, 575, 2365, 650),
    (2166, 705, 2365, 780),
]
"""
Bounding box coordinates of character names in 4-character single player mode.

First list entry --> 1st character, etc...

Each list entry is a tuple representing a rectangle: (top left X, top left Y, bottom right X, bottom right Y)
"""

BOSS_COORD = (943, 6, 1614, 66)
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

MAP_LOC_COORD = (1926, 124, 2534, 192)


DOMAIN_COORD = (1685, 154, 2490, 267)
"""
Bounding box coordinates for selected domain name.

(top left X, top left Y, bottom right X, bottom right Y)
"""

PARTY_SETUP_COORD = (148, 30, 376, 95)
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


ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
"""
Text characters whitelist to limit OCR results.

Ensure that text chars for place/character/boss/domain names are in this list.
"""

NAME_CONF_THRESH = 0.8
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
"""


"""
The following confgs set OCR rate.
Set number lower to increase OCR rate of that item.
Locations should be OCR'd as often as possible, as the location text is very transient.

Once character names are read, character names are OCR'd least often, since they persist throughout gameplay.
(Character names don't affect current active character. Active character detection is super fast.)
"""

OCR_CHARNAMES_ONE_IN = 60
"""Process character name every N loops"""
OCR_LOC_ONE_IN = 1
"""Process location every N loops"""
OCR_BOSS_ONE_IN = 6
"""Process boss name every N loops"""

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

DEBUG_MODE = False
"""
Set to true to print debug messages.
"""

# AUTO COORDINATE CALCULATION BASED ON 16:9 RESOLUTION
# MAY NOT WORK FOR ALL RESOLUTIONS. TEST THIS.
#
# NOTE: If new capture coordinate regions are added, update this section.

if GAME_RESOLUTION != 0:
    NUMBER_4P_COORD = [
        (round(x * GAME_RESOLUTION / 1440), round(y * GAME_RESOLUTION / 1440))
        for x, y in NUMBER_4P_COORD
    ]

    NAMES_4P_COORD = [
        tuple(round(px * GAME_RESOLUTION / 1440) for px in name_bbox)
        for name_bbox in NAMES_4P_COORD
    ]
    
    BOSS_COORD = tuple(round(px * GAME_RESOLUTION / 1440) for px in BOSS_COORD)
    LOCATION_COORD = tuple(round(px * GAME_RESOLUTION / 1440) for px in LOCATION_COORD)
    MAP_LOC_COORD = tuple(round(px * GAME_RESOLUTION / 1440) for px in MAP_LOC_COORD)
    DOMAIN_COORD = tuple(round(px * GAME_RESOLUTION / 1440) for px in DOMAIN_COORD)
    PARTY_SETUP_COORD = tuple(round(px * GAME_RESOLUTION / 1440) for px in PARTY_SETUP_COORD)
    
if __name__ == "__main__":
    print("This is a config file. It is not meant to be run.")