#!/usr/bin/env python3
import speech_recognition as sr
import pyttsx3
import time
import json
import subprocess
import os
from datetime import datetime

class FixedConversationTest:
    def __init__(self):
        """Initialize with proper USB audio setup"""
        print("🤖 Initializing Fixed Conversation Test...")
        
        # First, let's check and setup audio properly
        self.setup_audio_system()
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Initialize text-to-speech with USB audio
        self.setup_tts_engine()
        
        # Setup USB microphone
        self.setup_usb_microphone()
        
        # Conversation log
        self.conversation_log = []
        
        print("✅ Fixed Conversation Test ready!")
    
    def setup_audio_system(self):
        """Setup audio system for USB device"""
        print("🔧 Setting up audio system...")
        
        # Check current audio setup
        try:
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            print("📋 Available playback devices:")
            print(result.stdout)
            
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
            print("📋 Available recording devices:")
            print(result.stdout)
            
        except Exception as e:
            print(f"⚠️  Could not check audio devices: {e}")
    
    def setup_tts_engine(self):
        """Setup TTS engine with proper audio output"""
        print("🔊 Setting up text-to-speech...")
        
        try:
            self.tts_engine = pyttsx3.init()
            
            # Set properties
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            
            # Try to set voice to female if available
            voices = self.tts_engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                print(f"✅ TTS engine ready with voice: {voices[0].name if voices else 'default'}")
            else:
                print("✅ TTS engine ready with default voice")
                
        except Exception as e:
            print(f"❌ TTS setup error: {e}")
            self.tts_engine = None
    
    def setup_usb_microphone(self):
        """Setup USB microphone with proper device detection"""
        print("🎤 Setting up USB microphone...")
        
        try:
            import pyaudio
            
            p = pyaudio.PyAudio()
            
            print("🔍 Scanning for audio devices...")
            usb_device_index = None
            
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                print(f"Device {i}: {info['name']} - Input channels: {info['maxInputChannels']}")
                
                if info['maxInputChannels'] > 0:
                    if 'USB Audio' in info['name'] or 'Device' in info['name']:
                        usb_device_index = i
                        print(f"✅ Selected USB Audio Device at index {i}: {info['name']}")
                        break
            
            p.terminate()
            
            if usb_device_index is not None:
                self.microphone = sr.Microphone(device_index=usb_device_index, sample_rate=44100)
                print("✅ USB microphone configured")
            else:
                print("⚠️  USB device not found, using default microphone")
                self.microphone = sr.Microphone()
            
            # Calibrate microphone
            print("🔧 Calibrating microphone...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone calibrated")
            
        except Exception as e:
            print(f"❌ Microphone setup error: {e}")
            print("🔄 Falling back to default microphone")
            self.microphone = sr.Microphone()
    
    def speak_with_alsa(self, text):
        """Speak using ALSA directly to USB audio device"""
        print(f"\n🤖 AI SAYS: {text}")
        print("-" * 50)
        
        # Log the AI response
        self.conversation_log.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'speaker': 'AI',
            'text': text
        })
        
        # Try multiple methods to play audio
        audio_played = False
        
        # Method 1: Try pyttsx3 first
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                audio_played = True
                print("✅ Audio played via TTS engine")
            except Exception as e:
                print(f"⚠️  TTS engine failed: {e}")
        
        # Method 2: Try espeak with ALSA if TTS failed
        if not audio_played:
            try:
                # Use espeak with specific audio device
                cmd = ['espeak', '-s', '150', '-a', '100', text]
                subprocess.run(cmd, check=True, capture_output=True)
                audio_played = True
                print("✅ Audio played via espeak")
            except Exception as e:
                print(f"⚠️  espeak failed: {e}")
        
        # Method 3: Try festival if available
        if not audio_played:
            try:
                cmd = ['echo', text, '|', 'festival', '--tts']
                subprocess.run(' '.join(cmd), shell=True, check=True, capture_output=True)
                audio_played = True
                print("✅ Audio played via festival")
            except Exception as e:
                print(f"⚠️  festival failed: {e}")
        
        if not audio_played:
            print("❌ Could not play audio - text only mode")
        
        time.sleep(0.5)
    
    def listen_and_transcribe(self, prompt="", timeout=15):
        """Listen for speech and transcribe with better error handling"""
        if prompt:
            print(f"\n🎧 {prompt}")
        
        print("🎤 LISTENING... (speak clearly into your USB microphone)")
        print("=" * 50)
        
        try:
            with self.microphone as source:
                # Adjust for ambient noise briefly
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio with longer timeout
                print("👂 Recording audio...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            print("🔄 TRANSCRIBING... (this may take a moment)")
            
            # Try multiple recognition services
            text = None
            
            # Try Google first
            try:
                text = self.recognizer.recognize_google(audio)
                print("✅ Transcribed using Google Speech Recognition")
            except Exception as e:
                print(f"⚠️  Google recognition failed: {e}")
            
            # Try offline recognition if Google fails
            if not text:
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    print("✅ Transcribed using offline Sphinx")
                except Exception as e:
                    print(f"⚠️  Offline recognition failed: {e}")
            
            if text:
                # Display transcription
                print(f"👤 USER SAID: '{text}'")
                print("=" * 50)
                
                # Log the user response
                self.conversation_log.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'speaker': 'USER',
                    'text': text
                })
                
                return text
            else:
                print("❌ Could not transcribe audio")
                return None
                
        except sr.WaitTimeoutError:
            print("⏰ No speech detected within timeout period")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand the audio - please speak more clearly")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech service error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def test_audio_setup(self):
        """Test both microphone and speaker"""
        print("\n🧪 TESTING AUDIO SETUP")
        print("=" * 30)
        
        # Test speaker
        print("🔊 Testing speaker...")
        self.speak_with_alsa("This is a speaker test. Can you hear me clearly?")
        
        response = input("Did you hear the audio? (y/n): ").lower().strip()
        if response == 'y':
            print("✅ Speaker working!")
        else:
            print("❌ Speaker not working - will use text-only mode")
        
        # Test microphone
        print("\n🎤 Testing microphone...")
        print("Say 'Hello test' when ready...")
        result = self.listen_and_transcribe("Testing microphone...")
        
        if result:
            print("✅ Microphone working!")
            self.speak_with_alsa(f"Great! I heard you say: {result}")
            return True
        else:
            print("❌ Microphone not working properly")
            return False
    
    def run_conversation_flow(self):
        """Run the conversation flow with audio"""
        print("\n" + "="*60)
        print("🎬 STARTING CONVERSATION FLOW TEST")
        print("="*60)
        print("Flow: Hello → Ask Name → Wait → Ask Purpose → Show Transcription")
        print("="*60)
        
        # Step 1: Say Hello
        print("\n📍 STEP 1: GREETING")
        self.speak_with_alsa("Hello! Welcome to the smart door system.")
        
        time.sleep(2)
        
        # Step 2: Ask for name
        print("\n📍 STEP 2: ASKING FOR NAME")
        self.speak_with_alsa("What is your name?")
        
        # Listen for name
        user_name = self.listen_and_transcribe("Please tell me your name...")
        
        if user_name:
            response = f"Nice to meet you, {user_name}!"
            self.speak_with_alsa(response)
        else:
            self.speak_with_alsa("I didn't catch your name, but that's okay.")
        
        # Step 3: Wait
        print("\n📍 STEP 3: WAITING...")
        print("⏳ Waiting for 3 seconds...")
        time.sleep(3)
        
        # Step 4: Ask purpose
        print("\n📍 STEP 4: ASKING PURPOSE OF VISIT")
        self.speak_with_alsa("What is the purpose of your visit today?")
        
        # Listen for purpose
        purpose = self.listen_and_transcribe("Please tell me why you're here...")
        
        if purpose:
            response = f"I understand. You're here because: {purpose}. Thank you for letting me know!"
            self.speak_with_alsa(response)
        else:
            self.speak_with_alsa("I didn't catch your purpose, but thank you for visiting.")
        
        # Step 5: Show transcription
        print("\n📍 STEP 5: COMPLETE CONVERSATION TRANSCRIPTION")
        self.show_complete_transcription()
        
        # Final message
        self.speak_with_alsa("Thank you for testing the conversation flow. Have a great day!")
    
    def show_complete_transcription(self):
        """Show complete conversation log"""
        print("\n" + "="*60)
        print("📝 COMPLETE CONVERSATION TRANSCRIPTION")
        print("="*60)
        
        for i, entry in enumerate(self.conversation_log, 1):
            speaker_icon = "🤖" if entry['speaker'] == 'AI' else "👤"
            print(f"{i:2d}. [{entry['timestamp']}] {speaker_icon} {entry['speaker']}: {entry['text']}")
        
        print("="*60)
        
        # Save to file
        try:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.conversation_log, f, indent=2)
            print(f"💾 Conversation saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save: {e}")

