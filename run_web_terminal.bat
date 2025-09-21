@echo off
title AI-Powered Web Terminal
color 0A

echo.
echo ========================================
echo   🚀 AI-Powered Web Terminal Launcher
echo ========================================
echo.

echo 📦 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo ✅ Python found
echo.

echo 📦 Installing/Updating required packages...
pip install -r web_requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install required packages
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo ✅ Packages installed successfully
echo.

echo 🌐 Starting Web Terminal Server...
echo.
echo 🎯 Features:
echo    • Python Commands + Natural English
echo    • AI Integration with Gemini API
echo    • Real-time Web Interface
echo    • Session-based Command History
echo.
echo 🌐 Open your browser and go to: http://localhost:5000
echo.
echo ⚠️  Press Ctrl+C to stop the server
echo.

python web_terminal.py

echo.
echo 👋 Web Terminal stopped
pause
