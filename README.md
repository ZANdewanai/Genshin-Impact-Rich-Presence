# Genshin Impact Rich Presence v3.0

![Screenshot](resources/assets/Screenshot.png) ![Screenshot](resources/assets/Screenshot2.png) ![Screenshot](resources/assets/Screenshot3.png)

A Discord Rich Presence for Genshin Impact that shows your current location,
activity, party, and playtime. It does not tamper with game files — it scans
text in periodic screen captures using OCR (RapidOCR on ONNX Runtime) and
translates what it sees into Discord status updates.

> - **Windows 10/11 only**
> - **GPU required** — OCR runs exclusively through DirectML (NVIDIA, AMD, or Intel); the app refuses to start without it
> - **Game text language must be English**
> - **Single Player mode only**, any party size (1–6)
> - Works at any resolution or aspect ratio (auto-detected, ultrawide included)

-----

## 🚀 Quick Start

1. Double-click **`start_gui.bat`**
2. In the GUI's Settings tab, enter:
   - Your Genshin Impact username
   - Your main character (Aether/Lumine)
   - Wanderer name, if you've renamed them in-game
3. Click **"Start Rich Presence"**

The app detects the Genshin window automatically and starts updating Discord.
Discord must be running (desktop app).

### Alternative Launch Methods

```bash
# GUI mode directly
python3.12.8_embedded\python.exe webview_launcher.py

# Console mode - same OCR + Discord RPC, no GUI
python3.12.8_embedded\python.exe main.py
```

Console mode is configured by editing `CONFIG.py`; the GUI is recommended for
live monitoring and configuration.

-----

## ⚙️ Configuration

Most users configure everything through the GUI. Settings are stored in
`shared_config.json` (runtime-generated) and passed to the detection engine.

Advanced users can edit [CONFIG.py](CONFIG.py) directly:

- `USERNAME`, `MC_AETHER`, `WANDERER_NAME` — legacy; overridden by GUI settings
- `GAME_RESOLUTION` — auto-detected; manual override rarely needed (only for GPU-upscaling setups like DLDSR/DLSS)
- Manual screen coordinates — only needed for non-standard aspect ratios where auto-detection fails
- `USE_URL_ASSETS` / `ASSET_BASE_URL` — serve character/boss images to Discord from a URL instead of uploading assets (bypasses Discord's 300-asset limit)

-----

## ✨ How It Works

- **Screen capture → OCR → activity state.** The engine grabs the game window
  and reads region-specific text: location names, boss names, domain names,
  party slots, and menus.
- **Sensor worker architecture.** Character, location, and menu regions are
  scanned in dedicated worker threads coordinated via a shared blackboard,
  keeping the main loop responsive. A legacy sequential loop remains available
  (`USE_SENSOR_WORKERS = False`).
- **Adaptive character detection.** If UI scaling shifts the party HUD, the
  character name regions self-adjust within bounds instead of failing.
- **Hot-reloaded data.** The CSV files in `data/` reload on change — you can
  add missing locations/characters while playing without restarting.
- **OCR pauses when Genshin loses focus or is minimized**, so idle resource
  usage is minimal.

-----

## 📁 Project Structure

```
├── start_gui.bat / .ps1          # GUI launcher (recommended)
├── start_embedded.bat / .ps1     # Console-mode launcher
├── main.py                       # Console entry point (OCR + Discord RPC)
├── webview_launcher.py           # GUI entry point (pywebview + local HTTP server)
├── CONFIG.py                     # Advanced/manual configuration
├── core/
│   ├── detection.py              # Main detection loop logic
│   ├── sensors.py                # Sensor workers (char/location/menu scanning)
│   ├── coordinator.py            # Coordinates sensor workers & blackboard
│   ├── blackboard.py             # Shared JSON store for sensor results
│   ├── character_detection.py    # Adaptive party-HUD character detection
│   ├── ocr_engine.py             # RapidOCR wrapper (DirectML GPU enforcement)
│   ├── ocr_utils.py              # Screen capture & OCR text utilities
│   ├── discord_rpc.py            # Rich Presence update thread
│   ├── state.py                  # Global game-state management
│   ├── datatypes.py              # Activity/Character/Location types + CSV data
│   ├── ps_helper.py              # Window/process helpers (win32)
│   └── log_utils.py              # Timestamped, throttled logging
├── gui/
│   ├── api.py                    # Python-side API exposed to the web UI
│   └── src/                      # React + TypeScript front end (built to gui/dist)
├── data/                         # Game data (hot-reloaded CSVs)
│   ├── characters.csv            # Party characters
│   ├── bosses.csv                # Weekly/world bosses
│   ├── domains.csv               # Domains
│   ├── locations.csv             # Locations & points of interest
│   ├── gamemenus.csv             # Menu screens
│   ├── character_meta.csv        # Character metadata
│   └── GAME_DATA_DOCUMENTATION.md
├── tools/                        # Debug & calibration scripts
│   └── archive/                  # One-shot asset preparation scripts
├── docs/                         # Patch notes & coordinate guide
├── resources/                    # Images, icons, screenshots
├── requirements.txt              # Python dependencies (for reference)
└── python3.12.8_embedded/        # Bundled Python 3.12.8 environment
```

Runtime-generated files (safe to delete when the app is closed):
`shared_config.json`, `gui_shared_data.json`, `gui_config.json`.

## 🛠️ Troubleshooting

**Test if OCR works:**
```bash
python3.12.8_embedded\python.exe tools\test_imagegrab.py
```
Alt+tab into Genshin, switch characters, travel around, and watch the console output.

| Problem | Fix |
|---|---|
| OCR not detecting text | Ensure the game is in English; update GPU drivers |
| App won't start | Use `start_gui.bat`; verify `python3.12.8_embedded\` exists; allow it through antivirus |
| Discord not updating | Confirm the Discord desktop app is running; restart Discord |
| Poor performance | Close other GPU-intensive apps; update GPU drivers |

Debug tools live in `tools/`: `test_imagegrab.py` (capture test),
`capture_ocr_regions.py` (region inspection),
`interactive_coordinate_calibrator.py` (manual coordinate calibration),
`test_sensors.py` (sensor architecture test).

-----

## 🙏 Credits & License

**Author**: Created, developed, and maintained by [@ZANdewanai](https://github.com/ZANdewanai).
This version is a complete from-scratch rewrite — architecture, OCR pipeline,
sensor system, and GUI are all original work built on the same core idea of
screen-capture OCR driving Discord Rich Presence.

**Image Assets**: Intellectual property of HoYoverse © miHoYo. All rights reserved.
Some assets sourced from the [Genshin Impact Fandom Wiki](https://genshin-impact.fandom.com/).

**License**: See [LICENSE](LICENSE).

### Contributing

Contributions welcome! Data entry is the biggest ongoing need — see
[data/GAME_DATA_DOCUMENTATION.md](data/GAME_DATA_DOCUMENTATION.md) and check
[GitHub Issues](https://github.com/ZANdewanai/Genshin-Impact-Rich-Presence/issues).
