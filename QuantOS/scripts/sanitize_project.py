import os
import re
import sys

# Regex patterns for sensitive data
PATTERNS = {
    "Alpaca API Key": r"AK[A-Z0-9]{18}",
    "Generic API Key": r"[a-zA-Z0-9]{32,}",
    "Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "Hardcoded Password": r"""password\s*=\s*['"][^'"]+['"]"""
}

# Files/Directories to skip
SKIP = [".git", "venv", "node_modules", "__pycache__", "data", "static"]

def sanitize():
    print("🛡️  Starting Security Audit...")
    findings = 0
    
    for root, dirs, files in os.walk("."):
        # Prune skipped directories
        dirs[:] = [d for d in dirs if d not in SKIP]
        
        for file in files:
            if not file.endswith((".py", ".sh", ".json", ".txt")):
                continue
                
            path = os.path.join(root, file)
            
            # Skip the check for config files that are SUPPOSED to have keys (like .env or dynamic_settings)
            # but they should be ignored by git anyway
            if "dynamic_settings.json" in path or ".env" in path:
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                for name, pattern in PATTERNS.items():
                    matches = re.findall(pattern, content)
                    if matches:
                        # Filter out known safe strings or variables
                        # e.g., if it's "os.getenv('ALPACA_API_KEY')" it's safe
                        for match in matches:
                            if f'getenv("{match}")' in content or f"getenv('{match}')" in content:
                                continue
                            if name == "Generic API Key" and (len(match) < 32 or " " in match):
                                continue
                                
                            print(f"⚠️  POSSIBLE {name.upper()} FOUND in {path}: {match[:4]}****")
                            findings += 1
            except Exception as e:
                print(f"Could not read {path}: {e}")

    if findings > 0:
        print(f"\n❌ AUDIT FAILED: {findings} potential leaks found.")
        return False
    else:
        print("\n✅ AUDIT PASSED: No hardcoded credentials detected.")
        return True

if __name__ == "__main__":
    if not sanitize():
        sys.exit(1)
    sys.exit(0)
