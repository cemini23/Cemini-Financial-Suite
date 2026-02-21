import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# Configuration
MIN_PYTHON_VERSION = (3, 8)
VENV_NAME = "venv"
REQUIREMENTS_FILE = "requirements.txt"

def print_step(msg):
    print(f"[*] {msg}")

def print_error(msg):
    print(f"[!] ERROR: {msg}")

def check_python_version():
    current_version = sys.version_info
    if current_version < MIN_PYTHON_VERSION:
        print_error(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ is required.")
        print_error(f"You are running {current_version.major}.{current_version.minor}")
        sys.exit(1)
    print_step(f"Detected Python {current_version.major}.{current_version.minor} (Compatible)")

def get_venv_python():
    """Returns the path to the python executable inside the venv"""
    if platform.system() == "Windows":
        return os.path.join(VENV_NAME, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_NAME, "bin", "python")

def create_venv():
    if os.path.exists(VENV_NAME):
        print_step("Virtual environment exists.")
        return

    print_step(f"Creating virtual environment: {VENV_NAME}...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", VENV_NAME])
    except subprocess.CalledProcessError:
        print_error("Failed to create virtual environment.")
        sys.exit(1)

def install_dependencies():
    python_exec = get_venv_python()
    print_step("Checking dependencies...")
    
    # Upgrade PIP first
    subprocess.call([python_exec, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL)
    
    # Install requirements
    try:
        subprocess.check_call(
            [python_exec, "-m", "pip", "install", "-r", REQUIREMENTS_FILE],
            stdout=subprocess.DEVNULL
        )
        print_step("Dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print_error("Failed to install dependencies. Check requirements.txt.")
        sys.exit(1)

def launch_app():
    python_exec = get_venv_python()
    launcher_script = "launcher.py"
    
    # Set PYTHONPATH to root so modules can be imported
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    if not os.path.exists(launcher_script):
        # Fallback if launcher doesn't exist yet
        print_step("Launcher not found. Starting API server directly...")
        subprocess.call([python_exec, "-m", "uvicorn", "app.main:app", "--reload"], env=env)
    else:
        print_step("Launching Kalshi by Cemini...")
        try:
            # Replace current process with the launcher
            if platform.system() == "Windows":
                subprocess.call([python_exec, launcher_script], env=env)
            else:
                os.execv(python_exec, [python_exec, launcher_script])
        except KeyboardInterrupt:
            print("\n[!] Shutting down.")

def main():
    print("========================================")
    print("   KALSHI BY CEMINI | BOOTSTRAPPER      ")
    print("========================================")
    
    check_python_version()
    create_venv()
    install_dependencies()
    launch_app()

if __name__ == "__main__":
    main()
