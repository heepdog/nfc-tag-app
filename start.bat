@echo off
echo NFC Tag Reader Web Application
echo ===============================
echo.

REM Activate the virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Error: Virtual environment not found in venv folder.
    pause
    exit /b 1
)

REM Check if Python is available in venv
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found in virtual environment.
    pause
    exit /b 1
)

echo Starting application...
echo.

REM Start the application
python run.py

echo.
echo Application has stopped.
pause