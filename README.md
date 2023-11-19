# Genshin Impact Rich Presence

![Screenshot](images/discRPC%20sample%201.png) ![Screenshot](images/discRPC%20sample%202.png) ![Screenshot](images/discRPC%20sample%203.png)

> - Windows only
> - Game text language must be English.
> - Works best when traveling from a place to another instead of teleporting to it since it gives time for the app to read the place title you are in best
> - Supported resolutions: 1920x1080, 2560x1440, 2560x1080 (Ultrawide) fullscreen
> - Party must have 4 members, works for Single Player mode only (TODO: Alternate party setup support)

This Discord Rich Presence doesn't tamper with Genshin Impact game files in any way. It works by scanning text in screen captures.

-----

## Setup guide

### 1. Download project, install Python, update NVIDIA driver

You will need **Python 3.11 newer versions may break the scripts so avoid using too new versions** (latest Python version is recommended). Install from [here](https://www.python.org/downloads/).


**Check NVIDIA GeForce Experience for updates**. Game Ready graphics driver version >525 is required for this to work well.

### 2. Set game resolution/image capture coordinates

Edit these settings in [CONFIG.py](CONFIG.py):

If you're running the game in fullscreen with a standard 16:9 aspect ratio, set the `GAME_RESOLUTION` variable to your screen resolution (e.g. use `GAME_RESOLUTION = 1080` for 1920x1080, 1080p).

🟠 If you're using DLDSR/DLSS/NVIDIA Image Sharpening or any other GPU configuration that performs image upscaling or oversampling (not counting the built-in AMD FSR2 anti-aliasing mode), you'll need to set this to the final output resolution that your screen will display. E.g. 75% resolution with NVIDIA Image Sharpening will still result in an image with the same resolution as your monitor, so you should use the monitor resolution instead of the in-game resolution.

⚠️ The **`GAME_RESOLUTION` setting only works if you're running the game in fullscreen at a 16:9 aspect ratio.** Otherwise, you'll need to set `GAME_RESOLUTION = 0` and follow [this guide to configure the coordinates manually.](configure%20coordinates.md)

### 3. Configure settings in [CONFIG.py](CONFIG.py)

- Configure `USERNAME` to match your Genshin username (must be exactly the same)
- Set `MC_AETHER = True` if Aether is MC, `MC_AETHER = False` if Lumine is MC.
- (SPOILER) Set `WANDERER_NAME` to match custom Wanderer's name in lowercase.

### 4. Start Discord Rich Presence

**Double click [StartRichPresence.bat](StartRichPresence.bat)** to start Discord Rich Presence for Genshin Impact. You can create an application/desktop shortcut for run.bat to make it easier to start.

-----

## Contribution

### Data entry

The [data](data/) folder contains `.csv` (comma-separated values) data files that requires manual input. More information on how to edit these files can be found in the [data README](data/README.md).

Quite a few locations/points of interests may be missing from the current data, and as new domains/characters/bosses/locations get added, this project requires continuous updates to maintain these records.

The `.csv` data files have a hot-reload feature, so you don't need to restart the Discord RPC program to see effected changes to these files, you can enter them as you play the game and find unmarked locations/missing data.
-----
### Debugging: Test if image capture works

Run [test_imagegrab.py](test_imagegrab.py):

```bat
py test_imagegrab.py
```

- Alt+tab to Genshin and leave it running for about 10s. Then, change characters and visit a few places (make sure the location text pops up)
- Check the terminal to make sure everything works.
- If you have two monitors, you can enable the capture display windows by setting `SHOW_CHARACTERS = True`, `SHOW_LOC = True` etc... in [test_imagegrab.py](test_imagegrab.py). This way, you can monitor image captures without needing to alt+tab.

`py main.py` runs the program.

## Credits

Image assets are intellectual property of HoYoverse.

Some images are taken from the [GI fandom wiki](https://genshin-impact.fandom.com/).

This project is a Fork of the Genshin Impact Rich Rresence reimplementation from [@euwba](https//github.com/euwbah)'s fork.
