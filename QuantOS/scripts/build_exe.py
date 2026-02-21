"""
QuantOS™ v7.1.1 - Executable Build System
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import sys
import subprocess

def build_executable():
    # Use ; for Windows, : for Unix
    sep = ";" if sys.platform == "win32" else ":"
    
    print(f"🔨 Building QuantOS Executable for {sys.platform}...")
    
    # Discovery of pyinstaller path
    pyinstaller_path = "pyinstaller" # Default
    if os.path.exists(os.path.join("venv", "bin", "pyinstaller")):
        pyinstaller_path = os.path.join("venv", "bin", "pyinstaller")
    elif os.path.exists(os.path.join("venv", "Scripts", "pyinstaller.exe")):
        pyinstaller_path = os.path.join("venv", "Scripts", "pyinstaller.exe")

    cmd = [
        pyinstaller_path,
        "--onefile",
        "--name", "QuantOS",
        "--clean",
        # Data files (Templates & Assets)
        f"--add-data", f"interface/templates{sep}interface/templates",
        f"--add-data", f"static{sep}static",
        f"--add-data", f"version.txt{sep}.",
        # Hidden Imports (Critical for dynamic modules)
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "alpaca",
        "--hidden-import", "ib_insync",
        "--hidden-import", "robin_stocks",
        "--hidden-import", "schwab",
        "--hidden-import", "jinja2",
        "--hidden-import", "pandas_ta",
        "--hidden-import", "sklearn",
        "--hidden-import", "xgboost",
        "--hidden-import", "nest_asyncio",
        "run_app.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*40)
        print("✅ BUILD COMPLETE!")
        print(f"Location: {os.path.join(os.getcwd(), 'dist', 'QuantOS' + ('.exe' if sys.platform == 'win32' else ''))}")
        print("="*40)
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code {e.returncode}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    build_executable()
