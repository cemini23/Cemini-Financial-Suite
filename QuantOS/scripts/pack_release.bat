@echo off
set VERSION=v9_Install
set ZIP_NAME=QuantOS_%VERSION%.zip

echo 🔍 AUDITING CORE ASSETS...
if not exist "main.py" ( echo ❌ main.py missing! && exit /b 1 )
if not exist "requirements.txt" ( echo ❌ requirements.txt missing! && exit /b 1 )
if not exist "start.bat" ( echo ❌ start.bat missing! && exit /b 1 )
echo ✅ AUDIT COMPLETE.

echo 🧹 CLEANING TEMPORARY FILES...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.log >nul 2>&1
echo ✅ SYSTEM CLEANED.

echo 📦 PACKAGING RELEASE...
powershell -Command "Compress-Archive -Path '.\*' -DestinationPath '%ZIP_NAME%' -Exclude 'venv', '.env', '.git', '*.zip', '.pytest_cache', 'build', 'dist', 'QuantOS.spec'"

echo ---------------------------------------------------------
echo 📦 Release Ready. Send '%ZIP_NAME%' to friends.
echo ---------------------------------------------------------
pause
