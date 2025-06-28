#!/usr/bin/env python3
"""
Fingerprint Sensor Model Identifier
Identifies the exact sensor model and optimal protocol
"""

import serial
import time
import struct

class SensorIdentifier:
    """Identify fingerprint sensor model and capabilities"""
    
    def __init__(self, port='/dev/ttyUSB0', baud=57600):
        self.port = port
        self.baud = baud
        self.sensor = None
        
    def connect(self):
        """Connect to sensor"""
        try:
            self.sensor = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=2,
                write_timeout=2,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            time.sleep(0.3)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def send_command(self, command, expected_length=12):
        """Send command and get response"""
        try:
            self.sensor.reset_input_buffer()
            self.sensor.reset_output_buffer()
            
            self.sensor.write(command)
            self.sensor.flush()
            
            time.sleep(0.3)
            
            response = self.sensor.read(expected_length)
            return response
            
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return None
    
    def test_basic_handshake(self):
        """Test basic sensor handshake"""
        print("🤝 Testing basic handshake...")
        
        # Standard AS608/ZFM handshake
        handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
        response = self.send_command(handshake)
        
        if response and len(response) >= 9:
            print(f"✅ Handshake response: {response.hex()}")
            return True, response
        else:
            print(f"❌ No handshake response")
            return False, None
    
    def get_system_parameters(self):
        """Get sensor system parameters"""
        print("📋 Getting system parameters...")
        
        # ReadSysPara command
        cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x0F, 0x00, 0x13])
        response = self.send_command(cmd, expected_length=28)
        
        if response and len(response) >= 28 and response[8] == 0x00:
            print(f"✅ System parameters: {response.hex()}")
            
            # Parse parameters
            params = {}
            if len(response) >= 28:
                params['status_register'] = (response[9] << 8) | response[10]
                params['system_id'] = (response[11] << 8) | response[12]
                params['library_size'] = (response[13] << 8) | response[14]
                params['security_level'] = (response[15] << 8) | response[16]
                params['device_address'] = struct.unpack('>I', response[17:21])[0]
                params['data_packet_size'] = (response[21] << 8) | response[22]
                params['baud_setting'] = (response[23] << 8) | response[24]
                
            return True, params
        else:
            print(f"❌ Failed to get system parameters")
            return False, None
    
    def test_led_control(self):
        """Test LED control (if supported)"""
        print("💡 Testing LED control...")
        
        # LED control command (some sensors support this)
        led_on = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x07, 0x50, 0x01, 0x01, 0xFF, 0x00, 0x59])
        response = self.send_command(led_on)
        
        if response and len(response) >= 9:
            if response[8] == 0x00:
                print("✅ LED control supported")
                
                # Turn off LED
                led_off = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x07, 0x50, 0x01, 0x00, 0xFF, 0x00, 0x58])
                self.send_command(led_off)
                
                return True
            else:
                print(f"⚠️ LED control not supported (error: 0x{response[8]:02X})")
        else:
            print("⚠️ LED control not supported")
        
        return False
    
    def test_template_count(self):
        """Get template count"""
        print("📊 Getting template count...")
        
        # TemplateNum command
        cmd = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x1D, 0x00, 0x21])
        response = self.send_command(cmd)
        
        if response and len(response) >= 11 and response[8] == 0x00:
            template_count = (response[9] << 8) | response[10]
            print(f"✅ Template count: {template_count}")
            return True, template_count
        else:
            print("❌ Failed to get template count")
            return False, 0
    
    def test_image_capture_modes(self):
        """Test different image capture modes"""
        print("📸 Testing image capture modes...")
        
        results = {}
        
        # Mode 1: Standard GetImage
        print("   Testing standard GetImage...")
        cmd1 = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
        response1 = self.send_command(cmd1)
        
        if response1 and len(response1) >= 9:
            results['standard_getimage'] = {
                'supported': True,
                'error_code': response1[8],
                'response': response1.hex()
            }
            print(f"      Response: 0x{response1[8]:02X} ({response1.hex()})")
        else:
            results['standard_getimage'] = {'supported': False}
        
        # Mode 2: Alternative GetImage with different parameters
        print("   Testing alternative GetImage...")
        cmd2 = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x01, 0x01, 0x00, 0x07])
        response2 = self.send_command(cmd2)
        
        if response2 and len(response2) >= 9:
            results['alt_getimage'] = {
                'supported': True,
                'error_code': response2[8],
                'response': response2.hex()
            }
            print(f"      Response: 0x{response2[8]:02X} ({response2.hex()})")
        else:
            results['alt_getimage'] = {'supported': False}
        
        # Mode 3: Continuous capture mode
        print("   Testing continuous capture...")
        cmd3 = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x02, 0x00, 0x06])
        response3 = self.send_command(cmd3)
        
        if response3 and len(response3) >= 9:
            results['continuous_capture'] = {
                'supported': True,
                'error_code': response3[8],
                'response': response3.hex()
            }
            print(f"      Response: 0x{response3[8]:02X} ({response3.hex()})")
        else:
            results['continuous_capture'] = {'supported': False}
        
        return results
    
    def identify_sensor_model(self):
        """Identify the specific sensor model"""
        print("🔍 Identifying sensor model...")
        
        # Connect to sensor
        if not self.connect():
            return None
        
        try:
            sensor_info = {
                'port': self.port,
                'baud': self.baud,
                'model': 'Unknown',
                'capabilities': []
            }
            
            # Test basic handshake
            handshake_ok, handshake_response = self.test_basic_handshake()
            if not handshake_ok:
                return None
            
            sensor_info['handshake_response'] = handshake_response.hex()
            
            # Get system parameters
            params_ok, params = self.get_system_parameters()
            if params_ok:
                sensor_info['system_parameters'] = params
                
                # Identify model based on system ID
                system_id = params.get('system_id', 0)
                library_size = params.get('library_size', 0)
                
                if system_id == 0x0000:
                    if library_size == 80:
                        sensor_info['model'] = 'AS608'
                    elif library_size == 200:
                        sensor_info['model'] = 'R307'
                    elif library_size == 300:
                        sensor_info['model'] = 'R503'
                    else:
                        sensor_info['model'] = 'Generic AS608 Compatible'
                else:
                    sensor_info['model'] = f'Custom (ID: 0x{system_id:04X})'
            
            # Test capabilities
            if self.test_led_control():
                sensor_info['capabilities'].append('LED_CONTROL')
            
            template_ok, template_count = self.test_template_count()
            if template_ok:
                sensor_info['template_count'] = template_count
                sensor_info['capabilities'].append('TEMPLATE_COUNT')
            
            # Test image capture modes
            capture_modes = self.test_image_capture_modes()
            sensor_info['capture_modes'] = capture_modes
            
            # Analyze error patterns
            error_codes = []
            for mode, result in capture_modes.items():
                if result.get('supported') and 'error_code' in result:
                    error_codes.append(result['error_code'])
            
            if all(code == 0x03 for code in error_codes):
                sensor_info['diagnosis'] = 'IMAGING_FAIL_CONSISTENT'
                sensor_info['recommendations'] = [
                    'Check sensor surface for dirt/damage',
                    'Verify power supply (3.3V or 5V)',
                    'Try different finger placement',
                    'Check wiring connections',
                    'Sensor may need initialization sequence'
                ]
            elif all(code == 0x02 for code in error_codes):
                sensor_info['diagnosis'] = 'NO_FINGER_DETECTED'
                sensor_info['recommendations'] = [
                    'Sensor working but not detecting finger',
                    'Press finger more firmly',
                    'Clean sensor surface',
                    'Check sensor sensitivity settings'
                ]
            else:
                sensor_info['diagnosis'] = 'MIXED_ERRORS'
                sensor_info['recommendations'] = [
                    'Inconsistent responses - check connections',
                    'May need different protocol'
                ]
            
            return sensor_info
            
        finally:
            if self.sensor:
                self.sensor.close()
    
    def generate_optimized_protocol(self, sensor_info):
        """Generate optimized protocol based on sensor identification"""
        if not sensor_info:
            return None
        
        protocol = {
            'model': sensor_info['model'],
            'baud_rate': sensor_info['baud'],
            'commands': {},
            'timing': {},
            'special_handling': []
        }
        
        # Base commands for AS608 family
        protocol['commands'] = {
            'handshake': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05],
            'get_image': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05],
            'img2tz_1': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x01, 0x00, 0x08],
            'img2tz_2': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x02, 0x02, 0x00, 0x09],
            'create_model': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x05, 0x00, 0x09],
            'search': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x08, 0x04, 0x01, 0x00, 0x00, 0x00, 0x7F]
        }
        
        # Timing adjustments based on diagnosis
        if sensor_info.get('diagnosis') == 'IMAGING_FAIL_CONSISTENT':
            protocol['timing'] = {
                'pre_command_delay': 0.5,
                'post_command_delay': 1.0,
                'image_capture_timeout': 10,
                'retry_delay': 1.0
            }
            protocol['special_handling'] = [
                'EXTENDED_TIMEOUTS',
                'MULTIPLE_RETRIES',
                'BUFFER_CLEARING'
            ]
        else:
            protocol['timing'] = {
                'pre_command_delay': 0.2,
                'post_command_delay': 0.3,
                'image_capture_timeout': 5,
                'retry_delay': 0.5
            }
        
        # Model-specific adjustments
        if 'R307' in sensor_info['model']:
            protocol['special_handling'].append('R307_SPECIFIC')
        elif 'R503' in sensor_info['model']:
            protocol['special_handling'].append('R503_SPECIFIC')
        
        return protocol

