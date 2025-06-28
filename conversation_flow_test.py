#!/usr/bin/env python3
import speech_recognition as sr
import pyttsx3
import time
import json
from datetime import datetime

class ConversationFlowTest:
    def __init__(self):
        """Initialize the conversation flow tester"""
        print("🤖 Initializing Conversation Flow Test...")
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        
        # Find and setup USB microphone
        self.setup_usb_microphone()
        
        # Conversation log
        self.conversation_log = []
        
        print("✅ Conversation Flow Test ready!")
    
    def setup_usb_microphone(self):
        """Setup USB microphone (Card 3)"""
        import pyaudio
        
        print("🎤 Setting up USB microphone...")
        p = pyaudio.PyAudio()
        
        usb_device_index = None
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                if 'USB Audio' in info['name'] or 'Device' in info['name']:
                    usb_device_index = i
                    print(f"✅ Found USB Audio Device at index {i}: {info['name']}")
                    break
        
        p.terminate()
        
        if usb_device_index is not None:
            self.microphone = sr.Microphone(device_index=usb_device_index, sample_rate=44100)
        else:
            print("⚠️  USB device not found, using default microphone")
            self.microphone = sr.Microphone(sample_rate=44100)
        
        # Calibrate microphone
        print("🔧 Calibrating microphone for ambient noise...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone calibrated")
        except Exception as e:
            print(f"⚠️  Calibration warning: {e}")
    
    def speak_and_log(self, text):
        """Speak text and log it"""
        print(f"\n🤖 AI SAYS: {text}")
        print("-" * 50)
        
        # Log the AI response
        self.conversation_log.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'speaker': 'AI',
            'text': text
        })
        
        # Speak it
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"⚠️  TTS error: {e}")
        
        time.sleep(0.5)  # Brief pause
    
    def listen_and_transcribe(self, prompt="", timeout=10):
        """Listen for speech and transcribe to text"""
        if prompt:
            print(f"\n🎧 {prompt}")
        
        print("🎤 LISTENING... (speak now)")
        print("=" * 30)
        
        try:
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
            
            print("🔄 TRANSCRIBING...")
            
            # Convert speech to text
            text = self.recognizer.recognize_google(audio)
            
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
            
        except sr.WaitTimeoutError:
            print("⏰ No speech detected (timeout)")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand the audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech service error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def run_conversation_flow(self):
        """Run the specific conversation flow you requested"""
        print("\n" + "="*60)
        print("🎬 STARTING CONVERSATION FLOW TEST")
        print("="*60)
        print("Flow: Hello → Ask Name → Wait → Ask Purpose → Transcribe All")
        print("="*60)
        
        # Step 1: Say Hello
        print("\n📍 STEP 1: GREETING")
        self.speak_and_log("Hello! Welcome to the smart door system.")
        
        time.sleep(1)
        
        # Step 2: Ask for name
        print("\n📍 STEP 2: ASKING FOR NAME")
        self.speak_and_log("What is your name?")
        
        # Listen for name
        user_name = self.listen_and_transcribe("Waiting for your name...")
        
        if user_name:
            response = f"Nice to meet you, {user_name}!"
            self.speak_and_log(response)
        else:
            self.speak_and_log("I didn't catch your name, but that's okay.")
        
        # Step 3: Wait (as requested)
        print("\n📍 STEP 3: WAITING...")
        print("⏳ Waiting for 3 seconds...")
        time.sleep(3)
        
        # Step 4: Ask purpose of visit
        print("\n📍 STEP 4: ASKING PURPOSE OF VISIT")
        self.speak_and_log("What is the purpose of your visit today?")
        
        # Listen for purpose
        purpose = self.listen_and_transcribe("Waiting for your purpose of visit...")
        
        if purpose:
            response = f"I understand. You're here because: {purpose}. Thank you for letting me know!"
            self.speak_and_log(response)
        else:
            self.speak_and_log("I didn't catch your purpose, but thank you for visiting.")
        
        # Step 5: Show complete transcription
        print("\n📍 STEP 5: COMPLETE CONVERSATION TRANSCRIPTION")
        self.show_complete_transcription()
        
        # Final message
        self.speak_and_log("Thank you for testing the conversation flow. Have a great day!")
    
    def show_complete_transcription(self):
        """Show the complete conversation transcription"""
        print("\n" + "="*60)
        print("📝 COMPLETE CONVERSATION TRANSCRIPTION")
        print("="*60)
        
        for i, entry in enumerate(self.conversation_log, 1):
            speaker_icon = "🤖" if entry['speaker'] == 'AI' else "👤"
            print(f"{i:2d}. [{entry['timestamp']}] {speaker_icon} {entry['speaker']}: {entry['text']}")
        
        print("="*60)
        
        # Save to file
        try:
            filename = f"conversation_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.conversation_log, f, indent=2)
            print(f"💾 Conversation saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save conversation: {e}")
    
    def quick_test_menu(self):
        """Quick test menu for debugging"""
        while True:
            print("\n" + "="*40)
            print("🧪 CONVERSATION FLOW TEST")
            print("="*40)
            print("1. 🎬 Run Full Conversation Flow")
            print("2. 🎤 Test Microphone Only")
            print("3. 🔊 Test Speaker Only")
            print("4. 💬 Quick Speech Test")
            print("5. 🚪 Exit")
            print("="*40)
            
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == '1':
                self.run_conversation_flow()
            
            elif choice == '2':
                print("🎤 Say something...")
                result = self.listen_and_transcribe()
                if result:
                    print(f"✅ Microphone working! Heard: {result}")
                else:
                    print("❌ Microphone test failed")
            
            elif choice == '3':
                self.speak_and_log("This is a speaker test. Can you hear me clearly?")
            
            elif choice == '4':
                self.speak_and_log("Please say hello")
                result = self.listen_and_transcribe()
                if result:
                    self.speak_and_log(f"I heard you say: {result}")
            
            elif choice == '5':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice!")

def main():
    """Main function"""
    print("🎬 Conversation Flow Test")
    print("=" * 25)
    
    try:
        # Check dependencies
        try:
            import speech_recognition as sr
            import pyttsx3
            import pyaudio
            print("✅ All dependencies available")
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Install with: pip install SpeechRecognition pyttsx3 pyaudio")
            return
        
        # Create and run test
        tester = ConversationFlowTest()
        
        print("\n🎯 This will test the exact flow you requested:")
        print("   1. Say 'Hello'")
        print("   2. Ask 'What's your name?'")
        print("   3. Wait for response and transcribe")
        print("   4. Wait 3 seconds")
        print("   5. Ask 'What's your purpose of visit?'")
        print("   6. Wait for response and transcribe")
        print("   7. Show complete transcription")
        
        input("\n🚀 Press Enter to start the conversation flow test...")
        
        tester.run_conversation_flow()
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
