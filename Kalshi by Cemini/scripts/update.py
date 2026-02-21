import subprocess
import sys
import os
from colorama import init, Fore

init(autoreset=True)

def update_bot():
    print(f"{Fore.CYAN}Checking for updates from GitHub...")
    
    try:
        # Pull latest code
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        
        if "Already up to date" in result.stdout:
            print(f"{Fore.GREEN}You are already on the latest version.")
        else:
            print(f"{Fore.GREEN}Update found and downloaded!")
            print(f"{Fore.YELLOW}Log:
{result.stdout}")
            print(f"{Fore.CYAN}Please run the installer script again to rebuild the exe.")
            
    except Exception as e:
        print(f"{Fore.RED}Update failed: {e}")

if __name__ == "__main__":
    update_bot()
