#!/usr/bin/env python3
import subprocess
import time
import json
import os
from datetime import datetime

class SimpleWorkingConversation:
    def __init__(self):
        """Initialize simple conversation system"""
        print("🤖 Initializing Simple Working Conversation...")
        
        self.conversation_log = []
        
        # Check if we have basic audio tools
        self.check_audio_tools()
        
        print("✅ Simple conversation system ready!")
    
    def check_audio_tools(self):
        """Check available audio tools"""
        print("🔧 Checking audio tools...")
        
        # Check for espeak
        try:
            subprocess.run(['espeak', '--version'], capture_output=True, check=True)
            self.has_espeak = True
            print("✅ espeak available")
        except:
            self.has_espeak = False
            print("⚠️  espeak not available")
        
        # Check for arecord/aplay
        try:
            subprocess.run(['arecord', '--version'], capture_output=True, check=True)
            self.has_arecord = True
            print("✅ arecord available")
        except:
            self.has_arecord = False
            print("⚠️  arecord not available")
    
    def speak(self, text):
        """Speak text using available TTS"""
        print(f"\n🤖 AI SAYS: {text}")
        print("-" * 50)
        
        # Log the conversation
        self.conversation_log.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'speaker': 'AI',
            'text': text
        })
        
        # Try to speak using espeak
        if self.has_espeak:
            try:
                # Use espeak with slower speed and higher volume
                cmd = ['espeak', '-s', '140', '-a', '200', '-v', 'en+f3', text]
                subprocess.run(cmd, check=True)
                print("🔊 Audio played successfully")
            except Exception as e:
                print(f"⚠️  Audio failed: {e}")
        else:
            print("📝 Text-only mode (install espeak for audio)")
        
        time.sleep(1)
    
    def record_audio_file(self, duration=5):
        """Record audio to file using arecord"""
        if not self.has_arecord:
            print("❌ arecord not available")
            return None
        
        filename = f"/tmp/recording_{int(time.time())}.wav"
        
        try:
            print(f"🎤 Recording for {duration} seconds...")
            print("🗣️  SPEAK NOW!")
            
            # Record using your USB audio device
            cmd = [
                'arecord',
                '-D', 'plughw:3,0',  # Your USB audio device
                '-f', 'S16_LE',
                '-r', '16000',
                '-c', '1',
                '-d', str(duration),
                filename
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Recording completed")
                return filename
            else:
                print(f"❌ Recording failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return None
    
    def transcribe_with_vosk(self, audio_file):
        """Try to transcribe using Vosk (offline)"""
        try:
            import vosk
            import wave
            
            # Load Vosk model (you'd need to download this)
            model = vosk.Model("vosk-model-small-en-us-0.15")
            rec = vosk.KaldiRecognizer(model, 16000)
            
            wf = wave.open(audio_file, 'rb')
            
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get('text'):
                        results.append(result['text'])
            
            final_result = json.loads(rec.FinalResult())
            if final_result.get('text'):
                results.append(final_result['text'])
            
            return ' '.join(results) if results else None
            
        except ImportError:
            print("⚠️  Vosk not installed")
            return None
        except Exception as e:
            print(f"⚠️  Vosk transcription failed: {e}")
            return None
    
    def get_user_input_manual(self, prompt):
        """Get user input manually (fallback)"""
        print(f"\n🎧 {prompt}")
        print("🎤 Since speech recognition isn't working, please type your response:")
        
        try:
            user_input = input("👤 Type here: ").strip()
            if user_input:
                print(f"👤 USER SAID: '{user_input}'")
                print("=" * 50)
                
                # Log the user response
                self.conversation_log.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'speaker': 'USER',
                    'text': user_input
                })
                
                return user_input
            else:
                return None
        except KeyboardInterrupt:
            return None
    
    def listen_and_transcribe(self, prompt="", duration=5):
        """Listen and transcribe with multiple fallback methods"""
        print(f"\n🎧 {prompt}")
        print("🎤 LISTENING... (speak clearly)")
        print("=" * 50)
        
        # Method 1: Try recording audio
        audio_file = self.record_audio_file(duration)
        
        if audio_file:
            print("🔄 TRANSCRIBING...")
            
            # Try Vosk offline transcription
            text = self.transcribe_with_vosk(audio_file)
            
            # Clean up audio file
            try:
                os.remove(audio_file)
            except:
                pass
            
            if text and text.strip():
                print(f"👤 USER SAID: '{text}'")
                print("=" * 50)
                
                # Log the user response
                self.conversation_log.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'speaker': 'USER',
                    'text': text
                })
                
                return text
        
        # Fallback: Manual input
        print("❌ Speech recognition failed")
        return self.get_user_input_manual("Please type your response instead:")
    
    def test_audio_setup(self):
        """Test audio setup"""
        print("\n🧪 TESTING AUDIO SETUP")
        print("=" * 30)
        
        # Test speaker
        print("🔊 Testing speaker...")
        self.speak("This is a speaker test. Can you hear me clearly?")
        
        # Test microphone
        print("\n🎤 Testing microphone...")
        result = self.listen_and_transcribe("Say 'hello test'...", 3)
        
        if result:
            print("✅ Audio test completed!")
            self.speak(f"Great! I heard: {result}")
            return True
        else:
            print("⚠️  Using manual input mode")
            return False
    
    def run_conversation_flow(self):
        """Run the exact conversation flow requested"""
        print("\n" + "="*60)
        print("🎬 CONVERSATION FLOW: Hello → Name → Wait → Purpose")
        print("="*60)
        
        # Step 1: Say Hello
        print("\n📍 STEP 1: GREETING")
        self.speak("Hello! Welcome to the smart door system.")
        
        time.sleep(2)
        
        # Step 2: Ask for name
        print("\n📍 STEP 2: ASKING FOR NAME")
        self.speak("What is your name?")
        
        # Listen for name
        user_name = self.listen_and_transcribe("Please tell me your name...", 5)
        
        if user_name:
            response = f"Nice to meet you, {user_name}!"
            self.speak(response)
        else:
            self.speak("I didn't catch your name, but that's okay.")
        
        # Step 3: Wait (as requested)
        print("\n📍 STEP 3: WAITING...")
        print("⏳ Waiting for 3 seconds as requested...")
        time.sleep(3)
        
        # Step 4: Ask purpose
        print("\n📍 STEP 4: ASKING PURPOSE OF VISIT")
        self.speak("What is the purpose of your visit today?")
        
        # Listen for purpose
        purpose = self.listen_and_transcribe("Please tell me why you're here...", 7)
        
        if purpose:
            response = f"I understand. You're here because: {purpose}. Thank you!"
            self.speak(response)
        else:
            self.speak("Thank you for visiting.")
        
        # Step 5: Show complete transcription
        print("\n📍 STEP 5: COMPLETE TRANSCRIPTION")
        self.show_transcription()
        
        self.speak("Conversation flow completed. Thank you!")
    
    def show_transcription(self):
        """Show complete conversation transcription"""
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

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing Dependencies...")
    print("=" * 30)
    
    commands = [
        "sudo apt-get update",
        "sudo apt-get install -y espeak espeak-data",
        "sudo apt-get install -y alsa-utils",
        "pip install vosk"  # Optional offline speech recognition
    ]
    
    for cmd in commands:
        print(f"🔧 Running: {cmd}")
        try:
            subprocess.run(cmd.split(), check=True)
            print("✅ Success")
        except Exception as e:
            print(f"⚠️  Warning: {e}")

def main():
    """Main function"""
    print("🎬 Simple Working Conversation Test")
    print("=" * 40)
    
    try:
        tester = SimpleWorkingConversation()
        
        while True:
            print("\n" + "="*40)
            print("🎤 SIMPLE CONVERSATION MENU")
            print("="*40)
            print("1. 📦 Install Dependencies")
            print("2. 🧪 Test Audio Setup")
            print("3. 🎬 Run Conversation Flow")
            print("4. 🎤 Quick Mic Test")
            print("5. 🔊 Quick Speaker Test")
            print("6. 🚪 Exit")
            print("="*40)
            
            choice = input("Enter choice (1-6): ").strip()
            
            if choice == '1':
                install_dependencies()
            elif choice == '2':
                tester.test_audio_setup()
            elif choice == '3':
                print("\n🚀 Starting conversation flow...")
                input("Press Enter when ready...")
                tester.run_conversation_flow()
            elif choice == '4':
                result = tester.listen_and_transcribe("Say something...", 3)
                if result:
                    tester.speak(f"I heard: {result}")
            elif choice == '5':
                tester.speak("This is a speaker test. Can you hear me?")
            elif choice == '6':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice!")
    
    except KeyboardInterrupt:
        print("\n🛑 Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
