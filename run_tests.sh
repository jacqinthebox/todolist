#!/bin/bash
set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install package with test dependencies
echo "Installing package with test dependencies..."
pip install -e ".[test]"

# Run tests with coverage
echo "Running tests with coverage..."
python -m pytest --cov=todolist tests/ -v

# Run with additional flags if provided
if [ $# -gt 0 ]; then
    python -m pytest "$@"
fi

# Deactivation happens automatically when the script ends