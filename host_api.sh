#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")"
# Activate the virtual environment
source app/.venv/bin/activate

# Start the API server from the app directory
cd app
uvicorn main:app --reload