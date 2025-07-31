#!/bin/bash

# Galaksio Server Launch Script
# Updated for Galaxy 25.0 compatibility

# Set Python 3 as default
PYTHON_CMD=python3

# Check if Python 3 is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.9 or later."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Python 3.9 or later is required. Found Python $PYTHON_VERSION"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
fi

# Create necessary directories
mkdir -p ../log
mkdir -p ../tmp

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start the server
echo "Starting Galaksio server..."
$PYTHON_CMD launch_server.py "$@"
