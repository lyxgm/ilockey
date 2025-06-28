#!/usr/bin/env python3
"""
Smart Door Lock Web Application
A comprehensive web-based door lock system with camera integration,
user management, and activity logging.
"""

import os
import json
import hashlib
import datetime
import threading
import time
import subprocess
import io
import base64
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, send_from_directory
import queue

# Import fingerprint controller
try:
    from scripts.fingerprint_controller import FingerprintController
    FINGERPRINT_AVAILABLE = True
except ImportError:
    print("⚠️ Fingerprint controller not available")
    FINGERPRINT_AVAILABLE = False

# Import ultra-reliable speech recognition
try:
    from scripts.ultra_reliable_speech_controller import UltraReliableSpeechController
    ULTRA_SPEECH_AVAILABLE = True
except ImportError:
    print("⚠️ Ultra-reliable speech controller not available")
    ULTRA_SPEECH_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Global variables
users_data = {}
settings_data = {}
logs_data = []
notifications_data = []
door_locked = True
camera_enabled = False
camera_handler = None
door_controller = None
keypad_controller = None
fingerprint_controller = None
ultra_speech_controller = None

# File paths
USERS_FILE = 'data/users.json'
SETTINGS_FILE = 'data/settings.json'
LOGS_FILE = 'data/logs.json'
NOTIFICATIONS_FILE = 'data/notifications.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)
os.makedirs('static/captures', exist_ok=True)
os.makedirs('static/test', exist_ok=True)

def load_data():
    """Load all data files"""
    global users_data, settings_data, logs_data, notifications_data
    
    # Load users
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
        else:
            # Create default admin user
            users_data = {
                'admin': {
                    'password': hashlib.sha256('admin123'.encode()).hexdigest(),
                    'name': 'Administrator',
                    'email': 'admin@localhost',
                    'role': 'admin',
                    'permissions': ['unlock', 'view_logs', 'manage_users', 'change_settings'],
                    'approved': True,
                    'access_type': 'full',
                    'fingerprint_enrolled': False
                }
            }
            save_users()
    except Exception as e:
        print(f"Error loading users: {e}")
        users_data = {}
    
    # Load settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings_data = json.load(f)
        else:
            settings_data = {
                'system_passcode': '1234',
                'max_trials': 3,
                'lockout_passcode': '9999',
                'auto_lock_delay': 5,
                'camera_enabled': True,
                'keypad_enabled': True,
                'keypad_timeout': 30,
                'fingerprint_enabled': True,
                'fingerprint_timeout': 10
            }
            save_settings()
    except Exception as e:
        print(f"Error loading settings: {e}")
        settings_data = {}
    
    # Load logs
    try:
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, 'r') as f:
                logs_data = json.load(f)
        else:
            logs_data = []
    except Exception as e:
        print(f"Error loading logs: {e}")
        logs_data = []
    
    # Load notifications
    try:
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, 'r') as f:
                notifications_data = json.load(f)
        else:
            notifications_data = []
    except Exception as e:
        print(f"Error loading notifications: {e}")
        notifications_data = []

def save_users():
    """Save users data to file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

def save_settings():
    """Save settings data to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

def save_logs():
    """Save logs data to file"""
    try:
        with open(LOGS_FILE, 'w') as f:
            json.dump(logs_data, f, indent=2)
    except Exception as e:
        print(f"Error saving logs: {e}")

def save_notifications():
    """Save notifications data to file"""
    try:
        with open(NOTIFICATIONS_FILE, 'w') as f:
            json.dump(notifications_data, f, indent=2)
    except Exception as e:
        print(f"Error saving notifications: {e}")

def add_log(action, status, user='system', details=''):
    """Add a log entry"""
    global logs_data
    
    log_entry = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'status': status,
        'user': user,
        'details': details
    }
    
    logs_data.insert(0, log_entry)  # Insert at beginning for newest first
    
    # Keep only last 1000 logs
    if len(logs_data) > 1000:
        logs_data = logs_data[:1000]
    
    save_logs()
    
    # Add notification for important events
    if action in ['door', 'login', 'camera', 'fingerprint'] and status in ['unlock', 'failed', 'capture', 'success']:
        add_notification(f"{action.title()}: {status}", 'info')

