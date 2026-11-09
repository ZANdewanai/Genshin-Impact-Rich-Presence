# Manual Coordinate Configuration (Advanced Users Only)

> ⚠️ **IMPORTANT**: Most users **do not need** to manually configure coordinates anymore! The application now **automatically detects** your Genshin Impact client area (size *and* position) and scales coordinates accordingly.
>
> Only follow this guide if you encounter **persistent coordinate detection issues** with specific GPU upscaling configurations or non-standard aspect ratios.

## When Manual Configuration Might Be Needed

- Using GPU upscaling (DLDSR/DLSS/NVIDIA Image Sharpening) that changes final display resolution
- Non-standard aspect ratios (not 16:9)
- Multi-monitor setups with complex configurations
- Custom UI scaling or DPI settings

## Automatic Detection (Recommended)

For **99% of users**, the application will automatically:
- ✅ Detect your Genshin Impact window size **and** its on-screen position
- ✅ Scale all coordinates appropriately
- ✅ Work with any resolution (720p to 8K+)
- ✅ Handle ultrawide monitors
- ✅ Adapt to UI layout changes
- ✅ Work in windowed/borderless mode at any window position

**You can skip this entire guide if automatic detection works for you!**

## How Coordinates Work

All OCR regions are defined as bounding boxes `(x1, y1, x2, y2)` in two CSV files under `data/`:

- **`data/party_layouts.csv`** — the single `party_area` box covering the whole party-name list (CharSensor runs one OCR pass over it).
- **`data/region_coords.csv`** — the remaining regions: `activity`, `boss`, `domain`, `party_setup`, `location`, `map_loc`.

Coordinates are specified for the **base resolution of 2560x1440**, relative to the **top-left corner of the game client area** (not the whole screen). At runtime they are scaled to the detected client size and offset by the client origin — so the same values work at any resolution and any window position.

Both files are **hot-reloaded**: editing them while the engine runs takes effect within ~5 seconds (the coordinator stats them on every data check).

## Manual Configuration Process

⚠️ Coordinates are **window-relative** — (0, 0) is the top-left of the Genshin client area, not the screen. Measure against a fullscreen or maximized windowed-mode capture at 2560x1440 if possible; the scaling handles the rest.

1. Run Genshin at your desired resolution (windowed or borderless).
2. Press `PrintScreen` and paste the screenshot into an image editor.
3. Measure pixel coordinates of the text regions relative to the **game window's** top-left corner.
4. Edit the matching row in `data/party_layouts.csv` or `data/region_coords.csv`.
5. The engine picks up the change automatically — no restart needed.

Region reference:

- `party_area`: bounding box covering the **entire party name list**. Should include every name row plus a little margin, but don't make it huge — larger boxes mean slower OCR.
- `location`: bounding box of the location popup text. Should also capture 'Commission Accepted' and NPC-name location hints (e.g. "Prince" = The Cat's Tail). Don't set it too big — it causes lag.
- `boss`: bounding box of the upper boss name only (not the lower one).
- `map_loc`: bounding box of the teleport location name on the map screen.
- `activity`: bounding box of the activity/status text.
- `domain`: bounding box of the domain name.
- `party_setup`: bounding box of the **Party Setup** text in the pause menu.

## Debugging Aids

- `tools/capture_ocr_regions.py` — dumps the current OCR regions as images for inspection.
- `tools/debug_static_image.py <image.png>` — replays a screenshot through CharSensor offline and prints detected slots.
- The GUI **Logs** tab shows live engine output; enable debug mode in Settings for verbose sensor logging.

## Important Notes

⚠️ **Legacy Configuration**: This manual process is largely obsolete due to automatic detection. Only use if automatic detection fails.

⚠️ **Performance**: Keep bounding rectangles as small as possible to conserve processing power.

⚠️ **Testing**: Always test with characters/places/bosses that have long names to ensure your boxes are large enough.

## Recommendation

**Before attempting manual coordinate configuration, try these troubleshooting steps:**

1. Ensure Genshin Impact is running in **windowed** or **borderless windowed** mode
2. Verify your GPU drivers are up to date
3. Try toggling GPU acceleration settings in the GUI
4. Restart both Genshin Impact and the Rich Presence application
5. Check the GUI logs for any coordinate detection errors

**Manual configuration should be your last resort** — the automatic system works for the vast majority of users!