def main():
    """Main identification function"""
    print("🔍 Fingerprint Sensor Model Identifier")
    print("=" * 50)
    
    identifier = SensorIdentifier()
    
    print("🔌 Identifying sensor on /dev/ttyUSB0 at 57600 baud...")
    sensor_info = identifier.identify_sensor_model()
    
    if sensor_info:
        print("\n✅ SENSOR IDENTIFICATION COMPLETE")
        print("=" * 50)
        
        print(f"📱 Model: {sensor_info['model']}")
        print(f"🔌 Port: {sensor_info['port']}")
        print(f"⚡ Baud Rate: {sensor_info['baud']}")
        
        if 'system_parameters' in sensor_info:
            params = sensor_info['system_parameters']
            print(f"🆔 System ID: 0x{params.get('system_id', 0):04X}")
            print(f"📚 Library Size: {params.get('library_size', 0)}")
            print(f"🔒 Security Level: {params.get('security_level', 0)}")
        
        if 'template_count' in sensor_info:
            print(f"📊 Templates Stored: {sensor_info['template_count']}")
        
        if sensor_info['capabilities']:
            print(f"⚙️ Capabilities: {', '.join(sensor_info['capabilities'])}")
        
        print(f"\n🔍 Diagnosis: {sensor_info.get('diagnosis', 'Unknown')}")
        
        if 'recommendations' in sensor_info:
            print("\n💡 Recommendations:")
            for rec in sensor_info['recommendations']:
                print(f"   • {rec}")
        
        # Generate optimized protocol
        protocol = identifier.generate_optimized_protocol(sensor_info)
        if protocol:
            print(f"\n🛠️ Optimized Protocol Generated:")
            print(f"   • Model: {protocol['model']}")
            print(f"   • Timing: {protocol['timing']}")
            print(f"   • Special Handling: {protocol['special_handling']}")
            
            # Save protocol to file
            import json
            with open('data/sensor_protocol.json', 'w') as f:
                json.dump({
                    'sensor_info': sensor_info,
                    'protocol': protocol
                }, f, indent=2)
            
            print("💾 Protocol saved to data/sensor_protocol.json")
        
        print("\n🎯 Next Steps:")
        print("1. Follow the recommendations above")
        print("2. Run: python3 scripts/fingerprint_controller_optimized.py")
        print("3. Try fingerprint enrollment with optimized settings")
        
    else:
        print("❌ Failed to identify sensor")
        print("💡 Check connections and try again")

if __name__ == "__main__":
    main()
