# Manual configuration of coordinates

Follow this guide if you're not running genshin in fullscreen or in a 16:9 aspect ratio.

⚠️ Coordinates are specified in **screen pixels, where (0, 0) is the top left** of your screen. 

⚠️ If running the game in non-fullscreen mode, you will need to specify the coordinates relative to the entire screen/display, instead of the game.

1. Run genshin at whatever resolution. If in windowed/borderless windowed mode, you will need to ensure that the game is positioned at the exact same spot on the screen whenever you run it.
2. Hit the `PrintScreen` button (or `Ctrl`+`Alt`+`PrintScreen` if you have multiple monitors). Capture the entire screen, even if not running in fullscreen mode.
3. Paste image (`Ctrl`+`V`) in paint.exe/drawing app
4. Use paint.exe/drawing app to note down the pixel coordinates of text elements relative to the entire display/monitor.
5. Open up [CONFIG.py](CONFIG.py) and **set `GAME_RESOLUTION = 0` (VERY IMPORTANT)**
6. Modify the variable values in the section titled `MANUAL CONFIGURATION OF SCREEN COORDINATES`, according to the images below.

![Coordinate info](images/location%20party%20coordinates%20setup.png)

🟡 The **bounding box** of a capture region is written as `(x1, y1, x2, y2)`, where `x1` & `y1` are the X and Y coordinates of the top left corner of a rectangle, and `x2` & `y2` are the X and Y coordinates of the bottom right corner.

  - `LOCATION_COORD`: **bounding box** of location popup text. **This should also be big enough to capture the 'Commission Accepted' text**, and other text/NPC names that gives the location of the player (e.g. "Prince" = The Cat's Tail, "Tubby" = Serenitea Pot, etc...). However, **do not set this box too big**, otherwise it will cause lag.
  - `NAMES_4P_COORD`: list of **bounding boxes**, of the 1st to 4th character names (top to bottom).
  - `NUMBER_4P_COORD`: **list of `(X, Y)` coordinates** of a _single white pixel_ from the 1st-4th character select number display (1, 2, 3, 4). The pixel corresponding to the current active character will be darker compared to the others. (For controller mode, the highlighted button on the DPAD is white if a character can be selected.)

<br/>

![Boss coordinates](images/boss%20coord%20setup.png)

- `BOSS_COORD`: **bounding box** of the upper boss name. **Do not include the lower boss name.**

![Map loc coordinates](images/map%20loc%20coord%20setup.png)

- `MAP_LOC_COORD`: bounding box of the teleport location name.

![Domain coordinates](images/domain%20coord%20setup.png)

- `DOMAIN_COORD`: bounding box of the domain name.

![Party coordinates](images/party%20coords%20setup.png)

- `PARTY_SETUP_COORD`: bounding box of the **Party Setup** text.

## NOTE

⚠️ Ensure the configured bounding rectangles are as small as possible to conserve processing power.

⚠️ Test characters/places/bosses with long names.