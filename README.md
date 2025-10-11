# Genshin Impact Rich Presence v2.6

![Screenshot](resources/assets/Screenshot.png) ![Screenshot](resources/assets/Screenshot2.png) ![Screenshot](resources/assets/Screenshot3.png)

> - Windows only
> - Game text language must be English
> - **Location detection**: Works best when traveling between places (location text appears longer), but teleporting works too with fallback map detection(i.e thinking of traveling to location)
> - **Automatic resolution detection**: Works with any resolution (720p, 1080p, 1440p, 2160p, ultrawide, etc.)
> - **Party setup**: Works with any number of characters (1-4) in party, works for Single Player mode only
> - Now includes a modern GUI interface!

This Discord Rich Presence doesn't tamper with Genshin Impact game files in any way. It works by scanning text in screen captures using OCR (Optical Character Recognition).

-----

## Quick Start

### Option 1: GUI Version (Recommended)
1. Run `python_embedded\python.exe genshin_impact_rich_presence_gui.py`
2. Click "Start Rich Presence" in the GUI
3. The application will automatically detect your game and update Discord

### Option 2: Command Line Version
1. Run `python_embedded\python.exe main.py`
2. The application will start in console mode

-----

## Setup Guide

### 1. System Requirements

- **Windows 10/11**
- **Python 3.11+** (embedded version included in `python_embedded/`)
- **NVIDIA GPU** recommended (with recent drivers >525 for best OCR performance)
- **Genshin Impact** with English text language

### 2. Configure Game Settings

Edit [CONFIG.py](CONFIG.py) to match your setup:

- Set `USERNAME` to match your Genshin Impact username exactly
- Set `MC_AETHER = True` if Aether is your main character, `False` if Lumine
- Set `WANDERER_NAME` to your custom Wanderer name (if applicable)

� **Resolution Detection:** The application now automatically detects and scales coordinates for any resolution that's a multiple of 1080p (1920x1080). For ultrawide monitors or non-standard resolutions, set `GAME_RESOLUTION = 0` and follow the coordinate calibration guide in [configure coordinates.md](configure%20coordinates.md)

### 3. GPU Acceleration (Recommended)

The application uses EasyOCR for text recognition. GPU acceleration significantly improves performance:

- Set `USE_GPU = True` in CONFIG.py (default)
- Ensure you have CUDA-compatible NVIDIA drivers
- The embedded Python includes PyTorch with CUDA support

### 4. Start the Application

#### GUI Mode (Recommended):
```bash
python_embedded\python.exe genshin_impact_rich_presence_gui.py
```

#### Console Mode:
```bash
python_embedded\python.exe main.py
```

The application will:
- Connect to Discord
- Start monitoring Genshin Impact
- Display your current activity, character, and location on Discord

-----

## Contribution

### Data entry

The [data](data/) folder contains `.csv` (comma-separated values) data files that requires manual input. More information on how to edit these files can be found in the [data README](data/README.md).

Quite a few locations/points of interests may be missing from the current data, and as new domains/characters/bosses/locations get added, this project requires continuous updates to maintain these records.

The `.csv` data files have a hot-reload feature, so you don't need to restart the Discord RPC program to see effected changes to these files, you can enter them as you play the game and find unmarked locations/missing data.
-----

## Project Structure

```
├── main.py                          # Console version of the application
├── genshin_impact_rich_presence_gui.py  # GUI version (recommended)
├── CONFIG.py                        # Configuration file
├── datatypes.py                     # Data type definitions
├── ocr_engine.py                    # OCR processing engine
├── ps_helper.py                     # Process helper utilities
├── data/                           # Game data files
│   ├── characters.csv              # Character database
│   ├── locations.csv               # Location database
│   ├── domains.csv                 # Domain database
│   ├── bosses.csv                  # Boss database
│   ├── gamemenus.csv               # Game menu database
│   └── README.md                   # Data file documentation
├── DEV_resources/                  # Development resources
│   ├── requirements.txt            # Python dependencies
│   ├── for_debugging/              # Debug utilities
│   └── docs/                       # Documentation
├── python_embedded/                # Embedded Python environment
├── easyocr_cache/                  # OCR model cache
└── resources/                      # Assets and screenshots
```

## Troubleshooting

### Test Image Capture

Run the debugging script to verify OCR functionality:

```bash
python_embedded\python.exe DEV_resources\for_debugging\test_imagegrab.py
```

**What to do:**
- Alt+tab to Genshin Impact and leave it running
- Change characters and visit different locations
- Check the terminal output for successful OCR detection
- Enable capture display windows in the debug script for visual verification

### Common Issues

1. **OCR not detecting text:**
   - Ensure Genshin Impact is running in English
   - The application automatically detects your resolution - no manual setup needed
   - Verify GPU drivers are up to date (recommended for best performance)

2. **GUI not updating:**
   - Check the GUI log for error messages
   - Ensure the subprocess is running (check Task Manager)
   - Verify shared data file permissions

3. **Discord not updating:**
   - Confirm Discord is running
   - Check that the Discord app is connected
   - Verify the application ID in CONFIG.py

### Debug Tools

Located in `DEV_resources/for_debugging/`:
- `test_imagegrab.py` - Test OCR image capture
- `capture_ocr_regions.py` - Debug OCR regions
- `interactive_coordinate_calibrator.py` - Calibrate screen coordinates

## Credits

Image assets are intellectual property of HoYoverse, © All rights reserved by miHoYo

Some images are taken from the [GI fandom wiki](https://genshin-impact.fandom.com/).

This project is a Fork of the Genshin Impact Rich Presence reimplementation from [@euwba](https://github.com/euwbah)'s fork.
