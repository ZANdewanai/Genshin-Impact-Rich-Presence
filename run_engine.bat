@echo off
REM Genshin Impact Rich Presence - Engine Launcher
REM Sets ONNX Runtime log level to suppress verbose CUDA/DirectML warnings

set ORT_LOGGING_LEVEL=3
python3.12.8_embedded\python.exe main.py %*

if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause > nul
)