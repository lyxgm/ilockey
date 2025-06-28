#!/usr/bin/env python3
"""
Camera Diagnostic Tool for Smart Door Lock System
This script helps diagnose camera issues by checking various aspects of the camera setup.
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def run_command(command, description=None):
    """Run a shell command and print its output"""
    if description:
        print(f"\n> {description}:")
    
    print(f"$ {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error output: {result.stderr}")
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        print(f"Error executing command: {e}")
        return None, str(e), -1

def check_system_info():
    """Check basic system information"""
    print_header("SYSTEM INFORMATION")
    
    # Check OS version
    run_command(["lsb_release", "-a"], "OS Version")
    
    # Check kernel version
    run_command(["uname", "-a"], "Kernel Version")
    
    # Check Raspberry Pi model
    run_command(["cat", "/proc/device-tree/model"], "Raspberry Pi Model")
    
    # Check memory
    run_command(["free", "-h"], "Memory Information")
    
    # Check disk space
    run_command(["df", "-h"], "Disk Space")

def check_camera_modules():
    """Check if camera modules are loaded"""
    print_header("CAMERA MODULES")
    
    # Check loaded modules
    run_command(["lsmod"], "Loaded Kernel Modules")
    
    # Check specifically for camera modules
    run_command(["lsmod", "|", "grep", "camera"], "Camera Modules")
    run_command(["lsmod", "|", "grep", "bcm2835"], "BCM2835 Modules")
    run_command(["lsmod", "|", "grep", "v4l"], "V4L Modules")

def check_camera_devices():
    """Check camera devices"""
    print_header("CAMERA DEVICES")
    
    # Check video devices
    run_command(["ls", "-la", "/dev/video*"], "Video Devices")
    
    # Check v4l2 devices if available
    run_command(["v4l2-ctl", "--list-devices"], "V4L2 Devices")
    
    # Check if camera is enabled in config
    run_command(["vcgencmd", "get_camera"], "Camera Config")

def check_libcamera():
    """Check libcamera status"""
    print_header("LIBCAMERA STATUS")
    
    # Check libcamera version
    run_command(["apt", "list", "libcamera*"], "Libcamera Packages")
    
    # List available cameras
    run_command(["libcamera-hello", "--list-cameras"], "Available Cameras")
    
    # Get camera info
    run_command(["libcamera-hello", "--info"], "Camera Info")

def check_picamera2():
    """Check PiCamera2 status"""
    print_header("PICAMERA2 STATUS")
    
    # Check if PiCamera2 is installed
    print("Checking PiCamera2 installation...")
    try:
        import picamera2
        print(f"PiCamera2 is installed (version: {picamera2.__version__})")
        
        # Try to initialize camera
        print("\nAttempting to initialize PiCamera2...")
        try:
            from picamera2 import Picamera2
            picam2 = Picamera2()
            print("PiCamera2 initialized successfully")
            
            # Get camera properties
            props = picam2.camera_properties
            print(f"\nCamera properties: {json.dumps(props, indent=2)}")
            
            # Get camera configuration
            config = picam2.create_preview_configuration()
            print(f"\nDefault configuration: {config}")
            
            # Try to start camera
            print("\nAttempting to start camera...")
            picam2.start()
            print("Camera started successfully")
            
            # Try to capture a frame
            print("\nAttempting to capture a frame...")
            frame = picam2.capture_array()
            print(f"Frame captured successfully: shape={frame.shape}, dtype={frame.dtype}")
            
            # Clean up
            picam2.stop()
            picam2.close()
            print("Camera stopped and closed")
            
        except Exception as e:
            print(f"Error initializing PiCamera2: {e}")
    except ImportError:
        print("PiCamera2 is not installed")

def check_permissions():
    """Check permissions for camera access"""
    print_header("PERMISSIONS")
    
    # Check current user and groups
    run_command(["id"], "Current User")
    
    # Check permissions on video devices
    run_command(["ls", "-la", "/dev/video*"], "Video Device Permissions")
    
    # Check if user is in video group
    stdout, _, _ = run_command(["groups"], "User Groups")
    if stdout and "video" in stdout:
        print("\nUser is in the video group ✓")
    else:
        print("\nUser is NOT in the video group ✗")
        print("To add user to video group: sudo usermod -a -G video $USER")

def check_processes():
    """Check if any processes are using the camera"""
    print_header("PROCESSES USING CAMERA")
    
    # Check processes using video devices
    run_command(["fuser", "-v", "/dev/video0"], "Processes Using /dev/video0")
    
    # List all python processes
    run_command(["ps", "aux", "|", "grep", "python"], "Python Processes")

def test_capture():
    """Test capturing an image"""
    print_header("TEST CAPTURE")
    
    # Create output directory
    output_dir = "camera_test"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/test_capture_{timestamp}.jpg"
    
    print(f"Attempting to capture image to {filename}...")
    
    # Try with libcamera-still
    try:
        cmd = ["libcamera-still", "-o", filename, "--immediate"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"Image captured successfully with libcamera-still: {filename}")
            print(f"File size: {os.path.getsize(filename)} bytes")
        else:
            print(f"Failed to capture with libcamera-still: {result.stderr}")
            
            # Try with raspistill as fallback
            print("\nTrying with raspistill as fallback...")
            cmd = ["raspistill", "-o", filename]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"Image captured successfully with raspistill: {filename}")
                print(f"File size: {os.path.getsize(filename)} bytes")
            else:
                print(f"Failed to capture with raspistill: {result.stderr}")
    except Exception as e:
        print(f"Error during capture test: {e}")

def generate_report():
    """Generate a summary report"""
    print_header("DIAGNOSTIC SUMMARY")
    
    # Check if camera is detected
    stdout, _, _ = run_command(["vcgencmd", "get_camera"], "Camera Detection")
    camera_detected = "detected=1" in stdout if stdout else False
    
    # Check if libcamera can see cameras
    stdout, _, _ = run_command(["libcamera-hello", "--list-cameras"], "Libcamera Detection")
    libcamera_detected = "Available cameras" in stdout and not "No cameras available" in stdout if stdout else False
    
    # Check if video device exists
    stdout, _, _ = run_command(["ls", "/dev/video0"], "Video Device")
    video_device_exists = stdout is not None and "No such file" not in stdout
    
    # Print summary
    print("\nCamera Status Summary:")
    print(f"- Camera enabled in system config: {'Yes ✓' if camera_detected else 'No ✗'}")
    print(f"- Camera detected by libcamera: {'Yes ✓' if libcamera_detected else 'No ✗'}")
    print(f"- Video device exists: {'Yes ✓' if video_device_exists else 'No ✗'}")
    
    # Provide recommendations
    print("\nRecommendations:")
    
    if not camera_detected:
        print("- Enable camera in raspi-config: sudo raspi-config")
        print("  Navigate to Interface Options > Camera > Enable")
        print("  Then reboot: sudo reboot")
    
    if not video_device_exists:
        print("- Check camera connection (ribbon cable)")
        print("- Make sure camera is properly seated in the connector")
        print("- Try rebooting: sudo reboot")
    
    if not libcamera_detected and camera_detected and video_device_exists:
        print("- Check libcamera installation: sudo apt install -y libcamera-apps")
        print("- Check for firmware updates: sudo apt update && sudo apt upgrade")
    
    # Check permissions
    stdout, _, _ = run_command(["groups"], "User Groups")
    if stdout and "video" not in stdout:
        print("- Add user to video group: sudo usermod -a -G video $USER")
        print("  Then log out and log back in")
    
    # Final advice
    print("\nFor the web application:")
    print("- Make sure the web app is running as a user with camera access")
    print("- Check the web app logs for camera-related errors")
    print("- Try restarting the web app after fixing any issues")

def main():
    """Main function"""
    print_header("CAMERA DIAGNOSTIC TOOL")
    print("Running comprehensive camera diagnostics...")
    
    # Run all checks
    check_system_info()
    check_camera_modules()
    check_camera_devices()
    check_libcamera()
    check_picamera2()
    check_permissions()
    check_processes()
    test_capture()
    generate_report()
    
    print("\nDiagnostic complete!")

if __name__ == "__main__":
    main()
