# Manual Coordinate Configuration (Advanced Users Only)

> ⚠️ **IMPORTANT**: Most users **do not need** to manually configure coordinates anymore! The application now **automatically detects** your Genshin Impact window size and scales coordinates accordingly.
>
> Only follow this guide if you encounter **persistent coordinate detection issues** with specific GPU upscaling configurations or non-standard aspect ratios.

## When Manual Configuration Might Be Needed

- Using GPU upscaling (DLDSR/DLSS/NVIDIA Image Sharpening) that changes final display resolution
- Non-standard aspect ratios (not 16:9)
- Multi-monitor setups with complex configurations
- Custom UI scaling or DPI settings

## Automatic Detection (Recommended)

For **99% of users**, the application will automatically:
- ✅ Detect your Genshin Impact window size
- ✅ Scale all coordinates appropriately
- ✅ Work with any resolution (720p to 8K+)
- ✅ Handle ultrawide monitors
- ✅ Adapt to UI layout changes

**You can skip this entire guide if automatic detection works for you!**

## Manual Configuration Process

⚠️ Coordinates are specified in **screen pixels, where (0, 0) is the top left** of your screen.

⚠️ If running the game in non-fullscreen mode, you will need to specify the coordinates relative to the entire screen/display, instead of the game.

1. Run Genshin at your desired resolution. If in windowed/borderless windowed mode, ensure the game window is positioned at the **exact same spot** on screen every time.
2. Press `PrintScreen` (or `Ctrl`+`Alt`+`PrintScreen` for multi-monitor setups) to capture the entire screen.
3. Paste the screenshot (`Ctrl`+`V`) into Paint or any image editing application.
4. Use the image editor to measure pixel coordinates of text elements relative to the entire display/monitor.
5. Open [CONFIG.py](CONFIG.py) and locate the coordinate variables in the `MANUAL CONFIGURATION OF SCREEN COORDINATES` section.
6. Modify the coordinate values according to the reference images below.

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

## Important Notes

⚠️ **Legacy Configuration**: This manual process is largely obsolete due to automatic detection. Only use if automatic detection fails.

⚠️ **Performance**: If you must configure manually, keep bounding rectangles as small as possible to conserve processing power.

⚠️ **Testing**: Always test with characters/places/bosses that have long names to ensure your boxes are large enough.

⚠️ **Alternative Tools**: Consider using the `DEV_resources/for_debugging/interactive_coordinate_calibrator.py` script for easier coordinate setup if manual configuration is absolutely necessary.

## Recommendation

**Before attempting manual coordinate configuration, try these troubleshooting steps:**

1. Ensure Genshin Impact is running in **windowed** or **borderless windowed** mode
2. Verify your GPU drivers are up to date
3. Try toggling GPU acceleration settings in the GUI
4. Restart both Genshin Impact and the Rich Presence application
5. Check the GUI logs for any coordinate detection errors

**Manual configuration should be your last resort** - the automatic system works for the vast majority of users!
