#!/usr/bin/env python3
"""
AS608 Fingerprint Sensor Controller for Raspberry Pi GPIO UART
Direct connection via GPIO pins 14/15 (UART0) or 8/10 (UART1)
"""

import serial
import time
import json
import os
from datetime import datetime

class AS608GPIOController:
    """AS608 controller for Raspberry Pi GPIO UART"""
    
    def __init__(self):
        self.sensor = None
        self.port = None
        self.baud = None
        self.db_file = 'fingerprints.json'
        self.fingerprints = {}
        
        # Load existing fingerprints
        self.load_database()
        
        # Connect to GPIO UART
        self.connect_gpio_uart()
    
    def connect_gpio_uart(self):
        """Connect to AS608 via Raspberry Pi GPIO UART"""
        print("🔌 Connecting to AS608 via Raspberry Pi GPIO UART...")
        
        # Try common GPIO UART ports
        gpio_ports = [
            ('/dev/serial0', 'Primary UART (GPIO 14/15)'),
            ('/dev/ttyAMA0', 'Hardware UART (GPIO 14/15)'),
            ('/dev/ttyS0', 'Mini UART (GPIO 14/15)'),
            ('/dev/serial1', 'Secondary UART'),
            ('/dev/ttyAMA1', 'Hardware UART1 (GPIO 8/10)')
        ]
        
        # Common baud rates for AS608
        baud_rates = [57600, 9600, 19200, 38400, 115200]
        
        for port, description in gpio_ports:
            if not os.path.exists(port):
                print(f"⚠️ {port} ({description}) not found")
                continue
                
            print(f"🔍 Testing {port} ({description})...")
            
            for baud in baud_rates:
                try:
                    print(f"   📡 Testing at {baud} baud...")
                    
                    # Try to connect
                    test_sensor = serial.Serial(
                        port=port,
                        baudrate=baud,
                        timeout=2,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE
                    )
                    
                    time.sleep(0.5)
                    
                    # Test AS608 handshake
                    if self.test_handshake(test_sensor):
                        print(f"✅ AS608 found on {port} at {baud} baud!")
                        print(f"📍 Using: {description}")
                        
                        # Set up the working connection
                        test_sensor.close()
                        self.port = port
                        self.baud = baud
                        
                        # Create final connection
                        self.sensor = serial.Serial(
                            port=self.port,
                            baudrate=self.baud,
                            timeout=3,
                            bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE
                        )
                        
                        time.sleep(0.5)
                        return True
                    
                    test_sensor.close()
                    
                except Exception as e:
                    print(f"     ❌ Failed: {e}")
                    continue
        
        print("❌ No AS608 sensor found on GPIO UART ports")
        print("\n💡 GPIO UART Troubleshooting:")
        print("1. Check wiring:")
        print("   AS608 TX  -> Pi GPIO 15 (RX)")
        print("   AS608 RX  -> Pi GPIO 14 (TX)")
        print("   AS608 VCC -> Pi 3.3V or 5V")
        print("   AS608 GND -> Pi GND")
        print("\n2. Enable UART in raspi-config:")
        print("   sudo raspi-config -> Interface Options -> Serial Port")
        print("   Login shell: No, Serial hardware: Yes")
        print("\n3. Check /boot/config.txt:")
        print("   enable_uart=1")
        print("   dtoverlay=disable-bt  # if using primary UART")
        
        return False
    
    def test_handshake(self, sensor):
        """Test AS608 handshake command"""
        try:
            # Clear buffers
            sensor.reset_input_buffer()
            sensor.reset_output_buffer()
            
            # AS608 handshake: Get image command
            cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            sensor.write(cmd)
            sensor.flush()
            
            time.sleep(0.3)
            response = sensor.read(12)
            
            # Check for valid AS608 response
            if len(response) >= 9 and response[0:2] == b'\xEF\x01':
                return True
            
            return False
            
        except Exception:
            return False
    
    def send_command(self, cmd_list, response_length=12):
        """Send command to AS608 and get response"""
        try:
            if not self.sensor:
                return None
            
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
    
    def get_error_message(self, error_code):
        """Get human-readable error message"""
        error_messages = {
            0x00: "Success",
            0x01: "Packet receive error",
            0x02: "No finger on sensor",
            0x03: "Failed to capture finger image",
            0x04: "Image too messy",
            0x05: "Image too light",
            0x06: "Image too dark",
            0x07: "Image lacks detail",
            0x08: "Image doesn't match",
            0x09: "No matching fingerprint found",
            0x0A: "Failed to combine templates",
            0x0B: "Address code exceeds range",
            0x0C: "Error reading template from library",
            0x0D: "Error uploading template",
            0x0E: "Module can't receive data",
            0x0F: "Error uploading image",
            0x10: "Failed to delete template",
            0x11: "Failed to clear library",
            0x13: "Wrong password",
            0x15: "Primary image generation failure",
            0x18: "Error writing flash"
        }
        return error_messages.get(error_code, f"Unknown error: 0x{error_code:02X}")
    
    def enroll_fingerprint(self, username):
        """Enroll a new fingerprint"""
        if not self.sensor:
            print("❌ Sensor not connected")
            return False
        
        print(f"\n👆 Enrolling fingerprint for: {username}")
        print("=" * 50)
        
        try:
            # Find next available location
            location = 1
            while str(location) in self.fingerprints and location <= 127:
                location += 1
            
            if location > 127:
                print("❌ Sensor memory full (max 127 fingerprints)")
                return False
            
            # Step 1: Get first fingerprint image
            print("📸 Step 1: Place finger on sensor...")
            input("Press Enter when finger is placed...")
            
            attempts = 0
            while attempts < 10:
                result = self.get_image()
                
                if result == 0x00:  # Success
                    print("✅ First image captured!")
                    break
                else:
                    error_msg = self.get_error_message(result)
                    print(f"⚠️ {error_msg}")
                
                attempts += 1
                if attempts < 10:
                    input("Adjust finger position and press Enter to try again...")
            
            if attempts >= 10:
                print("❌ Failed to capture first image after 10 attempts")
                return False
            
            # Convert first image to template
            result = self.image_to_template(0x01)
            if result != 0x00:
                print(f"❌ Failed to process first image: {self.get_error_message(result)}")
                return False
            
            # Step 2: Get second fingerprint image
            print("\n🖐️ Remove finger and place the SAME finger again...")
            input("Press Enter when ready for second scan...")
            
            attempts = 0
            while attempts < 10:
                result = self.get_image()
                
                if result == 0x00:  # Success
                    print("✅ Second image captured!")
                    break
                else:
                    error_msg = self.get_error_message(result)
                    print(f"⚠️ {error_msg}")
                
                attempts += 1
                if attempts < 10:
                    input("Adjust finger position and press Enter to try again...")
            
            if attempts >= 10:
                print("❌ Failed to capture second image after 10 attempts")
                return False
            
            # Convert second image to template
            result = self.image_to_template(0x02)
            if result != 0x00:
                print(f"❌ Failed to process second image: {self.get_error_message(result)}")
                return False
            
            # Step 3: Create model
            print("🔧 Creating fingerprint model...")
            result = self.create_model()
            
            if result == 0x00:
                print("✅ Fingerprint model created!")
            else:
                print(f"❌ Failed to create model: {self.get_error_message(result)}")
                return False
            
            # Step 4: Store model
            print(f"💾 Storing fingerprint in location {location}...")
            result = self.store_model(location)
            if result != 0x00:
                print(f"❌ Failed to store fingerprint: {self.get_error_message(result)}")
                return False
            
            # Step 5: Save to database
            self.fingerprints[str(location)] = {
                'username': username,
                'enrolled_date': datetime.now().isoformat(),
                'location': location
            }
            self.save_database()
            
            print(f"🎉 Fingerprint enrolled successfully for {username} at location {location}!")
            return True
            
        except Exception as e:
            print(f"❌ Enrollment error: {e}")
            return False
    
    def authenticate_fingerprint(self):
        """Authenticate fingerprint"""
        if not self.sensor:
            print("❌ Sensor not connected")
            return False, None
        
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
                else:
                    error_msg = self.get_error_message(result)
                    print(f"⚠️ {error_msg}")
                
                attempts += 1
                if attempts < 5:
                    input("Adjust finger position and press Enter to try again...")
            
            if attempts >= 5:
                print("❌ Failed to capture image for authentication")
                return False, None
            
            # Convert to template
            result = self.image_to_template(0x01)
            if result != 0x00:
                print(f"❌ Failed to process image: {self.get_error_message(result)}")
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
                
            else:
                error_msg = self.get_error_message(result)
                print(f"❌ {error_msg}")
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
        
        for location, data in sorted(self.fingerprints.items(), key=lambda x: int(x[0])):
            enrolled_date = data['enrolled_date'][:10] if 'enrolled_date' in data else 'Unknown'
            print(f"📍 Location {location}: {data['username']} (enrolled: {enrolled_date})")
    
    def delete_fingerprint(self, location):
        """Delete fingerprint from database"""
        try:
            if str(location) in self.fingerprints:
                username = self.fingerprints[str(location)]['username']
                del self.fingerprints[str(location)]
                self.save_database()
                print(f"🗑️ Deleted fingerprint for {username} from location {location}")
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
    
    def test_sensor(self):
        """Test sensor connection"""
        if not self.sensor:
            return False
        
        try:
            result = self.get_image()
            if result in [0x00, 0x02]:  # Success or no finger (both indicate working sensor)
                return True
            return False
        except:
            return False
    
    def show_gpio_info(self):
        """Show GPIO UART information"""
        print("\n📍 Raspberry Pi GPIO UART Information")
        print("=" * 50)
        print("🔌 Wiring for AS608:")
        print("   AS608 TX  -> Pi GPIO 15 (Pin 10) - RX")
        print("   AS608 RX  -> Pi GPIO 14 (Pin 8)  - TX")
        print("   AS608 VCC -> Pi 3.3V (Pin 1) or 5V (Pin 2)")
        print("   AS608 GND -> Pi GND (Pin 6)")
        print("\n⚙️ UART Configuration:")
        print(f"   Port: {self.port}")
        print(f"   Baud: {self.baud}")
        print("\n🛠️ Enable UART:")
        print("   sudo raspi-config -> Interface Options -> Serial Port")
        print("   Login shell: No, Serial hardware: Yes")
        print("\n📝 /boot/config.txt should have:")
        print("   enable_uart=1")
        print("   dtoverlay=disable-bt  # if using primary UART")
    
    def close(self):
        """Close sensor connection"""
        if self.sensor:
            self.sensor.close()
            print("🔌 GPIO UART connection closed")

