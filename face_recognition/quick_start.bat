@echo off
REM Quick Start Script for Face Recognition Attendance System (Windows)

echo ==================================================
echo Face Recognition Attendance System - Quick Start
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10 and try again
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Error installing dependencies
    pause
    exit /b 1
)

echo Dependencies installed successfully
echo.

echo ==================================================
echo Setup Complete!
echo ==================================================
echo.
echo Next steps:
echo.
echo 1. Start the Flask server:
echo    python app.py
echo.
echo 2. Register students (in a new terminal):
echo    python register.py
echo.
echo 3. Start face recognition (in a new terminal):
echo    python main.py
echo.
echo 4. Open dashboard in browser:
echo    http://127.0.0.1:5000
echo.
echo ==================================================
pause
