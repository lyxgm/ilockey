#!/usr/bin/env python3
"""
Standalone AS608 Fingerprint Sensor Controller
Simple enrollment and authentication for AS608 biometric sensor
"""

import serial
import time
import json
import os
from datetime import datetime

class AS608Fingerprint:
    """Simple AS608 fingerprint sensor controller"""
    
    def __init__(self, port='/dev/ttyUSB0', baud=57600):
        self.port = port
        self.baud = baud
        self.sensor = None
        self.db_file = 'fingerprints.json'
        self.fingerprints = {}
        
        # Load existing fingerprints
        self.load_database()
        
        # Connect to sensor
        self.connect()
    
    def connect(self):
        """Connect to AS608 sensor"""
        try:
            print(f"🔌 Connecting to AS608 on {self.port} at {self.baud} baud...")
            
            self.sensor = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=3,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            time.sleep(0.5)
            
            # Test connection
            if self.test_connection():
                print("✅ AS608 sensor connected successfully!")
                return True
            else:
                print("❌ Failed to connect to AS608 sensor")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def test_connection(self):
        """Test sensor connection with handshake"""
        try:
            # AS608 handshake command
            cmd = [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05]
            response = self.send_command(cmd)
            
            if response and len(response) >= 9 and response[0:2] == [0xEF, 0x01]:
                print(f"📡 Handshake response: {' '.join(f'{b:02X}' for b in response)}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Test connection failed: {e}")
            return False
    
    def send_command(self, cmd_list, response_length=12):
        """Send command to sensor and get response"""
        try:
            # Clear buffers
            self.sensor.reset_input_buffer()
            self.sensor.reset_output_buffer()
            
            # Send command
            cmd_bytes = bytes(cmd_list)
            self.sensor.write(cmd_bytes)
            self.sensor.flush()
            
            # Wait and read response
            time.sleep(0.3)
            response = self.sensor.read(response_length)
            
            return list(response) if response else None
            
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return None
    
    def get_image(self):
        """Capture fingerprint image"""
        cmd = [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05]
        response = self.send_command(cmd)
        
        if response and len(response) >= 9:
            return response[8]  # Return confirmation code
        return 0xFF  # Error
    
    def image_to_template(self, buffer_id):
        """Convert captured image to template"""
        cmd = [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, buffer_id, 0x00]
        
        # Calculate checksum
        checksum = sum(cmd[6:]) & 0xFFFF
        cmd.extend([checksum >> 8, checksum & 0xFF])
        
        response = self.send_command(cmd)
        
        if response and len(response) >= 9:
            return response[8]  # Return confirmation code
        return 0xFF  # Error
    
    def create_model(self):
        """Create fingerprint model from two templates"""
        cmd = [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x05, 0x00, 0x09]
        response = self.send_command(cmd)
        
        if response and len(response) >= 9:
            return response[8]  # Return confirmation code
        return 0xFF  # Error
    
    def store_model(self, location):
        """Store fingerprint model in sensor memory"""
        cmd = [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x06, 0x06, 0x01]
        cmd.extend([location >> 8, location & 0xFF, 0x00])
        
        # Calculate checksum
        checksum = sum(cmd[6:]) & 0xFFFF
        cmd.extend([checksum >> 8, checksum & 0xFF])
        
        response = self.send_command(cmd)
        
        if response and len(response) >= 9:
            return response[8]  # Return confirmation code
        return 0xFF  # Error
    
    def search_fingerprint(self):
        """Search for fingerprint match"""
        cmd = [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x08, 0x04, 0x01, 0x00, 0x00, 0x00, 0x7F]
        
        # Calculate checksum
        checksum = sum(cmd[6:]) & 0xFFFF
        cmd.extend([checksum >> 8, checksum & 0xFF])
        
        response = self.send_command(cmd, response_length=16)
        
        if response and len(response) >= 13:
            if response[8] == 0x00:  # Match found
                page_id = (response[9] << 8) | response[10]
                match_score = (response[11] << 8) | response[12]
                return 0x00, page_id, match_score
            else:
                return response[8], None, None
        return 0xFF, None, None  # Error
    
    def enroll_fingerprint(self, user_id, username):
        """Enroll a new fingerprint"""
        print(f"\n👆 Enrolling fingerprint for: {username}")
        print("=" * 50)
        
        try:
            # Step 1: Get first fingerprint image
            print("📸 Step 1: Place finger on sensor...")
            input("Press Enter when finger is placed on sensor...")
            
            attempts = 0
            while attempts < 10:
                result = self.get_image()
                
                if result == 0x00:  # Success
                    print("✅ First image captured!")
                    break
                elif result == 0x02:  # No finger
                    print("⚠️ No finger detected, try again...")
                elif result == 0x03:  # Imaging fail
                    print("⚠️ Image capture failed, adjust finger position...")
                else:
                    print(f"⚠️ Error: 0x{result:02X}")
                
                attempts += 1
                time.sleep(1)
                
                if attempts < 10:
                    input("Press Enter to try again...")
            
            if attempts >= 10:
                print("❌ Failed to capture first image")
                return False
            
            # Convert first image to template
            if self.image_to_template(0x01) != 0x00:
                print("❌ Failed to process first image")
                return False
            
            # Step 2: Get second fingerprint image
            print("\n🖐️ Remove finger and place it again...")
            input("Press Enter when ready for second scan...")
            
            attempts = 0
            while attempts < 10:
                result = self.get_image()
                
                if result == 0x00:  # Success
                    print("✅ Second image captured!")
                    break
                elif result == 0x02:  # No finger
                    print("⚠️ No finger detected, try again...")
                elif result == 0x03:  # Imaging fail
                    print("⚠️ Image capture failed, adjust finger position...")
                else:
                    print(f"⚠️ Error: 0x{result:02X}")
                
                attempts += 1
                time.sleep(1)
                
                if attempts < 10:
                    input("Press Enter to try again...")
            
            if attempts >= 10:
                print("❌ Failed to capture second image")
                return False
            
            # Convert second image to template
            if self.image_to_template(0x02) != 0x00:
                print("❌ Failed to process second image")
                return False
            
            # Step 3: Create model
            print("🔧 Creating fingerprint model...")
            result = self.create_model()
            
            if result == 0x00:
                print("✅ Fingerprint model created!")
            elif result == 0x0A:
                print("❌ Fingerprints don't match, try again")
                return False
            else:
                print(f"❌ Failed to create model: 0x{result:02X}")
                return False
            
            # Step 4: Store model
            print(f"💾 Storing fingerprint in location {user_id}...")
            if self.store_model(user_id) != 0x00:
                print("❌ Failed to store fingerprint")
                return False
            
            # Step 5: Save to database
            self.fingerprints[str(user_id)] = {
                'username': username,
                'enrolled_date': datetime.now().isoformat(),
                'location': user_id
            }
            self.save_database()
            
            print(f"🎉 Fingerprint enrolled successfully for {username}!")
            return True
            
        except Exception as e:
            print(f"❌ Enrollment error: {e}")
            return False
    
    def authenticate_fingerprint(self):
        """Authenticate fingerprint"""
        print("\n🔍 Fingerprint Authentication")
        print("=" * 50)
        
        try:
            print("👆 Place finger on sensor for authentication...")
            input("Press Enter when finger is placed...")
            
            # Capture image
            attempts = 0
            while attempts < 5:
                result = self.get_image()
                
                if result == 0x00:  # Success
                    print("✅ Image captured!")
                    break
                elif result == 0x02:  # No finger
                    print("⚠️ No finger detected, try again...")
                elif result == 0x03:  # Imaging fail
                    print("⚠️ Image capture failed, adjust finger position...")
                else:
                    print(f"⚠️ Error: 0x{result:02X}")
                
                attempts += 1
                time.sleep(1)
                
                if attempts < 5:
                    input("Press Enter to try again...")
            
            if attempts >= 5:
                print("❌ Failed to capture image for authentication")
                return False, None
            
            # Convert to template
            if self.image_to_template(0x01) != 0x00:
                print("❌ Failed to process image")
                return False, None
            
            # Search for match
            print("🔍 Searching for match...")
            result, page_id, match_score = self.search_fingerprint()
            
            if result == 0x00:  # Match found
                print(f"✅ Match found!")
                print(f"📍 Location: {page_id}")
                print(f"📊 Match Score: {match_score}")
                
                # Find username
                username = "Unknown"
                if str(page_id) in self.fingerprints:
                    username = self.fingerprints[str(page_id)]['username']
                
                print(f"👤 User: {username}")
                return True, username
                
            elif result == 0x09:  # No match
                print("❌ No matching fingerprint found")
                return False, None
            else:
                print(f"❌ Search error: 0x{result:02X}")
                return False, None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False, None
    
    def list_enrolled_fingerprints(self):
        """List all enrolled fingerprints"""
        print("\n👥 Enrolled Fingerprints")
        print("=" * 50)
        
        if not self.fingerprints:
            print("No fingerprints enrolled")
            return
        
        for location, data in self.fingerprints.items():
            print(f"📍 Location {location}: {data['username']} (enrolled: {data['enrolled_date'][:10]})")
    
    def delete_fingerprint(self, location):
        """Delete fingerprint from sensor and database"""
        try:
            # Delete from sensor (simplified - just remove from database for now)
            if str(location) in self.fingerprints:
                username = self.fingerprints[str(location)]['username']
                del self.fingerprints[str(location)]
                self.save_database()
                print(f"🗑️ Deleted fingerprint for {username}")
                return True
            else:
                print(f"❌ No fingerprint found at location {location}")
                return False
                
        except Exception as e:
            print(f"❌ Delete error: {e}")
            return False
    
    def load_database(self):
        """Load fingerprint database"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    self.fingerprints = json.load(f)
                print(f"📂 Loaded {len(self.fingerprints)} fingerprints from database")
            else:
                self.fingerprints = {}
                print("📂 Created new fingerprint database")
        except Exception as e:
            print(f"❌ Database load error: {e}")
            self.fingerprints = {}
    
    def save_database(self):
        """Save fingerprint database"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.fingerprints, f, indent=2)
            print("💾 Database saved")
        except Exception as e:
            print(f"❌ Database save error: {e}")
    
    def close(self):
        """Close sensor connection"""
        if self.sensor:
            self.sensor.close()
            print("🔌 Sensor connection closed")

