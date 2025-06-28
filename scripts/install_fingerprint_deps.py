#!/usr/bin/env python3
"""
Install fingerprint sensor dependencies
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

def install_python_packages():
    """Install Python packages for UART fingerprint sensors"""
    packages = [
        "adafruit-circuitpython-fingerprint",  # Primary library for R307/R503
        "pyserial",                            # Essential for UART communication
        "adafruit-blinka",                     # CircuitPython compatibility
        "adafruit-circuitpython-busdevice",    # Bus device support
    ]
    
    print("📦 Installing UART fingerprint sensor packages...")
    
    for package in packages:
        success = run_command(f"{sys.executable} -m pip install {package}", 
                            f"Installing {package}")
        if not success and package in ["adafruit-circuitpython-fingerprint", "pyserial"]:
            print(f"❌ Critical package {package} failed to install!")
            return False
        elif not success:
            print(f"⚠️ Optional package {package} failed, continuing...")
    
    return True

def install_system_packages():
    """Install system packages for fingerprint support"""
    print("🔧 Installing system packages...")
    
    # Detect OS
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = f.read().lower()
    except:
        os_info = ""
    
    if 'ubuntu' in os_info or 'debian' in os_info:
        install_debian_packages()
    elif 'fedora' in os_info or 'centos' in os_info or 'rhel' in os_info:
        install_fedora_packages()
    elif 'arch' in os_info:
        install_arch_packages()
    else:
        print("⚠️ Unknown OS, please install packages manually:")
        print("   - libfprint development libraries")
        print("   - GObject introspection libraries")
        print("   - Python development headers")

def install_debian_packages():
    """Install packages on Debian/Ubuntu"""
    packages = [
        "libfprint-2-dev",      # Fingerprint library
        "gir1.2-fprint-2.0",    # GObject introspection
        "python3-dev",          # Python headers
        "python3-gi",           # Python GObject
        "libgirepository1.0-dev", # GI development
        "pkg-config",           # Package config
    ]
    
    # Update package list
    run_command("sudo apt update", "Updating package list")
    
    # Install packages
    package_list = " ".join(packages)
    run_command(f"sudo apt install -y {package_list}", 
               "Installing fingerprint support packages")

def install_fedora_packages():
    """Install packages on Fedora/CentOS/RHEL"""
    packages = [
        "libfprint-devel",
        "python3-devel", 
        "python3-gobject",
        "gobject-introspection-devel",
        "pkgconfig",
    ]
    
    package_list = " ".join(packages)
    run_command(f"sudo dnf install -y {package_list}",
               "Installing fingerprint support packages")

def install_arch_packages():
    """Install packages on Arch Linux"""
    packages = [
        "libfprint",
        "python-gobject",
        "gobject-introspection",
        "pkgconf",
    ]
    
    package_list = " ".join(packages)
    run_command(f"sudo pacman -S --noconfirm {package_list}",
               "Installing fingerprint support packages")

def setup_permissions():
    """Set up permissions for fingerprint devices"""
    print("🔐 Setting up device permissions...")
    
    # Add user to plugdev group for USB access
    username = os.getenv('USER')
    if username:
        run_command(f"sudo usermod -a -G plugdev {username}",
                   f"Adding {username} to plugdev group")
    
    # Create udev rules for fingerprint devices
    udev_rules = """
# Fingerprint sensor permissions
# R307/R503 UART sensors
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666", GROUP="plugdev"

# USB fingerprint readers
SUBSYSTEM=="usb", ATTRS{idVendor}=="147e", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="08ff", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="00bb", MODE="0666", GROUP="plugdev"

