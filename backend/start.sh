#!/bin/bash
echo "Starting Purrfect Spots Backend Server..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/lib/python*/site-packages/flask" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ".env file not found. Please create one from .env.example"
    echo "Copy .env.example to .env and update with your AWS credentials"
    exit 1
fi

# Start the server
echo "Starting Flask server..."
python app.py
