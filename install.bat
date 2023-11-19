@echo off
where py >nul 2>nul
if %ERRORLEVEL% NEQ 0 echo Python not found. Please download and install: https://www.python.org/ & pause & exit

echo Starting genshin discord rpc...
py -m pip install --upgrade pip
If Not Exist "venv\Scripts\activate.bat" (
    py -m venv venv
)
venv\Scripts\activate.bat &^
py install.py &^
py main.py