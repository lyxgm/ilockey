#!/usr/bin/env python3
"""
Integrated Keypad + AI Controller for Smart Door Lock
This combines keypad functionality with ultra-reliable speech recognition
"""

import time
import threading
import subprocess
import json
import os
import wave
import requests
from datetime import datetime
from pathlib import Path

class IntegratedKeypadAI:
    """Combined keypad and AI controller"""
    
    def __init__(self):
        print("🚀 Initializing Integrated Keypad + AI Controller...")
        
        # Keypad setup
        self.setup_keypad()
        
        # AI setup
        self.setup_ai()
        
        # State variables
        self.running = False
        self.ai_active = False
        self.conversation_log = []
        
        print("✅ Integrated Keypad + AI Controller ready!")
    
    def setup_keypad(self):
        """Setup keypad GPIO"""
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.gpio_available = True
            
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Keypad configuration
            self.ROWS = [18, 23, 24, 25]
            self.COLS = [4, 17, 27, 22]
            self.KEYS = [
                ['1', '2', '3', 'A'],
                ['4', '5', '6', 'B'],
                ['7', '8', '9', 'C'],
                ['*', '0', '#', 'D']
            ]
            
            # Setup GPIO pins
            for row_pin in self.ROWS:
                GPIO.setup(row_pin, GPIO.OUT)
                GPIO.output(row_pin, GPIO.HIGH)
            
            for col_pin in self.COLS:
                GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            print("✅ Keypad GPIO initialized")
            
        except ImportError:
            print("⚠️ RPi.GPIO not available - using simulation mode")
            self.gpio_available = False
            self.setup_mock_keypad()
        except Exception as e:
            print(f"⚠️ GPIO error: {e} - using simulation mode")
            self.gpio_available = False
            self.setup_mock_keypad()
    
    def setup_mock_keypad(self):
        """Setup mock keypad for testing"""
        class MockGPIO:
            BCM = "BCM"
            OUT = "OUT"
            IN = "IN"
            HIGH = 1
            LOW = 0
            PUD_UP = "PUD_UP"
            
            def setmode(self, mode): pass
            def setwarnings(self, enabled): pass
            def cleanup(self): pass
            def setup(self, pin, mode, **kwargs): pass
            def output(self, pin, value): pass
            def input(self, pin): return self.HIGH
        
        self.GPIO = MockGPIO()
        self.ROWS = [18, 23, 24, 25]
        self.COLS = [4, 17, 27, 22]
        self.KEYS = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ]
    
    def setup_ai(self):
        """Setup AI speech recognition"""
        self.speech_engines = {}
        
        # Setup Vosk
        try:
            import vosk
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
                    print("✅ Vosk engine loaded")
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
            print("✅ Google Speech Recognition loaded")
        except:
            self.speech_engines['google'] = {'available': False}
        
        # Setup Whisper
        try:
            import whisper
            self.speech_engines['whisper'] = {
                'model': whisper.load_model("base"),
                'available': True
            }
            print("✅ Whisper engine loaded")
        except:
            self.speech_engines['whisper'] = {'available': False}
    
    def scan_keypad(self):
        """Scan keypad for key presses"""
        if not self.gpio_available:
            return None
        
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
            print(f"❌ Keypad scan error: {e}")
            return None
    
    def log_to_system(self, action, status, user='keypad', details=''):
        """Log events to the main system"""
        try:
            data = {
                "action": action,
                "status": status,
                "user": user,
                "details": details
            }
            
            response = requests.post("http://localhost:5000/api/log", json=data, timeout=5)
            if response.status_code == 200:
                print(f"📝 Logged: {action} - {status}")
            else:
                print(f"⚠️ Log failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️ Logging error: {e}")
    
    def speak_to_visitor(self, text):
        """Speak to visitor using TTS"""
        print(f"🤖 AI SAYS: {text}")
        
        # Log AI speech
        self.conversation_log.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'speaker': 'AI',
            'text': text,
            'confidence': 1.0
        })
        
        # Log to main system
        self.log_to_system('ai_conversation', 'ai_speech', 'keypad', text)
        
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
                '-D', 'plughw:3,0',  # Your USB audio device
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
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio using multiple engines"""
        print("🔄 Transcribing audio...")
        
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
    
    def analyze_intent(self, text):
        """Analyze visitor intent"""
        if not text:
            return 'unknown'
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['delivery', 'package', 'mail', 'amazon', 'ups', 'fedex']):
            return 'delivery'
        elif any(word in text_lower for word in ['visit', 'see', 'looking for', 'here for']):
            return 'visit'
        elif any(word in text_lower for word in ['hello', 'hi', 'hey', 'good morning']):
            return 'greeting'
        else:
            return 'general'
    
    def generate_response(self, visitor_text, intent):
        """Generate appropriate response"""
        responses = {
            'delivery': "I understand you have a delivery. Let me notify the residents immediately.",
            'visit': "I heard you're here to visit someone. I'll let them know you're here.",
            'greeting': "Hello! Thank you for visiting. How can I help you today?",
            'general': "Thank you for speaking. I'm notifying the residents of your visit."
        }
        
        return responses.get(intent, responses['general'])
    
    def start_ai_conversation(self):
        """Start AI conversation (D key pressed)"""
        if self.ai_active:
            print("🤖 AI conversation already active")
            return
        
        print("🔔 D KEY PRESSED - Starting AI conversation...")
        self.ai_active = True
        self.conversation_log = []
        
        # Log the start
        self.log_to_system('ai', 'interaction_started', 'keypad', 'D key pressed - AI conversation started')
        
        def ai_conversation_thread():
            try:
                # Step 1: Greet visitor
                self.speak_to_visitor("Hello! Welcome to our smart door system. How can I help you today?")
                
                if not self.ai_active:  # Check if stopped
                    return
                
                # Step 2: Listen to visitor
                audio_file = self.record_visitor_audio(8)
                
                if audio_file and self.ai_active:
                    # Step 3: Transcribe speech
                    visitor_text, confidence = self.transcribe_audio(audio_file)
                    
                    # Clean up audio file
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                    
                    if visitor_text and confidence > 0.5:
                        print(f"👤 VISITOR SAID: '{visitor_text}' (confidence: {confidence:.2f})")
                        
                        # Log visitor speech to system
                        details = f"Confidence: {confidence:.2f} - {visitor_text}"
                        self.log_to_system('ai_conversation', 'visitor_speech', 'keypad', details)
                        
                        # Log to conversation
                        self.conversation_log.append({
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'speaker': 'VISITOR',
                            'text': visitor_text,
                            'confidence': confidence
                        })
                        
                        if self.ai_active:  # Check if still active
                            # Step 4: Analyze and respond
                            intent = self.analyze_intent(visitor_text)
                            response = self.generate_response(visitor_text, intent)
                            
                            print(f"🧠 Intent detected: {intent}")
                            self.log_to_system('ai_conversation', 'intent_detected', 'keypad', f"Intent: {intent}")
                            
                            self.speak_to_visitor(response)
                    else:
                        print("⚠️ Could not understand visitor")
                        if self.ai_active:
                            self.speak_to_visitor("I'm sorry, I didn't catch that clearly. The residents have been notified.")
                else:
                    print("⚠️ No audio recorded")
                    if self.ai_active:
                        self.speak_to_visitor("I didn't hear a response, but I've notified the residents.")
                
                # Final message
                if self.ai_active:
                    self.speak_to_visitor("Thank you for visiting! Have a great day!")
                
                print("✅ AI conversation completed")
                
            except Exception as e:
                print(f"❌ AI conversation error: {e}")
                self.log_to_system('ai', 'error', 'keypad', str(e))
            finally:
                self.ai_active = False
                self.log_to_system('ai', 'interaction_ended', 'keypad', 'AI conversation ended')
        
        # Start conversation in background thread
        threading.Thread(target=ai_conversation_thread, daemon=True).start()
    
    def stop_ai_conversation(self):
        """Stop AI conversation (# key pressed)"""
        if self.ai_active:
            print("🔇 # KEY PRESSED - Stopping AI conversation...")
            self.ai_active = False
            self.log_to_system('ai', 'interaction_stopped', 'keypad', '# key pressed - AI conversation stopped')
            print("✅ AI conversation stopped")
        else:
            print("🤖 No AI conversation active")
    
    def process_key(self, key):
        """Process keypad key press"""
        if key is None:
            return
        
        print(f"🔑 Key pressed: {key}")
        
        if key == 'D':
            # Start AI conversation
            self.start_ai_conversation()
        elif key == '#':
            # Stop AI conversation
            self.stop_ai_conversation()
        else:
            # Other keys (passcode, etc.)
            print(f"🔢 Key {key} pressed (not AI related)")
    
    def run(self):
        """Main loop"""
        print("=" * 60)
        print("🚀 INTEGRATED KEYPAD + AI CONTROLLER")
        print("=" * 60)
        print("📋 Controls:")
        print("   D = Start AI Conversation")
        print("   # = Stop AI Conversation")
        print("   Other keys = Normal keypad functions")
        print("=" * 60)
        print("🎯 Ready! Press keys or Ctrl+C to exit")
        print("=" * 60)
        
        self.running = True
        last_key_time = 0
        debounce_delay = 0.3
        
        try:
            while self.running:
                current_time = time.time()
                
                # Scan keypad
                key = self.scan_keypad()
                
                if key and (current_time - last_key_time) > debounce_delay:
                    last_key_time = current_time
                    self.process_key(key)
                    time.sleep(debounce_delay)
                
                time.sleep(0.05)  # 50ms scan interval
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        except Exception as e:
            print(f"❌ Runtime error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.ai_active = False
        
        if self.gpio_available:
            try:
                self.GPIO.cleanup()
                print("✅ GPIO cleaned up")
            except:
                pass
        
        print("👋 Integrated Keypad + AI Controller stopped")
    
    def simulate_key_press(self, key):
        """Simulate key press for testing"""
        print(f"🧪 SIMULATING KEY PRESS: {key}")
        self.process_key(key)

# Test function
def test_integration():
    """Test the integrated system"""
    print("🧪 Testing Integrated Keypad + AI System")
    
    controller = IntegratedKeypadAI()
    
    print("\n🔔 Simulating D key press...")
    controller.simulate_key_press('D')
    
    # Wait for conversation to start
    time.sleep(2)
    
    print("\n⏰ Waiting 10 seconds for conversation...")
    time.sleep(10)
    
    print("\n🔇 Simulating # key press...")
    controller.simulate_key_press('#')
    
    time.sleep(2)
    controller.cleanup()

if __name__ == "__main__":
    # Uncomment to test
    # test_integration()
    
    # Run the integrated controller
    controller = IntegratedKeypadAI()
    controller.run()
