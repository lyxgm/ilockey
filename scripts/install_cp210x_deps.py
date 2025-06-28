#!/usr/bin/env python3
"""
Install CP210x USB-to-UART Bridge dependencies for fingerprint sensors
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip()}")
        return False

def detect_cp210x_device():
    """Detect CP210x USB-to-UART bridge"""
    print("🔍 Detecting CP210x USB-to-UART bridge...")
    
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            
            for line in lines:
                if '10c4:ea60' in line.lower():
                    print(f"✅ Found CP210x device: {line.strip()}")
                    return True
                elif 'cp210x' in line.lower():
                    print(f"✅ Found CP210x device: {line.strip()}")
                    return True
            
            print("❌ CP210x device (10c4:ea60) not found")
            print("💡 Please connect your CP210x USB-to-UART bridge")
            return False
        else:
            print("⚠️ Could not run lsusb command")
            return False
            
    except Exception as e:
        print(f"❌ Error detecting CP210x: {e}")
        return False

def install_cp210x_driver():
    """Install CP210x driver"""
    print("🔧 Installing CP210x driver...")
    
    # Detect OS
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = f.read().lower()
    except:
        os_info = ""
    
    if 'ubuntu' in os_info or 'debian' in os_info:
        # Ubuntu/Debian
        packages = [
            "linux-modules-extra-$(uname -r)",
            "linux-image-extra-virtual"
        ]
        
        for package in packages:
            run_command(f"sudo apt update && sudo apt install -y {package}",
                       f"Installing {package}")
    
    elif 'fedora' in os_info or 'centos' in os_info or 'rhel' in os_info:
        # Fedora/CentOS/RHEL
        run_command("sudo dnf install -y kernel-modules-extra",
                   "Installing kernel modules")
    
    else:
        print("⚠️ Unknown OS, CP210x driver should be included in modern kernels")
    
    # Load the module
    run_command("sudo modprobe cp210x", "Loading CP210x module")

def check_cp210x_ports():
    """Check for CP210x serial ports"""
    print("🔍 Checking for CP210x serial ports...")
    
    import glob
    
    # Check for ttyUSB devices
    usb_ports = glob.glob('/dev/ttyUSB*')
    acm_ports = glob.glob('/dev/ttyACM*')
    
    all_ports = usb_ports + acm_ports
    
    if all_ports:
        print("✅ Found serial ports:")
        for port in sorted(all_ports):
            try:
                # Check port info
                result = subprocess.run(['udevadm', 'info', '--name=' + port], 
                                      capture_output=True, text=True)
                if 'cp210x' in result.stdout.lower() or '10c4' in result.stdout:
                    print(f"   📱 {port} (CP210x)")
                else:
                    print(f"   📄 {port}")
            except:
                print(f"   📄 {port}")
    else:
        print("❌ No serial ports found")
        print("💡 Try: sudo dmesg | grep cp210x")

def install_python_packages():
    """Install Python packages for CP210x fingerprint sensors (Raspberry Pi compatible)"""
    
    print("📦 Installing Python packages for CP210x (Raspberry Pi)...")
    
    # First try system packages (preferred on Raspberry Pi)
    system_packages = [
        "python3-serial",      # pyserial via apt
        "python3-pip",         # pip for additional packages
        "python3-venv",        # virtual environment support
    ]
    
    print("📦 Installing system packages...")
    for package in system_packages:
        run_command(f"sudo apt update && sudo apt install -y {package}", 
                   f"Installing {package}")
    
    # For packages not available via apt, use pip with --break-system-packages
    pip_packages = [
        "adafruit-circuitpython-fingerprint",
        "adafruit-blinka",
    ]
    
    print("📦 Installing additional packages via pip...")
    for package in pip_packages:
        success = run_command(f"{sys.executable} -m pip install {package} --break-system-packages", 
                            f"Installing {package}")
        if not success:
            print(f"⚠️ Optional package {package} failed, continuing...")
    
    # Test if pyserial is available
    try:
        import serial
        print("✅ pyserial is available")
        return True
    except ImportError:
        print("❌ pyserial not available")
        return False

def setup_permissions():
    """Set up permissions for CP210x devices"""
    print("🔐 Setting up CP210x device permissions...")
    
    # Add user to dialout group
    username = os.getenv('USER')
    if username:
        run_command(f"sudo usermod -a -G dialout {username}",
                   f"Adding {username} to dialout group")
    
    # Create udev rules for CP210x
    udev_rules = """
