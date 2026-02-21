@echo off
cd /d "%~dp0"
title Survivor Bot 🛡️

echo ==========================================
echo    🚀 SURVIVOR BOT LAUNCHER 🚀
echo ==========================================
echo ⚠️  NOTE: Please plug in your charger!
echo ⚠️  Set "Sleep" to NEVER in Settings.
echo ==========================================

:: Activate Brain
call venv\Scripts\activate

:: Run Bot
python main.py

:: Keep window open if it crashes
echo.
echo 🛑 Bot Stopped. Press any key to close.
pause