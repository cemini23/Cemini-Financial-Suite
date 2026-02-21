import os
import re

def sanitize():
    personal_names = [re.compile(r'User', re.IGNORECASE), re.compile(r'User', re.IGNORECASE)]
    api_key_pattern = re.compile(r'(AK|SK|PK|ROBINHOOD_)[A-Z0-9]{20,}')
    
    extensions = ('.py', '.bat', '.sh', '.md', '.txt')
    
    print("🧹 STARTING CODE SANITIZATION...")
    
    for root, dirs, files in os.walk("."):
        # Skip some dirs
        if any(d in root for d in ['.git', '__pycache__', 'venv', 'build', 'dist']):
            continue
            
        for file in files:
            if file.endswith(extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Scrub names
                    for name_pattern in personal_names:
                        content = name_pattern.sub('User', content)
                    
                    # Check for API keys
                    if api_key_pattern.search(content):
                        print(f"⚠️  POSSIBLE API KEY DETECTED in {file_path}")
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✅ Sanitized: {file_path}")
                        
                except Exception as e:
                    # logger or print
                    pass

if __name__ == "__main__":
    sanitize()
    print("✨ SANITIZATION COMPLETE.")