# CP210x USB-to-UART Bridge permissions
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"

# Generic CP210x devices
SUBSYSTEM=="tty", ATTRS{interface}=="CP2102 USB to UART Bridge Controller", MODE="0666", GROUP="dialout"
"""
    
    try:
        with open('/tmp/99-cp210x.rules', 'w') as f:
            f.write(udev_rules)
        
        run_command("sudo cp /tmp/99-cp210x.rules /etc/udev/rules.d/",
                   "Installing CP210x udev rules")
        run_command("sudo udevadm control --reload-rules",
                   "Reloading udev rules")
        run_command("sudo udevadm trigger",
                   "Triggering udev")
        
        os.remove('/tmp/99-cp210x.rules')
        
    except Exception as e:
        print(f"⚠️ Failed to set up udev rules: {e}")

def test_cp210x_connection():
    """Test CP210x connection"""
    print("🧪 Testing CP210x connection...")
    
    try:
        import serial
        import glob
        
        # Find potential CP210x ports
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        
        for port in sorted(ports):
            try:
                print(f"🔌 Testing {port}...")
                ser = serial.Serial(port, 9600, timeout=1)
                print(f"✅ {port} accessible")
                ser.close()
            except Exception as e:
                print(f"❌ {port} not accessible: {e}")
        
        if not ports:
            print("❌ No serial ports found")
            return False
        
        return True
        
    except ImportError:
        print("❌ pyserial not installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_fingerprint_sensor():
    """Test fingerprint sensor via CP210x"""
    print("🔐 Testing fingerprint sensor...")
    
    try:
        # Import our fingerprint controller
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from fingerprint_controller import FingerprintController
        
        fp_controller = FingerprintController()
        
        if fp_controller.available:
            print("✅ Fingerprint sensor detected and initialized")
            
            # Get sensor info
            info = fp_controller.get_sensor_info()
            print(f"📊 Sensor info: {info}")
            
            # Get CP210x info
            cp210x_info = fp_controller.get_cp210x_info()
            if cp210x_info:
                print(f"📱 CP210x info: {cp210x_info}")
            
            return True
        else:
            print("❌ Fingerprint sensor not detected")
            return False
            
    except Exception as e:
        print(f"❌ Fingerprint sensor test failed: {e}")
        return False

def main():
    """Main installation function"""
    print("🔐 CP210x USB-to-UART Fingerprint Sensor Setup")
    print("=" * 70)
    
    print("This script will set up CP210x USB-to-UART bridge for fingerprint sensors:")
    print("• Silicon Labs CP210x USB-to-UART Bridge (ID 10c4:ea60)")
    print("• R307/R503 fingerprint sensors via CP210x")
    print("• AS608 and other UART fingerprint modules")
    print()
    
    # Detect CP210x device first
    if not detect_cp210x_device():
        print("\n❌ CP210x device not found!")
        print("💡 Please:")
        print("   1. Connect your CP210x USB-to-UART bridge")
        print("   2. Connect fingerprint sensor to CP210x")
        print("   3. Run this script again")
        return
    
    response = input("\nContinue with CP210x setup? (y/N): ").strip().lower()
    if response != 'y':
        print("Setup cancelled")
        return
    
    print("\n🚀 Starting CP210x fingerprint sensor setup...")
    
    # Install CP210x driver
    install_cp210x_driver()
    
    # Install Python packages
    if not install_python_packages():
        print("❌ Critical packages failed to install")
        return
    
    # Set up permissions
    setup_permissions()
    
    # Check for ports
    check_cp210x_ports()
    
    # Test connection
    test_cp210x_connection()
    
    # Test fingerprint sensor
    test_fingerprint_sensor()
    
    print("\n" + "=" * 70)
    print("✅ CP210x fingerprint sensor setup completed!")
    print()
    print("📋 Next steps:")
    print("1. Logout and login again (for group permissions)")
    print("2. Connect fingerprint sensor to CP210x:")
    print("   VCC (Red)   -> 3.3V or 5V")
    print("   GND (Black) -> GND")
    print("   TX (White)  -> RX on CP210x")
    print("   RX (Green)  -> TX on CP210x")
    print("3. Test: python3 scripts/fingerprint_controller.py")
    print()
    print("🔧 Troubleshooting:")
    print("   - Check: lsusb | grep 10c4:ea60")
    print("   - Check: ls -l /dev/ttyUSB*")
    print("   - Check: groups $USER")

if __name__ == "__main__":
    main()
