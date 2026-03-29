@echo off
REM Genshin Impact Rich Presence GUI Launcher
REM This batch file starts the GUI using the embedded Python

echo Starting Genshin Impact Rich Presence GUI...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if embedded Python exists
if not exist "python3.13.11_embedded\python.exe" (
    echo ERROR: Embedded Python not found at python3.13.11_embedded\python.exe
    echo Please ensure the python3.13.11_embedded directory is present.
    pause
    exit /b 1
)

REM Check if GUI script exists
if not exist "genshin_impact_rich_presence_gui.py" (
    echo ERROR: GUI script not found: genshin_impact_rich_presence_gui.py
    pause
    exit /b 1
)

REM Start the GUI with embedded Python
echo Launching GUI...
python3.13.11_embedded\python.exe genshin_impact_rich_presence_gui.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo GUI exited with error code %errorlevel%
    pause
)
