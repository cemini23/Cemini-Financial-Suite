@echo off
:: Cemini Financial Suite — Windows Setup
:: Usage: Double-click setup.bat or run from Command Prompt

setlocal EnableDelayedExpansion

:: ── 1. Python version check ──────────────────────────────────────────────────
echo Checking Python version...

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)

if !PYMAJOR! LSS 3 (
    echo ERROR: Python 3.11+ is required. Found: !PYVER!
    echo Download from https://www.python.org/downloads/
    pause
    exit /b 1
)
if !PYMAJOR! EQU 3 if !PYMINOR! LSS 11 (
    echo ERROR: Python 3.11+ is required. Found: !PYVER!
    echo Download from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo   Found: Python !PYVER!

:: ── 2. Create venv ───────────────────────────────────────────────────────────
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

:: ── 3. Activate and install requirements ────────────────────────────────────
echo Installing requirements...
call venv\Scripts\activate
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

:: ── 4. Copy .env if missing ──────────────────────────────────────────────────
if not exist ".env" (
    copy .env.example .env >nul
    echo Created .env from .env.example
) else (
    echo .env already exists — skipping copy.
)

:: ── 5. Done ──────────────────────────────────────────────────────────────────
echo.
echo Setup complete! Edit .env with your API keys then run: docker compose up -d
echo.
pause
