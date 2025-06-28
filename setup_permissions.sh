#!/bin/bash

# Make scripts executable
chmod +x start_app.sh
chmod +x test_camera.py
chmod +x scripts/camera_diagnostic.py

# Create necessary directories
mkdir -p static/captures
mkdir -p static/test
mkdir -p camera_test

# Set proper permissions
chmod 755 static/captures
chmod 755 static/test
chmod 755 camera_test

echo "Permissions set successfully!"
echo "You can now run:"
echo "  ./test_camera.py - to test the camera directly"
echo "  ./start_app.sh - to start the application in production mode"
echo "  ./start_app.sh --debug - to start the application in debug mode"
