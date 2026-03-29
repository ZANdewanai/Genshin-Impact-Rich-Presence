@echo off
REM Download icons using embedded Python

cd /d "%~dp0"

echo Downloading icons from Genshin Impact Fandom wiki...
echo Using embedded Python: ..\python3.13.11_embedded\python.exe
echo.

..\python3.13.11_embedded\python.exe download_icons.py

if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause > nul
)
