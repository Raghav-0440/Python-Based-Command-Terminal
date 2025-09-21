#!/bin/bash

echo "Starting Python Terminal..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: Python is not installed"
        echo "Please install Python 3.6+ from your package manager"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to install some dependencies"
        echo "The terminal may not work properly"
        echo
    fi
fi

# Run the terminal
echo "Starting terminal..."
$PYTHON_CMD terminal.py
