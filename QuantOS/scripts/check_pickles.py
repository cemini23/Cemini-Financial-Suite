import robin_stocks.robinhood as r
import os

print(f"Current Working Directory: {os.getcwd()}")
print("If I log in, the token should save to '.tokens.pickle' in the directory above.")

# Check if we can find any pickle files anywhere in the project
import glob
pickles = glob.glob("**/*.pickle", recursive=True)
if pickles:
    print(f"Found these pickle files: {pickles}")
else:
    print("No .pickle files found in this directory or subdirectories.")
