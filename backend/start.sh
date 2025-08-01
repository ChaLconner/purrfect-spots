#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Start the application
uvicorn main:app --host 0.0.0.0 --port $PORT
