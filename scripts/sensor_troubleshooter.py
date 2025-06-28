#!/usr/bin/env python3
"""
Fingerprint Sensor Troubleshooter
Comprehensive diagnostic and repair tool for imaging issues
"""

import serial
import time
import os
import json
import subprocess

class SensorTroubleshooter:
    """Comprehensive sensor troubleshooting tool"""
    
    def __init__(self, port='/dev/ttyUSB0', baud=57600):
        self.port = port
        self.baud = baud
        self.sensor = None
        
    def connect(self):
        """Connect to sensor with robust settings"""
        try:
            self.sensor = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=3,
                write_timeout=3,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def check_hardware_connections(self):
        """Check hardware connections and power"""
        print("🔌 Checking Hardware Connections")
        print("-" * 40)
        
        # Check USB device
        try:
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            if '10c4:ea60' in result.stdout:
                print("✅ CP210x USB bridge detected")
            else:
                print("❌ CP210x USB bridge not found")
                return False
        except:
            print("⚠️ Cannot check USB devices")
        
        # Check serial port
        if os.path.exists(self.port):
            print(f"✅ Serial port {self.port} exists")
            
            # Check permissions
            stat_info = os.stat(self.port)
            print(f"📋 Port permissions: {oct(stat_info.st_mode)[-3:]}")
            
            # Check if port is accessible
            try:
                with open(self.port, 'rb') as f:
                    print("✅ Port is accessible")
            except PermissionError:
                print("❌ Permission denied - run: sudo usermod -a -G dialout $USER")
                return False
            except:
                print("⚠️ Port access test inconclusive")
        else:
            print(f"❌ Serial port {self.port} not found")
            return False
        
        return True
    
    def test_power_and_voltage(self):
        """Test sensor power and voltage levels"""
        print("\n⚡ Testing Power and Voltage")
        print("-" * 40)
        
        if not self.connect():
            return False
        
        try:
            # Test basic communication (indicates power is present)
            handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            
            self.sensor.reset_input_buffer()
            self.sensor.reset_output_buffer()
            
            self.sensor.write(handshake)
            self.sensor.flush()
            time.sleep(0.5)
            
            response = self.sensor.read(12)
            
            if response and len(response) >= 9:
                print("✅ Sensor is receiving power (responds to commands)")
                print(f"📡 Response: {response.hex()}")
                
                # Check response pattern for power issues
                if response[0:2] == bytes([0xEF, 0x01]):
                    print("✅ Communication protocol working")
                else:
                    print("⚠️ Unusual response pattern - possible power fluctuation")
                
                return True
            else:
                print("❌ No response - possible power issue")
                return False
                
        except Exception as e:
            print(f"❌ Power test failed: {e}")
            return False
        finally:
            if self.sensor:
                self.sensor.close()
    
    def test_different_baud_rates(self):
        """Test communication at different baud rates"""
        print("\n📡 Testing Different Baud Rates")
        print("-" * 40)
        
        baud_rates = [9600, 19200, 38400, 57600, 115200]
        working_rates = []
        
        for baud in baud_rates:
            print(f"Testing {baud} baud...")
            
            try:
                sensor = serial.Serial(
                    port=self.port,
                    baudrate=baud,
                    timeout=2,
                    write_timeout=2
                )
                time.sleep(0.3)
                
                # Test handshake
                handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
                sensor.write(handshake)
                sensor.flush()
                time.sleep(0.3)
                
                response = sensor.read(12)
                sensor.close()
                
                if response and len(response) >= 9 and response[0:2] == bytes([0xEF, 0x01]):
                    print(f"✅ {baud} baud: Working")
                    working_rates.append(baud)
                else:
                    print(f"❌ {baud} baud: No valid response")
                    
            except Exception as e:
                print(f"❌ {baud} baud: Error - {e}")
        
        if working_rates:
            print(f"\n✅ Working baud rates: {working_rates}")
            return working_rates
        else:
            print("\n❌ No working baud rates found")
            return []
    
    def test_sensor_initialization_sequences(self):
        """Test different sensor initialization sequences"""
        print("\n🔧 Testing Initialization Sequences")
        print("-" * 40)
        
        if not self.connect():
            return False
        
        try:
            sequences = [
                {
                    'name': 'Standard Handshake',
                    'commands': [
                        [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05]
                    ]
                },
                {
                    'name': 'Extended Handshake',
                    'commands': [
                        [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05],
                        [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x0F, 0x00, 0x13]  # ReadSysPara
                    ]
                },
                {
                    'name': 'Reset + Handshake',
                    'commands': [
                        [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x0D, 0x00, 0x11],  # SoftReset
                        [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05]   # GetImage
                    ]
                },
                {
                    'name': 'Alternative Address',
                    'commands': [
                        [0xEF, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05]  # Different address
                    ]
                }
            ]
            
            working_sequences = []
            
            for seq in sequences:
                print(f"Testing {seq['name']}...")
                
                success = True
                for i, cmd in enumerate(seq['commands']):
                    self.sensor.reset_input_buffer()
                    self.sensor.reset_output_buffer()
                    time.sleep(0.2)
                    
                    self.sensor.write(bytes(cmd))
                    self.sensor.flush()
                    time.sleep(0.5)
                    
                    response = self.sensor.read(12)
                    
                    if response and len(response) >= 9:
                        error_code = response[8] if len(response) > 8 else 0xFF
                        print(f"   Command {i+1}: Response 0x{error_code:02X}")
                        
                        if error_code == 0x03:  # Still getting imaging fail
                            print(f"   ⚠️ Still getting imaging fail (0x03)")
                        elif error_code == 0x00:
                            print(f"   ✅ Success!")
                        else:
                            print(f"   ⚠️ Different error: 0x{error_code:02X}")
                    else:
                        print(f"   ❌ No response to command {i+1}")
                        success = False
                        break
                
                if success:
                    working_sequences.append(seq['name'])
                    print(f"✅ {seq['name']}: Working")
                else:
                    print(f"❌ {seq['name']}: Failed")
                
                time.sleep(1)  # Delay between sequences
            
            return working_sequences
            
        except Exception as e:
            print(f"❌ Initialization test failed: {e}")
            return []
        finally:
            if self.sensor:
                self.sensor.close()
    
    def test_sensor_surface_and_imaging(self):
        """Test sensor surface and imaging capabilities"""
        print("\n👆 Testing Sensor Surface and Imaging")
        print("-" * 40)
        
        if not self.connect():
            return False
        
        try:
            # Test with different imaging parameters
            imaging_tests = [
                {
                    'name': 'Standard GetImage',
                    'cmd': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05],
                    'description': 'Place finger normally'
                },
                {
                    'name': 'GetImage with timeout',
                    'cmd': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05],
                    'description': 'Place finger VERY firmly and hold for 3 seconds'
                },
                {
                    'name': 'Alternative imaging',
                    'cmd': [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x04, 0x01, 0x01, 0x00, 0x07],
                    'description': 'Place finger with different pressure'
                }
            ]
            
            results = []
            
            for test in imaging_tests:
                print(f"\n🧪 {test['name']}")
                print(f"📋 {test['description']}")
                
                input("Press Enter when ready to test...")
                
                # Multiple attempts for each test
                for attempt in range(3):
                    print(f"   Attempt {attempt + 1}/3...")
                    
                    self.sensor.reset_input_buffer()
                    self.sensor.reset_output_buffer()
                    time.sleep(0.3)
                    
                    self.sensor.write(bytes(test['cmd']))
                    self.sensor.flush()
                    time.sleep(1.0)  # Extended wait
                    
                    response = self.sensor.read(12)
                    
                    if response and len(response) >= 9:
                        error_code = response[8]
                        print(f"      Response: 0x{error_code:02X} ({response.hex()})")
                        
                        if error_code == 0x00:
                            print("      ✅ SUCCESS! Image captured!")
                            results.append({'test': test['name'], 'success': True, 'attempt': attempt + 1})
                            break
                        elif error_code == 0x02:
                            print("      ⚠️ No finger detected")
                        elif error_code == 0x03:
                            print("      ❌ Imaging failed")
                        else:
                            print(f"      ⚠️ Other error: 0x{error_code:02X}")
                    else:
                        print("      ❌ No response")
                    
                    time.sleep(0.5)
                
                if not any(r['test'] == test['name'] and r['success'] for r in results):
                    results.append({'test': test['name'], 'success': False})
            
            return results
            
        except Exception as e:
            print(f"❌ Surface test failed: {e}")
            return []
        finally:
            if self.sensor:
                self.sensor.close()
    
    def generate_troubleshooting_report(self):
        """Generate comprehensive troubleshooting report"""
        print("\n🔍 COMPREHENSIVE SENSOR TROUBLESHOOTING")
        print("=" * 60)
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'hardware_ok': False,
            'power_ok': False,
            'communication_ok': False,
            'imaging_issue': True,
            'recommendations': []
        }
        
        # Test 1: Hardware connections
        print("\n1️⃣ HARDWARE CONNECTION TEST")
        hardware_ok = self.check_hardware_connections()
        report['hardware_ok'] = hardware_ok
        
        if not hardware_ok:
            report['recommendations'].extend([
                "Check USB cable connection",
                "Try different USB port",
                "Verify CP210x driver installation"
            ])
            return report
        
        # Test 2: Power and voltage
        print("\n2️⃣ POWER AND VOLTAGE TEST")
        power_ok = self.test_power_and_voltage()
        report['power_ok'] = power_ok
        
        if not power_ok:
            report['recommendations'].extend([
                "Check sensor power supply (3.3V or 5V)",
                "Verify wiring: VCC, GND, TX, RX",
                "Try external power supply if using USB power"
            ])
        
        # Test 3: Communication
        print("\n3️⃣ COMMUNICATION TEST")
        working_bauds = self.test_different_baud_rates()
        report['working_baud_rates'] = working_bauds
        report['communication_ok'] = len(working_bauds) > 0
        
        # Test 4: Initialization
        print("\n4️⃣ INITIALIZATION TEST")
        working_init = self.test_sensor_initialization_sequences()
        report['working_init_sequences'] = working_init
        
        # Test 5: Imaging (interactive)
        print("\n5️⃣ IMAGING TEST")
        print("This test requires finger placement on the sensor.")
        proceed = input("Proceed with imaging test? (y/N): ").lower().strip()
        
        if proceed == 'y':
            imaging_results = self.test_sensor_surface_and_imaging()
            report['imaging_results'] = imaging_results
            
            # Check if any imaging test succeeded
            if any(r.get('success', False) for r in imaging_results):
                report['imaging_issue'] = False
                print("\n✅ IMAGING WORKING! Some tests succeeded.")
            else:
                print("\n❌ IMAGING STILL FAILING")
        
        # Generate final recommendations
        print("\n📋 FINAL DIAGNOSIS AND RECOMMENDATIONS")
        print("=" * 60)
        
        if report['imaging_issue']:
            print("🔍 DIAGNOSIS: Persistent imaging failure (Error 0x03)")
            print("\n💡 RECOMMENDED SOLUTIONS (try in order):")
            
            solutions = [
                "1. CLEAN SENSOR SURFACE",
                "   • Use soft cloth with isopropyl alcohol",
                "   • Remove any dirt, oil, or residue",
                "   • Ensure surface is completely dry",
                "",
                "2. CHECK FINGER PLACEMENT",
                "   • Press finger FIRMLY on sensor",
                "   • Cover entire sensor surface",
                "   • Hold steady for 2-3 seconds",
                "   • Try different fingers",
                "",
                "3. VERIFY POWER SUPPLY",
                "   • Ensure stable 3.3V or 5V supply",
                "   • Check for voltage drops under load",
                "   • Try external power supply",
                "",
                "4. CHECK WIRING",
                "   • Verify TX/RX are not swapped",
                "   • Check for loose connections",
                "   • Ensure proper ground connection",
                "",
                "5. SENSOR HARDWARE ISSUE",
                "   • Sensor may be damaged",
                "   • Try different sensor if available",
                "   • Contact sensor manufacturer"
            ]
            
            for solution in solutions:
                print(solution)
        else:
            print("✅ SENSOR IS WORKING!")
            print("💡 Use the optimized controller for enrollment")
        
        # Save report
        os.makedirs('data', exist_ok=True)
        with open('data/troubleshooting_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to data/troubleshooting_report.json")
        
        return report

def main():
    """Main troubleshooting function"""
    print("🔧 Fingerprint Sensor Troubleshooter")
    print("=" * 50)
    print("This tool will comprehensively diagnose your sensor issues.")
    print("The process may take 5-10 minutes.")
    print()
    
    proceed = input("Start comprehensive troubleshooting? (Y/n): ").lower().strip()
    if proceed == 'n':
        return
    
    troubleshooter = SensorTroubleshooter()
    report = troubleshooter.generate_troubleshooting_report()
    
    print("\n🎯 TROUBLESHOOTING COMPLETE!")
    print("Check the recommendations above and try the suggested solutions.")

if __name__ == "__main__":
    main()
