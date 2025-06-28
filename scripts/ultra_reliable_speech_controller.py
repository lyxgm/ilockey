#!/usr/bin/env python3
"""
Ultra-Reliable Speech Controller for Smart Door Lock Integration
Integrates with the keypad D/# buttons and logs to the main system
"""

import subprocess
import time
import json
import os
import wave
import threading
import queue
import numpy as np
from datetime import datetime
from pathlib import Path

class UltraReliableSpeechController:
    """Ultra-reliable speech controller integrated with smart door lock system"""
    
    def __init__(self):
        """Initialize for smart door lock integration"""
        print("🚀 Initializing Ultra-Reliable Speech for Smart Door Lock...")
        
        self.conversation_active = False
        self.conversation_log = []
        self.stop_requested = False
        
        # Initialize speech engines
        self.engines = {}
        self.init_speech_engines()
        
        # Audio settings optimized for door lock use
        self.sample_rate = 16000
        self.confidence_threshold = 0.7
        self.max_conversation_time = 120  # 2 minutes max
        self.greeting_timeout = 8  # 8 seconds for responses
        
        print("✅ Ultra-Reliable Speech Controller ready for door lock!")
    
    def init_speech_engines(self):
        """Initialize all available speech engines"""
        # Vosk Engine
        try:
            import vosk
            model_paths = [
                Path.home() / "vosk-models" / "vosk-model-small-en-us-0.15",
                Path.home() / "vosk-models" / "vosk-model-en-us-0.22",
            ]
            
            model_path = None
            for path in model_paths:
                if path.exists():
                    model_path = str(path)
                    break
            
            if model_path:
                self.engines['vosk'] = {
                    'model': vosk.Model(model_path),
                    'recognizer': vosk.KaldiRecognizer(vosk.Model(model_path), self.sample_rate),
                    'available': True,
                    'confidence': 0.8
                }
                print("✅ Vosk engine loaded")
            else:
                self.engines['vosk'] = {'available': False}
        except:
            self.engines['vosk'] = {'available': False}
        
        # Google Engine
        try:
            import speech_recognition as sr
            self.engines['google'] = {
                'recognizer': sr.Recognizer(),
                'microphone': sr.Microphone(),
                'available': True,
                'confidence': 0.9
            }
            print("✅ Google Speech Recognition loaded")
        except:
            self.engines['google'] = {'available': False}
        
        # Whisper Engine
        try:
            import whisper
            model = whisper.load_model("base")
            self.engines['whisper'] = {
                'model': model,
                'available': True,
                'confidence': 0.95
            }
            print("✅ Whisper engine loaded")
        except:
            self.engines['whisper'] = {'available': False}
    
    def speak_to_visitor(self, text):
        """Speak to visitor through door system"""
        print(f"🤖 DOOR AI: {text}")
        
        # Log the AI speech
        self.conversation_log.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'speaker': 'AI',
            'text': text,
            'confidence': 1.0
        })
        
        # Use espeak for reliable TTS
        try:
            subprocess.run([
                'espeak', '-s', '140', '-a', '200', '-v', 'en+f3', text
            ], timeout=10)
        except:
            pass
        
        time.sleep(1)
    
    def record_visitor_audio(self, duration=6):
        """Record visitor audio through door microphone"""
        timestamp = int(time.time())
        filename = f"/tmp/door_visitor_{timestamp}.wav"
        
        try:
            print(f"🎤 Listening to visitor for {duration} seconds...")
            
            cmd = [
                'arecord',
                '-D', 'plughw:3,0',  # USB audio device
                '-f', 'S16_LE',
                '-r', str(self.sample_rate),
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
    
    def transcribe_visitor_speech(self, audio_file):
        """Transcribe visitor speech with multiple engines"""
        print("🔄 Transcribing visitor speech...")
        
        results = []
        
        # Try Whisper first (most accurate)
        if self.engines.get('whisper', {}).get('available'):
            try:
                model = self.engines['whisper']['model']
                result = model.transcribe(audio_file, language='en')
                text = result.get('text', '').strip()
                if text:
                    results.append({
                        'engine': 'whisper',
                        'text': text,
                        'confidence': 0.9
                    })
                    print(f"✅ WHISPER: '{text}'")
            except Exception as e:
                print(f"⚠️ Whisper failed: {e}")
        
        # Try Google as backup
        if self.engines.get('google', {}).get('available'):
            try:
                import speech_recognition as sr
                recognizer = self.engines['google']['recognizer']
                
                with sr.AudioFile(audio_file) as source:
                    audio = recognizer.record(source)
                
                text = recognizer.recognize_google(audio)
                if text:
                    results.append({
                        'engine': 'google',
                        'text': text,
                        'confidence': 0.85
                    })
                    print(f"✅ GOOGLE: '{text}'")
            except Exception as e:
                print(f"⚠️ Google failed: {e}")
        
        # Try Vosk as final backup
        if self.engines.get('vosk', {}).get('available'):
            try:
                recognizer = self.engines['vosk']['recognizer']
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
                    results.append({
                        'engine': 'vosk',
                        'text': text,
                        'confidence': 0.7
                    })
                    print(f"✅ VOSK: '{text}'")
            except Exception as e:
                print(f"⚠️ Vosk failed: {e}")
        
        # Choose best result
        if results:
            best_result = max(results, key=lambda x: x['confidence'])
            return best_result['text'], best_result['confidence']
        
        return None, 0
    
    def analyze_visitor_intent(self, text):
        """Analyze visitor's intent from speech"""
        if not text:
            return 'unknown'
        
        text_lower = text.lower()
        
        # Delivery detection
        if any(word in text_lower for word in ['delivery', 'package', 'mail', 'amazon', 'ups', 'fedex', 'dhl']):
            return 'delivery'
        
        # Visit detection
        elif any(word in text_lower for word in ['visit', 'see', 'looking for', 'here for', 'friend', 'family']):
            return 'visit'
        
        # Service detection
        elif any(word in text_lower for word in ['repair', 'maintenance', 'service', 'technician', 'plumber', 'electrician']):
            return 'service'
        
        # Emergency detection
        elif any(word in text_lower for word in ['emergency', 'urgent', 'help', 'police', 'fire', 'medical']):
            return 'emergency'
        
        # Greeting detection
        elif any(word in text_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return 'greeting'
        
        else:
            return 'general'
    
    def generate_smart_response(self, visitor_text, intent):
        """Generate smart response based on visitor's speech and intent"""
        responses = {
            'delivery': [
                "I understand you have a delivery. Let me notify the residents immediately.",
                "Thank you for the delivery. I'm alerting the homeowner now.",
                "Got it - you're here with a package. Please wait while I contact them."
            ],
            'visit': [
                "I heard you're here to visit someone. I'll let them know you're here.",
                "Thank you for visiting. I'm notifying the residents of your arrival.",
                "I understand you're here to see someone. Let me contact them for you."
            ],
            'service': [
                "I see you're here for service work. I'll notify the homeowner immediately.",
                "Thank you for coming. I'm alerting the residents about your service visit.",
                "I understand you're here for maintenance. Let me contact them right away."
            ],
            'emergency': [
                "I understand this is urgent. I'm immediately notifying the residents.",
                "This sounds important. I'm contacting them right now.",
                "I'll alert the homeowner immediately about your urgent matter."
            ],
            'greeting': [
                "Hello! Thank you for visiting. How can I help you today?",
                "Hi there! I'm the smart door assistant. What brings you here?",
                "Good day! I'm here to help. What can I do for you?"
            ],
            'general': [
                "I heard you, but could you please tell me more about your visit?",
                "Thank you for speaking. Could you clarify the purpose of your visit?",
                "I'm listening. Could you please explain why you're here today?"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses['general']))
    
    def run_doorbell_conversation(self):
        """Run the complete doorbell conversation flow"""
        if self.conversation_active:
            print("🤖 Conversation already active")
            return None
        
        self.conversation_active = True
        self.stop_requested = False
        self.conversation_log = []
        conversation_start = time.time()
        
        try:
            print("🔔 Starting Smart Door AI Conversation...")
            
            # Step 1: Initial greeting
            self.speak_to_visitor("Hello! Welcome to our smart door system. How can I help you today?")
            
            # Step 2: Listen for visitor response
            if not self.stop_requested:
                audio_file = self.record_visitor_audio(self.greeting_timeout)
                
                if audio_file:
                    visitor_text, confidence = self.transcribe_visitor_speech(audio_file)
                    
                    # Clean up audio file
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                    
                    if visitor_text and confidence > 0.5:
                        print(f"👤 VISITOR: '{visitor_text}' (confidence: {confidence:.2f})")
                        
                        # Log visitor speech
                        self.conversation_log.append({
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'speaker': 'VISITOR',
                            'text': visitor_text,
                            'confidence': confidence
                        })
                        
                        # Analyze intent and respond
                        intent = self.analyze_visitor_intent(visitor_text)
                        response = self.generate_smart_response(visitor_text, intent)
                        
                        print(f"🧠 Detected intent: {intent}")
                        
                        if not self.stop_requested:
                            self.speak_to_visitor(response)
                        
                        # For deliveries or services, ask for more details
                        if intent in ['delivery', 'service'] and not self.stop_requested:
                            time.sleep(2)
                            self.speak_to_visitor("Could you please provide any additional details?")
                            
                            # Listen for additional details
                            audio_file2 = self.record_visitor_audio(6)
                            if audio_file2:
                                details_text, details_confidence = self.transcribe_visitor_speech(audio_file2)
                                
                                try:
                                    os.remove(audio_file2)
                                except:
                                    pass
                                
                                if details_text and details_confidence > 0.4:
                                    print(f"👤 VISITOR DETAILS: '{details_text}' (confidence: {details_confidence:.2f})")
                                    
                                    self.conversation_log.append({
                                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                                        'speaker': 'VISITOR',
                                        'text': f"Additional details: {details_text}",
                                        'confidence': details_confidence
                                    })
                                    
                                    if not self.stop_requested:
                                        self.speak_to_visitor("Perfect! I have all the information. The residents have been notified.")
                    else:
                        print("⚠️ Could not understand visitor clearly")
                        if not self.stop_requested:
                            self.speak_to_visitor("I'm sorry, I didn't catch that clearly. The residents have been notified of your visit.")
                else:
                    print("⚠️ No audio recorded from visitor")
                    if not self.stop_requested:
                        self.speak_to_visitor("I didn't hear a response, but I've notified the residents of your presence.")
            
            # Final message
            if not self.stop_requested:
                self.speak_to_visitor("Thank you for visiting! Have a great day!")
            
            print("✅ Smart door conversation completed")
            
        except Exception as e:
            print(f"❌ Error in door conversation: {e}")
            if not self.stop_requested:
                self.speak_to_visitor("Thank you for your patience. The residents have been notified.")
        
        finally:
            self.conversation_active = False
            
            # Return conversation log for system logging
            return self.conversation_log.copy() if self.conversation_log else None
    
    def stop_conversation(self):
        """Stop the conversation (called by # key)"""
        print("🛑 Stopping door AI conversation...")
        self.stop_requested = True
        self.conversation_active = False
    
    def is_active(self):
        """Check if conversation is active"""
        return self.conversation_active

# Test function for standalone testing
def test_door_speech():
    """Test the door speech system"""
    print("🧪 Testing Smart Door Speech System")
    
    controller = UltraReliableSpeechController()
    
    print("\n🔔 Simulating doorbell press (D key)...")
    result = controller.run_doorbell_conversation()
    
    if result:
        print("\n📝 Conversation Log:")
        for entry in result:
            speaker_icon = "🤖" if entry['speaker'] == 'AI' else "👤"
            confidence_str = f" ({entry['confidence']:.2f})" if 'confidence' in entry else ""
            print(f"[{entry['timestamp']}] {speaker_icon} {entry['speaker']}: {entry['text']}{confidence_str}")

if __name__ == "__main__":
    test_door_speech()
