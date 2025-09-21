@echo off
echo Starting AI-Powered GUI Terminal...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.6+ from https://python.org
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Warning: Failed to install some dependencies
        echo The terminal may not work properly
        echo.
    )
)

REM Run the GUI terminal
echo Starting GUI terminal...
python gui_terminal.py

pause
