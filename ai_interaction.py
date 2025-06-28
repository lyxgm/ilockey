import os
import json
import time
import threading
import queue
from datetime import datetime

class AIInteractionController:
    """AI Interaction Controller for Smart Door Lock"""
    
    def __init__(self):
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
        
        print("🤖 AI Interaction Controller initialized")

    def _init_speech_recognition(self):
        """Initialize speech recognition"""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            print("🎤 Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            self.speech_available = True
            print("✓ Speech recognition initialized")
            
        except ImportError:
            print("⚠ speech_recognition not available - using text simulation")
            self.speech_available = False
        except Exception as e:
            print(f"⚠ Speech recognition error: {e} - using simulation")
            self.speech_available = False

    def _init_text_to_speech(self):
        """Initialize text-to-speech"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS settings
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Use female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.setProperty('rate', 150)  # Speaking rate
            self.tts_engine.setProperty('volume', 0.8)  # Volume level
            
            self.tts_available = True
            print("✓ Text-to-speech initialized")
            
        except ImportError:
            print("⚠ pyttsx3 not available - using text output")
            self.tts_available = False
        except Exception as e:
            print(f"⚠ TTS error: {e} - using text output")
            self.tts_available = False

    def _load_ai_responses(self):
        """Load AI response templates"""
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
            'wait': [
                "Please wait a moment while I contact the residents.",
                "Let me check if anyone is available to speak with you.",
                "One moment please, I'm notifying the homeowner."
            ],
            'goodbye': [
                "Thank you for visiting! Have a great day!",
                "Goodbye! Take care!",
                "Thanks for stopping by. See you later!"
            ],
            'help': [
                "I can help you contact the residents, provide information, or answer questions.",
                "I'm here to assist visitors. I can call the homeowner or help with deliveries.",
                "You can ask me to contact someone inside, or let me know how I can help."
            ],
            'delivery': [
                "Are you making a delivery? I can notify the residents for you.",
                "For deliveries, I can let the homeowner know you're here.",
                "Is this a package delivery? I'll alert the residents."
            ],
            'unknown': [
                "I'm sorry, I didn't quite understand. Could you repeat that?",
                "Could you please rephrase that? I want to make sure I help you properly.",
                "I'm not sure I caught that. Can you say it again?"
            ]
        }

    def start_interaction(self, trigger_source="doorbell"):
        """Start AI interaction"""
        if self.active:
            print("🤖 AI interaction already active")
            return False
        
        self.active = True
        self.conversation_start = time.time()
        self.conversation_history = []
        
        print(f"🔔 AI interaction started (triggered by: {trigger_source})")
        
        # Start interaction in separate thread
        self.response_thread = threading.Thread(target=self._interaction_loop, daemon=True)
        self.response_thread.start()
        
        return True

    def stop_interaction(self):
        """Stop AI interaction"""
        if not self.active:
            print("🤖 AI interaction not active")
            return False
        
        self.active = False
        print("🔇 AI interaction stopped")
        
        # Save conversation log
        self._save_conversation_log()
        
        return True

    def _interaction_loop(self):
        """Main AI interaction loop"""
        try:
            # Initial greeting
            greeting = self._get_response('greeting')
            self._speak(greeting)
            self._log_conversation("AI", greeting)
            
            while self.active:
                # Check timeout
                if time.time() - self.conversation_start > self.max_conversation_time:
                    self._speak("I need to end our conversation now. Thank you for visiting!")
                    break
                
                # Listen for user input
                user_input = self._listen_for_input()
                
                if user_input:
                    self._log_conversation("User", user_input)
                    
                    # Process input and generate response
                    response = self._process_input(user_input)
                    self._speak(response)
                    self._log_conversation("AI", response)
                    
                    # Check for conversation end keywords
                    if any(word in user_input.lower() for word in ['goodbye', 'bye', 'thanks', 'thank you']):
                        goodbye = self._get_response('goodbye')
                        self._speak(goodbye)
                        self._log_conversation("AI", goodbye)
                        break
                
                time.sleep(0.5)
                
        except Exception as e:
            print(f"✗ Error in AI interaction loop: {e}")
        finally:
            self.active = False

    def _listen_for_input(self):
        """Listen for user voice input"""
        if not self.speech_available:
            # Simulate user input for testing
            return self._simulate_user_input()
        
        try:
            print("🎤 Listening...")
            
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=self.response_timeout, phrase_time_limit=5)
            
            print("🔄 Processing speech...")
            
            # Recognize speech using Google Speech Recognition
            text = self.recognizer.recognize_google(audio)
            print(f"👤 User said: {text}")
            return text
            
        except Exception as e:
            print(f"⚠ Speech recognition error: {e}")
            return None

    def _simulate_user_input(self):
        """Simulate user input for testing"""
        # Simulate different types of visitor interactions
        import random
        
        simulated_inputs = [
            "Hello, I'm here to see John",
            "I have a delivery for this address",
            "Hi, is anyone home?",
            "I'm looking for Sarah",
            "Can you help me?",
            "Thank you, goodbye"
        ]
        
        time.sleep(2)  # Simulate thinking time
        user_input = random.choice(simulated_inputs)
        print(f"👤 [Simulated] User said: {user_input}")
        return user_input

    def _process_input(self, user_input):
        """Process user input and generate appropriate response"""
        user_input_lower = user_input.lower()
        
        # Identify intent
        if any(word in user_input_lower for word in ['delivery', 'package', 'mail', 'ups', 'fedex', 'amazon']):
            intent = 'delivery'
        elif any(word in user_input_lower for word in ['see', 'looking for', 'visit', 'here for']):
            intent = 'identify'
        elif any(word in user_input_lower for word in ['help', 'assist', 'question']):
            intent = 'help'
        elif any(word in user_input_lower for word in ['wait', 'hold on', 'moment']):
            intent = 'wait'
        elif any(word in user_input_lower for word in ['hello', 'hi', 'hey']):
            intent = 'greeting'
        else:
            intent = 'unknown'
        
        # Generate contextual response
        response = self._get_response(intent)
        
        # Add personalization based on conversation history
        if intent == 'identify' and len(self.conversation_history) > 2:
            response += " I'll let them know you're here."
        elif intent == 'delivery':
            response += " Please wait while I notify the residents."
        
        return response

    def _get_response(self, intent):
        """Get a response for the given intent"""
        import random
        responses = self.responses.get(intent, self.responses['unknown'])
        return random.choice(responses)

    def _speak(self, text):
        """Convert text to speech"""
        print(f"🤖 AI: {text}")
        
        if self.tts_available:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"⚠ TTS error: {e}")
        else:
            # Simulate speaking delay
            time.sleep(len(text) * 0.05)  # Roughly simulate speaking time

    def _log_conversation(self, speaker, message):
        """Log conversation entry"""
        entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'speaker': speaker,
            'message': message
        }
        self.conversation_history.append(entry)

    def _save_conversation_log(self):
        """Save conversation to log file"""
        try:
            log_filename = f"conversation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            conversation_data = {
                'start_time': datetime.fromtimestamp(self.conversation_start).strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration': time.time() - self.conversation_start,
                'conversation': self.conversation_history
            }
            
            with open(log_filename, 'w') as f:
                json.dump(conversation_data, f, indent=2)
            
            print(f"💾 Conversation saved to: {log_filename}")
            
        except Exception as e:
            print(f"⚠ Error saving conversation log: {e}")

    def get_status(self):
        """Get current AI interaction status"""
        return {
            'active': self.active,
            'speech_available': self.speech_available,
            'tts_available': self.tts_available,
            'conversation_duration': time.time() - self.conversation_start if self.active else 0,
            'conversation_entries': len(self.conversation_history)
        }

def test_ai_features():
    """Test individual AI features"""
    print("🧪 Testing AI Features")
    print("=" * 30)
    
    ai = AIInteractionController()
    
    # Test 1: Check initialization
    print("\n1️⃣ Testing Initialization:")
    status = ai.get_status()
    print(f"   ✓ Speech Recognition: {'Available' if status['speech_available'] else 'Simulated'}")
    print(f"   ✓ Text-to-Speech: {'Available' if status['tts_available'] else 'Text Only'}")
    
    # Test 2: Test responses
    print("\n2️⃣ Testing AI Responses:")
    test_inputs = [
        "Hello, I'm here to see John",
        "I have a delivery",
        "Can you help me?",
        "Is anyone home?",
        "Thank you, goodbye"
    ]
    
    for test_input in test_inputs:
        print(f"\n   👤 Test Input: '{test_input}'")
        response = ai._process_input(test_input)
        print(f"   🤖 AI Response: '{response}'")
    
    print("\n✅ Feature testing complete!")

def quick_demo():
    """Quick 30-second demo of AI interaction"""
    print("🎬 Quick AI Demo (30 seconds)")
    print("=" * 35)
    
    ai = AIInteractionController()
    ai.max_conversation_time = 30  # Shorter for demo
    
    print("🔔 Starting AI interaction demo...")
    ai.start_interaction("demo")
    
    # Wait for demo to complete
    while ai.active:
        time.sleep(1)
    
    print("✅ Demo complete!")

def interactive_test():
    """Interactive testing mode"""
    print("🎮 Interactive AI Test Mode")
    print("=" * 30)
    print("Type messages to test AI responses")
    print("Type 'quit' to exit")
    
    ai = AIInteractionController()
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if user_input:
            response = ai._process_input(user_input)
            print(f"🤖 AI: {response}")
    
    print("👋 Interactive test ended")

# Update the main function with better menu
def main():
    """Main function for testing AI interaction"""
    print("🤖 AI Interaction Controller")
    print("=" * 40)
    
    while True:
        print("\n📋 Test Menu:")
        print("1. 🎬 Quick Demo (30 seconds)")
        print("2. 🧪 Test AI Features")
        print("3. 🎮 Interactive Test Mode")
        print("4. 🔄 Full Conversation Test")
        print("5. 📊 Check System Status")
        print("6. 🚪 Exit")
        
        choice = input("\n🔢 Choose test (1-6): ").strip()
        
        if choice == '1':
            quick_demo()
        
        elif choice == '2':
            test_ai_features()
        
        elif choice == '3':
            interactive_test()
        
        elif choice == '4':
            print("🔄 Starting full conversation test...")
            ai_controller = AIInteractionController()
            if ai_controller.start_interaction("full_test"):
                print("✓ Full test started - will run automatically")
                while ai_controller.active:
                    time.sleep(1)
                print("✅ Full test completed")
        
        elif choice == '5':
            ai = AIInteractionController()
            status = ai.get_status()
            print(f"\n📊 System Status:")
            print(f"   🎤 Speech Recognition: {'✅ Available' if status['speech_available'] else '⚠️  Simulated'}")
            print(f"   🔊 Text-to-Speech: {'✅ Available' if status['tts_available'] else '⚠️  Text Only'}")
            print(f"   🤖 AI Responses: ✅ Ready")
            print(f"   💾 Logging: ✅ Enabled")
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Try again.")
