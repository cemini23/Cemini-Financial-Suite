@echo off
TITLE QuantOS Environment Manager
COLOR 0A

ECHO ==================================================
ECHO      QUANTOS MIDNIGHT EDITION - AUTO-SETUP
ECHO ==================================================

:: 1. CHECK & FIX FOLDER STRUCTURE
IF NOT EXIST "core\data" (
    ECHO [FIX] 'core\data' folder missing. Creating it...
    mkdir "core\data"
)

:: 2. ENSURE __INIT__ FILES EXIST (Crucial for Python imports)
IF NOT EXIST "core\__init__.py" type NUL > "core\__init__.py"
IF NOT EXIST "core\data\__init__.py" type NUL > "core\data\__init__.py"

:: 3. RESTORE MISSING FILES (If streamer.py is in the wrong place)
IF EXIST "core\streamer.py" (
    ECHO [FIX] Found 'streamer.py' in wrong folder. Moving to 'core\data'...
    move "core\streamer.py" "core\data\streamer.py"
)

:: 4. CHECK VENV
IF NOT EXIST "venv" (
    ECHO [SETUP] Creating Virtual Environment...
    python -m venv venv
    call venv\Scripts\activate
    ECHO [SETUP] Installing Dependencies...
    pip install -r requirements.txt
) ELSE (
    call venv\Scripts\activate
)

:: 5. LAUNCH
ECHO [BOOT] Starting QuantOS Engine...
python main.py
PAUSE
