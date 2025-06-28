#!/usr/bin/env python3
"""
Fixed Fingerprint Controller for CP210x USB-to-UART Bridge
Improved error handling and communication stability
"""

import time
import hashlib
import json
import os
import threading
from datetime import datetime

class FingerprintController:
    """Fixed fingerprint controller with better error handling"""
    
    def __init__(self):
        self.sensor = None
        self.sensor_type = None
        self.available = False
        self.fingerprint_db = {}
        self.db_file = 'data/fingerprints.json'
        self.uart_port = None
        self.baud_rate = None
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Load existing fingerprint database
        self.load_fingerprint_db()
        
        # Initialize sensor
        self.initialize_sensor()
    
    def initialize_sensor(self):
        """Initialize fingerprint sensor with improved error handling"""
        print("🔍 Detecting CP210x USB-to-UART fingerprint sensor...")
        
        # Kill any processes using the port first
        self._kill_port_processes()
        
        # Try CP210x USB-to-UART bridge
        if self._init_cp210x_sensor():
            return
        
        print("❌ No fingerprint sensor detected")
        print("💡 Run diagnostic: python3 scripts/cp210x_diagnostic.py")
    
    def _kill_port_processes(self):
        """Kill processes that might be using serial ports"""
        try:
            import subprocess
            
            # Find processes using ttyUSB ports
            result = subprocess.run(['lsof', '-t', '/dev/ttyUSB0'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        pid = int(pid.strip())
                        print(f"🔧 Killing process {pid} using serial port...")
                        os.kill(pid, 15)  # SIGTERM
                        time.sleep(0.5)
                    except:
                        pass
                        
        except Exception as e:
            pass  # Ignore errors, this is just cleanup
    
    def _init_cp210x_sensor(self):
        """Initialize CP210x sensor with robust communication"""
        try:
            import serial
            import glob
            
            # Get available ports
            ports = glob.glob('/dev/ttyUSB*')
            
            if not ports:
                print("❌ No USB serial ports found")
                return False
            
            # Test each port
            for port in sorted(ports):
                print(f"🔌 Testing {port}...")
                
                if self._test_port_communication(port):
                    return True
            
            return False
            
        except ImportError:
            print("❌ pyserial not installed")
            return False
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False
    
    def _test_port_communication(self, port):
        """Test communication on a specific port"""
        import serial
        
        baud_rates = [57600, 9600, 19200, 38400, 115200]
        
        for baud_rate in baud_rates:
            try:
                print(f"   Testing {baud_rate} baud...")
                
                # Open with robust settings
                ser = serial.Serial(
                    port=port,
                    baudrate=baud_rate,
                    timeout=2,
                    write_timeout=2,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False
                )
                
                # Allow port to stabilize
                time.sleep(0.3)
                
                # Clear buffers
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                
                # Test with fingerprint sensor handshake
                handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
                
                # Send command
                ser.write(handshake)
                ser.flush()  # Ensure data is sent
                
                # Wait for response
                time.sleep(0.5)
                
                # Read response
                response = ser.read(20)
                
                ser.close()
                
                if len(response) >= 9 and response[0:2] == bytes([0xEF, 0x01]):
                    print(f"   ✅ Valid response: {response.hex()}")
                    
                    # Initialize as working sensor
                    self.sensor = serial.Serial(
                        port=port,
                        baudrate=baud_rate,
                        timeout=3,
                        write_timeout=3,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        xonxoff=False,
                        rtscts=False,
                        dsrdtr=False
                    )
                    
                    self.sensor_type = 'GENERIC_CP210X'
                    self.uart_port = port
                    self.baud_rate = baud_rate
                    self.available = True
                    
                    print(f"✅ Sensor initialized on {port} at {baud_rate} baud")
                    return True
                else:
                    print(f"   ❌ Invalid response: {response.hex() if response else 'no data'}")
                    
            except Exception as e:
                print(f"   ❌ Error at {baud_rate}: {e}")
                continue
        
        return False
    
    def _send_command(self, command, expected_response_length=12, timeout=3):
        """Send command to sensor with error handling"""
        if not self.available:
            return None
        
        try:
            # Clear buffers
            self.sensor.reset_input_buffer()
            self.sensor.reset_output_buffer()
            
            # Send command
            self.sensor.write(command)
            self.sensor.flush()
            
            # Wait for response
            time.sleep(0.2)
            
            # Read response
            response = self.sensor.read(expected_response_length)
            
            return response
            
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return None
    
    def load_fingerprint_db(self):
        """Load fingerprint database from file"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    self.fingerprint_db = json.load(f)
                print(f"📂 Loaded {len(self.fingerprint_db)} fingerprint records")
            else:
                self.fingerprint_db = {}
                print("📂 Created new fingerprint database")
        except Exception as e:
            print(f"❌ Error loading fingerprint database: {e}")
            self.fingerprint_db = {}
    
    def save_fingerprint_db(self):
        """Save fingerprint database to file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.fingerprint_db, f, indent=2)
            print("💾 Fingerprint database saved")
        except Exception as e:
            print(f"❌ Error saving fingerprint database: {e}")
    
    def enroll_fingerprint(self, username, callback=None):
        """Enroll a new fingerprint with improved protocol"""
        if not self.available:
            return {'success': False, 'message': 'Fingerprint sensor not available'}
        
        print(f"👆 Starting fingerprint enrollment for {username}")
        
        try:
            return self._enroll_generic_uart_improved(username, callback)
        except Exception as e:
            print(f"❌ Enrollment error: {e}")
            return {'success': False, 'message': f'Enrollment failed: {str(e)}'}
    
    def _enroll_generic_uart_improved(self, username, callback=None):
        """Improved UART enrollment with better error handling"""
        try:
            if callback:
                callback("Place finger on sensor", 1, 4)
            
            print("👆 Place finger on sensor...")
            
            # Step 1: Get first image
            get_image_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            
            # Try multiple times to get image
            for attempt in range(15):
                print(f"   Attempt {attempt + 1}/15...")
                
                response = self._send_command(get_image_cmd)
                
                if response and len(response) >= 9:
                    if response[8] == 0x00:  # Success
                        print("✅ First image captured")
                        break
                    elif response[8] == 0x02:  # No finger
                        print("   Waiting for finger...")
                    else:
                        print(f"   Error code: 0x{response[8]:02X}")
                
                time.sleep(0.5)
            else:
                return {'success': False, 'message': 'Failed to capture first image - place finger firmly on sensor'}
            
            # Step 2: Convert to template 1
            img2tz_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x01, 0x00, 0x08])
            response = self._send_command(img2tz_cmd)
            
            if not (response and len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to process first image'}
            
            if callback:
                callback("Remove finger, then place again", 2, 4)
            
            print("🖐️ Remove finger and place same finger again...")
            time.sleep(2)
            
            # Step 3: Get second image
            for attempt in range(15):
                print(f"   Attempt {attempt + 1}/15...")
                
                response = self._send_command(get_image_cmd)
                
                if response and len(response) >= 9:
                    if response[8] == 0x00:  # Success
                        print("✅ Second image captured")
                        break
                    elif response[8] == 0x02:  # No finger
                        print("   Waiting for finger...")
                    else:
                        print(f"   Error code: 0x{response[8]:02X}")
                
                time.sleep(0.5)
            else:
                return {'success': False, 'message': 'Failed to capture second image - place same finger firmly on sensor'}
            
            # Step 4: Convert to template 2
            img2tz_cmd2 = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x02, 0x00, 0x09])
            response = self._send_command(img2tz_cmd2)
            
            if not (response and len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to process second image'}
            
            if callback:
                callback("Creating template...", 3, 4)
            
            # Step 5: Create model
            create_model_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x05, 0x00, 0x09])
            response = self._send_command(create_model_cmd)
            
            if not (response and len(response) >= 9 and response[8] == 0x00):
                error_msg = "Failed to create fingerprint model"
                if response and len(response) >= 9:
                    if response[8] == 0x0A:
                        error_msg += " - fingerprints don't match, try again"
                    else:
                        error_msg += f" - error code: 0x{response[8]:02X}"
                return {'success': False, 'message': error_msg}
            
            # Step 6: Store model
            slot_id = self._find_next_slot()
            if slot_id is None:
                return {'success': False, 'message': 'No available slots in sensor memory'}
            
            if callback:
                callback("Storing template...", 4, 4)
            
            # Calculate checksum for store command
            store_data = [0x06, 0x01, (slot_id >> 8) & 0xFF, slot_id & 0xFF]
            checksum = sum([0x01, 0x00, 0x06] + store_data) & 0xFFFF
            
            store_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x06] + 
                            store_data + [(checksum >> 8) & 0xFF, checksum & 0xFF])
            
            response = self._send_command(store_cmd)
            
            if not (response and len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to store fingerprint template'}
            
            # Save to database
            fingerprint_data = {
                'username': username,
                'slot_id': slot_id,
                'enrolled_date': datetime.now().isoformat(),
                'sensor_type': self.sensor_type,
                'uart_port': self.uart_port,
                'baud_rate': self.baud_rate
            }
            
            self.fingerprint_db[username] = fingerprint_data
            self.save_fingerprint_db()
            
            print(f"✅ Fingerprint enrolled successfully for {username} in slot {slot_id}")
            
            return {
                'success': True,
                'message': 'Fingerprint enrolled successfully',
                'slot_id': slot_id
            }
            
        except Exception as e:
            print(f"❌ Enrollment error: {e}")
            return {'success': False, 'message': f'Enrollment failed: {str(e)}'}
    
    def authenticate_fingerprint(self, timeout=15):
        """Authenticate fingerprint with improved protocol"""
        if not self.available:
            return {'success': False, 'message': 'Fingerprint sensor not available'}
        
        print("🔍 Starting fingerprint authentication...")
        
        try:
            return self._authenticate_generic_uart_improved(timeout)
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return {'success': False, 'message': f'Authentication failed: {str(e)}'}
    
    def _authenticate_generic_uart_improved(self, timeout=15):
        """Improved UART authentication"""
        try:
            print("👆 Place finger on sensor for authentication...")
            
            # Step 1: Get image
            get_image_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            
            start_time = time.time()
            image_captured = False
            
            while not image_captured and (time.time() - start_time) < timeout:
                response = self._send_command(get_image_cmd)
                
                if response and len(response) >= 9:
                    if response[8] == 0x00:  # Success
                        image_captured = True
                        print("✅ Image captured for authentication")
                        break
                    elif response[8] == 0x02:  # No finger
                        print("   Waiting for finger...")
                    else:
                        print(f"   Error: 0x{response[8]:02X}")
                
                time.sleep(0.3)
            
            if not image_captured:
                return {'success': False, 'message': 'Timeout waiting for finger'}
            
            # Step 2: Convert to template
            img2tz_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x01, 0x00, 0x08])
            response = self._send_command(img2tz_cmd)
            
            if not (response and len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to process fingerprint image'}
            
            # Step 3: Search for match
            search_checksum = sum([0x01, 0x00, 0x08, 0x04, 0x01, 0x00, 0x00, 0x00, 0x7F]) & 0xFFFF
            search_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x08, 0x04, 0x01, 
                              0x00, 0x00, 0x00, 0x7F, (search_checksum >> 8) & 0xFF, search_checksum & 0xFF])
            
            response = self._send_command(search_cmd, expected_response_length=16)
            
            if response and len(response) >= 9:
                if response[8] == 0x00:  # Match found
                    if len(response) >= 13:
                        slot_id = (response[9] << 8) | response[10]
                        confidence = (response[11] << 8) | response[12]
                        
                        print(f"✅ Fingerprint match found! Slot: {slot_id}, Confidence: {confidence}")
                        
                        # Find username for this slot
                        username = self._find_username_by_slot(slot_id)
                        
                        if username:
                            return {
                                'success': True,
                                'username': username,
                                'slot_id': slot_id,
                                'confidence': confidence,
                                'message': 'Authentication successful'
                            }
                        else:
                            return {
                                'success': False,
                                'message': f'Fingerprint matched but no user found for slot {slot_id}'
                            }
                    else:
                        return {'success': False, 'message': 'Invalid search response'}
                elif response[8] == 0x09:  # No match
                    print("❌ No fingerprint match found")
                    return {'success': False, 'message': 'Fingerprint not recognized'}
                else:
                    print(f"❌ Search error: 0x{response[8]:02X}")
                    return {'success': False, 'message': f'Search failed with error 0x{response[8]:02X}'}
            else:
                return {'success': False, 'message': 'No response from sensor'}
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return {'success': False, 'message': f'Authentication failed: {str(e)}'}
    
    def _find_next_slot(self):
        """Find next available slot in sensor memory"""
        used_slots = set()
        
        for data in self.fingerprint_db.values():
            slot_id = data.get('slot_id')
            if slot_id is not None:
                used_slots.add(slot_id)
        
        # Find first available slot (typically 1-127 for most sensors)
        for slot in range(1, 128):
            if slot not in used_slots:
                return slot
        
        return None  # No available slots
    
    def _find_username_by_slot(self, slot_id):
        """Find username associated with a slot ID"""
        for username, data in self.fingerprint_db.items():
            if data.get('slot_id') == slot_id:
                return username
        return None
    
    def get_sensor_info(self):
        """Get sensor information"""
        if not self.available:
            return {'available': False}
        
        return {
            'available': True,
            'sensor_type': self.sensor_type,
            'uart_port': self.uart_port,
            'baud_rate': self.baud_rate,
            'enrolled_count': len(self.fingerprint_db)
        }
    
    def list_enrolled_users(self):
        """List all enrolled users"""
        return list(self.fingerprint_db.keys())
    
    def test_sensor(self):
        """Test sensor functionality"""
        if not self.available:
            return {'success': False, 'message': 'Sensor not available'}
        
        try:
            print("🧪 Testing fingerprint sensor...")
            
            # Test basic communication
            test_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            response = self._send_command(test_cmd)
            
            if response and len(response) >= 9:
                return {
                    'success': True,
                    'message': 'Sensor test passed',
                    'details': {
                        'sensor_type': self.sensor_type,
                        'uart_port': self.uart_port,
                        'baud_rate': self.baud_rate,
                        'enrolled_users': len(self.fingerprint_db),
                        'response': response.hex()
                    }
                }
            else:
                return {'success': False, 'message': 'No response from sensor'}
                
        except Exception as e:
            return {'success': False, 'message': f'Sensor test failed: {str(e)}'}

