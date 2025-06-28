#!/usr/bin/env python3
"""
Sensor Repair Kit - Targeted solutions for Error 0x03
Based on troubleshooting results showing perfect communication but imaging failure
"""

import serial
import time
import os

class SensorRepairKit:
    """Targeted repair solutions for imaging issues"""
    
    def __init__(self):
        self.port = '/dev/ttyUSB0'
        self.baud = 57600
        self.sensor = None
    
    def connect(self):
        """Connect to sensor"""
        try:
            self.sensor = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=3,
                write_timeout=3
            )
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def test_sensor_response(self):
        """Quick sensor response test"""
        if not self.connect():
            return False
        
        try:
            handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
            self.sensor.write(handshake)
            self.sensor.flush()
            time.sleep(0.5)
            
            response = self.sensor.read(12)
            if response and len(response) >= 9:
                error_code = response[8]
                print(f"📡 Sensor response: 0x{error_code:02X}")
                return error_code
            return None
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return None
        finally:
            if self.sensor:
                self.sensor.close()
    
    def guided_cleaning_process(self):
        """Step-by-step cleaning guide"""
        print("🧽 GUIDED SENSOR CLEANING PROCESS")
        print("=" * 50)
        print()
        print("Your sensor has perfect communication but Error 0x03 (Imaging Fail).")
        print("This is almost always a surface contamination issue.")
        print()
        
        # Pre-cleaning test
        print("📊 PRE-CLEANING TEST")
        print("-" * 20)
        error_code = self.test_sensor_response()
        if error_code == 0x03:
            print("✅ Confirmed: Error 0x03 (Imaging Fail)")
        print()
        
        # Cleaning steps
        cleaning_steps = [
            {
                'step': 1,
                'title': 'POWER OFF SYSTEM',
                'instructions': [
                    "• Disconnect USB cable from Raspberry Pi",
                    "• Wait 10 seconds for complete power down",
                    "• This prevents damage during cleaning"
                ]
            },
            {
                'step': 2,
                'title': 'PREPARE CLEANING MATERIALS',
                'instructions': [
                    "• Get isopropyl alcohol (70% or higher)",
                    "• Get soft, lint-free cloth (microfiber preferred)",
                    "• Get cotton swabs (optional for edges)",
                    "• Ensure good lighting to see sensor surface"
                ]
            },
            {
                'step': 3,
                'title': 'INSPECT SENSOR SURFACE',
                'instructions': [
                    "• Look closely at the sensor surface",
                    "• Check for: fingerprints, oils, dust, scratches",
                    "• Note any visible contamination",
                    "• The sensor should be smooth and clean"
                ]
            },
            {
                'step': 4,
                'title': 'CLEAN SENSOR SURFACE',
                'instructions': [
                    "• Dampen cloth with isopropyl alcohol",
                    "• Gently wipe sensor in circular motions",
                    "• DO NOT press hard - light pressure only",
                    "• Clean edges with cotton swab if needed",
                    "• Repeat until surface looks completely clean"
                ]
            },
            {
                'step': 5,
                'title': 'DRY COMPLETELY',
                'instructions': [
                    "• Let alcohol evaporate completely (30-60 seconds)",
                    "• Ensure NO moisture remains",
                    "• Surface should be completely dry",
                    "• Check for any residue or streaks"
                ]
            },
            {
                'step': 6,
                'title': 'RECONNECT AND TEST',
                'instructions': [
                    "• Reconnect USB cable to Raspberry Pi",
                    "• Wait for system to recognize device",
                    "• We'll test the sensor after cleaning"
                ]
            }
        ]
        
        for step_info in cleaning_steps:
            print(f"STEP {step_info['step']}: {step_info['title']}")
            print("-" * 30)
            for instruction in step_info['instructions']:
                print(instruction)
            print()
            
            if step_info['step'] < 6:  # Don't wait after last step
                input("Press Enter when this step is completed...")
                print()
        
        # Post-cleaning test
        print("📊 POST-CLEANING TEST")
        print("-" * 20)
        print("Testing sensor after cleaning...")
        
        time.sleep(2)  # Give time for reconnection
        error_code = self.test_sensor_response()
        
        if error_code == 0x00:
            print("🎉 SUCCESS! Sensor is now working!")
            print("✅ Error 0x03 resolved by cleaning")
            return True
        elif error_code == 0x03:
            print("⚠️ Still getting Error 0x03")
            print("💡 Try additional solutions below")
            return False
        else:
            print(f"⚠️ Different response: 0x{error_code:02X}")
            return False
    
    def advanced_solutions(self):
        """Advanced solutions if cleaning doesn't work"""
        print("\n🔧 ADVANCED SOLUTIONS")
        print("=" * 30)
        print()
        print("If cleaning didn't resolve Error 0x03, try these:")
        print()
        
        solutions = [
            {
                'title': 'FINGER TECHNIQUE',
                'steps': [
                    "• Use a different finger (index finger works best)",
                    "• Ensure finger is clean and dry",
                    "• Press VERY firmly on sensor",
                    "• Cover entire sensor surface",
                    "• Hold completely still for 3-5 seconds",
                    "• Don't slide or move finger during capture"
                ]
            },
            {
                'title': 'POWER SUPPLY CHECK',
                'steps': [
                    "• Measure voltage at sensor VCC pin",
                    "• Should be stable 3.3V or 5V",
                    "• Check for voltage drops during operation",
                    "• Try powered USB hub if using Pi USB",
                    "• Consider external power supply"
                ]
            },
            {
                'title': 'WIRING VERIFICATION',
                'steps': [
                    "• Double-check all connections:",
                    "  - VCC to 3.3V or 5V",
                    "  - GND to Ground",
                    "  - TX (sensor) to RX (CP210x)",
                    "  - RX (sensor) to TX (CP210x)",
                    "• Ensure no loose connections",
                    "• Try different jumper wires"
                ]
            },
            {
                'title': 'SENSOR HARDWARE',
                'steps': [
                    "• Sensor surface may be damaged",
                    "• Check for scratches or cracks",
                    "• Try different sensor if available",
                    "• Some sensors are defective from factory",
                    "• Contact supplier for replacement"
                ]
            }
        ]
        
        for i, solution in enumerate(solutions, 1):
            print(f"{i}. {solution['title']}")
            print("-" * 20)
            for step in solution['steps']:
                print(step)
            print()
    
    def test_with_optimized_settings(self):
        """Test with optimized settings after repair"""
        print("🧪 TESTING WITH OPTIMIZED SETTINGS")
        print("=" * 40)
        
        if not self.connect():
            return False
        
        try:
            # Test with extended timeouts and multiple attempts
            print("Testing with extended timeouts...")
            
            for attempt in range(5):
                print(f"Attempt {attempt + 1}/5...")
                
                # Clear buffers
                self.sensor.reset_input_buffer()
                self.sensor.reset_output_buffer()
                time.sleep(0.5)
                
                # Send command with extended timing
                handshake = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
                self.sensor.write(handshake)
                self.sensor.flush()
                time.sleep(2.0)  # Extended wait
                
                response = self.sensor.read(12)
                
                if response and len(response) >= 9:
                    error_code = response[8]
                    print(f"   Response: 0x{error_code:02X}")
                    
                    if error_code == 0x00:
                        print("🎉 SUCCESS! Sensor working with optimized settings!")
                        return True
                    elif error_code == 0x02:
                        print("   No finger detected")
                    elif error_code == 0x03:
                        print("   Still imaging fail")
                
                time.sleep(1)
            
            print("❌ Still not working with optimized settings")
            return False
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        finally:
            if self.sensor:
                self.sensor.close()

