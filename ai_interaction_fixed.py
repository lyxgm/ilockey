#!/usr/bin/env python3
import os
import json
import time
import threading
import queue
from datetime import datetime
import random

class AIInteractionController:
    """AI Interaction Controller for Smart Door Lock"""
    
    def __init__(self):
        print("🤖 Initializing AI Interaction Controller...")
        
        self.active = False
        self.conversation_history = []
        self.audio_queue = queue.Queue()
        self.response_thread = None
        
        # AI Configuration
        self.ai_enabled = True
        self.max_conversation_time = 60  # 60 seconds max
        self.response_timeout = 10  # 10 seconds to respond
        
        # Initialize components
        self._init_speech_recognition()
        self._init_text_to_speech()
        self._load_ai_responses()
        
        print("✅ AI Interaction Controller initialized successfully!")

    def _init_speech_recognition(self):
        """Initialize speech recognition"""
        print("🎤 Checking speech recognition...")
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Quick test without ambient noise calibration for now
            self.speech_available = True
            print("✅ Speech recognition available")
            
        except ImportError:
            print("⚠️  speech_recognition not installed - using simulation mode")
            self.speech_available = False
        except Exception as e:
            print(f"⚠️  Speech recognition error: {e} - using simulation mode")
            self.speech_available = False

    def _init_text_to_speech(self):
        """Initialize text-to-speech"""
        print("🔊 Checking text-to-speech...")
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Basic configuration
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.8)
            
            self.tts_available = True
            print("✅ Text-to-speech available")
            
        except ImportError:
            print("⚠️  pyttsx3 not installed - using text-only mode")
            self.tts_available = False
        except Exception as e:
            print(f"⚠️  TTS error: {e} - using text-only mode")
            self.tts_available = False

    def _load_ai_responses(self):
        """Load AI response templates"""
        print("🧠 Loading AI responses...")
        self.responses = {
            'greeting': [
                "Hello! Welcome to the smart door. How can I help you today?",
                "Hi there! I'm the AI assistant for this door. What can I do for you?",
                "Welcome! I'm here to help. Are you looking for someone specific?"
            ],
            'identify': [
                "Could you please tell me your name?",
                "Who are you here to see?",
                "May I ask who's visiting today?"
            ],
            'delivery': [
                "Are you making a delivery? I can notify the residents for you.",
                "For deliveries, I can let the homeowner know you're here.",
                "Is this a package delivery? I'll alert the residents."
            ],
            'help': [
                "I can help you contact the residents or answer questions.",
                "I'm here to assist visitors. How can I help you today?",
                "You can ask me to contact someone inside, or let me know what you need."
            ],
            'goodbye': [
                "Thank you for visiting! Have a great day!",
                "Goodbye! Take care!",
                "Thanks for stopping by. See you later!"
            ],
            'unknown': [
                "I'm sorry, I didn't quite understand. Could you repeat that?",
                "Could you please rephrase that?",
                "I'm not sure I caught that. Can you say it again?"
            ]
        }
        print("✅ AI responses loaded")

    def _get_response(self, intent):
        """Get a response for the given intent"""
        responses = self.responses.get(intent, self.responses['unknown'])
        return random.choice(responses)

    def _process_input(self, user_input):
        """Process user input and generate appropriate response"""
        user_input_lower = user_input.lower()
        
        # Simple intent detection
        if any(word in user_input_lower for word in ['delivery', 'package', 'mail']):
            intent = 'delivery'
        elif any(word in user_input_lower for word in ['see', 'looking for', 'visit']):
            intent = 'identify'
        elif any(word in user_input_lower for word in ['help', 'assist']):
            intent = 'help'
        elif any(word in user_input_lower for word in ['hello', 'hi', 'hey']):
            intent = 'greeting'
        elif any(word in user_input_lower for word in ['bye', 'goodbye', 'thanks']):
            intent = 'goodbye'
        else:
            intent = 'unknown'
        
        return self._get_response(intent)

    def _speak(self, text):
        """Convert text to speech or print"""
        print(f"🤖 AI: {text}")
        
        if self.tts_available:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"⚠️  TTS error: {e}")
        
        # Always add a small delay to simulate speaking
        time.sleep(len(text) * 0.03)

    def test_responses(self):
        """Test AI responses with sample inputs"""
        print("\n🧪 Testing AI Responses:")
        print("=" * 30)
        
        test_inputs = [
            "Hello, I'm here to see John",
            "I have a delivery for this address", 
            "Can you help me?",
            "Is anyone home?",
            "Thank you, goodbye"
        ]
        
        for i, test_input in enumerate(test_inputs, 1):
            print(f"\n{i}. 👤 Test: '{test_input}'")
            response = self._process_input(test_input)
            print(f"   🤖 Response: '{response}'")
            time.sleep(1)  # Pause between tests

    def interactive_chat(self):
        """Interactive chat mode"""
        print("\n💬 Interactive Chat Mode")
        print("=" * 25)
        print("Type your messages (or 'quit' to exit)")
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Chat ended")
                    break
                
                if user_input:
                    response = self._process_input(user_input)
                    self._speak(response)
                    
            except KeyboardInterrupt:
                print("\n👋 Chat interrupted")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def simulate_conversation(self):
        """Simulate a full conversation"""
        print("\n🎬 Simulating Visitor Conversation")
        print("=" * 35)
        
        # Simulated conversation flow
        conversation = [
            ("AI", "Hello! Welcome to the smart door. How can I help you today?"),
            ("Visitor", "Hi, I have a delivery for this address"),
            ("AI", "Are you making a delivery? I can notify the residents for you."),
            ("Visitor", "Yes, it's from Amazon"),
            ("AI", "Perfect! Let me alert the homeowner about your Amazon delivery."),
            ("Visitor", "Thank you so much"),
            ("AI", "You're welcome! Have a great day!")
        ]
        
        for speaker, message in conversation:
            if speaker == "AI":
                self._speak(message)
            else:
                print(f"👤 {speaker}: {message}")
                time.sleep(2)  # Pause between messages

    def get_status(self):
        """Get system status"""
        return {
            'speech_available': self.speech_available,
            'tts_available': self.tts_available,
            'responses_loaded': len(self.responses) > 0
        }

def show_menu():
    """Display the main menu"""
    print("\n" + "="*50)
    print("🤖 AI INTERACTION CONTROLLER")
    print("="*50)
    print("1. 📊 Check System Status")
    print("2. 🧪 Test AI Responses")
    print("3. 💬 Interactive Chat Mode")
    print("4. 🎬 Simulate Conversation")
    print("5. 🚪 Exit")
    print("="*50)

def main():
    """Main function"""
    print("🚀 Starting AI Interaction Controller...")
    
    try:
        # Initialize AI controller
        ai = AIInteractionController()
        
        while True:
            show_menu()
            
            try:
                choice = input("🔢 Enter your choice (1-5): ").strip()
                
                if choice == '1':
                    print("\n📊 System Status:")
                    status = ai.get_status()
                    print(f"   🎤 Speech Recognition: {'✅ Available' if status['speech_available'] else '⚠️  Simulated'}")
                    print(f"   🔊 Text-to-Speech: {'✅ Available' if status['tts_available'] else '⚠️  Text Only'}")
                    print(f"   🧠 AI Responses: {'✅ Loaded' if status['responses_loaded'] else '❌ Error'}")
                
                elif choice == '2':
                    ai.test_responses()
                
                elif choice == '3':
                    ai.interactive_chat()
                
                elif choice == '4':
                    ai.simulate_conversation()
                
                elif choice == '5':
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        return 1
    
    return 0

# Make sure this runs when called directly
if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