def main():
    """Test the fixed fingerprint controller"""
    print("🔐 Fixed CP210x Fingerprint Controller Test")
    print("=" * 60)
    
    # Initialize controller
    fp_controller = FingerprintController()
    
    if not fp_controller.available:
        print("❌ No fingerprint sensor available")
        print("\n💡 Try running diagnostic first:")
        print("   python3 scripts/cp210x_diagnostic.py")
        return
    
    # Show sensor info
    info = fp_controller.get_sensor_info()
    print(f"\n📱 Sensor Info: {info}")
    
    # Test sensor
    test_result = fp_controller.test_sensor()
    print(f"\n🧪 Sensor test: {test_result}")
    
    # Interactive menu
    while True:
        print("\n" + "=" * 60)
        print("📋 Fixed Fingerprint Controller Menu")
        print("1. Enroll fingerprint")
        print("2. Authenticate fingerprint") 
        print("3. Delete fingerprint")
        print("4. List enrolled users")
        print("5. Sensor info")
        print("6. Test sensor")
        print("0. Exit")
        print("=" * 60)
        
        try:
            choice = input("Enter choice (0-6): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                username = input("Enter username to enroll: ").strip()
                if username:
                    result = fp_controller.enroll_fingerprint(username)
                    print(f"📝 Enrollment result: {result}")
                    
            elif choice == '2':
                print("👆 Place finger on sensor...")
                result = fp_controller.authenticate_fingerprint()
                print(f"🔍 Authentication result: {result}")
                
            elif choice == '3':
                username = input("Enter username to delete: ").strip()
                if username:
                    if username in fp_controller.fingerprint_db:
                        del fp_controller.fingerprint_db[username]
                        fp_controller.save_fingerprint_db()
                        print(f"🗑️ Deleted {username} from database")
                    else:
                        print(f"❌ User {username} not found")
                    
            elif choice == '4':
                users = fp_controller.list_enrolled_users()
                print(f"👥 Enrolled users: {users}")
                
            elif choice == '5':
                info = fp_controller.get_sensor_info()
                print(f"ℹ️ Sensor info: {info}")
                
            elif choice == '6':
                result = fp_controller.test_sensor()
                print(f"🧪 Test result: {result}")
                
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
