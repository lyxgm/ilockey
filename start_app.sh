#!/bin/bash

# Smart Door Lock Web Application Startup Script

# Change to the application directory
cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if camera is detected
echo "Checking camera status..."
if libcamera-hello --list-cameras 2>/dev/null | grep -q "Available cameras"; then
    echo "Camera detected!"
else
    echo "Warning: No camera detected. The application will use a placeholder stream."
fi

# Check if user is in video group
if groups | grep -q "video"; then
    echo "User has video group permissions."
else
    echo "Warning: Current user is not in the video group."
    echo "Consider adding user to video group with: sudo usermod -a -G video $USER"
fi

# Check if any process is using the camera
if fuser -v /dev/video0 2>/dev/null; then
    echo "Warning: Another process is using the camera. This may cause issues."
fi

# Start the application
echo "Starting Smart Door Lock application..."
echo "Access the web interface at http://$(hostname -I | awk '{print $1}'):5000"

# Run with or without debug mode based on argument
if [ "$1" == "--debug" ]; then
    echo "Running in debug mode..."
    FLASK_APP=app.py FLASK_DEBUG=1 python app.py
else
    echo "Running in production mode..."
    # Redirect stdout and stderr to log file
    python app.py > app.log 2>&1
fi