def main():
    """Main function with menu"""
    print("🎬 Fixed Conversation Test with Audio")
    print("=" * 40)
    
    # Check dependencies
    missing_deps = []
    try:
        import speech_recognition as sr
    except ImportError:
        missing_deps.append("SpeechRecognition")
    
    try:
        import pyttsx3
    except ImportError:
        missing_deps.append("pyttsx3")
    
    try:
        import pyaudio
    except ImportError:
        missing_deps.append("pyaudio")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return
    
    try:
        tester = FixedConversationTest()
        
        while True:
            print("\n" + "="*40)
            print("🎤 CONVERSATION TEST MENU")
            print("="*40)
            print("1. 🧪 Test Audio Setup First")
            print("2. 🎬 Run Full Conversation Flow")
            print("3. 🎤 Quick Microphone Test")
            print("4. 🔊 Quick Speaker Test")
            print("5. 🚪 Exit")
            print("="*40)
            
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == '1':
                if tester.test_audio_setup():
                    print("✅ Audio setup successful! You can now run the full conversation.")
                else:
                    print("❌ Audio setup needs attention.")
            
            elif choice == '2':
                print("\n🚀 Starting full conversation flow...")
                input("Press Enter when ready...")
                tester.run_conversation_flow()
            
            elif choice == '3':
                print("🎤 Say something...")
                result = tester.listen_and_transcribe()
                if result:
                    print(f"✅ Heard: {result}")
                    tester.speak_with_alsa(f"I heard you say: {result}")
            
            elif choice == '4':
                tester.speak_with_alsa("This is a speaker test. Can you hear me?")
            
            elif choice == '5':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice!")
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
