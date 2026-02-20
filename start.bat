@echo off
echo NFC Tag Reader Web Application
echo ===============================
echo.

REM Check if Python 3.11 is available
python3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3.11 not found. Please install Python 3.11 or update the script.
    pause
    exit /b 1
)

echo Starting application with Python 3.11...
echo.

REM Start the application
python3.11 run.py

echo.
echo Application has stopped.
pause