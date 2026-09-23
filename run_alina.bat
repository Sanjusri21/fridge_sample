@echo off
title ALINA - AI Smart Fridge Voice Assistant
color 0B

echo ============================================================
echo   ALINA - AI-POWERED SMART FRIDGE VOICE ASSISTANT
echo   Food Expiry Management ^& Waste Reduction System
echo ============================================================
echo.

cd /d "%~dp0"

:: Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (venv)...
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (..\venv)...
    call ..\venv\Scripts\activate.bat
) else (
    echo [INFO] Using system Python environment...
)

echo.
echo [INFO] Starting ALINA Smart Fridge server...
echo [INFO] Dashboard URL: http://127.0.0.1:8000
echo.

:: Open default browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"

:: Launch application
python -m app.main

pause
