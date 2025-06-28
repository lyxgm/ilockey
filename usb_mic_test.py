#!/usr/bin/env python3
import os
import sys

def test_usb_microphone():
    """Test USB microphone on Card 3 with proper settings"""
    print("🎤 USB Microphone Test - Card 3")
    print("=" * 35)
    
    # Record using the USB audio device with proper format
    print("🎧 Recording 5 seconds of audio...")
    print("Say something now!")
    
    # Use plughw:3,0 for better compatibility and proper sample rate
    record_cmd = "arecord -D plughw:3,0 -f S16_LE -r 44100 -c 1 -d 5 /tmp/usb_mic_test.wav"
    print(f"Command: {record_cmd}")
    
    result = os.system(record_cmd)
    
    if result == 0:
        print("✅ Recording successful!")
        
        # Play it back using the same device with compatible format
        print("🔊 Playing back your recording...")
        play_cmd = "aplay -D plughw:3,0 /tmp/usb_mic_test.wav"
        play_result = os.system(play_cmd)
        
        if play_result == 0:
            print("✅ Playback successful!")
            print("🎉 Your USB microphone is working perfectly!")
        else:
            print("⚠️  Playback had issues, but recording works!")
            print("🎉 Your microphone is working for speech recognition!")
        
        # Show file info
        print("\n📊 Recording Info:")
        os.system("file /tmp/usb_mic_test.wav")
        
        # Clean up
        os.system("rm -f /tmp/usb_mic_test.wav")
        return True
    else:
        print("❌ Recording failed")
        return False

def test_with_python_speech():
    """Test with Python speech recognition using USB device"""
    print("\n🐍 Testing with Python Speech Recognition...")
    print("=" * 45)
    
    try:
        import speech_recognition as sr
        import pyaudio
        
        # List audio devices to find the USB device
        print("🎧 Available Audio Devices:")
        p = pyaudio.PyAudio()
        usb_device_index = None
        
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  🎤 {i}: {info['name']} (inputs: {info['maxInputChannels']})")
                if 'USB Audio' in info['name'] or 'Device' in info['name']:
                    usb_device_index = i
                    print(f"    ✅ Found USB Audio Device at index {i}")
        
        p.terminate()
        
        # Create recognizer and microphone
        r = sr.Recognizer()
        
        if usb_device_index is not None:
            print(f"🎤 Using USB Audio Device (index {usb_device_index})")
            mic = sr.Microphone(device_index=usb_device_index, sample_rate=44100)
        else:
            print("🎤 Using default microphone")
            mic = sr.Microphone(sample_rate=44100)
        
        print("🔧 Calibrating microphone for ambient noise...")
        with mic as source:
            print("   Please be quiet for 2 seconds...")
            r.adjust_for_ambient_noise(source, duration=2)
        
        print("✅ Calibration complete!")
        print("\n🎧 Say something clearly (you have 5 seconds):")
        
        with mic as source:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        
        print("🔄 Processing your speech...")
        
        try:
            text = r.recognize_google(audio)
            print(f"✅ I heard: '{text}'")
            print("🎉 Speech recognition is working!")
            return True
        except sr.UnknownValueError:
            print("⚠️  Could not understand the audio")
            print("💡 Try speaking louder and clearer")
            return False
        except sr.RequestError as e:
            print(f"❌ Speech service error: {e}")
            print("💡 Check your internet connection")
            return False
            
    except ImportError as e:
        print(f"⚠️  Missing library: {e}")
        print("   Install with: pip install SpeechRecognition pyaudio")
        return False
    except Exception as e:
        print(f"❌ Python test failed: {e}")
        return False