def main():
    """Main repair process"""
    print("🔧 Fingerprint Sensor Repair Kit")
    print("=" * 40)
    print()
    print("Based on troubleshooting results:")
    print("✅ Hardware: Working")
    print("✅ Power: Working") 
    print("✅ Communication: Working")
    print("❌ Imaging: Error 0x03 (Imaging Fail)")
    print()
    print("This indicates a sensor surface or hardware issue.")
    print()
    
    repair_kit = SensorRepairKit()
    
    # Step 1: Guided cleaning
    print("🧽 SOLUTION 1: GUIDED CLEANING PROCESS")
    proceed = input("Start guided cleaning process? (Y/n): ").lower().strip()
    
    if proceed != 'n':
        success = repair_kit.guided_cleaning_process()
        
        if success:
            print("\n🎉 REPAIR SUCCESSFUL!")
            print("Your sensor is now working. Try enrollment:")
            print("python3 scripts/fingerprint_controller_optimized.py")
            return
    
    # Step 2: Advanced solutions
    print("\n🔧 SOLUTION 2: ADVANCED TROUBLESHOOTING")
    repair_kit.advanced_solutions()
    
    # Step 3: Test with optimized settings
    print("🧪 SOLUTION 3: OPTIMIZED SETTINGS TEST")
    proceed = input("Test with optimized settings? (Y/n): ").lower().strip()
    
    if proceed != 'n':
        success = repair_kit.test_with_optimized_settings()
        
        if success:
            print("\n🎉 WORKING WITH OPTIMIZED SETTINGS!")
            print("Use the optimized controller for enrollment")
        else:
            print("\n❌ SENSOR HARDWARE ISSUE")
            print("💡 Recommendations:")
            print("• Try different fingerprint sensor")
            print("• Check sensor datasheet for specific requirements")
            print("• Contact sensor manufacturer")
            print("• Sensor may be defective")

if __name__ == "__main__":
    main()
