@echo off
REM ============================================================
REM  Genshin Impact Rich Presence - one-click release builder
REM  Builds both exes (GUI + engine) and assembles the
REM  distributable folder into  builds\GenshinRichPresence\
REM
REM  Close the app first - running exes lock their DLLs.
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================
echo  Building Genshin Impact Rich Presence
echo ============================================
echo.

set PYTHON=python3.12.8_embedded\python.exe

if not exist "%PYTHON%" (
    echo ERROR: %PYTHON% not found.
    echo The embedded Python folder must be next to this script.
    pause
    exit /b 1
)

"%PYTHON%" build_dist.py %*
if errorlevel 1 (
    echo.
    echo BUILD FAILED - see messages above.
    pause
    exit /b 1
)

echo.
echo Build succeeded: builds\GenshinRichPresence\
pause
