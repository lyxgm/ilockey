#!/usr/bin/env python3
"""
CP210x USB-to-UART Bridge Diagnostic Tool
Troubleshoot fingerprint sensor communication issues
"""

import subprocess
import time
import os
import signal

def run_command(command, description="Running command"):
    """Run a command and return result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_cp210x_device():
    """Check CP210x USB device"""
    print("🔍 Checking CP210x USB device...")
    
    success, stdout, stderr = run_command("lsusb | grep -i '10c4:ea60\\|cp210x'")
    
    if success and stdout.strip():
        print(f"✅ CP210x device found:")
        for line in stdout.strip().split('\n'):
            print(f"   {line}")
        return True
    else:
        print("❌ CP210x device not found")
        print("💡 Check USB connection")
        return False

def check_serial_ports():
    """Check available serial ports"""
    print("\n🔍 Checking serial ports...")
    
    import glob
    
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    
    if ports:
        print("✅ Found serial ports:")
        for port in sorted(ports):
            # Check permissions
            try:
                stat_info = os.stat(port)
                perms = oct(stat_info.st_mode)[-3:]
                print(f"   {port} (permissions: {perms})")
            except Exception as e:
                print(f"   {port} (error: {e})")
    else:
        print("❌ No serial ports found")
        return False
    
    return len(ports) > 0

def check_port_usage():
    """Check if any process is using the serial ports"""
    print("\n🔍 Checking port usage...")
    
    # Check for processes using ttyUSB ports
    success, stdout, stderr = run_command("lsof /dev/ttyUSB* 2>/dev/null")
    
    if success and stdout.strip():
        print("⚠️ Processes using serial ports:")
        print(stdout)
        return True
    else:
        print("✅ No processes using serial ports")
        return False

def kill_serial_processes():
    """Kill processes using serial ports"""
    print("\n🔧 Killing processes using serial ports...")
    
    # Get PIDs of processes using ttyUSB
    success, stdout, stderr = run_command("lsof -t /dev/ttyUSB* 2>/dev/null")
    
    if success and stdout.strip():
        pids = stdout.strip().split('\n')
        for pid in pids:
            try:
                pid = int(pid.strip())
                print(f"   Killing PID {pid}...")
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.5)
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Process already dead
            except Exception as e:
                print(f"   Failed to kill PID {pid}: {e}")
        
        time.sleep(1)
        print("✅ Serial port processes terminated")
        return True
    else:
        print("✅ No processes to kill")
        return False

def reset_usb_device():
    """Reset CP210x USB device"""
    print("\n🔧 Resetting CP210x USB device...")
    
    # Find USB device path
    success, stdout, stderr = run_command("lsusb -d 10c4:ea60")
    
    if not success or not stdout.strip():
        print("❌ CP210x device not found for reset")
        return False
    
    # Extract bus and device numbers
    try:
        line = stdout.strip()
        parts = line.split()
        bus = parts[1]
        device = parts[3].rstrip(':')
        
        usb_path = f"/dev/bus/usb/{bus}/{device}"
        
        print(f"   USB path: {usb_path}")
        
        # Try to reset using usbreset if available
        success, stdout, stderr = run_command(f"which usbreset")
        if success:
            success, stdout, stderr = run_command(f"sudo usbreset {usb_path}")
            if success:
                print("✅ USB device reset successful")
                time.sleep(2)
                return True
        
        # Alternative: unbind and rebind driver
        print("   Trying driver unbind/rebind...")
        
        # Find the device in sysfs
        success, stdout, stderr = run_command(f"find /sys/bus/usb/devices -name '*10c4:ea60*' -type d")
        
        if success and stdout.strip():
            device_path = stdout.strip().split('\n')[0]
            driver_path = f"{device_path}/driver"
            
            if os.path.exists(driver_path):
                device_name = os.path.basename(device_path)
                
                # Unbind
                run_command(f"echo '{device_name}' | sudo tee /sys/bus/usb/drivers/cp210x/unbind")
                time.sleep(1)
                
                # Rebind
                run_command(f"echo '{device_name}' | sudo tee /sys/bus/usb/drivers/cp210x/bind")
                time.sleep(2)
                
                print("✅ Driver unbind/rebind completed")
                return True
        
        print("⚠️ Could not reset USB device")
        return False
        
    except Exception as e:
        print(f"❌ USB reset failed: {e}")
        return False

def test_serial_communication():
    """Test basic serial communication"""
    print("\n🧪 Testing serial communication...")
    
    try:
        import serial
        import glob
        
        ports = glob.glob('/dev/ttyUSB*')
        
        for port in ports:
            print(f"\n🔌 Testing {port}...")
            
            baud_rates = [57600, 9600, 19200, 38400, 115200]
            
            for baud in baud_rates:
                try:
                    print(f"   Testing {baud} baud...")
                    
                    # Open serial port with short timeout
                    ser = serial.Serial(
                        port=port,
                        baudrate=baud,
                        timeout=1,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        xonxoff=False,
                        rtscts=False,
                        dsrdtr=False
                    )
                    
                    time.sleep(0.2)
                    
                    # Clear buffers
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                    
                    # Send fingerprint sensor handshake
                    handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
                    ser.write(handshake)
                    
                    time.sleep(0.5)
                    
                    # Read response
                    response = ser.read(20)  # Read more bytes
                    
                    ser.close()
                    
                    if len(response) > 0:
                        print(f"   ✅ Response at {baud}: {response.hex()}")
                        
                        # Check if it's a valid fingerprint sensor response
                        if len(response) >= 2 and response[0:2] == bytes([0xEF, 0x01]):
                            print(f"   🎯 Valid fingerprint sensor found at {port}:{baud}")
                            return port, baud
                    else:
                        print(f"   ❌ No response at {baud}")
                        
                except Exception as e:
                    print(f"   ❌ Error at {baud}: {e}")
                    continue
        
        print("❌ No working fingerprint sensor found")
        return None, None
        
    except ImportError:
        print("❌ pyserial not installed")
        return None, None
    except Exception as e:
        print(f"❌ Serial test failed: {e}")
        return None, None

def check_permissions():
    """Check user permissions for serial ports"""
    print("\n🔐 Checking permissions...")
    
    # Check if user is in dialout group
    success, stdout, stderr = run_command("groups $USER")
    
    if success:
        groups = stdout.strip()
        if 'dialout' in groups:
            print("✅ User is in dialout group")
        else:
            print("❌ User is NOT in dialout group")
            print("💡 Run: sudo usermod -a -G dialout $USER")
            print("💡 Then logout and login again")
            return False
    
    # Check port permissions
    import glob
    ports = glob.glob('/dev/ttyUSB*')
    
    for port in ports:
        try:
            stat_info = os.stat(port)
            mode = stat_info.st_mode
            
            # Check if readable/writable by group
            if mode & 0o060:  # Group read/write
                print(f"✅ {port} has group permissions")
            else:
                print(f"❌ {port} lacks group permissions")
                return False
                
        except Exception as e:
            print(f"❌ Cannot check {port}: {e}")
            return False
    
    return True

def install_usbreset():
    """Install usbreset utility"""
    print("\n📦 Installing usbreset utility...")
    
    # Check if usbreset exists
    success, stdout, stderr = run_command("which usbreset")
    if success:
        print("✅ usbreset already installed")
        return True
    
    # Try to install usbutils
    success, stdout, stderr = run_command("sudo apt update && sudo apt install -y usbutils")
    if success:
        print("✅ usbutils installed")
        
        # Check again
        success, stdout, stderr = run_command("which usbreset")
        if success:
            print("✅ usbreset now available")
            return True
    
    # If not available, create a simple reset script
    print("📝 Creating USB reset script...")
    
    reset_script = '''#!/bin/bash
# Simple USB device reset script
if [ $# -ne 1 ]; then
    echo "Usage: $0 /dev/bus/usb/BUS/DEV"
    exit 1
fi

DEVICE=$1

if [ ! -e "$DEVICE" ]; then
    echo "Device $DEVICE not found"
    exit 1
fi

echo "Resetting USB device: $DEVICE"

# Method 1: Use ioctl reset
python3 -c "
import fcntl
import sys
USBDEVFS_RESET = 0x5514
try:
    with open('$DEVICE', 'wb') as f:
        fcntl.ioctl(f, USBDEVFS_RESET, 0)
    print('USB device reset successful')
except Exception as e:
    print(f'USB reset failed: {e}')
    sys.exit(1)
"
'''
    
    try:
        with open('/tmp/usbreset', 'w') as f:
            f.write(reset_script)
        
        run_command("chmod +x /tmp/usbreset")
        run_command("sudo mv /tmp/usbreset /usr/local/bin/")
        
        print("✅ USB reset script created")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create reset script: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🔐 CP210x USB-to-UART Fingerprint Sensor Diagnostic")
    print("=" * 70)
    
    # Step 1: Check CP210x device
    if not check_cp210x_device():
        print("\n❌ CP210x device not found. Check USB connection.")
        return
    
    # Step 2: Check serial ports
    if not check_serial_ports():
        print("\n❌ No serial ports found. Check driver installation.")
        return
    
    # Step 3: Check permissions
    if not check_permissions():
        print("\n❌ Permission issues found. Fix permissions first.")
        return
    
    # Step 4: Check for port conflicts
    if check_port_usage():
        print("\n⚠️ Port conflicts detected. Attempting to resolve...")
        kill_serial_processes()
    
    # Step 5: Reset USB device
    print("\n🔧 Resetting CP210x device...")
    install_usbreset()
    reset_usb_device()
    
    # Step 6: Test communication
    port, baud = test_serial_communication()
    
    if port and baud:
        print(f"\n✅ SUCCESS: Fingerprint sensor working on {port} at {baud} baud")
        print("\n📋 Next steps:")
        print("1. Run: python3 scripts/fingerprint_controller.py")
        print("2. Test fingerprint enrollment")
        print("3. Test fingerprint authentication")
    else:
        print("\n❌ FAILED: Could not establish communication with fingerprint sensor")
        print("\n🔧 Additional troubleshooting:")
        print("1. Check wiring connections")
        print("2. Try different baud rates")
        print("3. Check sensor power supply")
        print("4. Verify sensor model compatibility")

if __name__ == "__main__":
    main()
