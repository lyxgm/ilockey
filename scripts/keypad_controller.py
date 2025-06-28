#!/usr/bin/env python3
# This script would run on the Raspberry Pi to control the keypad
# It's included here for reference but would not be part of the web app

import time
import requests
import threading

class KeypadController:
    def __init__(self):
        self.gpio_available = False
        self.api_available = False
        self.running = False
        
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.gpio_available = True
            
            # Set up GPIO with proper cleanup
            GPIO.cleanup()  # Clean any previous setup
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Updated GPIO configuration for rows
            self.ROWS = [18, 23, 24, 25]   # GPIO pins for rows (outputs)
            self.COLS = [4, 17, 27, 22]  # GPIO pins for columns (inputs) 
            
            # FIXED: Correct keypad layout for standard 4x4 keypad
            self.KEYS = [
                ['1', '2', '3', 'A'],
                ['4', '5', '6', 'B'], 
                ['7', '8', '9', 'C'],
                ['*', '0', '#', 'D']
            ]
            
            # Setup GPIO pins with proper configuration
            self._setup_gpio_pins()
            
            print("✓ GPIO initialized successfully")
            print(f"✓ Row pins: {self.ROWS}")
            print(f"✓ Column pins: {self.COLS}")
            
        except ImportError:
            print("⚠ RPi.GPIO not available - running in simulation mode")
            self._setup_mock_gpio()
        except Exception as e:
            print(f"⚠ GPIO setup error: {e} - running in simulation mode")
            self._setup_mock_gpio()
        
        # Initialize other components
        self._init_components()

    def _setup_gpio_pins(self):
        """Setup GPIO pins with FIXED configuration for 4x4 keypad"""
        try:
            # FIXED: Set up row pins as outputs with initial HIGH state
            for row_pin in self.ROWS:
                self.GPIO.setup(row_pin, self.GPIO.OUT)
                self.GPIO.output(row_pin, self.GPIO.HIGH)
                print(f"✓ Row pin {row_pin} configured as OUTPUT (HIGH)")
            
            # FIXED: Set up column pins as inputs with pull-up resistors
            # This is crucial - we need pull-up, not pull-down!
            for col_pin in self.COLS:
                self.GPIO.setup(col_pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
                print(f"✓ Column pin {col_pin} configured as INPUT (PULL-UP)")
            
            # Door lock relay pin (separate from keypad)
            self.DOOR_RELAY_PIN = 21
            self.GPIO.setup(self.DOOR_RELAY_PIN, self.GPIO.OUT)
            self.GPIO.output(self.DOOR_RELAY_PIN, self.GPIO.LOW)  # Start locked
            print(f"✓ Door relay pin {self.DOOR_RELAY_PIN} configured")
            
            # Test GPIO setup
            self._test_gpio_setup()
            
        except Exception as e:
            print(f"✗ Error setting up GPIO pins: {e}")
            raise

    def _test_gpio_setup(self):
        """Test GPIO setup by reading initial states"""
        print("\n--- GPIO Test ---")
        for i, col_pin in enumerate(self.COLS):
            state = self.GPIO.input(col_pin)
            print(f"Column {i+1} (pin {col_pin}): {'HIGH' if state else 'LOW'}")
        print("--- End Test ---\n")

    def _setup_mock_gpio(self):
        """Setup mock GPIO for testing without hardware"""
        self.gpio_available = False
        
        class MockGPIO:
            BCM = "BCM"
            OUT = "OUT"
            IN = "IN"
            HIGH = 1
            LOW = 0
            PUD_UP = "PUD_UP"
            PUD_DOWN = "PUD_DOWN"
            
            def __init__(self):
                self.pin_states = {}
                self.mock_key_pressed = None
            
            def setmode(self, mode): pass
            def setwarnings(self, enabled): pass
            def cleanup(self): pass
            
            def setup(self, pin, mode, **kwargs):
                if mode == self.OUT:
                    self.pin_states[pin] = self.HIGH
                else:
                    self.pin_states[pin] = self.HIGH  # Pull-up default
            
            def output(self, pin, value):
                self.pin_states[pin] = value
            
            def input(self, pin):
                # Simulate keypad press for testing
                if hasattr(self, 'simulate_press') and self.simulate_press:
                    return self.LOW if pin == 4 else self.HIGH  # Simulate key '1'
                return self.pin_states.get(pin, self.HIGH)
        
        self.GPIO = MockGPIO()
        self.ROWS = [18, 23, 24, 25]  
        self.COLS = [4, 17, 27, 22]  
        self.DOOR_RELAY_PIN = 21
        
        # FIXED: Same keypad layout
        self.KEYS = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ]
        
        print("✓ Mock GPIO initialized for testing")

    def _init_components(self):
        """Initialize other components"""
        # Variables for passcode handling
        self.current_input = ""
        self.system_passcode = "1234"
        self.lockout_passcode = "9999"
        self.max_trials = 3
        self.failed_attempts = 0
        self.is_locked_out = False
        self.last_key_time = 0
        self.last_input_time = 0  # Track when last input was made
        self.input_timeout = 30  # Default 30 seconds
        self.debounce_delay = 0.3  # 300ms debounce
        self.ai_active = False  # Track AI interaction state
        
        # API configuration
        self.API_URL = "http://localhost:5000/api"
        self.settings = {}
        
        # Test API connection
        self._test_api_connection()

    def _test_api_connection(self):
        """Test if API is available"""
        try:
            response = requests.get(f"{self.API_URL}/settings", timeout=5)
            self.api_available = response.status_code == 200
            if self.api_available:
                print("✓ API connection successful")
            else:
                print(f"⚠ API connection failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠ API not available: {e}")
            self.api_available = False
    
    def scan_keypad(self):
        """FIXED: Proper keypad scanning with correct logic"""
        try:
            # Scan each row
            for row_num, row_pin in enumerate(self.ROWS):
                # Set current row LOW (active)
                self.GPIO.output(row_pin, self.GPIO.LOW)
                
                # Small delay for signal to settle
                time.sleep(0.001)
                
                # Check each column
                for col_num, col_pin in enumerate(self.COLS):
                    # If column reads LOW, key is pressed (pulled down by row)
                    if self.GPIO.input(col_pin) == self.GPIO.LOW:
                        key = self.KEYS[row_num][col_num]
                        
                        # Reset row to HIGH before returning
                        self.GPIO.output(row_pin, self.GPIO.HIGH)
                        
                        # Reset all other rows to HIGH
                        for other_row in self.ROWS:
                            self.GPIO.output(other_row, self.GPIO.HIGH)
                        
                        return key
                
                # Reset row to HIGH after checking
                self.GPIO.output(row_pin, self.GPIO.HIGH)
            
            return None
            
        except Exception as e:
            print(f"✗ Error scanning keypad: {e}")
            return None
    
    def process_key(self, key):
        """Process a key press with improved feedback"""
        if key is None:
            return
        
        # Debounce check
        current_time = time.time()
        if current_time - self.last_key_time < self.debounce_delay:
            return
        
        self.last_key_time = current_time
        
        print(f"🔑 Key pressed: {key}")
        
        if key == 'A':
            # A = Enter/Submit passcode
            print("📝 Submitting passcode...")
            self.check_passcode()
            self.current_input = ""
            print("✓ Passcode submitted")
            
        elif key == 'B':
            # B = Backspace
            if self.current_input:
                self.current_input = self.current_input[:-1]
                print(f"⌫ Backspace: {'*' * len(self.current_input)} ({len(self.current_input)} digits)")
            else:
                print("⌫ Nothing to delete")
                
        elif key == 'C':
            # C = Clear entire input
            self.current_input = ""
            print("🗑 Input cleared")
            
        elif key == 'D':
            # D = Doorbell/AI interaction (start only)
            print("🔔 Doorbell pressed - Starting AI interaction")
            self.log_event("doorbell", "pressed", "AI interaction requested")
            self.start_ai_interaction()
            
        elif key == '#':
            # # = Stop AI interaction (dedicated off toggle)
            print("🔇 Stop key pressed")
            self.stop_ai_interaction()
            
        elif key in '0123456789':
            # Add digit to current input
            self.current_input += key
            print(f"🔢 Current input: {'*' * len(self.current_input)} ({len(self.current_input)} digits)")
            
        elif key == '*':
            # * = Can be used in passcode
            self.current_input += key
            print(f"🔢 Current input: {'*' * len(self.current_input)} ({len(self.current_input)} digits)")
            
        else:
            print(f"❓ Unknown key: {key}")
    
    def check_passcode(self):
        """Check if the entered passcode is correct"""
        if not self.current_input:
            print("❌ No passcode entered")
            return
            
        print(f"🔍 Checking passcode: {'*' * len(self.current_input)}")
        
        if self.is_locked_out:
            if self.current_input == self.lockout_passcode:
                print("🔓 Lockout override successful!")
                self.is_locked_out = False
                self.failed_attempts = 0
                self.log_event("passcode", "lockout_override")
            else:
                print("🔒 System is locked out. Use override code.")
                self.log_event("passcode", "lockout_attempt")
            return
        
        if self.current_input == self.system_passcode:
            print("✅ Passcode correct! Unlocking door...")
            self.unlock_door()
            self.failed_attempts = 0
            self.log_event("passcode", "success")
        else:
            print("❌ Incorrect passcode")
            self.failed_attempts += 1
            self.log_event("passcode", "failed")
            
            print(f"⚠ Failed attempts: {self.failed_attempts}/{self.max_trials}")
            
            if self.failed_attempts >= self.max_trials:
                print(f"🚫 Too many failed attempts! System locked out.")
                print(f"🔑 Use override code: {self.lockout_passcode}")
                self.is_locked_out = True
                self.log_event("system", "lockout")
    
    def unlock_door(self):
        """Unlock the door for the configured auto-lock delay"""
        try:
            # Get the current settings
            self.update_settings()
            
            # Get auto_lock_delay from settings
            auto_lock_delay = self.settings.get("auto_lock_delay", 5)
            
            # Activate relay to unlock door
            self.GPIO.output(self.DOOR_RELAY_PIN, self.GPIO.HIGH)
            print("🚪 Door UNLOCKED!")
            self.log_event("door", "unlock")
            
            print(f"⏰ Door will auto-lock in {auto_lock_delay} seconds...")
            
            # Auto-lock after delay
            def auto_lock():
                time.sleep(auto_lock_delay)
                self.GPIO.output(self.DOOR_RELAY_PIN, self.GPIO.LOW)
                print("🔒 Door AUTO-LOCKED!")
                self.log_event("door", "lock", "Auto-lock")
            
            # Run auto-lock in separate thread so keypad remains responsive
            threading.Thread(target=auto_lock, daemon=True).start()
            
        except Exception as e:
            print(f"✗ Error unlocking door: {e}")
    
    def log_event(self, action, status, details=None):
        """Log an event to the web app"""
        if not self.api_available:
            print(f"📝 Log (offline): {action} - {status}")
            return
            
        try:
            data = {
                "action": action,
                "status": status,
                "user": "keypad",
                "details": details if details else ""
            }
            
            response = requests.post(f"{self.API_URL}/log", json=data, timeout=5)
            if response.status_code == 200:
                print(f"📝 Event logged: {action} - {status}")
            else:
                print(f"⚠ Failed to log event: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠ Error logging event: {e}")

    def start_ai_interaction(self):
        """Start AI interaction when doorbell is pressed"""
        try:
            if not hasattr(self, 'ai_active'):
                self.ai_active = False

            if not self.ai_active:
                print("🔔 Doorbell pressed - Starting Ultra-Reliable AI interaction...")
                self.ai_active = True
        
                # Start ultra-reliable AI processing
                def ultra_ai_processing():
                    try:
                        # Import the ultra speech controller
                        global ultra_speech_controller
                        if ultra_speech_controller:
                            print("🤖 Starting ultra-reliable conversation...")
                            
                            # Run the conversation flow
                            conversation_result = ultra_speech_controller.run_doorbell_conversation()
                            
                            # Log the conversation to the main system
                            if conversation_result:
                                for entry in conversation_result:
                                    speaker = entry.get('speaker', 'unknown')
                                    text = entry.get('text', '')
                                    confidence = entry.get('confidence', 0)
                                    
                                    # Log to main system with detailed info
                                    details = f"Confidence: {confidence:.2f}" if confidence > 0 else ""
                                    add_log('ai_conversation', speaker.lower(), 'keypad', f"{text} ({details})")
                            
                            print("✅ Ultra-reliable AI conversation completed")
                        else:
                            # Fallback to simple AI
                            print("🤖 AI: Welcome! How can I help you today?")
                            print("🔊 Playing audio response...")
                            add_log('ai', 'interaction_started', 'keypad', 'Simple AI interaction (ultra-speech not available)')
                    
                    except Exception as e:
                        print(f"✗ Error in ultra AI processing: {e}")
                        add_log('ai', 'error', 'keypad', str(e))
            
                # Start background thread
                threading.Thread(target=ultra_ai_processing, daemon=True).start()
                add_log('ai', 'interaction_started', 'keypad', 'Ultra-reliable AI interaction started')
            
            else:
                print("🤖 AI interaction already active")
                print("🔇 Press # to stop AI interaction")
    
        except Exception as e:
            print(f"✗ Error in keypad AI interaction: {e}")
            add_log('ai', 'error', 'keypad', str(e))

    def stop_ai_interaction(self):
        """Stop AI interaction when # is pressed"""
        try:
            if not hasattr(self, 'ai_active'):
                self.ai_active = False
    
            if self.ai_active:
                print("🔇 Stop key pressed - Stopping ultra-reliable AI interaction...")
                self.ai_active = False
            
                # Stop ultra speech controller if active
                global ultra_speech_controller
                if ultra_speech_controller:
                    ultra_speech_controller.stop_conversation()
                    print("🤖 Ultra-reliable AI conversation stopped")
            
                print("🔊 Audio stopped")
                add_log('ai', 'interaction_stopped', 'keypad', 'Ultra-reliable AI interaction stopped via # key')
            else:
                print("🤖 AI interaction not active")
        
        except Exception as e:
            print(f"✗ Error stopping AI interaction: {e}")
            add_log('ai', 'error', 'keypad', str(e))
    
    def update_settings(self):
        """Update settings from the web app"""
        if not self.api_available:
            return
            
        try:
            response = requests.get(f"{self.API_URL}/settings", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.settings = data.get("settings", {})
            
            # Update local settings
            old_passcode = self.system_passcode
            self.system_passcode = self.settings.get("system_passcode", self.system_passcode)
            self.max_trials = self.settings.get("max_trials", self.max_trials)
            self.lockout_passcode = self.settings.get("lockout_passcode", self.lockout_passcode)
            
            # Update keypad timeout
            self.input_timeout = self.settings.get("keypad_timeout", 30)
            
            # Check if keypad should be enabled/disabled
            keypad_enabled = self.settings.get("keypad_enabled", True)
            if not keypad_enabled and self.running:
                print("⚠ Keypad disabled via settings")
                return False  # Signal to stop keypad
            
            if old_passcode != self.system_passcode:
                print(f"🔄 System passcode updated")
                
            print("⚙ Settings updated from server")
            return True
        else:
            print(f"⚠ Failed to update settings: HTTP {response.status_code}")
            return True
        except Exception as e:
            print(f"⚠ Error updating settings: {e}")
            return True

    def run(self):
        """Main loop to continuously scan the keypad"""
        print("=" * 50)
        print("🚀 Keypad Controller Starting...")
        print("=" * 50)
        print("📋 Key Functions:")
        print("   0-9: Enter digits")
        print("   A:   Submit passcode")
        print("   B:   Backspace")
        print("   C:   Clear all")
        print("   D:   Start Doorbell/AI")
        print("   #:   Stop AI interaction")
        print("   *:   Can be used in passcode")
        print("=" * 50)
        print("🎯 Ready! Press keys on the 4x4 keypad...")
        print("   Press Ctrl+C to exit")
        print("=" * 50)
        
        self.running = True
        
        try:
            # Update settings on startup
            self.update_settings()
            
            # Start the keypad scanning loop in a separate thread
            self._run_loop()
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        except Exception as e:
            print(f"✗ Runtime error: {e}")
        finally:
            self.cleanup()

    def _run_loop(self):
        """Main keypad scanning loop"""
        print("🎯 Keypad controller ready - scanning for key presses...")
        
        settings_update_interval = 10  # Update settings every 10 seconds
        last_settings_update = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                # Check for input timeout
                if self.current_input and (current_time - self.last_input_time) > self.input_timeout:
                    print(f"⏰ Input timeout ({self.input_timeout}s) - clearing input")
                    self.current_input = ""
                
                # Update settings periodically
                if current_time - last_settings_update > settings_update_interval:
                    if not self.update_settings():
                        break  # Keypad disabled via settings
                    last_settings_update = current_time
                
                key = self.scan_keypad()
                if key:
                    self.last_input_time = current_time  # Update input time
                    self.process_key(key)
                    time.sleep(self.debounce_delay)
                
                time.sleep(0.05)  # 50ms scan interval
                
        except Exception as e:
            print(f"✗ Keypad controller error: {e}")
        finally:
            print("🛑 Keypad controller loop ended")

    def cleanup(self):
        """Cleanup GPIO and resources"""
        self.running = False
        if self.gpio_available:
            try:
                # Ensure door is locked on exit
                self.GPIO.output(self.DOOR_RELAY_PIN, self.GPIO.LOW)
                self.GPIO.cleanup()
                print("✓ GPIO cleaned up")
            except:
                pass
        print("👋 Keypad controller stopped")

    def test_keypad(self):
        """Test function to verify keypad is working"""
        print("🧪 Testing keypad - press any key (Ctrl+C to stop)...")
        
        try:
            while True:
                key = self.scan_keypad()
                if key:
                    print(f"✓ Key detected: {key}")
                    time.sleep(0.5)  # Longer delay for testing
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n✓ Keypad test completed")

if __name__ == "__main__":
    controller = KeypadController()
    
    # Uncomment the next line to run keypad test instead of full controller
    # controller.test_keypad()
    
    controller.run()
