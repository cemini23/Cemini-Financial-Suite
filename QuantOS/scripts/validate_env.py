"""
QuantOS™ v8.0.0 - Environment Validator & Repair Tool
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import sys
import os
import importlib

REQUIRED_DIRS = ['data', 'logs', 'config', 'interface/static/charts', 'core', 'strategies', 'interface']

def validate():
    print("📋 QuantOS Pre-flight Health Check...")
    
    # 1. Python Version Check
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 10):
        print(f"❌ ERROR: Python 3.10+ required. Found {major}.{minor}")
        sys.exit(1)
    print(f"✅ Python {major}.{minor} detected.")

    # 2. Critical Library Check
    libraries = ["pandas", "numpy", "alpaca", "dotenv", "requests", "ta", "joblib"]
    missing = []
    for lib in libraries:
        try:
            importlib.import_module(lib if lib != "dotenv" else "dotenv")
        except ImportError:
            missing.append(lib)
    
    if missing:
        print(f"❌ ERROR: Missing libraries: {', '.join(missing)}")
        print("💡 Run: pip install -r requirements.txt")
        sys.exit(1)
    print("✅ All critical libraries imported successfully.")

    # 3. Config Check
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("⚠️  .env missing. Creating from .env.example...")
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ Created .env. Please fill in your API keys.")
        else:
            print("⚠️  WARNING: .env and .env.example missing.")
    else:
        print("✅ .env configuration file detected.")

    # 4. Folder Structure (Active Repair)
    print("🔎 Verifying directory structure...")
    for folder in REQUIRED_DIRS:
        if not os.path.exists(folder):
            print(f"🛠️  Repairing: Creating missing folder '{folder}'...")
            os.makedirs(folder, exist_ok=True)
        else:
            # Check if it is a file instead of a directory
            if os.path.isfile(folder):
                print(f"❌ ERROR: '{folder}' exists but is a file. Please remove it so a directory can be created.")
                sys.exit(1)
    
    print("🚀 System Health: EXCELLENT. Ready to launch.")

if __name__ == "__main__":
    validate()
