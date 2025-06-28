#!/usr/bin/env python3
"""
Quick keypad test script to verify 4x4 matrix keypad is working
Run this first to test your keypad before running the full controller
"""

import time
import sys

def test_keypad():
    """Test the 4x4 keypad with different pin configurations"""
    
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("❌ RPi.GPIO not available. Install with: pip install RPi.GPIO")
        return False
    
    # Common 4x4 keypad pin configurations to try
    configs = [
        {
            'name': 'Config 1 (Default)',
            'rows': [18, 23, 24, 25],
            'cols': [4, 17, 27, 22]
        },
        {
            'name': 'Config 2 (Alternative)',
            'rows': [5, 6, 13, 19],
            'cols': [4, 17, 27, 22]
        },
        {
            'name': 'Config 3 (Sequential)',
            'rows': [2, 3, 4, 17],
            'cols': [27, 22, 10, 9]
        }
    ]
    
    keys = [
        ['1', '2', '3', 'A'],
        ['4', '5', '6', 'B'],
        ['7', '8', '9', 'C'],
        ['*', '0', '#', 'D']
    ]
    
    for config in configs:
        print(f"\n🧪 Testing {config['name']}")
        print(f"   Rows: {config['rows']}")
        print(f"   Cols: {config['cols']}")
        
        try:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup pins
            for row_pin in config['rows']:
                GPIO.setup(row_pin, GPIO.OUT)
                GPIO.output(row_pin, GPIO.HIGH)
            
            for col_pin in config['cols']:
                GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            print("   ✓ GPIO configured")
            print("   🎯 Press any key on keypad (10 second test)...")
            
            # Test for 10 seconds
            start_time = time.time()
            keys_detected = []
            
            while time.time() - start_time < 10:
                for row_num, row_pin in enumerate(config['rows']):
                    GPIO.output(row_pin, GPIO.LOW)
                    time.sleep(0.001)
                    
                    for col_num, col_pin in enumerate(config['cols']):
                        if GPIO.input(col_pin) == GPIO.LOW:
                            key = keys[row_num][col_num]
                            if key not in keys_detected:
                                keys_detected.append(key)
                                print(f"   ✅ Key detected: {key}")
                    
                    GPIO.output(row_pin, GPIO.HIGH)
                
                time.sleep(0.05)
            
            if keys_detected:
                print(f"   🎉 SUCCESS! Keys detected: {keys_detected}")
                print(f"   👍 Use this configuration in your main script")
                return config
            else:
                print(f"   ❌ No keys detected with this configuration")
                
        except Exception as e:
            print(f"   ❌ Error testing config: {e}")
        
        finally:
            GPIO.cleanup()
    
    print("\n❌ No working configuration found!")
    print("🔧 Check your wiring:")
    print("   - Ensure keypad is connected properly")
    print("   - Verify pin numbers match your wiring")
    print("   - Check for loose connections")
    print("   - Try different GPIO pins")
    
    return None

def interactive_test():
    """Interactive test to help identify correct pins"""
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("❌ RPi.GPIO not available")
        return
    
    print("\n🔧 Interactive Pin Test")
    print("This will help you identify which pins your keypad is connected to")
    
    # Get user input for pins
    try:
        print("\nEnter your row pins (4 pins, space separated):")
        row_input = input("Row pins: ").strip()
        rows = [int(x) for x in row_input.split()]
        
        print("\nEnter your column pins (4 pins, space separated):")
        col_input = input("Column pins: ").strip()
        cols = [int(x) for x in col_input.split()]
        
        if len(rows) != 4 or len(cols) != 4:
            print("❌ Need exactly 4 row pins and 4 column pins")
            return
        
        print(f"\n🧪 Testing with rows: {rows}, cols: {cols}")
        
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins
        for row_pin in rows:
            GPIO.setup(row_pin, GPIO.OUT)
            GPIO.output(row_pin, GPIO.HIGH)
        
        for col_pin in cols:
            GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        keys = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ]
        
        print("✓ GPIO configured")
        print("🎯 Press keys on your keypad (Ctrl+C to stop)...")
        
        while True:
            for row_num, row_pin in enumerate(rows):
                GPIO.output(row_pin, GPIO.LOW)
                time.sleep(0.001)
                
                for col_num, col_pin in enumerate(cols):
                    if GPIO.input(col_pin) == GPIO.LOW:
                        key = keys[row_num][col_num]
                        print(f"✅ Key pressed: {key} (Row {row_num+1}, Col {col_num+1})")
                        time.sleep(0.3)  # Debounce
                
                GPIO.output(row_pin, GPIO.HIGH)
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n✓ Test completed")
    except ValueError:
        print("❌ Invalid pin numbers entered")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    print("🔑 4x4 Keypad Test Utility")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        print("🚀 Running automatic configuration test...")
        working_config = test_keypad()
        
        if working_config:
            print(f"\n🎉 RECOMMENDED CONFIGURATION:")
            print(f"ROWS = {working_config['rows']}")
            print(f"COLS = {working_config['cols']}")
        else:
            print(f"\n🔧 Run interactive test: python test_keypad.py interactive")
