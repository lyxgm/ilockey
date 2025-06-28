#!/usr/bin/env python3
"""
Restore Working State - Get sensor back to working condition
Since it was working before, this is likely a software/state issue
"""

import serial
import time
import subprocess
import os
import json

class WorkingStateRestorer:
    """Restore sensor to previously working state"""
    
    def __init__(self):
        self.port = '/dev/ttyUSB0'
        self.baud = 57600
        
    def check_previous_working_state(self):
        """Check evidence of previous working state"""
        print("🔍 Checking Previous Working State")
        print("-" * 40)
        
        # Check fingerprint database
        db_file = 'data/fingerprints.json'
        if os.path.exists(db_file):
            try:
                with open(db_file, 'r') as f:
                    db = json.load(f)
                print(f"✅ Found fingerprint database with {len(db)} users:")
                for username, data in db.items():
                    print(f"   • {username} (enrolled: {data.get('enrolled_date', 'unknown')})")
                return True
            except:
                print("⚠️ Database file exists but couldn't read it")
        else:
            print("❌ No previous fingerprint database found")
        
        return False
    
    def kill_conflicting_processes(self):
        """Kill any processes that might be using the serial port"""
        print("\n🔄 Clearing Process Conflicts")
        print("-" * 40)
        
        try:
            # Check what's using the port
            result = subprocess.run(['lsof', self.port], capture_output=True, text=True)
            if result.stdout:
                print("📋 Processes using serial port:")
                print(result.stdout)
                
                # Kill processes using the port
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[1]
                            try:
                                subprocess.run(['kill', '-9', pid], check=True)
                                print(f"✅ Killed process {pid}")
                            except:
                                print(f"⚠️ Couldn't kill process {pid}")
            else:
                print("✅ No processes using serial port")
                
        except FileNotFoundError:
            print("⚠️ lsof not available, trying alternative method")
            
            # Alternative: kill any python processes that might be using serial
            try:
                result = subprocess.run(['pkill', '-f', 'fingerprint'], capture_output=True)
                print("✅ Killed any fingerprint-related processes")
            except:
                pass
    
    def reset_usb_device(self):
        """Reset the CP210x USB device"""
        print("\n🔌 Resetting USB Device")
        print("-" * 40)
        
        try:
            # Find the USB device
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            if '10c4:ea60' in result.stdout:
                print("✅ CP210x device found")
                
                # Try to reset via USB
                usb_path = "/dev/bus/usb/001/003"  # From previous output
                if os.path.exists(usb_path):
                    try:
                        # Unbind and rebind driver
                        subprocess.run(['sudo', 'sh', '-c', f'echo "1-1.3" > /sys/bus/usb/drivers/usb/unbind'], 
                                     capture_output=True)
                        time.sleep(1)
                        subprocess.run(['sudo', 'sh', '-c', f'echo "1-1.3" > /sys/bus/usb/drivers/usb/bind'], 
                                     capture_output=True)
                        print("✅ USB device reset attempted")
                        time.sleep(2)
                    except:
                        print("⚠️ USB reset failed, continuing anyway")
                
            else:
                print("❌ CP210x device not found")
                return False
                
        except Exception as e:
            print(f"⚠️ USB reset error: {e}")
        
        return True
    
    def test_basic_communication(self):
        """Test if basic communication is restored"""
        print("\n📡 Testing Basic Communication")
        print("-" * 40)
        
        try:
            sensor = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=2,
                write_timeout=2
            )
            time.sleep(0.5)
            
            # Test handshake
            handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            sensor.write(handshake)
            sensor.flush()
            time.sleep(0.5)
            
            response = sensor.read(12)
            sensor.close()
            
            if response and len(response) >= 9:
                error_code = response[8]
                print(f"📡 Response: {response.hex()}")
                print(f"🔍 Error code: 0x{error_code:02X}")
                
                if error_code == 0x00:
                    print("🎉 SUCCESS! Sensor is responding normally!")
                    return True
                elif error_code == 0x03:
                    print("⚠️ Still getting Error 0x03 (but communication works)")
                    return True  # Communication is working
                else:
                    print(f"⚠️ Different error: 0x{error_code:02X}")
                    return True  # Still communicating
            else:
                print("❌ No response from sensor")
                return False
                
        except Exception as e:
            print(f"❌ Communication test failed: {e}")
            return False
    
    def try_sensor_reset_sequence(self):
        """Try different sensor reset sequences"""
        print("\n🔄 Trying Sensor Reset Sequences")
        print("-" * 40)
        
        try:
            sensor = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=3,
                write_timeout=3
            )
            time.sleep(0.5)
            
            reset_sequences = [
                {
                    'name': 'Soft Reset',
                    'cmd': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x0D, 0x00, 0x11]
                },
                {
                    'name': 'Clear Buffer',
                    'cmd': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x12, 0x00, 0x16]
                },
                {
                    'name': 'Read System Parameters',
                    'cmd': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x0F, 0x00, 0x13]
                }
            ]
            
            for seq in reset_sequences:
                print(f"Trying {seq['name']}...")
                
                sensor.reset_input_buffer()
                sensor.reset_output_buffer()
                time.sleep(0.2)
                
                sensor.write(bytes(seq['cmd']))
                sensor.flush()
                time.sleep(1.0)
                
                response = sensor.read(20)  # Read more bytes for system params
                
                if response and len(response) >= 9:
                    error_code = response[8]
                    print(f"   Response: 0x{error_code:02X}")
                    
                    if error_code == 0x00:
                        print(f"   ✅ {seq['name']} successful!")
                    else:
                        print(f"   ⚠️ {seq['name']} returned error 0x{error_code:02X}")
                else:
                    print(f"   ❌ No response to {seq['name']}")
                
                time.sleep(0.5)
            
            sensor.close()
            
        except Exception as e:
            print(f"❌ Reset sequence failed: {e}")
    
    def test_image_capture_again(self):
        """Test if image capture is working again"""
        print("\n👆 Testing Image Capture")
        print("-" * 40)
        print("Let's test if the sensor can capture images again...")
        
        try:
            sensor = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=5,
                write_timeout=5
            )
            time.sleep(0.5)
            
            print("Place your finger on the sensor...")
            input("Press Enter when finger is on sensor...")
            
            # Try image capture
            get_image = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            
            sensor.reset_input_buffer()
            sensor.reset_output_buffer()
            time.sleep(0.3)
            
            sensor.write(get_image)
            sensor.flush()
            time.sleep(1.0)
            
            response = sensor.read(12)
            sensor.close()
            
            if response and len(response) >= 9:
                error_code = response[8]
                print(f"📡 Response: {response.hex()}")
                
                if error_code == 0x00:
                    print("🎉 SUCCESS! Image capture is working again!")
                    return True
                elif error_code == 0x02:
                    print("⚠️ No finger detected - try placing finger more firmly")
                    return False
                elif error_code == 0x03:
                    print("❌ Still getting imaging fail")
                    return False
                else:
                    print(f"⚠️ Different error: 0x{error_code:02X}")
                    return False
            else:
                print("❌ No response")
                return False
                
        except Exception as e:
            print(f"❌ Image capture test failed: {e}")
            return False
    
    def restore_working_state(self):
        """Main restoration process"""
        print("🔄 RESTORING SENSOR TO WORKING STATE")
        print("=" * 50)
        print("Your sensor was working before - let's get it back!")
        print()
        
        # Step 1: Check previous state
        had_working_state = self.check_previous_working_state()
        
        if not had_working_state:
            print("⚠️ No evidence of previous working state found")
            print("But let's try to restore it anyway...")
        
        # Step 2: Clear conflicts
        self.kill_conflicting_processes()
        
        # Step 3: Reset USB device
        self.reset_usb_device()
        
        # Step 4: Test communication
        comm_ok = self.test_basic_communication()
        
        if not comm_ok:
            print("❌ Basic communication failed")
            return False
        
        # Step 5: Try reset sequences
        self.try_sensor_reset_sequence()
        
        # Step 6: Test image capture
        print("\n🧪 FINAL TEST")
        print("=" * 20)
        capture_ok = self.test_image_capture_again()
        
        if capture_ok:
            print("\n🎉 RESTORATION SUCCESSFUL!")
            print("Your sensor is working again!")
            print("\n🎯 Next steps:")
            print("1. Try the optimized controller:")
            print("   python3 scripts/fingerprint_controller_optimized.py")
            print("2. Test enrollment with your existing user")
            return True
        else:
            print("\n⚠️ PARTIAL RESTORATION")
            print("Communication works but imaging still has issues")
            print("\n💡 Since it worked before, try:")
            print("1. Reboot the Raspberry Pi")
            print("2. Unplug and reconnect the sensor")
            print("3. Try the working controller again")
            return False

def main():
    """Main restoration function"""
    print("🔄 Sensor Working State Restorer")
    print("=" * 40)
    print()
    print("You're right - your sensor WAS working earlier!")
    print("Let's figure out what changed and restore it.")
    print()
    
    restorer = WorkingStateRestorer()
    success = restorer.restore_working_state()
    
    if success:
        print("\n✅ Try your sensor now - it should be working!")
    else:
        print("\n💡 If this doesn't work, try:")
        print("• Reboot: sudo reboot")
        print("• Unplug/replug USB")
        print("• Use the original working controller")

if __name__ == "__main__":
    main()
