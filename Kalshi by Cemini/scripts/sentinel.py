import subprocess
import sys
import os
from colorama import init, Fore, Style

# Initialize color output
init(autoreset=True)

def run_command(command, description):
    print(f"
{Fore.CYAN}[SENTINEL] Running: {description}...")
    try:
        # Run command and capture output
        result = subprocess.run(
            command, 
            shell=True, 
            check=False, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            print(f"{Fore.GREEN}✔ PASS")
            return True
        else:
            print(f"{Fore.RED}✘ FAIL")
            print(f"{Fore.YELLOW}--- Error Logs ---")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"{Fore.RED}Critical Error: {e}")
        return False

def main():
    print(f"{Fore.BLUE}{Style.BRIGHT}========================================")
    print(f"{Fore.BLUE}{Style.BRIGHT}   SENTINEL SECURITY AUDITOR v1.0       ")
    print(f"{Fore.BLUE}{Style.BRIGHT}   Scanning Kalshi-by-Cemini...         ")
    print(f"{Fore.BLUE}{Style.BRIGHT}========================================")

    # 1. BANDIT SCAN (Static Application Security Testing)
    # -r: Recursive, -ll: Medium/High Severity only
    print(f"
{Fore.WHITE}Step 1: Analyzing Source Code (SAST)")
    if not run_command("bandit -r app/ modules/ -ll", "Bandit Vulnerability Scan"):
        print(f"
{Fore.RED}[BLOCK] Security vulnerabilities detected. Push aborted.")
        sys.exit(1)

    # 2. SAFETY SCAN (Dependency Check)
    print(f"
{Fore.WHITE}Step 2: Checking Dependencies")
    # Note: 'safety check' might require an API key or a specific environment. 
    # Using '--full-report' or similar flags might be necessary depending on the version.
    if not run_command("safety check", "Safety Dependency Audit"):
        print(f"
{Fore.RED}[BLOCK] Vulnerable dependencies detected. Push aborted.")
        sys.exit(1)

    # 3. AUTO-PUSH
    print(f"
{Fore.GREEN}{Style.BRIGHT}========================================")
    print(f"{Fore.GREEN}{Style.BRIGHT}   ALL SYSTEMS GREEN. INITIATING PUSH.  ")
    print(f"{Fore.GREEN}{Style.BRIGHT}========================================")

    commit_msg = input(f"{Fore.CYAN}Enter Commit Message: {Fore.WHITE}")
    if not commit_msg:
        commit_msg = "Sentinel Auto-Push: Security Verified"

    commands = [
        f'git add .',
        f'git commit -m "{commit_msg}"',
        f'git push origin main'
    ]

    for cmd in commands:
        if not run_command(cmd, cmd):
            print(f"{Fore.RED}[ERROR] Git command failed: {cmd}")
            sys.exit(1)

    print(f"
{Fore.GREEN}{Style.BRIGHT}✔ SUCCESS: Codebase secured and pushed to GitHub.")

if __name__ == "__main__":
    main()