def main():
    """Main program"""
    print("🔐 AS608 Fingerprint Sensor Controller")
    print("=" * 60)
    
    # Initialize sensor
    sensor = AS608Fingerprint()
    
    if not sensor.sensor:
        print("❌ Failed to initialize sensor")
        return
    
    try:
        while True:
            print("\n" + "=" * 60)
            print("📋 AS608 Fingerprint Menu")
            print("1. 👆 Enroll new fingerprint")
            print("2. 🔍 Authenticate fingerprint")
            print("3. 👥 List enrolled fingerprints")
            print("4. 🗑️ Delete fingerprint")
            print("5. 🧪 Test sensor connection")
            print("0. 🚪 Exit")
            print("=" * 60)
            
            choice = input("Enter your choice (0-5): ").strip()
            
            if choice == '0':
                break
                
            elif choice == '1':
                username = input("Enter username: ").strip()
                if username:
                    # Find next available location
                    location = 1
                    while str(location) in sensor.fingerprints:
                        location += 1
                    
                    if location > 127:  # AS608 typically supports 0-127
                        print("❌ Sensor memory full")
                    else:
                        sensor.enroll_fingerprint(location, username)
                else:
                    print("❌ Username cannot be empty")
            
            elif choice == '2':
                success, username = sensor.authenticate_fingerprint()
                if success:
                    print(f"🎉 Authentication successful! Welcome, {username}!")
                else:
                    print("❌ Authentication failed")
            
            elif choice == '3':
                sensor.list_enrolled_fingerprints()
            
            elif choice == '4':
                sensor.list_enrolled_fingerprints()
                try:
                    location = int(input("Enter location to delete: "))
                    sensor.delete_fingerprint(location)
                except ValueError:
                    print("❌ Invalid location")
            
            elif choice == '5':
                if sensor.test_connection():
                    print("✅ Sensor connection OK")
                else:
                    print("❌ Sensor connection failed")
            
            else:
                print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    finally:
        sensor.close()

if __name__ == "__main__":
    main()
