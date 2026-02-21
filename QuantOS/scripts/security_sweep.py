import os
import re
import sys

# High-sensitivity regex patterns
PATTERNS = {
    "API_KEY": r"(?:api_key|secret|token|apikey)\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]",
    "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "PASSWORD": r"password\s*=\s*['\"][^'\"]{8,}['\"]",
    "PRIVATE_KEY": r"BEGIN (?:RSA|OPENSSH) PRIVATE KEY"
}

SKIP_DIRS = [".git", "venv", "__pycache__", "data", "node_modules"]

def sweep():
    print("🛡️  QuantOS Security Sweep Initiated...")
    violations = 0
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if not file.endswith((".py", ".sh", ".json", ".txt")):
                continue
            
            path = os.path.join(root, file)
            # Skip legit config files that are gitignored
            if "dynamic_settings.json" in path or ".env" in path:
                continue
                
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for name, pattern in PATTERNS.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Simple whitelist for common safe variables
                        snippet = content[max(0, match.start()-20):min(len(content), match.end()+20)]
                        if "os.getenv" in snippet or "config." in snippet:
                            continue
                            
                        print(f"❌ VIOLATION [{name}] in {path}: ...{match.group()}...")
                        violations += 1
            except Exception as e:
                print(f"⚠️ Could not read {path}: {e}")

    if violations > 0:
        print(f"\n🛑 SWEEP FAILED: {violations} potential security risks found.")
        return False
    
    print("\n✅ SWEEP PASSED: No hardcoded secrets detected.")
    return True

if __name__ == "__main__":
    if not sweep():
        sys.exit(1)
    sys.exit(0)
