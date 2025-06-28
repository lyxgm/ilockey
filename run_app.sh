#!/bin/bash

# Display a message
echo "Checking for existing camera processes..."

# Check for and kill any existing camera processes
# This helps prevent "Camera already in use" errors
ps aux | grep -E 'libcamera|picamera|raspistill' | grep -v grep
if [ $? -eq 0 ]; then
    echo "Found existing camera processes, attempting to stop them..."
    # Don't use sudo killall as it can cause issues
    # Instead, just notify the user if processes are found
    echo "Warning: Camera may be in use by another process."
    echo "If the app fails to start, you may need to reboot or manually stop camera processes."
fi

# Set environment variables to disable reloader
export WERKZEUG_RUN_MAIN=true
export FLASK_DEBUG=0

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start the application
echo "Starting application..."
python app.py

# Deactivate virtual environment when done
echo "Deactivating virtual environment..."
deactivate
