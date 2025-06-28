#!/bin/bash

# Simple startup script for the Smart Door Lock application
# This script runs Flask without debug mode to avoid termios errors

# Change to the application directory
cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set Flask environment variables
export FLASK_APP=app.py
export FLASK_DEBUG=0  # Disable debug mode

echo "Starting Smart Door Lock application..."
echo "Access the web interface at http://$(hostname -I | awk '{print $1}'):5000"

# Run Flask without debug mode
python app.py
