@echo off
setlocal enabledelayedexpansion
echo Searching for Python installation...

:: List of common Python installation paths
set "PYTHON_PATHS="

:: Add Python from Program Files
if exist "%ProgramFiles%\Python3*\python.exe" (
    for /d %%i in ("%ProgramFiles%\Python3*") do (
        set "PYTHON_PATHS=!PYTHON_PATHS! "%%~i\python.exe""
    )
)

:: Add Python from Local AppData
if exist "%LOCALAPPDATA%\Programs\Python\Python3*\python.exe" (
    for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        set "PYTHON_PATHS=!PYTHON_PATHS! "%%~i\python.exe""
    )
)

:: Add Python from User AppData
if exist "%APPDATA%\Python\Python3*\python.exe" (
    for /d %%i in ("%APPDATA%\Python\Python3*") do (
        set "PYTHON_PATHS=!PYTHON_PATHS! "%%~i\python.exe""
    )
)

:: Try each found Python
for %%i in (!PYTHON_PATHS!) do (
    if exist "%%~i" (
        echo Found Python: %%~i
        "%%~i" -m pip install -q -r "%~dp0requirements.txt"
        "%%~i" "%~dp0GenshinImpactRichPresence_GUI.py"
        pause
        exit /b 0
    )
)

:: If no Python found, show download link
echo Python not found. Please install Python 3.7 or later from:
echo https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
pause