def add_notification(message, type='info'):
    """Add a notification"""
    global notifications_data
    
    notification = {
        'message': message,
        'type': type,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    notifications_data.insert(0, notification)
    
    # Keep only last 50 notifications
    if len(notifications_data) > 50:
        notifications_data = notifications_data[:50]
    
    save_notifications()

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        
        username = session['username']
        user = users_data.get(username, {})
        
        if user.get('role') not in ['admin', 'administrator']:
            return jsonify({'success': False, 'message': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

class DoorController:
    """Mock door controller for demonstration"""
    
    def __init__(self):
        self.locked = True
        print("Door controller initialized (mock)")
    
    def unlock(self):
        """Unlock the door"""
        try:
            self.locked = False
            add_log('door', 'unlock', session.get('username', 'system'))
            print("Door unlocked")
            return True
        except Exception as e:
            print(f"Error unlocking door: {e}")
            return False
    
    def lock(self):
        """Lock the door"""
        try:
            self.locked = True
            add_log('door', 'lock', session.get('username', 'system'))
            print("Door locked")
            return True
        except Exception as e:
            print(f"Error locking door: {e}")
            return False
    
    def is_locked(self):
        """Check if door is locked"""
        return self.locked

class CameraHandler:
    """Camera handler with multiple backend support"""
    
    def __init__(self):
        self.enabled = False
        self.camera_type = None
        self.camera = None
        self.stream_active = False
        print("Initializing camera handler...")
        
        # Try to detect and initialize camera
        self._detect_camera()
    
    def _detect_camera(self):
        """Detect available camera backend"""
        try:
            # Try PiCamera2 first (recommended for Raspberry Pi)
            try:
                from picamera2 import Picamera2
                self.camera = Picamera2()
                self.camera_type = 'picamera2'
                print("PiCamera2 detected and initialized")
                return True
            except ImportError:
                print("PiCamera2 not available")
            except Exception as e:
                print(f"PiCamera2 initialization failed: {e}")
            
            # Try libcamera-still
            try:
                result = subprocess.run(['libcamera-hello', '--list-cameras'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and "Available cameras" in result.stdout:
                    self.camera_type = 'libcamera'
                    print("libcamera detected")
                    return True
            except Exception as e:
                print(f"libcamera detection failed: {e}")
            
            # Try OpenCV as fallback
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    cap.release()
                    self.camera_type = 'opencv'
                    print("OpenCV camera detected")
                    return True
            except Exception as e:
                print(f"OpenCV detection failed: {e}")
            
            print("No camera detected")
            return False
            
        except Exception as e:
            print(f"Camera detection error: {e}")
            return False
    
    def start_stream(self):
        """Start camera stream"""
        try:
            if not self.camera_type:
                return False
            
            if self.camera_type == 'picamera2':
                if not self.camera:
                    from picamera2 import Picamera2
                    self.camera = Picamera2()
                
                config = self.camera.create_preview_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                )
                self.camera.configure(config)
                self.camera.start()
                
            self.enabled = True
            self.stream_active = True
            add_log('camera', 'streaming_started', session.get('username', 'system'))
            print("Camera stream started")
            return True
            
        except Exception as e:
            print(f"Error starting camera stream: {e}")
            return False
    
    def stop_stream(self):
        """Stop camera stream"""
        try:
            if self.camera_type == 'picamera2' and self.camera:
                self.camera.stop()
            
            self.enabled = False
            self.stream_active = False
            add_log('camera', 'streaming_stopped', session.get('username', 'system'))
            print("Camera stream stopped")
            return True
            
        except Exception as e:
            print(f"Error stopping camera stream: {e}")
            return False
    
    def capture_image(self):
        """Capture an image"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            filepath = os.path.join('static/captures', filename)
            
            if self.camera_type == 'picamera2' and self.camera:
                self.camera.capture_file(filepath)
            elif self.camera_type == 'libcamera':
                subprocess.run(['libcamera-still', '-o', filepath, '--immediate'], 
                             timeout=10, check=True)
            elif self.camera_type == 'opencv':
                import cv2
                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite(filepath, frame)
                cap.release()
            else:
                # Create a placeholder image
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (640, 480), color='lightgray')
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
                
                text = f"Camera Placeholder\n{timestamp}"
                if font:
                    draw.text((320, 240), text, fill='black', font=font, anchor='mm')
                else:
                    draw.text((320, 240), text, fill='black', anchor='mm')
                
                img.save(filepath)
            
            add_log('camera', 'capture', session.get('username', 'system'), filename)
            print(f"Image captured: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None
    
    def get_stream_frame(self):
        """Get a frame for streaming"""
        try:
            if not self.stream_active:
                return None
            
            if self.camera_type == 'picamera2' and self.camera:
                # Capture frame as JPEG
                stream = io.BytesIO()
                self.camera.capture_file(stream, format='jpeg')
                stream.seek(0)
                return stream.read()
            elif self.camera_type == 'opencv':
                import cv2
                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                if ret:
                    _, buffer = cv2.imencode('.jpg', frame)
                    cap.release()
                    return buffer.tobytes()
                cap.release()
            
            return None
            
        except Exception as e:
            print(f"Error getting stream frame: {e}")
            return None
    
    def generate_stream(self):
        """Generate MJPEG stream"""
        while self.stream_active:
            try:
                frame = self.get_stream_frame()
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    # Send placeholder frame
                    placeholder = self._create_placeholder_frame()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
                
                time.sleep(0.1)  # 10 FPS
                
            except Exception as e:
                print(f"Stream generation error: {e}")
                break
    
    def _create_placeholder_frame(self):
        """Create a placeholder frame"""
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (640, 480), color='darkgray')
            draw = ImageDraw.Draw(img)
            draw.text((320, 240), "Camera Not Available", fill='white', anchor='mm')
            
            stream = io.BytesIO()
            img.save(stream, format='JPEG')
            return stream.getvalue()
        except:
            # Return minimal JPEG if PIL fails
            return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x01\xe0\x02\x80\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'

class KeypadController:
    """Integrated keypad controller for the smart door lock system"""
    
    def __init__(self, app_instance=None):
        self.app = app_instance
        self.gpio_available = False
        self.running = False
        self.thread = None
        self.command_queue = queue.Queue()
        
        # AI Integration
        self.ai_active = False
        self.conversation_log = []
        self.speech_engines = {}
        self.init_ai_engines()  # Add this line
        
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.gpio_available = True
            
            # Set up GPIO with proper cleanup
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Updated GPIO configuration for rows
            self.ROWS = [18, 23, 24, 25]   # GPIO pins for rows (outputs)
            self.COLS = [4, 17, 27, 22]  # GPIO pins for columns (inputs)
            
            # Standard 4x4 keypad layout
            self.KEYS = [
                ['1', '2', '3', 'A'],
                ['4', '5', '6', 'B'], 
                ['7', '8', '9', 'C'],
                ['*', '0', '#', 'D']
            ]
            
            # Setup GPIO pins
            self._setup_gpio_pins()
            print("✓ Keypad GPIO initialized successfully")
            
        except ImportError:
            print("⚠ RPi.GPIO not available - keypad running in simulation mode")
            self._setup_mock_gpio()
        except Exception as e:
            print(f"⚠ Keypad GPIO setup error: {e} - running in simulation mode")
            self._setup_mock_gpio()
        
        # Initialize keypad state
        self._init_keypad_state()

    def _setup_gpio_pins(self):
        """Setup GPIO pins for keypad"""
        try:
            # Set up row pins as outputs with initial HIGH state
            for row_pin in self.ROWS:
                self.GPIO.setup(row_pin, self.GPIO.OUT)
                self.GPIO.output(row_pin, self.GPIO.HIGH)
            
            # Set up column pins as inputs with pull-up resistors
            for col_pin in self.COLS:
                self.GPIO.setup(col_pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
                
        except Exception as e:
            print(f"✗ Error setting up keypad GPIO pins: {e}")
            raise

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
            
            def __init__(self):
                self.pin_states = {}
            
            def setmode(self, mode): pass
            def setwarnings(self, enabled): pass
            def cleanup(self): pass
            
            def setup(self, pin, mode, **kwargs):
                if mode == self.OUT:
                    self.pin_states[pin] = self.HIGH
                else:
                    self.pin_states[pin] = self.HIGH
            
            def output(self, pin, value):
                self.pin_states[pin] = value
            
            def input(self, pin):
                return self.pin_states.get(pin, self.HIGH)
        
        self.GPIO = MockGPIO()
        self.ROWS = [18, 23, 24, 25]
        self.COLS = [4, 17, 27, 22]
        
        self.KEYS = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ]

    def _init_keypad_state(self):
        """Initialize keypad state variables"""
        self.current_input = ""
        self.failed_attempts = 0
        self.is_locked_out = False
        self.last_key_time = 0
        self.last_input_time = 0
        self.input_timeout = 30
        self.debounce_delay = 0.3
        self.ai_active = False

    def scan_keypad(self):
        """Scan the keypad for pressed keys"""
        try:
            for row_num, row_pin in enumerate(self.ROWS):
                self.GPIO.output(row_pin, self.GPIO.LOW)
                time.sleep(0.001)
                
                for col_num, col_pin in enumerate(self.COLS):
                    if self.GPIO.input(col_pin) == self.GPIO.LOW:
                        key = self.KEYS[row_num][col_num]
                        self.GPIO.output(row_pin, self.GPIO.HIGH)
                        
                        for other_row in self.ROWS:
                            self.GPIO.output(other_row, self.GPIO.HIGH)
                        
                        return key
                
                self.GPIO.output(row_pin, self.GPIO.HIGH)
            
            return None
            
        except Exception as e:
            print(f"✗ Error scanning keypad: {e}")
            return None

    def process_key(self, key):
        """Process a key press"""
        if key is None:
            return
        
        # Debounce check
        current_time = time.time()
        if current_time - self.last_key_time < self.debounce_delay:
            return
        
        self.last_key_time = current_time
        self.last_input_time = current_time  # Update input time
        
        print(f"🔑 Keypad key pressed: {key}")
        
        if key == 'A':
            # A = Submit passcode
            print("📝 Submitting passcode...")
            self.check_passcode()
            self.current_input = ""
        
        elif key == 'B':
            # B = Backspace
            if self.current_input:
                self.current_input = self.current_input[:-1]
                print(f"⌫ Keypad input: {'*' * len(self.current_input)}")
            
        elif key == 'C':
            # C = Clear entire input
            self.current_input = ""
            print("🗑 Keypad input cleared")
        
        elif key == 'D':
            # D = Start Doorbell/AI interaction
            self.start_ai_interaction()
        
        elif key == '#':
            # # = Stop AI interaction (dedicated off toggle)
            self.stop_ai_interaction()
        
        elif key in '0123456789*':
            # Add digit or * to current input
            self.current_input += key
            print(f"🔢 Keypad input: {'*' * len(self.current_input)}")

    def check_passcode(self):
        """Check if the entered passcode is correct"""
        global door_controller, door_locked
        
        if not self.current_input:
            print("❌ No passcode entered on keypad")
            return
            
        print(f"🔍 Checking keypad passcode: {'*' * len(self.current_input)}")
        
        # Get current settings from global settings_data
        system_passcode = settings_data.get('system_passcode', '1234')
        lockout_passcode = settings_data.get('lockout_passcode', '9999')
        max_trials = settings_data.get('max_trials', 3)
        
        if self.is_locked_out:
            if self.current_input == lockout_passcode:
                print("🔓 Keypad lockout override successful!")
                self.is_locked_out = False
                self.failed_attempts = 0
                add_log('passcode', 'lockout_override', 'keypad')
            else:
                print("🔒 Keypad system is locked out. Use override code.")
                add_log('passcode', 'lockout_attempt', 'keypad')
            return
        
        if self.current_input == system_passcode:
            print("✅ Keypad passcode correct! Unlocking door...")
            self.unlock_door_via_keypad()
            self.failed_attempts = 0
            add_log('passcode', 'success', 'keypad')
        else:
            print("❌ Incorrect keypad passcode")
            self.failed_attempts += 1
            add_log('passcode', 'failed', 'keypad')
        
        print(f"⚠ Keypad failed attempts: {self.failed_attempts}/{max_trials}")
        
        if self.failed_attempts >= max_trials:
            print(f"🚫 Too many keypad failed attempts! System locked out.")
            self.is_locked_out = True
            add_log('system', 'lockout', 'keypad')

    def unlock_door_via_keypad(self):
        """Unlock the door via keypad"""
        global door_controller, door_locked
        
        try:
            # Get current auto-lock delay from settings
            auto_lock_delay = settings_data.get('auto_lock_delay', 5)
        
            # Mock implementation without Flask context
            door_locked = False
            add_log('door', 'unlock', 'keypad')
        
            print("🚪 Door UNLOCKED via keypad!")
            print(f"⏰ Door will auto-lock in {auto_lock_delay} seconds...")
        
            # Auto-lock after delay
            def auto_lock():
                time.sleep(auto_lock_delay)
                global door_locked
                add_log('door', 'lock', 'keypad', 'Auto-lock')
                door_locked = True
                print("🔒 Door AUTO-LOCKED!")
        
            threading.Thread(target=auto_lock, daemon=True).start()
        
        except Exception as e:
            print(f"✗ Error unlocking door via keypad: {e}")

    def init_ai_engines(self):
        """Initialize AI speech engines for keypad integration"""
        print("🤖 Initializing AI engines for keypad...")
        
        # Setup Vosk
        try:
            import vosk
            from pathlib import Path
            model_paths = [
                Path.home() / "vosk-models" / "vosk-model-small-en-us-0.15",
                Path.home() / "vosk-models" / "vosk-model-en-us-0.22",
            ]
            
            for path in model_paths:
                if path.exists():
                    self.speech_engines['vosk'] = {
                        'model': vosk.Model(str(path)),
                        'recognizer': vosk.KaldiRecognizer(vosk.Model(str(path)), 16000),
                        'available': True
                    }
                    print("✅ Vosk engine loaded for keypad")
                    break
        except:
            self.speech_engines['vosk'] = {'available': False}
        
        # Setup Google Speech
        try:
            import speech_recognition as sr
            self.speech_engines['google'] = {
                'recognizer': sr.Recognizer(),
                'microphone': sr.Microphone(),
                'available': True
            }
            print("✅ Google Speech Recognition loaded for keypad")
        except:
            self.speech_engines['google'] = {'available': False}
        
        # Setup Whisper
        try:
            import whisper
            self.speech_engines['whisper'] = {
                'model': whisper.load_model("base"),
                'available': True
            }
            print("✅ Whisper engine loaded for keypad")
        except:
            self.speech_engines['whisper'] = {'available': False}

    

    def start_ai_interaction(self):
    """Start AI interaction when D key is pressed"""
    try:
        if self.ai_active:
            print("🤖 AI conversation already active")
            return
        
        print("🔔 D KEY PRESSED - Starting integrated AI conversation...")
        self.ai_active = True
        self.conversation_log = []

        # Log the start
        add_log('ai', 'interaction_started', 'keypad', 'D key pressed - AI conversation started')

        def ai_conversation_thread():
            try:
                # Step 1: Greet visitor and ask for name
                self.speak_to_visitor("Hello! Welcome to our smart door system. May I please have your name?")

                if not self.ai_active:
                    return

                # Step 2: Listen for visitor's name
                audio_file = self.record_visitor_audio(8)
                visitor_name = "Unknown Visitor"

                if audio_file and self.ai_active:
                    # Transcribe name
                    name_text, name_confidence = self.transcribe_visitor_audio(audio_file)

                    # Clean up audio file
                    try:
                        os.remove(audio_file)
                    except:
                        pass

                    if name_text and name_confidence > 0.4:
                        visitor_name = name_text.strip()
                        print(f"👤 VISITOR NAME: '{visitor_name}' (confidence: {name_confidence:.2f})")

                        # Log visitor name with full details
                        name_details = f"Name: {visitor_name} | Confidence: {name_confidence:.2f}"
                        add_log('ai_conversation', 'visitor_name', 'keypad', name_details)

                        if self.ai_active:
                            self.speak_to_visitor(f"Nice to meet you, {visitor_name}. What is the purpose of your visit today?")
                    else:
                        print("⚠️ Could not understand visitor's name")
                        if self.ai_active:
                            self.speak_to_visitor("I didn't catch your name clearly, but that's okay. What is the purpose of your visit today?")
                        add_log('ai_conversation', 'name_unclear', 'keypad', f"Name transcription failed | Confidence: {name_confidence:.2f}")
                else:
                    print("⚠️ No audio recorded for name")
                    if self.ai_active:
                        self.speak_to_visitor("I didn't hear your name, but that's fine. What is the purpose of your visit today?")
                    add_log('ai_conversation', 'name_no_audio', 'keypad', 'No audio recorded for name')

                if not self.ai_active:
                    return

                # Step 3: Listen for purpose of visit
                audio_file2 = self.record_visitor_audio(10)  # Longer time for purpose explanation

                if audio_file2 and self.ai_active:
                    # Transcribe purpose
                    purpose_text, purpose_confidence = self.transcribe_visitor_audio(audio_file2)

                    # Clean up audio file
                    try:
                        os.remove(audio_file2)
                    except:
                        pass

                    if purpose_text and purpose_confidence > 0.4:
                        print(f"👤 VISIT PURPOSE: '{purpose_text}' (confidence: {purpose_confidence:.2f})")

                        # Log purpose with full details
                        purpose_details = f"Purpose: {purpose_text} | Confidence: {purpose_confidence:.2f} | Visitor: {visitor_name}"
                        add_log('ai_conversation', 'visit_purpose', 'keypad', purpose_details)

                        if self.ai_active:
                            # Analyze intent and respond
                            intent = self.analyze_visitor_intent(purpose_text)
                            response = self.generate_smart_response(purpose_text, intent, visitor_name)

                            print(f"🧠 Intent: {intent}")
                            add_log('ai_conversation', 'intent_detected', 'keypad', f"Intent: {intent} | Visitor: {visitor_name}")

                            self.speak_to_visitor(response)

                            # Log the complete interaction summary
                            summary = f"Visitor: {visitor_name} | Purpose: {purpose_text} | Intent: {intent}"
                            add_log('ai_conversation', 'interaction_summary', 'keypad', summary)
                    else:
                        print("⚠️ Could not understand purpose of visit")
                        if self.ai_active:
                            self.speak_to_visitor(f"I didn't catch the purpose clearly, {visitor_name}, but I've notified the residents of your visit.")
                        purpose_details = f"Purpose unclear | Confidence: {purpose_confidence:.2f} | Visitor: {visitor_name}"
                        add_log('ai_conversation', 'purpose_unclear', 'keypad', purpose_details)
                else:
                    print("⚠️ No audio recorded for purpose")
                    if self.ai_active:
                        self.speak_to_visitor(f"I didn't hear the purpose, {visitor_name}, but I've notified the residents.")
                    add_log('ai_conversation', 'purpose_no_audio', 'keypad', f'No audio for purpose | Visitor: {visitor_name}')

                # Step 4: Final message
                if self.ai_active:
                    self.speak_to_visitor(f"Thank you, {visitor_name}! The residents have been notified. Have a great day!")

                print("✅ AI conversation completed")
                add_log('ai_conversation', 'completed', 'keypad', f'Conversation completed with {visitor_name}')

            except Exception as e:
                print(f"❌ AI conversation error: {e}")
                add_log('ai', 'error', 'keypad', f'Conversation error: {str(e)}')
            finally:
                self.ai_active = False
                add_log('ai', 'interaction_ended', 'keypad', 'AI conversation session ended')

        # Start conversation in background thread
        threading.Thread(target=ai_conversation_thread, daemon=True).start()

    except Exception as e:
        print(f"✖ Error starting AI interaction: {e}")
        add_log('ai', 'error', 'keypad', str(e))








    def stop_ai_interaction(self):
        """Stop AI interaction when # key is pressed"""
        try:
            if self.ai_active:
                print("🔇 # KEY PRESSED - Stopping AI conversation...")
                self.ai_active = False
                add_log('ai', 'interaction_stopped', 'keypad', '# key pressed - AI conversation stopped')
                print("✅ AI conversation stopped")
            else:
                print("🤖 No AI conversation active")
        except Exception as e:
            print(f"✗ Error stopping AI interaction: {e}")
            add_log('ai', 'error', 'keypad', str(e))

    def speak_to_visitor(self, text):
        """Speak to visitor using TTS"""
        print(f"🤖 AI SAYS: {text}")
        
        # Log AI speech
        add_log('ai_conversation', 'ai_speech', 'keypad', text)
        
        # Use espeak for TTS
        try:
            subprocess.run([
                'espeak', '-s', '140', '-a', '200', '-v', 'en+f3', text
            ], timeout=10)
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
        
        time.sleep(1)

    def record_visitor_audio(self, duration=6):
        """Record visitor audio"""
        timestamp = int(time.time())
        filename = f"/tmp/visitor_audio_{timestamp}.wav"
        
        try:
            print(f"🎤 Recording visitor for {duration} seconds...")
            
            cmd = [
                'arecord',
                '-D', 'plughw:3,0',  # USB audio device
                '-f', 'S16_LE',
                '-r', '16000',
                '-c', '1',
                '-d', str(duration),
                filename
            ]
            
            subprocess.run(cmd, timeout=duration + 2)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                return filename
        
        except Exception as e:
            print(f"⚠️ Recording error: {e}")
        
        return None

    def transcribe_visitor_audio(self, audio_file):
        """Transcribe visitor audio using multiple engines"""
        print("🔄 Transcribing visitor audio...")
        
        best_result = None
        best_confidence = 0
        
        # Try Whisper first
        if self.speech_engines.get('whisper', {}).get('available'):
            try:
                model = self.speech_engines['whisper']['model']
                result = model.transcribe(audio_file, language='en')
                text = result.get('text', '').strip()
                if text:
                    confidence = 0.9
                    if confidence > best_confidence:
                        best_result = text
                        best_confidence = confidence
                    print(f"✅ WHISPER: '{text}' (confidence: {confidence})")
            except Exception as e:
                print(f"⚠️ Whisper failed: {e}")
        
        # Try Google as backup
        if self.speech_engines.get('google', {}).get('available'):
            try:
                import speech_recognition as sr
                recognizer = self.speech_engines['google']['recognizer']
            
                with sr.AudioFile(audio_file) as source:
                    audio = recognizer.record(source)
            
                text = recognizer.recognize_google(audio)
                if text:
                    confidence = 0.85
                    if confidence > best_confidence:
                        best_result = text
                        best_confidence = confidence
                    print(f"✅ GOOGLE: '{text}' (confidence: {confidence})")
            except Exception as e:
                print(f"⚠️ Google failed: {e}")
        
        # Try Vosk as final backup
        if self.speech_engines.get('vosk', {}).get('available'):
            try:
                import json
                import wave
                recognizer = self.speech_engines['vosk']['recognizer']
                wf = wave.open(audio_file, 'rb')
            
                text_parts = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        if result.get('text'):
                            text_parts.append(result['text'])
            
                final_result = json.loads(recognizer.FinalResult())
                if final_result.get('text'):
                    text_parts.append(final_result['text'])
            
                if text_parts:
                    text = ' '.join(text_parts).strip()
                    confidence = 0.7
                    if confidence > best_confidence:
                        best_result = text
                        best_confidence = confidence
                    print(f"✅ VOSK: '{text}' (confidence: {confidence})")
            
                wf.close()
            except Exception as e:
                print(f"⚠️ Vosk failed: {e}")
        
        return best_result, best_confidence

    def analyze_visitor_intent(self, text):
        """Analyze visitor intent from speech"""
        if not text:
            return 'unknown'
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['delivery', 'package', 'mail', 'amazon', 'ups', 'fedex', 'dhl']):
            return 'delivery'
        elif any(word in text_lower for word in ['visit', 'see', 'looking for', 'here for', 'friend', 'family']):
            return 'visit'
        elif any(word in text_lower for word in ['repair', 'maintenance', 'service', 'technician']):
            return 'service'
        elif any(word in text_lower for word in ['emergency', 'urgent', 'help', 'police', 'fire']):
            return 'emergency'
        elif any(word in text_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return 'greeting'
        else:
            return 'general'

    def generate_smart_response(self, visitor_text, intent, visitor_name=""):
        """Generate smart response based on visitor intent and name"""
        name_part = f", {visitor_name}" if visitor_name and visitor_name != "Unknown Visitor" else ""
        
        responses = {
            'delivery': f"Thank you{name_part}. I understand you have a delivery. I'm notifying the residents immediately and they'll be with you shortly.",
            'visit': f"Thank you{name_part}. I've noted that you're here for a visit. I'm alerting the residents now.",
            'service': f"Thank you{name_part}. I see you're here for service work. I'm notifying the homeowner immediately.",
            'emergency': f"I understand this is urgent{name_part}. I'm immediately contacting the residents about this matter.",
            'greeting': f"Hello{name_part}! Thank you for visiting. I'm processing your visit information now.",
            'general': f"Thank you{name_part}. I've recorded your visit details and I'm notifying the residents now."
        }
        
        return responses.get(intent, responses['general'])

    def show_system_status(self):
        """Show system status via keypad special function"""
        global door_locked, camera_handler
        
        door_status = "LOCKED" if door_locked else "UNLOCKED"
        camera_status = "ON" if (camera_handler and camera_handler.enabled) else "OFF"
        
        print(f"📊 System Status - Door: {door_status}, Camera: {camera_status}")
        add_log('system', 'status_check', 'keypad', f'Door: {door_status}, Camera: {camera_status}')

    def start(self):
        """Start the keypad controller in a separate thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("✓ Keypad controller started")

    def stop(self):
        """Stop the keypad controller"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        
        if self.gpio_available:
            try:
                self.GPIO.cleanup()
            except:
                pass
        
        print("✓ Keypad controller stopped")

    def _run_loop(self):
        """Main keypad scanning loop"""
        print("🎯 Keypad controller ready - scanning for key presses...")
        
        settings_update_interval = 5  # Check settings every 5 seconds
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
                    # Check if keypad is disabled
                    if not settings_data.get('keypad_enabled', True):
                        print("⚠ Keypad disabled via settings - stopping gracefully")
                        break
                
                    # Update timeout from settings
                    new_timeout = settings_data.get('keypad_timeout', 30)
                    if new_timeout != self.input_timeout:
                        print(f"⚙ Updated keypad timeout: {self.input_timeout}s -> {new_timeout}s")
                        self.input_timeout = new_timeout
                
                    last_settings_update = current_time
        
                key = self.scan_keypad()
                if key:
                    self.last_input_time = current_time
                    self.process_key(key)
                    time.sleep(self.debounce_delay)
        
                time.sleep(0.05)  # 50ms scan interval
        
        except Exception as e:
            print(f"✗ Keypad controller error: {e}")
        finally:
            print("🛑 Keypad controller loop ended")
            self.running = False

# Routes
@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'})
        
        user = users_data.get(username)
        if not user:
            add_log('login', 'failed', username, 'User not found')
            return jsonify({'success': False, 'message': 'Invalid username or password'})
        
        # Check if user is approved
        if not user.get('approved', False):
            add_log('login', 'failed', username, 'User not approved')
            return jsonify({'success': False, 'message': 'Account pending approval'})
        
        # Check password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.get('password') != password_hash:
            add_log('login', 'failed', username, 'Wrong password')
            return jsonify({'success': False, 'message': 'Invalid username or password'})
        
        # Check access expiry
        if user.get('access_type') == 'limited' and user.get('access_until'):
            try:
                access_until = datetime.datetime.strptime(user['access_until'], '%Y-%m-%d')
                if datetime.datetime.now() > access_until:
                    add_log('login', 'failed', username, 'Access expired')
                    return jsonify({'success': False, 'message': 'Access has expired'})
            except:
                pass
        
        session['username'] = username
        add_log('login', 'success', username)
        return jsonify({'success': True})
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not all([username, name, email, password]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if username in users_data:
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Create new user
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        users_data[username] = {
            'password': password_hash,
            'name': name,
            'email': email,
            'role': 'guest',
            'permissions': ['unlock'],
            'approved': False,  # Requires admin approval
            'access_type': 'full',
            'fingerprint_enrolled': False
        }
        
        save_users()
        add_log('user', 'signup', username)
        add_notification(f'New user signup: {username}', 'info')
        
        return jsonify({'success': True, 'message': 'Account created successfully. Awaiting approval.'})
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout"""
    username = session.get('username', 'unknown')
    session.clear()
    add_log('logout', 'success', username)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/people')
@login_required
def people():
    """People management page"""
    return render_template('people.html', active_page='people')

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('settings.html', active_page='settings')

@app.route('/logs')
@login_required
def logs():
    """Logs page"""
    return render_template('logs.html', active_page='logs')

@app.route('/metrics')
@login_required
def metrics():
    """Metrics page"""
    return render_template('metrics.html', active_page='metrics')

@app.route('/guide')
@login_required
def guide():
    """User guide page"""
    return render_template('guide.html', active_page='guide')

@app.route('/profile')
@login_required
def profile():
    """Profile page"""
    return render_template('profile.html', active_page='profile')

# API Routes
@app.route('/api/door/status')
@login_required
def door_status():
    """Get door status"""
    global door_controller
    if door_controller:
        locked = door_controller.is_locked()
    else:
        locked = door_locked
    
    return jsonify({
        'success': True,
        'locked': locked
    })

@app.route('/api/door/toggle', methods=['POST'])
@login_required
def toggle_door():
    """Toggle door lock"""
    global door_controller, door_locked
    
    data = request.get_json()
    action = data.get('action')
    
    username = session.get('username')
    user = users_data.get(username, {})
    
    # Check permissions
    if 'unlock' not in user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    try:
        if door_controller:
            if action == 'unlock':
                success = door_controller.unlock()
                door_locked = False
            else:
                success = door_controller.lock()
                door_locked = True
        else:
            # Mock implementation
            if action == 'unlock':
                door_locked = False
                add_log('door', 'unlock', username)
            else:
                door_locked = True
                add_log('door', 'lock', username)
            success = True
        
        if success:
            return jsonify({
                'success': True,
                'locked': door_locked,
                'auto_lock': action == 'unlock'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to control door'})
            
    except Exception as e:
        print(f"Error toggling door: {e}")
        return jsonify({'success': False, 'message': 'Door control error'})

@app.route('/api/door/passcode', methods=['POST'])
def door_passcode():
    """Unlock door with passcode"""
    global door_controller, door_locked
    
    data = request.get_json()
    passcode = data.get('passcode', '').strip()
    
    if not passcode:
        return jsonify({'success': False, 'message': 'Passcode required'})
    
    # Check against system passcode
    if passcode == settings_data.get('system_passcode', '1234'):
        try:
            if door_controller:
                success = door_controller.unlock()
                door_locked = False
            else:
                door_locked = False
                add_log('door', 'unlock', 'passcode')
                success = True
            
            if success:
                return jsonify({'success': True, 'message': 'Door unlocked'})
            else:
                return jsonify({'success': False, 'message': 'Failed to unlock door'})
                
        except Exception as e:
            print(f"Error unlocking with passcode: {e}")
            return jsonify({'success': False, 'message': 'Door control error'})
    else:
        add_log('door', 'failed', 'passcode', 'Wrong passcode')
        return jsonify({'success': False, 'message': 'Invalid passcode'})

@app.route('/api/camera/status')
@login_required
def camera_status():
    """Get camera status"""
    global camera_handler
    
    if camera_handler:
        return jsonify({
            'success': True,
            'enabled': camera_handler.enabled,
            'type': camera_handler.camera_type,
            'streaming': camera_handler.stream_active
        })
    else:
        return jsonify({
            'success': True,
            'enabled': False,
            'type': 'none',
            'streaming': False
        })

@app.route('/api/camera/toggle', methods=['POST'])
@login_required
def toggle_camera():
    """Toggle camera stream"""
    global camera_handler
    
    data = request.get_json()
    action = data.get('action')
    
    if not camera_handler:
        return jsonify({'success': False, 'message': 'Camera not available'})
    
    try:
        if action == 'on':
            success = camera_handler.start_stream()
        else:
            success = camera_handler.stop_stream()
        
        return jsonify({'success': success})
        
    except Exception as e:
        print(f"Error toggling camera: {e}")
        return jsonify({'success': False, 'message': 'Camera control error'})

@app.route('/api/camera/stream')
@login_required
def camera_stream():
    """Camera MJPEG stream"""
    global camera_handler
    
    if camera_handler and camera_handler.stream_active:
        return Response(camera_handler.generate_stream(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        # Return placeholder stream
        def placeholder_stream():
            while True:
                try:
                    from PIL import Image, ImageDraw
                    img = Image.new('RGB', (640, 480), color='darkgray')
                    draw = ImageDraw.Draw(img)
                    draw.text((320, 240), "Camera Not Available", fill='white', anchor='mm')
                    
                    stream = io.BytesIO()
                    img.save(stream, format='JPEG')
                    frame = stream.getvalue()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    time.sleep(1)
                except:
                    break
        
        return Response(placeholder_stream(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/capture', methods=['POST'])
@login_required
def capture_image():
    """Capture an image"""
    global camera_handler
    
    if not camera_handler:
        return jsonify({'success': False, 'message': 'Camera not available'})
    
    try:
        filename = camera_handler.capture_image()
        if filename:
            return jsonify({'success': True, 'filename': filename})
        else:
            return jsonify({'success': False, 'message': 'Failed to capture image'})
            
    except Exception as e:
        print(f"Error capturing image: {e}")
        return jsonify({'success': False, 'message': 'Capture error'})

@app.route('/api/camera/gallery')
@login_required
def camera_gallery():
    """Get gallery images"""
    try:
        captures_dir = 'static/captures'
        if not os.path.exists(captures_dir):
            return jsonify({'success': True, 'images': []})
        
        images = []
        for filename in os.listdir(captures_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(filename)
        
        # Sort by filename (which includes timestamp)
        images.sort(reverse=True)
        
        # Limit results if requested
        limit = request.args.get('limit', type=int)
        if limit:
            images = images[:limit]
        
        return jsonify({'success': True, 'images': images})
        
    except Exception as e:
        print(f"Error getting gallery: {e}")
        return jsonify({'success': False, 'message': 'Gallery error'})

@app.route('/api/camera/delete', methods=['POST'])
@login_required
def delete_image():
    """Delete an image"""
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'message': 'Filename required'})
    
    try:
        filepath = os.path.join('static/captures', filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            add_log('camera', 'delete', session.get('username'), filename)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'File not found'})
            
    except Exception as e:
        print(f"Error deleting image: {e}")
        return jsonify({'success': False, 'message': 'Delete error'})

@app.route('/api/users')
@login_required
def get_users():
    """Get all users"""
    username = session.get('username')
    user = users_data.get(username, {})
    
    # Check permissions
    if 'manage_users' not in user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    # Remove passwords from response
    safe_users = {}
    for uname, udata in users_data.items():
        safe_users[uname] = {k: v for k, v in udata.items() if k != 'password'}
    
    return jsonify({'success': True, 'users': safe_users})

@app.route('/api/users/<username>', methods=['PUT'])
@login_required
def update_user(username):
    """Update user"""
    current_username = session.get('username')
    current_user = users_data.get(current_username, {})
    
    # Check permissions
    if 'manage_users' not in current_user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    if username not in users_data:
        return jsonify({'success': False, 'message': 'User not found'})
    
    data = request.get_json()
    user = users_data[username]
    
    # Update allowed fields
    if 'approved' in data:
        user['approved'] = bool(data['approved'])
    if 'role' in data:
        user['role'] = data['role']
    if 'permissions' in data:
        user['permissions'] = data['permissions']
    if 'access_type' in data:
        user['access_type'] = data['access_type']
    if 'access_until' in data:
        user['access_until'] = data['access_until']
    
    save_users()
    add_log('user', 'updated', current_username, f'Updated user: {username}')
    
    return jsonify({'success': True})

@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def delete_user(username):
    """Delete user"""
    current_username = session.get('username')
    current_user = users_data.get(current_username, {})
    
    # Check permissions
    if 'manage_users' not in current_user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    if username not in users_data:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Don't allow deleting yourself
    if username == current_username:
        return jsonify({'success': False, 'message': 'Cannot delete yourself'})
    
    del users_data[username]
    save_users()
    add_log('user', 'deleted', current_username, f'Deleted user: {username}')
    
    return jsonify({'success': True})

@app.route('/api/settings')
@login_required
def get_settings():
    """Get settings"""
    return jsonify({'success': True, 'settings': settings_data})

@app.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    """Update settings"""
    username = session.get('username')
    user = users_data.get(username, {})
    
    # Check permissions
    if 'change_settings' not in user.get('permissions', []) and user.get('role') not in ['admin', 'administrator']:
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    data = request.get_json()
    
    # Update settings
    for key, value in data.items():
        if key in ['system_passcode', 'max_trials', 'lockout_passcode', 
                  'auto_lock_delay', 'camera_enabled', 'keypad_enabled', 'keypad_timeout']:
            settings_data[key] = value
    
    save_settings()
    add_log('settings', 'updated', username)
    
    # Apply settings to system components
    try:
        # Update keypad controller settings if it exists
        global keypad_controller
        if keypad_controller:
            keypad_controller.input_timeout = settings_data.get('keypad_timeout', 30)
            
            # If keypad is disabled, we don't stop it immediately to avoid issues
            # It will check the setting in its loop and stop gracefully
            if not settings_data.get('keypad_enabled', True):
                print("⚠ Keypad will be disabled on next check")
        
        # Update camera handler settings if it exists
        global camera_handler
        if camera_handler and not settings_data.get('camera_enabled', True):
            camera_handler.stop_stream()
            print("⚠ Camera disabled via settings")
        
        print("✓ Settings applied to system components")
        
    except Exception as e:
        print(f"⚠ Error applying settings to components: {e}")
    
    return jsonify({'success': True, 'message': 'Settings updated and applied successfully'})

@app.route('/api/logs')
@login_required
def get_logs():
    """Get logs"""
    username = session.get('username')
    user = users_data.get(username, {})
    
    # Check permissions
    if 'view_logs' not in user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    return jsonify({'success': True, 'logs': logs_data})

@app.route('/api/log', methods=['POST'])
def add_log_entry():
    """Add log entry (for keypad controller)"""
    data = request.get_json()
    
    action = data.get('action', '')
    status = data.get('status', '')
    user = data.get('user', 'system')
    details = data.get('details', '')
    
    add_log(action, status, user, details)
    
    return jsonify({'success': True})

@app.route('/api/notifications')
@login_required
def get_notifications():
    """Get notifications"""
    return jsonify({'success': True, 'notifications': notifications_data})

@app.route('/api/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    """Clear all notifications"""
    global notifications_data
    notifications_data = []
    save_notifications()
    return jsonify({'success': True})

@app.route('/api/profile', methods=['GET', 'POST'])
@login_required
def profile_api():
    """Get or update user profile"""
    username = session.get('username')
    user = users_data.get(username, {})
    
    if request.method == 'GET':
        # Return profile data (without password)
        profile_data = {k: v for k, v in user.items() if k != 'password'}
        return jsonify({'success': True, 'profile': profile_data})
    
    else:  # POST
        data = request.get_json()
        
        # Update allowed profile fields
        if 'name' in data:
            user['name'] = data['name']
        if 'email' in data:
            user['email'] = data['email']
        
        # Handle password change
        if 'current_password' in data and 'new_password' in data:
            current_password_hash = hashlib.sha256(data['current_password'].encode()).hexdigest()
            if user.get('password') == current_password_hash:
                new_password_hash = hashlib.sha256(data['new_password'].encode()).hexdigest()
                user['password'] = new_password_hash
                add_log('profile', 'password_changed', username)
            else:
                return jsonify({'success': False, 'message': 'Current password incorrect'})
        
        save_users()
        add_log('profile', 'updated', username)
        
        return jsonify({'success': True})

@app.route('/api/user/current')
@login_required
def get_current_user():
    """Get current user information"""
    username = session.get('username')
    user = users_data.get(username, {})
    
    if user:
        # Remove password from response
        safe_user = {k: v for k, v in user.items() if k != 'password'}
        safe_user['username'] = username
        return jsonify({'success': True, 'user': safe_user})
    else:
        return jsonify({'success': False, 'message': 'User not found'})

@app.route('/api/metrics')
@login_required
def get_metrics():
    """Get system metrics"""
    # Calculate metrics from logs
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Count events by type
    door_unlocks = len([log for log in logs_data if log['action'] == 'door' and log['status'] == 'unlock'])
    failed_attempts = len([log for log in logs_data if log['action'] == 'passcode' and log['status'] == 'failed'])
    camera_captures = len([log for log in logs_data if log['action'] == 'camera' and log['status'] == 'capture'])
    
    # Today's activity
    today_logs = [log for log in logs_data if log['timestamp'].startswith(today)]
    today_unlocks = len([log for log in today_logs if log['action'] == 'door' and log['status'] == 'unlock'])
    
    # Recent activity (last 7 days)
    week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    recent_logs = [log for log in logs_data if log['timestamp'] >= week_ago]
    
    # Activity by day (last 7 days)
    daily_activity = {}
    for i in range(7):
        date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        daily_activity[date] = len([log for log in logs_data if log['timestamp'].startswith(date)])
    
    metrics = {
        'total_unlocks': door_unlocks,
        'failed_attempts': failed_attempts,
        'camera_captures': camera_captures,
        'today_unlocks': today_unlocks,
        'total_users': len(users_data),
        'active_users': len([u for u in users_data.values() if u.get('approved', False)]),
        'daily_activity': daily_activity,
        'recent_activity': len(recent_logs)
    }
    
    return jsonify({'success': True, 'metrics': metrics})

@app.route('/api/camera/test')
@login_required
def test_camera():
    """Test camera functionality"""
    global camera_handler
    
    try:
        if not camera_handler:
            camera_handler = CameraHandler()
        
        # Test capture
        filename = camera_handler.capture_image()
        
        if filename:
            return jsonify({
                'success': True,
                'message': 'Camera test successful',
                'filename': filename,
                'type': camera_handler.camera_type
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Camera test failed - could not capture image'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Camera test error: {str(e)}'
        })

@app.route('/api/keypad/status')
@login_required
def keypad_status():
    """Get keypad status"""
    global keypad_controller
    
    if keypad_controller:
        return jsonify({
            'success': True,
            'available': keypad_controller.gpio_available,
            'running': keypad_controller.running,
            'current_input_length': len(keypad_controller.current_input),
            'failed_attempts': keypad_controller.failed_attempts,
            'is_locked_out': keypad_controller.is_locked_out
        })
    else:
        return jsonify({
            'success': True,
            'available': False,
            'running': False,
            'current_input_length': 0,
            'failed_attempts': 0,
            'is_locked_out': False
        })

@app.route('/api/keypad/simulate', methods=['POST'])
@login_required
def simulate_keypad():
    """Simulate keypad key press (for testing)"""
    global keypad_controller
    
    data = request.get_json()
    key = data.get('key')
    
    if not key:
        return jsonify({'success': False, 'message': 'Key required'})
    
    if keypad_controller:
        keypad_controller.process_key(key)
        return jsonify({'success': True, 'message': f'Key {key} simulated'})
    else:
        return jsonify({'success': False, 'message': 'Keypad not available'})

@app.route('/api/keypad/reset', methods=['POST'])
@admin_required
def reset_keypad():
    """Reset keypad state (admin only)"""
    global keypad_controller
    
    if keypad_controller:
        keypad_controller.current_input = ""
        keypad_controller.failed_attempts = 0
        keypad_controller.is_locked_out = False
        add_log('keypad', 'reset', session.get('username', 'admin'))
        return jsonify({'success': True, 'message': 'Keypad state reset'})
    else:
        return jsonify({'success': False, 'message': 'Keypad not available'})

# Fingerprint API Routes
@app.route('/api/fingerprint/authenticate', methods=['POST'])
def fingerprint_authenticate():
    """Authenticate using real fingerprint hardware"""
    global fingerprint_controller
    
    if not fingerprint_controller or not fingerprint_controller.available:
        return jsonify({
            'success': False,
            'message': 'Fingerprint sensor not available'
        })
    
    try:
        # Get timeout from settings
        timeout = settings_data.get('fingerprint_timeout', 10)
        
        # Perform real fingerprint authentication
        result = fingerprint_controller.authenticate_fingerprint(timeout)
        
        if result['success']:
            username = result.get('username')
            if username and username in users_data:
                user_data = users_data[username]
                
                # Check if user is approved and has access
                if not user_data.get('approved', False):
                    add_log('fingerprint', 'failed', username, 'User not approved')
                    return jsonify({
                        'success': False,
                        'message': 'User account not approved'
                    })
                
                # Check access expiry
                if user_data.get('access_type') == 'limited' and user_data.get('access_until'):
                    try:
                        access_until = datetime.datetime.strptime(user_data['access_until'], '%Y-%m-%d')
                        if datetime.datetime.now() > access_until:
                            add_log('fingerprint', 'failed', username, 'Access expired')
                            return jsonify({
                                'success': False,
                                'message': 'Access has expired'
                            })
                    except:
                        pass
                
                add_log('fingerprint', 'success', username, f'Hardware authentication successful')
                
                return jsonify({
                    'success': True,
                    'username': username,
                    'confidence': result.get('confidence', 0),
                    'message': 'Fingerprint recognized'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Fingerprint matched but user not found'
                })
        else:
            add_log('fingerprint', 'failed', 'unknown', result.get('message', 'Authentication failed'))
            return jsonify(result)
            
    except Exception as e:
        print(f"Error in fingerprint authentication: {e}")
        add_log('fingerprint', 'error', 'system', str(e))
        return jsonify({
            'success': False,
            'message': 'Fingerprint authentication error'
        })
   
@app.route('/api/fingerprint/enroll', methods=['POST'])
@login_required
def fingerprint_enroll():
    """Enroll fingerprint using real hardware"""
    global fingerprint_controller
    
    if not fingerprint_controller or not fingerprint_controller.available:
        return jsonify({
            'success': False,
            'message': 'Fingerprint sensor not available'
        })
    
    try:
        data = request.get_json()
        target_username = data.get('username', '').strip()
        
        current_username = session.get('username')
        current_user = users_data.get(current_username, {})
        
        # Check permissions
        if target_username != current_username and 'manage_users' not in current_user.get('permissions', []):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        if not target_username:
            return jsonify({'success': False, 'message': 'Username required'})
        
        target_user = users_data.get(target_username)
        if not target_user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        # Perform real fingerprint enrollment
        result = fingerprint_controller.enroll_fingerprint(target_username)
        
        if result['success']:
            # Update user data
            target_user['fingerprint_enrolled'] = True
            target_user['fingerprint_enrolled_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            target_user['fingerprint_enrolled_by'] = current_username
            target_user['fingerprint_slot_id'] = result.get('slot_id')
            
            save_users()
            add_log('fingerprint', 'enrolled', current_username, 
                   f'Hardware enrollment successful for {target_username}, slot: {result.get("slot_id")}')
            
            return jsonify({
                'success': True,
                'message': 'Fingerprint enrolled successfully',
                'slot_id': result.get('slot_id')
            })
        else:
            add_log('fingerprint', 'enrollment_failed', current_username, 
                   f'Hardware enrollment failed for {target_username}: {result.get("message")}')
            return jsonify(result)
            
    except Exception as e:
        print(f"Error in fingerprint enrollment: {e}")
        add_log('fingerprint', 'error', 'system', str(e))
        return jsonify({
            'success': False,
            'message': f'Fingerprint enrollment error: {str(e)}'
        })
   
@app.route('/api/fingerprint/sensor/info')
@login_required
def fingerprint_sensor_info():
    """Get UART fingerprint sensor information"""
    global fingerprint_controller
    
    if not fingerprint_controller:
        return jsonify({
            'success': False,
            'message': 'Fingerprint controller not available'
        })
    
    try:
        sensor_info = fingerprint_controller.get_sensor_info()
        uart_info = fingerprint_controller.get_uart_info() if hasattr(fingerprint_controller, 'get_uart_info') else None
        
        return jsonify({
            'success': True,
            'sensor_info': sensor_info,
            'uart_info': uart_info,
            'enrolled_users': fingerprint_controller.list_enrolled_users()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting sensor info: {str(e)}'
        })
   
@app.route('/api/fingerprint/sensor/test')
@login_required
def test_fingerprint_sensor():
    """Test UART fingerprint sensor"""
    global fingerprint_controller
    
    if not fingerprint_controller:
        return jsonify({
            'success': False,
            'message': 'Fingerprint controller not available'
        })
    
    try:
        result = fingerprint_controller.test_sensor()
        add_log('fingerprint', 'test', session.get('username'), 
               f'Sensor test: {result.get("message")}')
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Sensor test error: {str(e)}'
        })

@app.route('/api/fingerprint/delete', methods=['POST'])
@login_required
def fingerprint_delete():
    """Delete fingerprint data for a user"""
    try:
        data = request.get_json()
        target_username = data.get('username', '').strip()
        
        current_username = session.get('username')
        current_user = users_data.get(current_username, {})
        
        # Check if user can manage fingerprints (admin or self)
        if target_username != current_username and 'manage_users' not in current_user.get('permissions', []):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        if not target_username:
            return jsonify({'success': False, 'message': 'Username required'})
        
        target_user = users_data.get(target_username)
        if not target_user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        if not target_user.get('fingerprint_enrolled', False):
            return jsonify({'success': False, 'message': 'No fingerprint data to delete'})
        
        # Remove fingerprint data
        target_user['fingerprint_enrolled'] = False
        if 'fingerprint_enrolled_date' in target_user:
            del target_user['fingerprint_enrolled_date']
        if 'fingerprint_enrolled_by' in target_user:
            del target_user['fingerprint_enrolled_by']
        if 'fingerprint_slot_id' in target_user:
            del target_user['fingerprint_slot_id']
        
        save_users()
        add_log('fingerprint', 'deleted', current_username, f'Fingerprint data deleted for {target_username}')
        
        return jsonify({
            'success': True,
            'message': 'Fingerprint data deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting fingerprint: {e}")
        add_log('fingerprint', 'error', 'system', str(e))
        return jsonify({
            'success': False,
            'message': 'Fingerprint deletion error'
        })

@app.route('/api/fingerprint/status/<username>')
@login_required
def fingerprint_status(username):
    """Get fingerprint enrollment status for a user"""
    try:
        current_username = session.get('username')
        current_user = users_data.get(current_username, {})
        
        # Check if user can view fingerprint status (admin or self)
        if username != current_username and 'manage_users' not in current_user.get('permissions', []):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        target_user = users_data.get(username)
        if not target_user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        return jsonify({
            'success': True,
            'enrolled': target_user.get('fingerprint_enrolled', False),
            'enrolled_date': target_user.get('fingerprint_enrolled_date'),
            'enrolled_by': target_user.get('fingerprint_enrolled_by'),
            'slot_id': target_user.get('fingerprint_slot_id')
        })
        
    except Exception as e:
        print(f"Error getting fingerprint status: {e}")
        return jsonify({
            'success': False,
            'message': 'Error getting fingerprint status'
        })

@app.route('/api/users/add', methods=['POST'])
@login_required
def add_user():
    """Add a new user (pre-registration)"""
    current_username = session.get('username')
    current_user = users_data.get(current_username, {})
    
    # Check permissions
    if 'manage_users' not in current_user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'guest')
    permissions = data.get('permissions', ['unlock'])
    access_type = data.get('access_type', 'full')
    access_until = data.get('access_until')
    
    if not username:
        return jsonify({'success': False, 'message': 'Username required'})
    
    if username in users_data:
        return jsonify({'success': False, 'message': 'Username already exists'})
    
    # Create new user entry (pre-registered)
    users_data[username] = {
        'password': None,  # Will be set when user signs up
        'name': '',  # Will be set when user signs up
        'email': email,
        'role': role,
        'permissions': permissions,
        'approved': False,
        'pre_approved': True,  # Mark as pre-approved for automatic approval
        'access_type': access_type,
        'access_until': access_until,
        'fingerprint_enrolled': False,
        'created_by': current_username,
        'created_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    save_users()
    add_log('user', 'pre_registered', current_username, f'Pre-registered user: {username}')
    
    return jsonify({'success': True, 'message': 'User pre-registered successfully'})

@app.route('/api/users/edit', methods=['POST'])
@login_required
def edit_user():
    """Edit an existing user"""
    current_username = session.get('username')
    current_user = users_data.get(current_username, {})
    
    # Check permissions
    if 'manage_users' not in current_user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username or username not in users_data:
        return jsonify({'success': False, 'message': 'User not found'})
    
    user = users_data[username]
    
    # Update user data
    if 'email' in data:
        user['email'] = data['email']
    if 'role' in data:
        user['role'] = data['role']
    if 'permissions' in data:
        user['permissions'] = data['permissions']
    if 'access_type' in data:
        user['access_type'] = data['access_type']
    if 'access_until' in data:
        user['access_until'] = data['access_until']
    
    user['modified_by'] = current_username
    user['modified_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    save_users()
    add_log('user', 'edited', current_username, f'Edited user: {username}')
    
    return jsonify({'success': True, 'message': 'User updated successfully'})

@app.route('/api/users/delete', methods=['POST'])
@login_required
def delete_user_api():
    """Delete a user"""
    current_username = session.get('username')
    current_user = users_data.get(current_username, {})
    
    # Check permissions
    if 'manage_users' not in current_user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': 'Username required'})
    
    if username not in users_data:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Don't allow deleting yourself
    if username == current_username:
        return jsonify({'success': False, 'message': 'Cannot delete yourself'})
    
    del users_data[username]
    save_users()
    add_log('user', 'deleted', current_username, f'Deleted user: {username}')
    
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@app.route('/api/users/approve', methods=['POST'])
@login_required
def approve_user():
    """Approve a pending user"""
    current_username = session.get('username')
    current_user = users_data.get(current_username, {})
    
    # Check permissions
    if 'manage_users' not in current_user.get('permissions', []):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': 'Username required'})
    
    if username not in users_data:
        return jsonify({'success': False, 'message': 'User not found'})
    
    user = users_data[username]
    user['approved'] = True
    user['approved_by'] = current_username
    user['approved_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    save_users()
    add_log('user', 'approved', current_username, f'Approved user: {username}')
    add_notification(f'User {username} has been approved', 'success')
    
    return jsonify({'success': True, 'message': 'User approved successfully'})

# Static file serving for captures
@app.route('/static/captures/<filename>')
def serve_capture(filename):
    """Serve captured images"""
    return send_from_directory('static/captures', filename)

def initialize_system():
    """Initialize the smart door lock system"""
    global door_controller, camera_handler, keypad_controller, fingerprint_controller, ultra_speech_controller
    
    print("🚀 Initializing Smart Door Lock System...")
    
    # Load data
    load_data()
    print("✓ Data loaded")
    
    # Initialize door controller
    try:
        door_controller = DoorController()
        print("✓ Door controller initialized")
    except Exception as e:
        print(f"⚠ Door controller error: {e}")
    
    # Initialize camera handler
    try:
        camera_handler = CameraHandler()
        print("✓ Camera handler initialized")
    except Exception as e:
        print(f"⚠ Camera handler error: {e}")
    
    # Initialize keypad controller
    try:
        keypad_controller = KeypadController(app)
        keypad_controller.start()
        print("✓ Keypad controller initialized")
    except Exception as e:
        print(f"⚠ Keypad controller error: {e}")
    
    # Initialize fingerprint controller
    try:
        if FINGERPRINT_AVAILABLE:
            fingerprint_controller = FingerprintController()
            print("✓ Fingerprint controller initialized")
        else:
            fingerprint_controller = None
            print("⚠ Fingerprint controller not available")
    except Exception as e:
        print(f"⚠ Fingerprint controller error: {e}")
        fingerprint_controller = None

    # Initialize ultra-reliable speech controller
    try:
        if ULTRA_SPEECH_AVAILABLE:
            ultra_speech_controller = UltraReliableSpeechController()
            print("✅ Ultra-reliable speech controller initialized")
        else:
            ultra_speech_controller = None
            print("⚠ Ultra-reliable speech controller not available")
    except Exception as e:
        print(f"⚠ Ultra-reliable speech controller error: {e}")
        ultra_speech_controller = None
    
    print("🎯 Smart Door Lock System ready!")

if __name__ == '__main__':
    try:
        initialize_system()
        
        # Start Flask app
        print("🌐 Starting web server...")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        
        # Cleanup
        if keypad_controller:
            keypad_controller.stop()
        
        if camera_handler:
            camera_handler.stop_stream()

        if ultra_speech_controller:
            ultra_speech_controller.stop()
        
        print("👋 Smart Door Lock System stopped")
        
    except Exception as e:
        print(f"✗ System error: {e}")
