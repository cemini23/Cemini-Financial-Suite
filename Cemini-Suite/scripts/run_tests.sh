#!/bin/bash

# Run all Python unit tests in the current directory and subdirectories
python3 -m unittest discover -s scripts -p "test_*.py"
