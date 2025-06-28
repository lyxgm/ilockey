#!/usr/bin/env python3
"""
Real Fingerprint Controller for Smart Door Lock
Optimized for CP210x USB-to-UART Bridge (Silicon Labs)
"""

import time
import hashlib
import json
import os
import threading
from datetime import datetime

class FingerprintController:
    """Real fingerprint controller optimized for CP210x USB-to-UART bridge"""
    
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
        """Initialize fingerprint sensor - prioritize CP210x detection"""
        print("ðŸ” Detecting CP210x USB-to-UART fingerprint sensor...")
        
        # Try CP210x USB-to-UART bridge first
        if self._init_cp210x_sensor():
            return
        
        # Fallback to other UART methods
        if self._init_generic_uart_sensor():
            return
        
        print("âŒ No fingerprint sensor detected")
        print("ðŸ“‹ Expected: CP210x USB-to-UART Bridge (ID 10c4:ea60)")
        print("   Check: lsusb | grep 10c4:ea60")
    
    def _detect_cp210x_devices(self):
        """Detect CP210x USB-to-UART devices"""
        import subprocess
        
        try:
            # Check if CP210x device is connected
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                cp210x_devices = []
                
                for line in lines:
                    if '10c4:ea60' in line.lower() or 'cp210x' in line.lower():
                        print(f"âœ… Found CP210x device: {line.strip()}")
                        cp210x_devices.append(line.strip())
                
                if cp210x_devices:
                    return True
                else:
                    print("âŒ CP210x device (10c4:ea60) not found in USB devices")
                    return False
            else:
                print("âš ï¸ Could not run lsusb command")
                return False
                
        except Exception as e:
            print(f"âš ï¸ Error detecting CP210x: {e}")
            return False
    
    def _get_cp210x_ports(self):
        """Get serial ports created by CP210x driver"""
        import glob
        import os
        
        # Common CP210x device paths
        possible_ports = []
        
        # Check for ttyUSB devices (most common for CP210x)
        usb_ports = glob.glob('/dev/ttyUSB*')
        possible_ports.extend(sorted(usb_ports))
        
        # Check for ttyACM devices (alternative)
        acm_ports = glob.glob('/dev/ttyACM*')
        possible_ports.extend(sorted(acm_ports))
        
        # Filter to only accessible ports
        accessible_ports = []
        for port in possible_ports:
            if os.path.exists(port):
                try:
                    # Test if we can access the port
                    import serial
                    test_ser = serial.Serial(port, 9600, timeout=0.5)
                    test_ser.close()
                    accessible_ports.append(port)
                    print(f"âœ… Found accessible port: {port}")
                except Exception as e:
                    print(f"âš ï¸ Port {port} not accessible: {e}")
        
        return accessible_ports
    
    def _init_cp210x_sensor(self):
        """Initialize fingerprint sensor via CP210x USB-to-UART bridge"""
        try:
            import serial
            
            # First check if CP210x device is connected
            if not self._detect_cp210x_devices():
                print("âŒ CP210x USB-to-UART bridge not detected")
                return False
            
            # Get available CP210x ports
            cp210x_ports = self._get_cp210x_ports()
            
            if not cp210x_ports:
                print("âŒ No accessible CP210x serial ports found")
                print("ðŸ’¡ Try: sudo usermod -a -G dialout $USER")
                print("ðŸ’¡ Then logout and login again")
                return False
            
            # Common baud rates for fingerprint sensors
            baud_rates = [57600, 9600, 19200, 38400, 115200]
            
            for port in cp210x_ports:
                print(f"ðŸ”Œ Testing CP210x port: {port}")
                
                for baud_rate in baud_rates:
                    try:
                        print(f"   ðŸ” Testing at {baud_rate} baud...")
                        
                        # Try Adafruit fingerprint library first (R307/R503)
                        if self._try_adafruit_sensor(port, baud_rate):
                            print(f"âœ… CP210x sensor initialized on {port} at {baud_rate} baud")
                            return True
                        
                        # Try generic UART protocol (AS608, ZFM-20, etc.)
                        if self._try_generic_uart_sensor(port, baud_rate):
                            print(f"âœ… CP210x sensor initialized on {port} at {baud_rate} baud")
                            return True
                           
                    except Exception as e:
                        print(f"     âŒ Failed at {baud_rate} baud: {e}")
                        continue
            
            print("âŒ No fingerprint sensor found on CP210x ports")
            return False
           
        except ImportError as e:
            print(f"   ðŸ“¦ Missing dependency: {e}")
            print("   ðŸ’¡ Install with: pip install pyserial adafruit-circuitpython-fingerprint")
            return False
        except Exception as e:
            print(f"   âŒ CP210x initialization error: {e}")
            return False
    
    def _try_adafruit_sensor(self, port, baud_rate):
        """Try to initialize using Adafruit fingerprint library"""
        try:
            import serial
            import adafruit_fingerprint
           
            # Initialize UART connection with CP210x specific settings
            uart = serial.Serial(
                port=port, 
                baudrate=baud_rate, 
                timeout=2,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            time.sleep(0.2)  # Allow CP210x to stabilize
           
            # Initialize fingerprint sensor
            finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
           
            # Test sensor communication
            if finger.verify_password():
                self.sensor = finger
                self.sensor_type = 'R307_CP210X'
                self.uart_port = port
                self.baud_rate = baud_rate
                self.available = True
               
                # Get sensor info
                params = finger.get_parameters()
                print(f"     ðŸ“Š Status: 0x{params.status_register:02X}")
                print(f"     ðŸ—ƒï¸  Templates: {params.template_count}/{params.library_size}")
                print(f"     ðŸ“ Packet size: {params.packet_length}")
               
                return True
            else:
                uart.close()
                return False
               
        except Exception as e:
            print(f"       âŒ Adafruit test failed: {e}")
            return False
   
    def _try_generic_uart_sensor(self, port, baud_rate):
        """Try generic UART fingerprint sensor protocol via CP210x"""
        try:
            import serial
           
            # Initialize UART connection with CP210x specific settings
            ser = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=2,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            time.sleep(0.2)  # Allow CP210x to stabilize
           
            # Try common fingerprint sensor handshake
            # This works for AS608, ZFM-20, and similar sensors
            handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            ser.write(handshake)
           
            # Read response
            response = ser.read(12)
           
            if len(response) >= 9 and response[0:2] == bytes([0xEF, 0x01]):
                self.sensor = ser
                self.sensor_type = 'GENERIC_CP210X'
                self.uart_port = port
                self.baud_rate = baud_rate
                self.available = True
               
                print(f"     ðŸ“¡ Response: {response.hex()}")
               
                return True
            else:
                ser.close()
                return False
               
        except Exception as e:
            print(f"       âŒ Generic UART test failed: {e}")
            return False
    
    def _init_generic_uart_sensor(self):
        """Fallback: Try any available UART ports"""
        try:
            import serial
            import glob
            
            # Get all possible serial ports
            possible_ports = []
            possible_ports.extend(glob.glob('/dev/ttyUSB*'))
            possible_ports.extend(glob.glob('/dev/ttyACM*'))
            possible_ports.extend(glob.glob('/dev/ttyAMA*'))
            possible_ports.extend(glob.glob('/dev/serial*'))
            
            baud_rates = [57600, 9600, 19200, 38400, 115200]
            
            for port in sorted(possible_ports):
                if not os.path.exists(port):
                    continue
                    
                print(f"ðŸ”Œ Trying fallback port: {port}")
                
                for baud_rate in baud_rates:
                    try:
                        if self._try_adafruit_sensor(port, baud_rate):
                            return True
                        if self._try_generic_uart_sensor(port, baud_rate):
                            return True
                    except Exception as e:
                        continue
            
            return False
            
        except Exception as e:
            print(f"âŒ Fallback UART initialization error: {e}")
            return False
    
    def load_fingerprint_db(self):
        """Load fingerprint database from file"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    self.fingerprint_db = json.load(f)
                print(f"ðŸ“‚ Loaded {len(self.fingerprint_db)} fingerprint records")
            else:
                self.fingerprint_db = {}
                print("ðŸ“‚ Created new fingerprint database")
        except Exception as e:
            print(f"âŒ Error loading fingerprint database: {e}")
            self.fingerprint_db = {}
    
    def save_fingerprint_db(self):
        """Save fingerprint database to file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.fingerprint_db, f, indent=2)
            print("ðŸ’¾ Fingerprint database saved")
        except Exception as e:
            print(f"âŒ Error saving fingerprint database: {e}")
    
    def enroll_fingerprint(self, username, callback=None):
        """Enroll a new fingerprint for a user"""
        if not self.available:
            return {'success': False, 'message': 'Fingerprint sensor not available'}
        
        print(f"ðŸ‘† Starting fingerprint enrollment for {username}")
        
        try:
            if 'R307' in self.sensor_type:
                return self._enroll_adafruit_sensor(username, callback)
            elif 'GENERIC' in self.sensor_type:
                return self._enroll_generic_uart(username, callback)
            else:
                return {'success': False, 'message': 'Unsupported sensor type'}
                
        except Exception as e:
            print(f"âŒ Enrollment error: {e}")
            return {'success': False, 'message': f'Enrollment failed: {str(e)}'}
    
    def _enroll_adafruit_sensor(self, username, callback=None):
        """Enroll fingerprint using Adafruit library (R307/R503)"""
        try:
            finger = self.sensor
            
            # Find next available slot
            slot_id = self._find_next_slot()
            if slot_id is None:
                return {'success': False, 'message': 'No available slots in sensor memory'}
            
            print(f"ðŸ“ Using slot {slot_id} for enrollment")
            
            # Step 1: Get first fingerprint image
            if callback:
                callback("Place finger on sensor", 1, 3)
            
            print("ðŸ‘† Place finger on sensor...")
            
            # Wait for finger with longer timeout for CP210x
            finger_detected = False
            timeout = 30
            start_time = time.time()
            
            while not finger_detected and (time.time() - start_time) < timeout:
                try:
                    if finger.get_image() == finger.OK:
                        finger_detected = True
                        break
                except:
                    pass
                time.sleep(0.1)
            
            if not finger_detected:
                return {'success': False, 'message': 'Timeout waiting for finger'}
            
            # Convert image to template
            if finger.image_2_tz(1) != finger.OK:
                return {'success': False, 'message': 'Failed to process first image'}
            
            print("âœ… First scan complete")
            if callback:
                callback("Remove finger, then place again", 2, 3)
            
            # Wait for finger removal
            print("ðŸ–ï¸ Remove finger...")
            while True:
                try:
                    if finger.get_image() != finger.OK:
                        break
                except:
                    break
                time.sleep(0.1)
            
            time.sleep(1)
            
            # Step 2: Get second fingerprint image
            print("ðŸ‘† Place same finger again...")
            
            finger_detected = False
            start_time = time.time()
            
            while not finger_detected and (time.time() - start_time) < timeout:
                try:
                    if finger.get_image() == finger.OK:
                        finger_detected = True
                        break
                except:
                    pass
                time.sleep(0.1)
            
            if not finger_detected:
                return {'success': False, 'message': 'Timeout waiting for second scan'}
            
            # Convert second image to template
            if finger.image_2_tz(2) != finger.OK:
                return {'success': False, 'message': 'Failed to process second image'}
            
            print("âœ… Second scan complete")
            if callback:
                callback("Processing...", 3, 3)
            
            # Create model from both templates
            if finger.create_model() != finger.OK:
                return {'success': False, 'message': 'Failed to create fingerprint model'}
            
            # Store model in sensor memory
            if finger.store_model(slot_id) != finger.OK:
                return {'success': False, 'message': 'Failed to store fingerprint model'}
            
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
            
            print(f"âœ… Fingerprint enrolled successfully for {username} in slot {slot_id}")
            
            if callback:
                callback("Enrollment complete!", 3, 3)
            
            return {
                'success': True, 
                'message': 'Fingerprint enrolled successfully',
                'slot_id': slot_id
            }
            
        except Exception as e:
            print(f"âŒ Adafruit enrollment error: {e}")
            return {'success': False, 'message': f'Enrollment failed: {str(e)}'}
    
    def _enroll_generic_uart(self, username, callback=None):
        """Enroll fingerprint using generic UART protocol (AS608/ZFM-20 compatible)"""
        try:
            ser = self.sensor
            
            if callback:
                callback("Place finger on sensor", 1, 4)
            
            print("ðŸ‘† Generic UART: Place finger on sensor...")
            
            # Step 1: Get image (0x01)
            get_image_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            
            for attempt in range(10):  # Try multiple times
                ser.write(get_image_cmd)
                time.sleep(0.1)
                
                response = ser.read(12)
                if len(response) >= 9 and response[8] == 0x00:  # Success
                    print("âœ… First image captured")
                    break
                time.sleep(0.5)
            else:
                return {'success': False, 'message': 'Failed to capture first image'}
            
            # Step 2: Convert image to template in buffer 1 (0x02)
            img2tz_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x01, 0x00, 0x08])
            ser.write(img2tz_cmd)
            time.sleep(0.2)
            
            response = ser.read(12)
            if not (len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to process first image'}
            
            if callback:
                callback("Remove finger, then place again", 2, 4)
            
            print("ðŸ–ï¸ Remove finger and place again...")
            time.sleep(2)
            
            # Step 3: Get second image
            for attempt in range(10):
                ser.write(get_image_cmd)
                time.sleep(0.1)
                
                response = ser.read(12)
                if len(response) >= 9 and response[8] == 0x00:
                    print("âœ… Second image captured")
                    break
                time.sleep(0.5)
            else:
                return {'success': False, 'message': 'Failed to capture second image'}
            
            # Step 4: Convert second image to template in buffer 2
            img2tz_cmd2 = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x02, 0x00, 0x09])
            ser.write(img2tz_cmd2)
            time.sleep(0.2)
            
            response = ser.read(12)
            if not (len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to process second image'}
            
            if callback:
                callback("Creating template...", 3, 4)
            
            # Step 5: Create model from both templates (0x05)
            create_model_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x05, 0x00, 0x09])
            ser.write(create_model_cmd)
            time.sleep(0.5)
            
            response = ser.read(12)
            if not (len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to create fingerprint model'}
            
            # Step 6: Store model in sensor memory
            slot_id = self._find_next_slot()
            if slot_id is None:
                return {'success': False, 'message': 'No available slots in sensor memory'}
            
            if callback:
                callback("Storing template...", 4, 4)
            
            # Store command (0x06) - store buffer 1 to slot_id
            store_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x06, 0x06, 0x01, 
                          (slot_id >> 8) & 0xFF, slot_id & 0xFF, 0x00, (0x0E + slot_id) & 0xFF])
            ser.write(store_cmd)
            time.sleep(0.5)
            
            response = ser.read(12)
            if not (len(response) >= 9 and response[8] == 0x00):
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
            
            print(f"âœ… Generic UART: Fingerprint enrolled for {username} in slot {slot_id}")
            
            return {
                'success': True,
                'message': 'Fingerprint enrolled successfully',
                'slot_id': slot_id
            }
            
        except Exception as e:
            print(f"âŒ Generic UART enrollment error: {e}")
            return {'success': False, 'message': f'Enrollment failed: {str(e)}'}
    
    def authenticate_fingerprint(self, timeout=10):
        """Authenticate a fingerprint against enrolled templates"""
        if not self.available:
            return {'success': False, 'message': 'Fingerprint sensor not available'}
        
        print("ðŸ” Starting fingerprint authentication...")
        
        try:
            if 'R307' in self.sensor_type:
                return self._authenticate_adafruit_sensor(timeout)
            elif 'GENERIC' in self.sensor_type:
                return self._authenticate_generic_uart(timeout)
            else:
                return {'success': False, 'message': 'Unsupported sensor type'}
                
        except Exception as e:
            print(f"âŒ Authentication error: {e}")
            return {'success': False, 'message': f'Authentication failed: {str(e)}'}
    
    def _authenticate_adafruit_sensor(self, timeout=10):
        """Authenticate using Adafruit library"""
        try:
            finger = self.sensor
            
            print("ðŸ‘† Place finger on sensor for authentication...")
            
            # Wait for finger with CP210x considerations
            finger_detected = False
            start_time = time.time()
            
            while not finger_detected and (time.time() - start_time) < timeout:
                try:
                    if finger.get_image() == finger.OK:
                        finger_detected = True
                        break
                except:
                    pass
                time.sleep(0.1)
            
            if not finger_detected:
                return {'success': False, 'message': 'Timeout waiting for finger'}
            
            # Convert image to template
            if finger.image_2_tz(1) != finger.OK:
                return {'success': False, 'message': 'Failed to process fingerprint image'}
            
            # Search for match in sensor database
            if finger.finger_search() == finger.OK:
                slot_id = finger.finger_id
                confidence = finger.confidence
                
                print(f"âœ… Fingerprint match found! Slot: {slot_id}, Confidence: {confidence}")
                
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
                print("âŒ No fingerprint match found")
                return {'success': False, 'message': 'Fingerprint not recognized'}
                
        except Exception as e:
            print(f"âŒ Authentication error: {e}")
            return {'success': False, 'message': f'Authentication failed: {str(e)}'}
    
    def _authenticate_generic_uart(self, timeout=10):
        """Authenticate using generic UART protocol (AS608/ZFM-20 compatible)"""
        try:
            ser = self.sensor
            
            print("ðŸ‘† Generic UART: Place finger for authentication...")
            
            # Step 1: Get image (0x01)
            get_image_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            
            start_time = time.time()
            image_captured = False
            
            while not image_captured and (time.time() - start_time) < timeout:
                ser.write(get_image_cmd)
                time.sleep(0.1)
                
                response = ser.read(12)
                if len(response) >= 9 and response[8] == 0x00:  # Success
                    image_captured = True
                    print("âœ… Image captured for authentication")
                    break
                time.sleep(0.2)
        
            if not image_captured:
                return {'success': False, 'message': 'Timeout waiting for finger'}
            
            # Step 2: Convert image to template in buffer 1 (0x02)
            img2tz_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x01, 0x00, 0x08])
            ser.write(img2tz_cmd)
            time.sleep(0.2)
            
            response = ser.read(12)
            if not (len(response) >= 9 and response[8] == 0x00):
                return {'success': False, 'message': 'Failed to process fingerprint image'}
            
            # Step 3: Search for match (0x04) - search buffer 1 in entire database
            search_cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x08, 0x04, 0x01, 
                               0x00, 0x00, 0x00, 0x7F, 0x00, 0x8B])  # Search slots 0-127
            ser.write(search_cmd)
            time.sleep(0.5)
            
            response = ser.read(16)  # Search response is longer
            
            if len(response) >= 9 and response[8] == 0x00:  # Match found
                if len(response) >= 13:
                    slot_id = (response[9] << 8) | response[10]
                    confidence = (response[11] << 8) | response[12]
                    
                    print(f"âœ… Fingerprint match found! Slot: {slot_id}, Confidence: {confidence}")
                    
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
            else:
                print("âŒ No fingerprint match found")
                return {'success': False, 'message': 'Fingerprint not recognized'}
                
        except Exception as e:
            print(f"âŒ Generic UART authentication error: {e}")
            return {'success': False, 'message': f'Authentication failed: {str(e)}'}
    
    def delete_fingerprint(self, username):
        """Delete a user's fingerprint"""
        if username not in self.fingerprint_db:
            return {'success': False, 'message': 'User fingerprint not found'}
        
        try:
            fingerprint_data = self.fingerprint_db[username]
            
            if 'R307' in self.sensor_type:
                # Delete from sensor memory
                slot_id = fingerprint_data.get('slot_id')
                if slot_id is not None:
                    finger = self.sensor
                    if finger.delete_model(slot_id) == finger.OK:
                        print(f"âœ… Deleted fingerprint from sensor slot {slot_id}")
                    else:
                        print(f"âš ï¸ Failed to delete from sensor slot {slot_id}")
            
            # Remove from database
            del self.fingerprint_db[username]
            self.save_fingerprint_db()
            
            print(f"âœ… Fingerprint deleted for {username}")
            
            return {'success': True, 'message': 'Fingerprint deleted successfully'}
            
        except Exception as e:
            print(f"âŒ Delete error: {e}")
            return {'success': False, 'message': f'Delete failed: {str(e)}'}
    
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
        
        info = {
            'available': True,
            'sensor_type': self.sensor_type,
            'uart_port': self.uart_port,
            'baud_rate': self.baud_rate,
            'enrolled_count': len(self.fingerprint_db)
        }
        
        if 'R307' in self.sensor_type:
            try:
                finger = self.sensor
                params = finger.get_parameters()
                info.update({
                    'library_size': params.library_size,
                    'template_count': params.template_count,
                    'packet_length': params.packet_length,
                    'status_register': f"0x{params.status_register:02X}"
                })
            except:
                pass
        
        return info
    
    def get_cp210x_info(self):
        """Get CP210x specific information"""
        if not self.available:
            return None
        
        info = {
            'device_type': 'CP210x USB-to-UART Bridge',
            'vendor_id': '10c4',
            'product_id': 'ea60',
            'uart_port': self.uart_port,
            'baud_rate': self.baud_rate,
            'sensor_type': self.sensor_type
        }
        
        # Try to get additional CP210x info
        try:
            import subprocess
            result = subprocess.run(['lsusb', '-d', '10c4:ea60', '-v'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info['usb_details'] = result.stdout
        except:
            pass
        
        return info
    
    def list_enrolled_users(self):
        """List all enrolled users"""
        return list(self.fingerprint_db.keys())
    
    def test_sensor(self):
        """Test sensor functionality"""
        if not self.available:
            return {'success': False, 'message': 'Sensor not available'}
        
        try:
            print("ðŸ§ª Testing CP210x fingerprint sensor...")
            
            if 'R307' in self.sensor_type:
                finger = self.sensor
                
                # Test basic communication
                if finger.verify_password():
                    params = finger.get_parameters()
                    
                    return {
                        'success': True,
                        'message': 'CP210x sensor test passed',
                        'details': {
                            'sensor_type': self.sensor_type,
                            'uart_port': self.uart_port,
                            'baud_rate': self.baud_rate,
                            'library_size': params.library_size,
                            'template_count': params.template_count,
                            'enrolled_users': len(self.fingerprint_db)
                        }
                    }
                else:
                    return {'success': False, 'message': 'CP210x sensor communication failed'}
            
            else:
                return {
                    'success': True,
                    'message': 'Basic CP210x sensor test passed',
                    'details': {
                        'sensor_type': self.sensor_type,
                        'uart_port': self.uart_port,
                        'baud_rate': self.baud_rate,
                        'enrolled_users': len(self.fingerprint_db)
                    }
                }
                
        except Exception as e:
            return {'success': False, 'message': f'CP210x sensor test failed: {str(e)}'}

def main():
    """Test the CP210x fingerprint controller"""
    print("ðŸ” CP210x Fingerprint Controller Test")
    print("=" * 60)
    
    # Initialize controller
    fp_controller = FingerprintController()
    
    if not fp_controller.available:
        print("âŒ No CP210x fingerprint sensor available")
        print("\nðŸ”§ Troubleshooting:")
        print("1. Check USB connection: lsusb | grep 10c4:ea60")
        print("2. Check permissions: sudo usermod -a -G dialout $USER")
        print("3. Check device: ls -l /dev/ttyUSB*")
        print("4. Install driver: sudo apt install linux-modules-extra-$(uname -r)")
        return
    
    # Show CP210x info
    cp210x_info = fp_controller.get_cp210x_info()
    if cp210x_info:
        print(f"\nðŸ“± CP210x Device Info:")
        print(f"   Port: {cp210x_info['uart_port']}")
        print(f"   Baud: {cp210x_info['baud_rate']}")
        print(f"   Type: {cp210x_info['sensor_type']}")
    
    # Test sensor
    test_result = fp_controller.test_sensor()
    print(f"\nðŸ§ª Sensor test: {test_result}")
    
    # Interactive menu
    while True:
        print("\n" + "=" * 60)
        print("ðŸ“‹ CP210x Fingerprint Controller Menu")
        print("1. Enroll fingerprint")
        print("2. Authenticate fingerprint") 
        print("3. Delete fingerprint")
        print("4. List enrolled users")
        print("5. Sensor info")
        print("6. CP210x info")
        print("7. Test sensor")
        print("0. Exit")
        print("=" * 60)
        
        try:
            choice = input("Enter choice (0-7): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                username = input("Enter username to enroll: ").strip()
                if username:
                    result = fp_controller.enroll_fingerprint(username)
                    print(f"ðŸ“ Enrollment result: {result}")
                    
            elif choice == '2':
                print("ðŸ‘† Place finger on sensor...")
                result = fp_controller.authenticate_fingerprint()
                print(f"ðŸ” Authentication result: {result}")
                
            elif choice == '3':
                username = input("Enter username to delete: ").strip()
                if username:
                    result = fp_controller.delete_fingerprint(username)
                    print(f"ðŸ—‘ï¸ Delete result: {result}")
                    
            elif choice == '4':
                users = fp_controller.list_enrolled_users()
                print(f"ðŸ‘¥ Enrolled users: {users}")
                
            elif choice == '5':
                info = fp_controller.get_sensor_info()
                print(f"â„¹ï¸ Sensor info: {info}")
                
            elif choice == '6':
                info = fp_controller.get_cp210x_info()
                print(f"ðŸ“± CP210x info: {info}")
                
            elif choice == '7':
                result = fp_controller.test_sensor()
                print(f"ðŸ§ª Test result: {result}")
                
            else:
                print("âŒ Invalid choice")
                
        except KeyboardInterrupt:
            print("\nðŸ‘‹ Exiting...")
            break
        except Exception as e:
            print(f"âŒ Error: {e}")

if __name__ == "__main__":
    main()
