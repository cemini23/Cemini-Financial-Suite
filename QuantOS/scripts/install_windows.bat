@echo off
cd /d "%~dp0"

echo ==========================================
echo    🚀 SURVIVOR BOT INSTALLER (WINDOWS) 🚀
echo ==========================================

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed!
    echo 👉 Please download it from python.org and check "Add to PATH".
    pause
    exit /b
)

:: 2. Create Virtual Environment
echo 📦 Creating virtual environment...
python -m venv venv

:: 3. Activate & Install
echo ⬇️  Installing brains (libraries)...
call venv\Scripts\activate
pip install --upgrade pip
pip install pandas ta robin_stocks python-dotenv requests

:: 4. Setup Config File
if not exist .env (
    echo ⚙️  Creating .env configuration file...
    copy .env.example .env
    echo ✅ Created .env file!
) else (
    echo ✅ Config file already exists.
)

echo ==========================================
echo 🎉 INSTALLATION COMPLETE!
echo ==========================================
echo 1. Open the file named ".env" with Notepad and add your Robinhood Login.
echo 2. To start the bot, double-click "run_bot.bat".
echo ==========================================
pause