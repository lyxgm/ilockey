#!/usr/bin/env python3
"""
Optimized Fingerprint Controller
Uses sensor-specific protocol and timing
"""

import time
import json
import os
import serial
from datetime import datetime

class OptimizedFingerprintController:
    """Optimized controller using sensor-specific protocol"""
    
    def __init__(self):
        self.sensor = None
        self.available = False
        self.fingerprint_db = {}
        self.db_file = 'data/fingerprints.json'
        self.protocol_file = 'data/sensor_protocol.json'
        self.protocol = None
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Load protocol and database
        self.load_protocol()
        self.load_fingerprint_db()
        
        # Initialize sensor
        self.initialize_sensor()
    
    def load_protocol(self):
        """Load sensor-specific protocol"""
        try:
            if os.path.exists(self.protocol_file):
                with open(self.protocol_file, 'r') as f:
                    data = json.load(f)
                    self.protocol = data.get('protocol')
                    print(f"📋 Loaded optimized protocol for {self.protocol['model']}")
            else:
                print("⚠️ No optimized protocol found, using defaults")
                self.protocol = self._default_protocol()
        except Exception as e:
            print(f"❌ Error loading protocol: {e}")
            self.protocol = self._default_protocol()
    
    def _default_protocol(self):
        """Default protocol settings"""
        return {
            'model': 'Generic',
            'baud_rate': 57600,
            'commands': {
                'get_image': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05],
                'img2tz_1': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x01, 0x00, 0x08],
                'img2tz_2': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x02, 0x00, 0x09],
                'create_model': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x05, 0x00, 0x09]
            },
            'timing': {
                'pre_command_delay': 0.5,
                'post_command_delay': 1.0,
                'image_capture_timeout': 10,
                'retry_delay': 1.0
            },
            'special_handling': ['EXTENDED_TIMEOUTS', 'MULTIPLE_RETRIES', 'BUFFER_CLEARING']
        }
    
    def initialize_sensor(self):
        """Initialize sensor with optimized settings"""
        print("🔍 Initializing optimized fingerprint sensor...")
        
        try:
            self.sensor = serial.Serial(
                port='/dev/ttyUSB0',
                baudrate=self.protocol['baud_rate'],
                timeout=3,
                write_timeout=3,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Extended initialization delay
            time.sleep(0.5)
            
            # Test communication
            if self._test_communication():
                self.available = True
                print(f"✅ Sensor initialized with {self.protocol['model']} protocol")
            else:
                print("❌ Sensor communication test failed")
                
        except Exception as e:
            print(f"❌ Sensor initialization failed: {e}")
    
    def _test_communication(self):
        """Test sensor communication"""
        try:
            handshake = bytes(self.protocol['commands']['get_image'])
            response = self._send_command_optimized(handshake)
            
            return response is not None and len(response) >= 9
            
        except Exception as e:
            print(f"❌ Communication test failed: {e}")
            return False
    
    def _send_command_optimized(self, command, expected_length=12):
        """Send command with optimized timing"""
        if not self.sensor:
            return None
        
        try:
            timing = self.protocol['timing']
            
            # Pre-command delay
            time.sleep(timing['pre_command_delay'])
            
            # Clear buffers if specified
            if 'BUFFER_CLEARING' in self.protocol['special_handling']:
                self.sensor.reset_input_buffer()
                self.sensor.reset_output_buffer()
                time.sleep(0.1)
            
            # Send command
            self.sensor.write(command)
            self.sensor.flush()
            
            # Post-command delay
            time.sleep(timing['post_command_delay'])
            
            # Read response
            response = self.sensor.read(expected_length)
            
            return response
            
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return None
    
    def load_fingerprint_db(self):
        """Load fingerprint database"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    self.fingerprint_db = json.load(f)
                print(f"📂 Loaded {len(self.fingerprint_db)} fingerprint records")
            else:
                self.fingerprint_db = {}
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            self.fingerprint_db = {}
    
    def save_fingerprint_db(self):
        """Save fingerprint database"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.fingerprint_db, f, indent=2)
            print("💾 Database saved")
        except Exception as e:
            print(f"❌ Error saving database: {e}")
    
    def enroll_fingerprint_optimized(self, username, callback=None):
        """Optimized fingerprint enrollment"""
        if not self.available:
            return {'success': False, 'message': 'Sensor not available'}
        
        print(f"👆 Starting optimized enrollment for {username}")
        print(f"🛠️ Using {self.protocol['model']} protocol with extended timeouts")
        
        try:
            timing = self.protocol['timing']
            commands = self.protocol['commands']
            
            # Step 1: Capture first image with extended timeout
            if callback:
                callback("Place finger firmly on sensor", 1, 4)
            
            print("👆 Place finger FIRMLY on sensor and hold still...")
            print("   (Using extended timeout for better capture)")
            
            success = False
            max_attempts = 20 if 'MULTIPLE_RETRIES' in self.protocol['special_handling'] else 10
            
            for attempt in range(max_attempts):
                print(f"   Attempt {attempt + 1}/{max_attempts}...")
                
                # Send get image command
                get_image_cmd = bytes(commands['get_image'])
                response = self._send_command_optimized(get_image_cmd)
                
                if response and len(response) >= 9:
                    error_code = response[8]
                    
                    if error_code == 0x00:  # Success
                        print("✅ First image captured successfully!")
                        success = True
                        break
                    elif error_code == 0x02:  # No finger
                        print("   No finger detected - press more firmly")
                    elif error_code == 0x03:  # Imaging fail
                        print("   Imaging failed - adjust finger position")
                        # Extra delay for imaging fail
                        time.sleep(timing['retry_delay'])
                    else:
                        print(f"   Error code: 0x{error_code:02X}")
                
                # Longer delay between attempts
                time.sleep(timing['retry_delay'])
            
            if not success:
                return {
                    'success': False, 
                    'message': 'Failed to capture first image. Try:\n• Press finger more firmly\n• Clean sensor surface\n• Check sensor power supply'
                }
            
            # Step 2: Convert to template 1
            print("🔄 Converting first image to template...")
            img2tz_cmd = bytes(commands['img2tz_1'])
            response = self._send_command_optimized(img2tz_cmd)
            
            if not (response and len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to process first image'}
            
            # Step 3: Get second image
            if callback:
                callback("Remove finger, then place same finger again", 2, 4)
            
            print("🖐️ Remove finger completely...")
            time.sleep(2)
            print("👆 Place SAME finger again, firmly...")
            
            success = False
            for attempt in range(max_attempts):
                print(f"   Attempt {attempt + 1}/{max_attempts}...")
                
                response = self._send_command_optimized(get_image_cmd)
                
                if response and len(response) >= 9:
                    error_code = response[8]
                    
                    if error_code == 0x00:  # Success
                        print("✅ Second image captured successfully!")
                        success = True
                        break
                    elif error_code == 0x02:  # No finger
                        print("   No finger detected - press more firmly")
                    elif error_code == 0x03:  # Imaging fail
                        print("   Imaging failed - adjust finger position")
                        time.sleep(timing['retry_delay'])
                    else:
                        print(f"   Error code: 0x{error_code:02X}")
                
                time.sleep(timing['retry_delay'])
            
            if not success:
                return {'success': False, 'message': 'Failed to capture second image'}
            
            # Step 4: Convert to template 2
            print("🔄 Converting second image to template...")
            img2tz_cmd2 = bytes(commands['img2tz_2'])
            response = self._send_command_optimized(img2tz_cmd2)
            
            if not (response and len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to process second image'}
            
            # Step 5: Create model
            if callback:
                callback("Creating fingerprint model...", 3, 4)
            
            print("🔧 Creating fingerprint model...")
            create_cmd = bytes(commands['create_model'])
            response = self._send_command_optimized(create_cmd)
            
            if not (response and len(response) >= 9 and response[8] == 0x00):
                error_msg = "Failed to create fingerprint model"
                if response and len(response) >= 9:
                    if response[8] == 0x0A:
                        error_msg += " - fingerprints don't match, try again"
                return {'success': False, 'message': error_msg}
            
            # Step 6: Store model (simplified for now)
            if callback:
                callback("Enrollment complete!", 4, 4)
            
            # Save to database
            slot_id = len(self.fingerprint_db) + 1
            fingerprint_data = {
                'username': username,
                'slot_id': slot_id,
                'enrolled_date': datetime.now().isoformat(),
                'protocol': self.protocol['model']
            }
            
            self.fingerprint_db[username] = fingerprint_data
            self.save_fingerprint_db()
            
            print(f"✅ Fingerprint enrolled successfully for {username}!")
            
            return {
                'success': True,
                'message': 'Fingerprint enrolled successfully',
                'slot_id': slot_id
            }
            
        except Exception as e:
            print(f"❌ Enrollment error: {e}")
            return {'success': False, 'message': f'Enrollment failed: {str(e)}'}

def main():
    """Test optimized controller"""
    print("🔐 Optimized Fingerprint Controller")
    print("=" * 50)
    
    # Check if protocol exists
    if not os.path.exists('data/sensor_protocol.json'):
        print("⚠️ No optimized protocol found!")
        print("💡 Run sensor identification first:")
        print("   python3 scripts/sensor_identifier.py")
        return
    
    controller = OptimizedFingerprintController()
    
    if not controller.available:
        print("❌ Sensor not available")
        return
    
    # Interactive menu
    while True:
        print("\n" + "=" * 50)
        print("📋 Optimized Fingerprint Controller")
        print(f"🛠️ Protocol: {controller.protocol['model']}")
        print("1. Enroll fingerprint (optimized)")
        print("2. List enrolled users")
        print("3. Delete fingerprint")
        print("4. Show protocol info")
        print("0. Exit")
        print("=" * 50)
        
        try:
            choice = input("Enter choice (0-4): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                username = input("Enter username to enroll: ").strip()
                if username:
                    result = controller.enroll_fingerprint_optimized(username)
                    print(f"📝 Result: {result}")
                    
            elif choice == '2':
                users = list(controller.fingerprint_db.keys())
                print(f"👥 Enrolled users: {users}")
                
            elif choice == '3':
                username = input("Enter username to delete: ").strip()
                if username in controller.fingerprint_db:
                    del controller.fingerprint_db[username]
                    controller.save_fingerprint_db()
                    print(f"🗑️ Deleted {username}")
                else:
                    print(f"❌ User {username} not found")
                    
            elif choice == '4':
                print(f"🛠️ Protocol Info:")
                print(f"   Model: {controller.protocol['model']}")
                print(f"   Timing: {controller.protocol['timing']}")
                print(f"   Special: {controller.protocol['special_handling']}")
                
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break

if __name__ == "__main__":
    main()