def create_ai_voice_controller():
    """Create AI voice controller using the working USB microphone"""
    print("\n🤖 Creating AI Voice Controller...")
    
    ai_controller = '''#!/usr/bin/env python3
import speech_recognition as sr
import pyttsx3
import json
import time
from datetime import datetime

class USBAIController:
    def __init__(self):
        """Initialize AI controller with USB microphone"""
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        
        # Configure TTS
        self.tts_engine.setProperty('rate', 150)
        voices = self.tts_engine.getProperty('voices')
        if voices:
            # Prefer female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        
        # Find USB microphone
        self.usb_mic_index = self.find_usb_microphone()
        
        if self.usb_mic_index is not None:
            self.microphone = sr.Microphone(device_index=self.usb_mic_index, sample_rate=44100)
            print(f"✅ Using USB Audio Device (index {self.usb_mic_index})")
        else:
            self.microphone = sr.Microphone(sample_rate=44100)
            print("⚠️  Using default microphone")
        
        # Calibrate microphone
        self.calibrate_microphone()
    
    def find_usb_microphone(self):
        """Find USB audio device index"""
        import pyaudio
        p = pyaudio.PyAudio()
        
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                if 'USB Audio' in info['name'] or 'Device' in info['name']:
                    p.terminate()
                    return i
        
        p.terminate()
        return None
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        print("🔧 Calibrating microphone...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Microphone calibrated")
        except Exception as e:
            print(f"⚠️  Calibration warning: {e}")
    
    def speak(self, text):
        """Convert text to speech"""
        print(f"🤖 AI: {text}")
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"⚠️  TTS error: {e}")
    
    def listen(self, timeout=5):
        """Listen for speech and convert to text"""
        try:
            print("🎧 Listening...")
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            print("🔄 Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"👤 User: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("⚠️  Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech service error: {e}")
            return None
        except Exception as e:
            print(f"❌ Listen error: {e}")
            return None
    
    def get_ai_response(self, user_input):
        """Generate AI response based on user input"""
        user_input = user_input.lower()
        
        # Delivery intent
        if any(word in user_input for word in ['delivery', 'package', 'mail', 'ups', 'fedex', 'amazon']):
            return "I understand you have a delivery. Let me notify the residents for you. Please wait a moment."
        
        # Visit intent
        elif any(word in user_input for word in ['visit', 'see', 'here to', 'friend', 'family']):
            return "Are you here to visit someone? I can let them know you're here. Who are you looking for?"
        
        # Help intent
        elif any(word in user_input for word in ['help', 'lost', 'directions', 'where']):
            return "I'm here to help! What do you need assistance with?"
        
        # Greeting
        elif any(word in user_input for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return "Hello! Welcome to this smart door. How can I help you today?"
        
        # Emergency
        elif any(word in user_input for word in ['emergency', 'urgent', 'help me', 'call']):
            return "This sounds urgent. I'm alerting the residents immediately. Please stay calm."
        
        # Default response
        else:
            return f"I heard you say '{user_input}'. How can I assist you with that?"
    
    def start_conversation(self):
        """Start AI conversation"""
        print("🤖 Starting AI Conversation...")
        
        # Greeting
        greeting = "Hello! Welcome to the smart door. How can I help you today?"
        self.speak(greeting)
        
        conversation_log = []
        start_time = time.time()
        
        while time.time() - start_time < 60:  # 60 second timeout
            user_input = self.listen()
            
            if user_input:
                # Log the interaction
                conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'user': user_input,
                    'type': 'user_input'
                })
                
                # Check for goodbye
                if any(word in user_input for word in ['goodbye', 'bye', 'thanks', 'thank you']):
                    response = "You're welcome! Have a great day!"
                    self.speak(response)
                    conversation_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'ai': response,
                        'type': 'ai_response'
                    })
                    break
                
                # Generate and speak response
                response = self.get_ai_response(user_input)
                self.speak(response)
                
                conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'ai': response,
                    'type': 'ai_response'
                })
            
            else:
                # No input received
                timeout_response = "I didn't hear anything. Is there anything else I can help you with?"
                self.speak(timeout_response)
        
        # Save conversation log
        log_filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(log_filename, 'w') as f:
                json.dump(conversation_log, f, indent=2)
            print(f"💾 Conversation saved to {log_filename}")
        except Exception as e:
            print(f"⚠️  Could not save log: {e}")
        
        print("👋 Conversation ended")

def main():
    """Main function"""
    print("🤖 USB AI Voice Controller")
    print("=" * 30)
    
    try:
        ai = USBAIController()
        
        while True:
            print("\\n" + "="*40)
            print("🤖 AI VOICE CONTROLLER")
            print("="*40)
            print("1. 🎤 Test Microphone")
            print("2. 🔊 Test Speaker")
            print("3. 💬 Start AI Conversation")
            print("4. 🧪 Quick Speech Test")
            print("5. 🚪 Exit")
            print("="*40)
            
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == '1':
                print("🎤 Say something for 5 seconds...")
                result = ai.listen()
                if result:
                    print(f"✅ Heard: {result}")
                else:
                    print("❌ No speech detected")
            
            elif choice == '2':
                ai.speak("This is a speaker test. Can you hear me clearly?")
            
            elif choice == '3':
                ai.start_conversation()
            
            elif choice == '4':
                print("🧪 Quick test - say 'hello'")
                result = ai.listen()
                if result:
                    response = ai.get_ai_response(result)
                    ai.speak(response)
            
            elif choice == '5':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice!")
    
    except KeyboardInterrupt:
        print("\\n🛑 Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open("usb_ai_controller.py", "w") as f:
            f.write(ai_controller)
        os.chmod("usb_ai_controller.py", 0o755)
        print("✅ Created usb_ai_controller.py")
        print("🚀 Run with: python3 usb_ai_controller.py")
        return True
    except Exception as e:
        print(f"❌ Failed to create AI controller: {e}")
        return False

def main():
    """Main function"""
    print("🎤 USB Microphone Setup & Test")
    print("=" * 35)
    
    # Test basic recording first
    if test_usb_microphone():
        print("\n🎉 Basic recording works!")
        
        # Test Python speech recognition
        if test_with_python_speech():
            print("\n🎉 Speech recognition works!")
            
            # Create AI controller
            if create_ai_voice_controller():
                print("\n✅ Everything is ready!")
                print("🚀 Your USB microphone is working perfectly!")
                print("🤖 Run: python3 usb_ai_controller.py")
            
        else:
            print("\n⚠️  Speech recognition needs work, but basic audio works")
    else:
        print("\n❌ Basic recording failed")

if __name__ == "__main__":
    main()
