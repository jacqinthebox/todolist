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

# Install dependencies
echo "Installing dependencies..."
pip install -e .

# Run the application
echo "Starting the Todo List application..."
echo "API will be available at http://localhost:8000"
todolist --host 127.0.0.1 --port 8000

# Deactivation happens automatically when the script ends