# Generic fingerprint devices
SUBSYSTEM=="usb", ATTR{bInterfaceClass}=="03", ATTR{bInterfaceSubClass}=="00", MODE="0666", GROUP="plugdev"
"""
    
    try:
        with open('/tmp/99-fingerprint.rules', 'w') as f:
            f.write(udev_rules)
        
        run_command("sudo cp /tmp/99-fingerprint.rules /etc/udev/rules.d/",
                   "Installing udev rules")
        run_command("sudo udevadm control --reload-rules",
                   "Reloading udev rules")
        run_command("sudo udevadm trigger",
                   "Triggering udev")
        
        os.remove('/tmp/99-fingerprint.rules')
        
    except Exception as e:
        print(f"⚠️ Failed to set up udev rules: {e}")

def enable_uart():
    """Enable UART on Raspberry Pi"""
    print("📡 Checking UART configuration...")
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        if 'raspberry pi' in cpuinfo.lower():
            print("🍓 Raspberry Pi detected")
            
            # Check if UART is enabled
            config_file = '/boot/config.txt'
            if not os.path.exists(config_file):
                config_file = '/boot/firmware/config.txt'  # Ubuntu on Pi
            
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = f.read()
                    
                    if 'enable_uart=1' not in config:
                        print("⚙️ UART not enabled, please add to /boot/config.txt:")
                        print("   enable_uart=1")
                        print("   Then reboot the system")
                    else:
                        print("✅ UART already enabled")
                        
                except Exception as e:
                    print(f"⚠️ Could not check UART config: {e}")
            
    except:
        print("ℹ️ Not running on Raspberry Pi")

def configure_raspberry_pi_uart():
    """Configure Raspberry Pi UART for fingerprint sensor"""
    print("🍓 Configuring Raspberry Pi UART...")
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        if 'raspberry pi' not in cpuinfo.lower():
            print("ℹ️ Not running on Raspberry Pi, skipping UART configuration")
            return True
            
    except:
        print("ℹ️ Could not detect Raspberry Pi, skipping UART configuration")
        return True
    
    # Check and configure boot config
    config_files = ['/boot/config.txt', '/boot/firmware/config.txt']
    config_file = None
    
    for cf in config_files:
        if os.path.exists(cf):
            config_file = cf
            break
    
    if not config_file:
        print("⚠️ Could not find boot config file")
        return False
    
    try:
        # Read current config
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        # Check if UART is already enabled
        uart_enabled = 'enable_uart=1' in config_content
        serial_disabled = 'console=serial0' not in config_content
        
        if uart_enabled and serial_disabled:
            print("✅ UART already properly configured")
            return True
        
        print("⚙️ UART configuration needed")
        print("📝 Required changes to", config_file, ":")
        
        if not uart_enabled:
            print("   + enable_uart=1")
        
        print("\n📝 Required changes to /boot/cmdline.txt:")
        print("   - Remove: console=serial0,115200")
        
        print("\n⚠️ Manual configuration required:")
        print("1. Edit", config_file)
        print("   Add: enable_uart=1")
        print("2. Edit /boot/cmdline.txt")
        print("   Remove: console=serial0,115200")
        print("3. Reboot the system")
        print("4. Test with: ls -l /dev/serial*")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring UART: {e}")
        return False

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    # Test Python imports
    test_imports = [
        ("serial", "PySerial"),
        ("adafruit_fingerprint", "Adafruit Fingerprint"),
    ]
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name} import successful")
        except ImportError:
            print(f"❌ {name} import failed")
    
    # Test libfprint
    try:
        import gi
        gi.require_version('FPrint', '2.0')
        from gi.repository import FPrint
        print("✅ libfprint import successful")
    except Exception as e:
        print(f"❌ libfprint import failed: {e}")
    
    # Check for devices
    print("\n🔍 Checking for devices...")
    
    # Check UART devices
    uart_devices = ['/dev/ttyUSB0', '/dev/ttyAMA0', '/dev/serial0']
    for device in uart_devices:
        if os.path.exists(device):
            print(f"✅ Found UART device: {device}")
    
    # Check USB devices
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            fingerprint_keywords = ['fingerprint', 'biometric', '147e:', '08ff:']
            
            for line in lines:
                for keyword in fingerprint_keywords:
                    if keyword.lower() in line.lower():
                        print(f"✅ Possible fingerprint device: {line.strip()}")
                        break
    except:
        pass

def detect_uart_devices():
    """Detect available UART devices"""
    print("🔍 Detecting UART devices...")
    
    uart_devices = [
        '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2',
        '/dev/ttyAMA0', '/dev/ttyAMA1',
        '/dev/serial0', '/dev/serial1',
        '/dev/ttyS0', '/dev/ttyS1'
    ]
    
    found_devices = []
    
    for device in uart_devices:
        if os.path.exists(device):
            try:
                # Check if device is accessible
                import serial
                ser = serial.Serial(device, 9600, timeout=1)
                ser.close()
                found_devices.append(device)
                print(f"✅ Found accessible UART device: {device}")
            except Exception as e:
                print(f"⚠️ Found but cannot access {device}: {e}")
    
    if not found_devices:
        print("❌ No accessible UART devices found")
        print("💡 Troubleshooting:")
        print("   - Check physical connections")
        print("   - Verify UART is enabled (Raspberry Pi)")
        print("   - Check user permissions: sudo usermod -a -G dialout $USER")
        print("   - Try: sudo chmod 666 /dev/ttyUSB0")
    
    return found_devices

def main():
    """Main installation function"""
    print("🔐 UART Fingerprint Sensor Setup")
    print("=" * 60)
    
    print("This script will set up UART fingerprint sensors:")
    print("• R307/R503 UART sensors")
    print("• AS608 optical sensors")
    print("• ZFM-20 series sensors")
    print("• Generic UART fingerprint modules")
    print()
    
    response = input("Continue with UART sensor setup? (y/N): ").strip().lower()
    if response != 'y':
        print("Setup cancelled")
        return
    
    print("\n🚀 Starting UART fingerprint sensor setup...")
    
    # Install Python packages
    if not install_python_packages():
        print("❌ Critical packages failed to install")
        return
    
    # Configure Raspberry Pi UART
    configure_raspberry_pi_uart()
    
    # Set up permissions
    setup_permissions()
    
    # Detect UART devices
    uart_devices = detect_uart_devices()
    
    # Test installation
    test_installation()
    
    print("\n" + "=" * 60)
    print("✅ UART fingerprint sensor setup completed!")
    print()
    print("📋 Next steps:")
    print("1. Connect your UART fingerprint sensor:")
    print("   VCC -> 3.3V or 5V")
    print("   GND -> GND") 
    print("   TX  -> GPIO 15 (RX)")
    print("   RX  -> GPIO 14 (TX)")
    print("2. Reboot if on Raspberry Pi")
    print("3. Test: python3 scripts/fingerprint_controller.py")
    print()
    if uart_devices:
        print(f"🔌 Available UART devices: {', '.join(uart_devices)}")
    print("🔧 Troubleshooting: Check wiring and permissions")

if __name__ == "__main__":
    main()
