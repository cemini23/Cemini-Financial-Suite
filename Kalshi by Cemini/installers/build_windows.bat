@echo off
title Kalshi by Cemini - Builder
color 0A

echo ==================================================
echo      KALSHI BY CEMINI | WINDOWS BUILD SYSTEM
echo ==================================================
echo.

:: 1. Install Requirements
echo [*] Checking dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Error installing dependencies.
    pause
    exit /b
)

:: 2. Clean previous builds
echo [*] Cleaning old builds...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

:: 3. Build the Exe
:: --onedir: Creates a folder (faster, more reliable for web apps)
echo [*] Compiling Application...
pyinstaller --name "KalshiByCemini" --onedir --clean --noconfirm app/main.py

:: 4. Copy Frontend Assets (The Robust Fix)
echo [*] Copying Dashboard & Logo...
xcopy "frontend" "dist\KalshiByCemini\frontend\" /E /I /Y

echo.
echo ==================================================
echo [OK] BUILD COMPLETE!
echo ==================================================
echo Your app is ready in: dist\KalshiByCemini\KalshiByCemini.exe
echo.
pause
