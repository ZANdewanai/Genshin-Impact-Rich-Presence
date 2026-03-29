@echo off
REM Launcher script for Genshin Impact Rich Presence using embedded Python

cd /d "%~dp0"

echo Starting Genshin Impact Rich Presence...
echo Using embedded Python: python3.13.11_embedded\python.exe
echo.

python3.13.11_embedded\python.exe main.py

if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause > nul
)
