#!/usr/bin/env python3
"""
Simple Camera Test Script for Smart Door Lock System
This script tests if the camera can be accessed and captures a test image.
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def test_picamera2():
    """Test PiCamera2 functionality"""
    print_header("TESTING PICAMERA2")
    
    try:
        from picamera2 import Picamera2
        import picamera2
        
        print(f"PiCamera2 version: {picamera2.__version__}")
        
        # Initialize camera
        print("Initializing camera...")
        picam2 = Picamera2()
        
        # Get camera info
        props = picam2.camera_properties
        print(f"Camera properties found: {', '.join(props.keys())}")
        
        if 'Model' in props:
            print(f"Camera model: {props['Model']}")
        
        # Configure camera
        print("Configuring camera...")
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        picam2.configure(config)
        
        # Start camera
        print("Starting camera...")
        picam2.start()
        print("Camera started successfully")
        
        # Wait for camera to initialize
        print("Waiting for camera to initialize...")
        time.sleep(2)
        
        # Create output directory
        os.makedirs("camera_test", exist_ok=True)
        
        # Capture image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"camera_test/test_image_{timestamp}.jpg"
        
        print(f"Capturing image to {output_file}...")
        picam2.capture_file(output_file)
        print(f"Image captured successfully to {output_file}")
        
        # Clean up
        picam2.stop()
        picam2.close()
        print("Camera stopped and closed")
        
        print("\nPiCamera2 TEST PASSED!")
        return True
        
    except ImportError:
        print("PiCamera2 is not installed")
        return False
    except Exception as e:
        print(f"Error testing PiCamera2: {e}")
        return False

def test_libcamera():
    """Test libcamera functionality"""
    print_header("TESTING LIBCAMERA")
    
    try:
        import subprocess
        
        # Check if libcamera-hello is available
        print("Checking if libcamera-hello is available...")
        result = subprocess.run(['which', 'libcamera-hello'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("libcamera-hello not found")
            return False
        
        print(f"libcamera-hello found at: {result.stdout.strip()}")
        
        # List cameras
        print("Listing available cameras...")
        result = subprocess.run(['libcamera-hello', '--list-cameras'], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        
        if "No cameras available" in result.stdout:
            print("No cameras detected by libcamera")
            return False
        
        # Create output directory
        os.makedirs("camera_test", exist_ok=True)
        
        # Capture test image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"camera_test/libcamera_test_{timestamp}.jpg"
        
        print(f"Capturing image to {output_file}...")
        result = subprocess.run(['libcamera-still', '-o', output_file, '--immediate'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Image captured successfully to {output_file}")
            print("\nLIBCAMERA TEST PASSED!")
            return True
        else:
            print(f"Failed to capture image: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error testing libcamera: {e}")
        return False

def test_raspistill():
    """Test raspistill functionality"""
    print_header("TESTING RASPISTILL")
    
    try:
        # Check if raspistill is available
        print("Checking if raspistill is available...")
        result = subprocess.run(['which', 'raspistill'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("raspistill not found")
            return False
        
        print(f"raspistill found at: {result.stdout.strip()}")
        
        # Create output directory
        os.makedirs("camera_test", exist_ok=True)
        
        # Capture test image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"camera_test/raspistill_test_{timestamp}.jpg"
        
        print(f"Capturing image to {output_file}...")
        result = subprocess.run(['raspistill', '-o', output_file], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Image captured successfully to {output_file}")
            print("\nRASPISTILL TEST PASSED!")
            return True
        else:
            print(f"Failed to capture image: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error testing raspistill: {e}")
        return False

def check_permissions():
    """Check permissions for camera access"""
    print_header("CHECKING PERMISSIONS")
    
    try:
        import subprocess
        
        # Check current user and groups
        print("Current user and groups:")
        result = subprocess.run(['id'], capture_output=True, text=True)
        print(result.stdout)
        
        # Check if user is in video group
        if "video" in result.stdout:
            print("User is in the video group ✓")
        else:
            print("User is NOT in the video group ✗")
            print("To add user to video group: sudo usermod -a -G video $USER")
        
        # Check permissions on video devices
        print("\nVideo device permissions:")
        result = subprocess.run(['ls', '-la', '/dev/video*'], 
                              capture_output=True, text=True)
        
        if "No such file or directory" in result.stderr:
            print("No video devices found")
        else:
            print(result.stdout)
            
    except Exception as e:
        print(f"Error checking permissions: {e}")

def main():
    """Main function"""
    print_header("CAMERA TEST UTILITY")
    print("This script will test if the camera can be accessed and capture a test image.")
    
    # Check permissions
    check_permissions()
    
    # Test libcamera
    libcamera_success = test_libcamera()
    
    # Test raspistill
    raspistill_success = test_raspistill()
    
    # Test PiCamera2
    picamera2_success = test_picamera2()
    
    # Summary
    print_header("TEST SUMMARY")
    print(f"libcamera test: {'PASSED' if libcamera_success else 'FAILED'}")
    print(f"raspistill test: {'PASSED' if raspistill_success else 'FAILED'}")
    print(f"PiCamera2 test: {'PASSED' if picamera2_success else 'FAILED'}")
    
    if libcamera_success or raspistill_success or picamera2_success:
        print("\nAt least one camera interface is working!")
        print("Check the camera_test directory for captured test images.")
    else:
        print("\nAll camera tests failed.")
        print("Please check your camera connection and permissions.")
        print("Make sure the camera is enabled in raspi-config.")
        print("Run: sudo raspi-config")
        print("Navigate to: Interface Options > Camera > Enable")
        print("\nAlso check if the user running this script is in the 'video' group:")
        print("sudo usermod -a -G video $USER")

if __name__ == "__main__":
    main()