def main():
    """Main program"""
    print("🔐 AS608 Fingerprint Sensor - Raspberry Pi GPIO UART")
    print("=" * 60)
    
    # Initialize sensor
    sensor = AS608GPIOController()
    
    if not sensor.sensor:
        print("❌ Failed to initialize AS608 sensor via GPIO UART")
        return
    
    try:
        while True:
            print("\n" + "=" * 60)
            print("📋 AS608 GPIO UART Menu")
            print("1. 👆 Enroll new fingerprint")
            print("2. 🔍 Authenticate fingerprint")
            print("3. 👥 List enrolled fingerprints")
            print("4. 🗑️ Delete fingerprint")
            print("5. 🧪 Test sensor")
            print("6. ℹ️ Sensor info")
            print("7. 📍 GPIO wiring info")
            print("0. 🚪 Exit")
            print("=" * 60)
            
            choice = input("Enter your choice (0-7): ").strip()
            
            if choice == '0':
                break
                
            elif choice == '1':
                username = input("Enter username: ").strip()
                if username:
                    sensor.enroll_fingerprint(username)
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
                if sensor.test_sensor():
                    print("✅ AS608 sensor is working properly via GPIO UART")
                else:
                    print("❌ AS608 sensor test failed")
            
            elif choice == '6':
                print(f"\n📱 Sensor Information:")
                print(f"   Port: {sensor.port}")
                print(f"   Baud Rate: {sensor.baud}")
                print(f"   Connection: GPIO UART")
                print(f"   Enrolled: {len(sensor.fingerprints)} fingerprints")
                print(f"   Database: {sensor.db_file}")
            
            elif choice == '7':
                sensor.show_gpio_info()
            
            else:
                print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    finally:
        sensor.close()

if __name__ == "__main__":
    main()
