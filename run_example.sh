#!/bin/bash
# Example script to run the Network LAB Automation Framework

echo "Network LAB Automation Framework - Example Run"
echo "=============================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Run the automation
echo "Running network automation..."
python3 main.py

echo "Automation completed!" 