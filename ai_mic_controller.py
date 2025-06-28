#!/usr/bin/env python3
import os
import json
import time
import threading
import queue
from datetime import datetime
import random

class AIMicController:
    """AI Controller with Real Microphone Support"""
    
    def __init__(self):
        print("🎤 Initializing AI Microphone Controller...")
        
        self.active = False
        self.conversation_history = []
        self.listening = False
        
        # Initialize speech recognition
        self._init_speech_recognition()
        self._init_text_to_speech()
        self._load_ai_responses()
        
        print("✅ AI Microphone Controller ready!")

    def _init_speech_recognition(self):
        """Initialize speech recognition with microphone"""
        print("🎤 Setting up microphone...")
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            print("🔧 Calibrating microphone for ambient noise...")
            with self.microphone as source:
                print("   📢 Please be quiet for 2 seconds...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print("   ✅ Microphone calibrated!")
            
            # Test microphone
            print("🧪 Testing microphone...")
            self._test_microphone()
            
            self.speech_available = True
            print("✅ Microphone ready for speech recognition!")
            
        except ImportError:
            print("❌ speech_recognition not installed!")
            print("   Run: pip install SpeechRecognition pyaudio")
            self.speech_available = False
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            print("   Make sure your microphone is connected and working")
            self.speech_available = False

    def _test_microphone(self):
        """Test microphone functionality"""
        try:
            import speech_recognition as sr
            
            # Quick 1-second test
            with self.microphone as source:
                print("   🎧 Listening for 1 second...")
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=1)
                print("   ✅ Audio captured successfully!")
                
        except sr.WaitTimeoutError:
            print("   ⚠️  No audio detected (this is normal)")
        except Exception as e:
            print(f"   ⚠️  Test warning: {e}")

    def _init_text_to_speech(self):
        """Initialize text-to-speech"""
        print("🔊 Setting up text-to-speech...")
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Configure voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            
            self.tts_available = True
            print("✅ Text-to-speech ready!")
            
        except ImportError:
            print("❌ pyttsx3 not installed!")
            print("   Run: pip install pyttsx3")
            self.tts_available = False
        except Exception as e:
            print(f"❌ TTS error: {e}")
            self.tts_available = False

    def _load_ai_responses(self):
        """Load AI response templates"""
        self.responses = {
            'greeting': [
                "Hello! I can hear you clearly. How can I help you today?",
                "Hi there! I'm listening. What brings you here?",
                "Welcome! I heard you. How may I assist you?"
            ],
            'delivery': [
                "I understand you have a delivery. Let me notify the residents right away.",
                "Got it - you're here with a package. I'll alert the homeowner immediately.",
                "Perfect! I'll let them know about the delivery. Please wait a moment."
            ],
            'visit': [
                "I heard you're here to visit someone. Who are you looking for?",
                "You're here to see someone? Could you tell me their name?",
                "I understand you're visiting. Who should I contact for you?"
            ],
            'help': [
                "I heard you need help. I can contact the residents or answer questions.",
                "You need assistance? I'm here to help. What do you need?",
                "I understand you need help. How can I assist you today?"
            ],
            'unclear': [
                "I'm sorry, I didn't catch that clearly. Could you speak a bit louder?",
                "I heard you but couldn't understand. Could you repeat that please?",
                "Sorry, the audio wasn't clear. Could you say that again?"
            ],
            'goodbye': [
                "Thank you! Have a wonderful day!",
                "You're welcome! Take care!",
                "Goodbye! Thanks for visiting!"
            ]
        }

    def _speak(self, text):
        """Speak the response"""
        print(f"🤖 AI: {text}")
        
        if self.tts_available:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"⚠️  TTS error: {e}")

    def _listen_for_speech(self, timeout=5):
        """Listen for speech from microphone"""
        if not self.speech_available:
            print("❌ Speech recognition not available!")
            return None
        
        try:
            import speech_recognition as sr
            
            print(f"🎧 Listening for {timeout} seconds...")
            print("   💬 Please speak now...")
            
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            print("🔄 Processing speech...")
            
            # Try Google Speech Recognition first
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"✅ Heard: '{text}'")
                return text
                
            except sr.UnknownValueError:
                print("⚠️  Could not understand the audio")
                return "unclear"
                
            except sr.RequestError as e:
                print(f"⚠️  Google Speech Recognition error: {e}")
                
                # Fallback to offline recognition
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    print(f"✅ Heard (offline): '{text}'")
                    return text
                except:
                    print("⚠️  Offline recognition also failed")
                    return "unclear"
                    
        except sr.WaitTimeoutError:
            print("⏰ No speech detected in time limit")
            return None
            
        except Exception as e:
            print(f"❌ Speech recognition error: {e}")
            return None

    def _process_speech(self, text):
        """Process recognized speech and generate response"""
        if not text or text == "unclear":
            return self.responses['unclear'][0]
        
        text_lower = text.lower()
        
        # Intent detection
        if any(word in text_lower for word in ['delivery', 'package', 'mail', 'amazon', 'ups', 'fedex']):
            intent = 'delivery'
        elif any(word in text_lower for word in ['visit', 'see', 'looking for', 'here for']):
            intent = 'visit'
        elif any(word in text_lower for word in ['help', 'assist', 'need']):
            intent = 'help'
        elif any(word in text_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            intent = 'greeting'
        elif any(word in text_lower for word in ['bye', 'goodbye', 'thank you', 'thanks']):
            intent = 'goodbye'
        else:
            intent = 'greeting'  # Default to greeting for unknown
        
        return random.choice(self.responses[intent])

    def start_conversation(self):
        """Start a voice conversation"""
        if not self.speech_available:
            print("❌ Cannot start voice conversation - microphone not available!")
            return
        
        print("\n🎤 Starting Voice Conversation")
        print("=" * 35)
        
        # Greet the visitor
        greeting = "Hello! I can hear you. How can I help you today?"
        self._speak(greeting)
        
        conversation_count = 0
        max_exchanges = 5  # Limit conversation length
        
        while conversation_count < max_exchanges:
            # Listen for response
            speech_text = self._listen_for_speech(timeout=10)
            
            if speech_text is None:
                self._speak("I didn't hear anything. Have a great day!")
                break
            
            # Process and respond
            response = self._process_speech(speech_text)
            self._speak(response)
            
            # Check if conversation should end
            if speech_text and any(word in speech_text.lower() for word in ['bye', 'goodbye', 'thank you', 'thanks']):
                break
                
            conversation_count += 1
        
        print("✅ Conversation ended")

    def test_microphone_live(self):
        """Test microphone with live audio"""
        if not self.speech_available:
            print("❌ Microphone not available for testing!")
            return
        
        print("\n🎤 Live Microphone Test")
        print("=" * 25)
        print("Say something and I'll repeat it back!")
        print("Say 'stop' to end the test")
        
        while True:
            speech_text = self._listen_for_speech(timeout=8)
            
            if speech_text is None:
                print("⏰ No speech detected. Try again or say 'stop' to exit.")
                continue
            
            if speech_text.lower() in ['stop', 'quit', 'exit']:
                print("🛑 Microphone test ended")
                break
            
            if speech_text == "unclear":
                print("⚠️  Audio was unclear. Please speak more clearly.")
                continue
            
            print(f"🔄 You said: '{speech_text}'")
            self._speak(f"I heard you say: {speech_text}")

    def get_audio_devices(self):
        """List available audio devices"""
        try:
            import pyaudio
            
            print("\n🎧 Available Audio Devices:")
            print("=" * 30)
            
            p = pyaudio.PyAudio()
            
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:  # Input device
                    print(f"🎤 {i}: {info['name']} (Input)")
                elif info['maxOutputChannels'] > 0:  # Output device
                    print(f"🔊 {i}: {info['name']} (Output)")
            
            p.terminate()
            
        except ImportError:
            print("❌ pyaudio not installed - cannot list devices")
        except Exception as e:
            print(f"❌ Error listing devices: {e}")

def show_menu():
    """Display menu"""
    print("\n" + "="*50)
    print("🎤 AI MICROPHONE CONTROLLER")
    print("="*50)
    print("1. 🎧 List Audio Devices")
    print("2. 🧪 Test Microphone")
    print("3. 🎤 Start Voice Conversation")
    print("4. 📊 Check System Status")
    print("5. 🚪 Exit")
    print("="*50)

def main():
    """Main function"""
    print("🚀 Starting AI Microphone Controller...")
    
    # Check dependencies first
    try:
        import speech_recognition
        import pyaudio
        print("✅ Required packages found")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("\n📦 Install required packages:")
        print("   pip install SpeechRecognition pyaudio pyttsx3")
        print("\n🐧 On Raspberry Pi, you might also need:")
        print("   sudo apt-get install portaudio19-dev python3-pyaudio")
        return 1
    
    try:
        ai = AIMicController()
        
        while True:
            show_menu()
            
            try:
                choice = input("🔢 Enter choice (1-5): ").strip()
                
                if choice == '1':
                    ai.get_audio_devices()
                
                elif choice == '2':
                    ai.test_microphone_live()
                
                elif choice == '3':
                    ai.start_conversation()
                
                elif choice == '4':
                    print(f"\n📊 System Status:")
                    print(f"   🎤 Speech Recognition: {'✅ Ready' if ai.speech_available else '❌ Not Available'}")
                    print(f"   🔊 Text-to-Speech: {'✅ Ready' if ai.tts_available else '❌ Not Available'}")
                
                elif choice == '5':
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice")
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted")
                break
                
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
