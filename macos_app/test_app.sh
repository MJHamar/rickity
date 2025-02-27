#!/bin/bash

# Make sure the API server is running
echo "Checking if API server is running..."
curl -s http://localhost:8000/timer > /dev/null
if [ $? -ne 0 ]; then
  echo "API server is not running. Please start it first with:"
  echo "cd .. && sh host_api.sh"
  exit 1
fi

echo "API server is running. Starting macOS app..."

# Run the app
python run.py 