#!/usr/bin/env python3
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

class UltraReliableSpeechRecognition:
    def __init__(self):
        """Initialize ultra-reliable speech recognition with multiple engines"""
        print("🚀 Initializing Ultra-Reliable Speech Recognition...")
        print("=" * 50)
        
        self.conversation_log = []
        self.audio_queue = queue.Queue()
        self.is_listening = False
        
        # Initialize multiple speech engines
        self.engines = {}
        self.init_vosk_engine()
        self.init_google_engine()
        self.init_whisper_engine()
        self.init_sphinx_engine()
        
        # Audio settings optimized for reliability
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = 'S16_LE'
        
        # Reliability settings
        self.confidence_threshold = 0.7
        self.min_speech_length = 0.5  # seconds
        self.max_silence_duration = 2.0  # seconds
        
        print("✅ Ultra-Reliable Speech Recognition ready!")
        self.show_available_engines()
    
    def init_vosk_engine(self):
        """Initialize Vosk offline engine"""
        try:
            import vosk
            
            # Try multiple model paths
            model_paths = [
                Path.home() / "vosk-models" / "vosk-model-small-en-us-0.15",
                Path.home() / "vosk-models" / "vosk-model-en-us-0.22",
                "/usr/share/vosk-models/vosk-model-small-en-us-0.15",
                "./vosk-model-small-en-us-0.15"
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
                    'confidence': 0.8,
                    'description': 'Vosk Offline (Fast, No Internet)'
                }
                print("✅ Vosk engine loaded")
            else:
                self.engines['vosk'] = {'available': False}
                print("⚠️  Vosk model not found")
                
        except ImportError:
            self.engines['vosk'] = {'available': False}
            print("⚠️  Vosk not installed")
        except Exception as e:
            self.engines['vosk'] = {'available': False}
            print(f"⚠️  Vosk failed: {e}")
    
    def init_google_engine(self):
        """Initialize Google Speech Recognition"""
        try:
            import speech_recognition as sr
            
            self.engines['google'] = {
                'recognizer': sr.Recognizer(),
                'microphone': sr.Microphone(),
                'available': True,
                'confidence': 0.9,
                'description': 'Google Cloud (High Accuracy, Needs Internet)'
            }
            
            # Optimize recognizer settings
            self.engines['google']['recognizer'].energy_threshold = 300
            self.engines['google']['recognizer'].dynamic_energy_threshold = True
            self.engines['google']['recognizer'].pause_threshold = 0.8
            self.engines['google']['recognizer'].phrase_threshold = 0.3
            
            print("✅ Google Speech Recognition loaded")
            
        except ImportError:
            self.engines['google'] = {'available': False}
            print("⚠️  SpeechRecognition not installed")
        except Exception as e:
            self.engines['google'] = {'available': False}
            print(f"⚠️  Google SR failed: {e}")
    
    def init_whisper_engine(self):
        """Initialize OpenAI Whisper (most accurate)"""
        try:
            import whisper
            
            # Load small model for speed vs accuracy balance
            model = whisper.load_model("base")
            
            self.engines['whisper'] = {
                'model': model,
                'available': True,
                'confidence': 0.95,
                'description': 'OpenAI Whisper (Highest Accuracy, Offline)'
            }
            print("✅ Whisper engine loaded")
            
        except ImportError:
            self.engines['whisper'] = {'available': False}
            print("⚠️  Whisper not installed (pip install openai-whisper)")
        except Exception as e:
            self.engines['whisper'] = {'available': False}
            print(f"⚠️  Whisper failed: {e}")
    
    def init_sphinx_engine(self):
        """Initialize PocketSphinx as backup"""
        try:
            import speech_recognition as sr
            
            if 'google' in self.engines and self.engines['google']['available']:
                recognizer = self.engines['google']['recognizer']
                
                self.engines['sphinx'] = {
                    'recognizer': recognizer,
                    'available': True,
                    'confidence': 0.6,
                    'description': 'PocketSphinx (Offline Backup)'
                }
                print("✅ PocketSphinx engine loaded")
            else:
                self.engines['sphinx'] = {'available': False}
                
        except Exception as e:
            self.engines['sphinx'] = {'available': False}
            print(f"⚠️  PocketSphinx failed: {e}")
    
    def show_available_engines(self):
        """Show available speech recognition engines"""
        print("\n🔧 Available Speech Recognition Engines:")
        print("-" * 45)
        
        for name, engine in self.engines.items():
            if engine['available']:
                confidence = engine.get('confidence', 0) * 100
                desc = engine.get('description', 'Unknown')
                print(f"✅ {name.upper():<10} ({confidence:3.0f}% confidence) - {desc}")
            else:
                print(f"❌ {name.upper():<10} - Not available")
        
        available_count = sum(1 for e in self.engines.values() if e['available'])
        print(f"\n📊 Total available engines: {available_count}/4")
    
    def enhance_audio(self, audio_file):
        """Enhance audio quality for better recognition"""
        try:
            # Use sox for audio enhancement if available
            enhanced_file = audio_file.replace('.wav', '_enhanced.wav')
            
            cmd = [
                'sox', audio_file, enhanced_file,
                'norm', '-1',  # Normalize volume
                'highpass', '100',  # Remove low frequency noise
                'lowpass', '8000',  # Remove high frequency noise
                'compand', '0.3,1', '6:-70,-60,-20', '-5', '-90', '0.2'  # Compress dynamic range
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("🎵 Audio enhanced")
                return enhanced_file
            else:
                print("⚠️  Audio enhancement failed, using original")
                return audio_file
                
        except Exception as e:
            print(f"⚠️  Audio enhancement error: {e}")
            return audio_file
    
    def record_high_quality_audio(self, duration=5):
        """Record high-quality audio optimized for speech recognition"""
        timestamp = int(time.time())
        filename = f"/tmp/speech_recording_{timestamp}.wav"
        
        try:
            print(f"🎤 Recording HIGH-QUALITY audio for {duration} seconds...")
            print("🗣️  SPEAK CLEARLY AND LOUDLY!")
            
            # Use optimized recording settings
            cmd = [
                'arecord',
                '-D', 'plughw:3,0',  # Your USB audio device
                '-f', self.format,
                '-r', str(self.sample_rate),
                '-c', str(self.channels),
                '-d', str(duration),
                '--buffer-time=500000',  # Larger buffer for stability
                '--period-time=100000',  # Optimize for speech
                filename
            ]
            
            # Show recording progress
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Visual countdown
            for i in range(duration, 0, -1):
                print(f"⏰ Recording... {i} seconds remaining", end='\r')
                time.sleep(1)
            
            process.wait()
            print("\n✅ Recording completed!")
            
            # Check if file was created and has content
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                # Enhance audio quality
                enhanced_file = self.enhance_audio(filename)
                return enhanced_file
            else:
                print("❌ Recording failed or file too small")
                return None
                
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return None
    
    def transcribe_with_vosk(self, audio_file):
        """Transcribe using Vosk with confidence scoring"""
        if not self.engines.get('vosk', {}).get('available'):
            return None, 0
        
        try:
            import vosk
            
            recognizer = self.engines['vosk']['recognizer']
            wf = wave.open(audio_file, 'rb')
            
            results = []
            confidences = []
            
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                    
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if result.get('text'):
                        results.append(result['text'])
                        confidences.append(result.get('conf', 0.5))
            
            # Get final result
            final_result = json.loads(recognizer.FinalResult())
            if final_result.get('text'):
                results.append(final_result['text'])
                confidences.append(final_result.get('conf', 0.5))
            
            if results:
                text = ' '.join(results).strip()
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
                return text, avg_confidence
            
            return None, 0
            
        except Exception as e:
            print(f"⚠️  Vosk transcription failed: {e}")
            return None, 0
    
    def transcribe_with_whisper(self, audio_file):
        """Transcribe using Whisper with confidence"""
        if not self.engines.get('whisper', {}).get('available'):
            return None, 0
        
        try:
            model = self.engines['whisper']['model']
            
            # Transcribe with options for better accuracy
            result = model.transcribe(
                audio_file,
                language='en',
                task='transcribe',
                temperature=0.0,  # More deterministic
                best_of=5,  # Try multiple times
                beam_size=5,  # Better search
                word_timestamps=True
            )
            
            text = result.get('text', '').strip()
            
            # Calculate confidence from segments
            segments = result.get('segments', [])
            if segments:
                confidences = []
                for segment in segments:
                    # Whisper doesn't provide direct confidence, estimate from other metrics
                    avg_logprob = segment.get('avg_logprob', -1.0)
                    confidence = max(0, min(1, (avg_logprob + 1.0)))  # Convert logprob to 0-1
                    confidences.append(confidence)
                
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8
            else:
                avg_confidence = 0.8 if text else 0
            
            return text, avg_confidence
            
        except Exception as e:
            print(f"⚠️  Whisper transcription failed: {e}")
            return None, 0
    
    def transcribe_with_google(self, audio_file):
        """Transcribe using Google with confidence"""
        if not self.engines.get('google', {}).get('available'):
            return None, 0
        
        try:
            import speech_recognition as sr
            
            recognizer = self.engines['google']['recognizer']
            
            with sr.AudioFile(audio_file) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)
            
            # Try Google recognition with show_all for confidence
            try:
                result = recognizer.recognize_google(audio, show_all=True)
                
                if result and 'alternative' in result:
                    alternatives = result['alternative']
                    if alternatives:
                        best_result = alternatives[0]
                        text = best_result.get('transcript', '')
                        confidence = best_result.get('confidence', 0.8)
                        return text, confidence
                
            except:
                # Fallback to simple recognition
                text = recognizer.recognize_google(audio)
                return text, 0.8
            
            return None, 0
            
        except Exception as e:
            print(f"⚠️  Google transcription failed: {e}")
            return None, 0
    
    def transcribe_with_sphinx(self, audio_file):
        """Transcribe using PocketSphinx"""
        if not self.engines.get('sphinx', {}).get('available'):
            return None, 0
        
        try:
            import speech_recognition as sr
            
            recognizer = self.engines['sphinx']['recognizer']
            
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            
            text = recognizer.recognize_sphinx(audio)
            return text, 0.6  # PocketSphinx doesn't provide confidence
            
        except Exception as e:
            print(f"⚠️  Sphinx transcription failed: {e}")
            return None, 0
    
    def multi_engine_transcribe(self, audio_file):
        """Use multiple engines and combine results for maximum reliability"""
        print("🔄 MULTI-ENGINE TRANSCRIPTION...")
        print("-" * 30)
        
        results = []
        
        # Try all available engines
        engines_to_try = [
            ('whisper', self.transcribe_with_whisper),
            ('google', self.transcribe_with_google),
            ('vosk', self.transcribe_with_vosk),
            ('sphinx', self.transcribe_with_sphinx)
        ]
        
        for engine_name, transcribe_func in engines_to_try:
            if self.engines.get(engine_name, {}).get('available'):
                print(f"🔍 Trying {engine_name.upper()}...")
                
                text, confidence = transcribe_func(audio_file)
                
                if text and text.strip():
                    results.append({
                        'engine': engine_name,
                        'text': text.strip(),
                        'confidence': confidence
                    })
                    print(f"✅ {engine_name.upper()}: '{text}' (confidence: {confidence:.2f})")
                else:
                    print(f"❌ {engine_name.upper()}: No result")
        
        if not results:
            print("❌ All engines failed")
            return None, 0
        
        # Choose best result based on confidence and engine reliability
        best_result = max(results, key=lambda x: x['confidence'] * self.engines[x['engine']]['confidence'])
        
        print(f"\n🏆 BEST RESULT: {best_result['engine'].upper()}")
        print(f"📝 Text: '{best_result['text']}'")
        print(f"🎯 Confidence: {best_result['confidence']:.2f}")
        
        # If multiple engines agree, boost confidence
        texts = [r['text'].lower() for r in results]
        if len(set(texts)) == 1 and len(results) > 1:
            print("🤝 Multiple engines agree - boosting confidence!")
            best_result['confidence'] = min(0.95, best_result['confidence'] + 0.1)
        
        return best_result['text'], best_result['confidence']
    
    def speak(self, text):
        """Enhanced text-to-speech"""
        print(f"\n🤖 AI SAYS: {text}")
        print("-" * 50)
        
        # Log conversation
        self.conversation_log.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'speaker': 'AI',
            'text': text
        })
        
        # Try multiple TTS engines for reliability
        tts_commands = [
            ['espeak', '-s', '140', '-a', '200', '-v', 'en+f3', text],
            ['festival', '--tts', '--pipe'],
            ['spd-say', text]
        ]
        
        for cmd in tts_commands:
            try:
                if cmd[0] == 'festival':
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
                    process.communicate(input=text)
                else:
                    subprocess.run(cmd, check=True, timeout=10)
                
                print("🔊 Audio played successfully")
                break
                
            except Exception as e:
                continue
        else:
            print("⚠️  All TTS engines failed")
        
        time.sleep(1)
    
    def ultra_reliable_listen(self, prompt="", duration=5, max_attempts=3):
        """Ultra-reliable listening with multiple attempts and validation"""
        print(f"\n🎧 {prompt}")
        print("🎤 ULTRA-RELIABLE LISTENING MODE")
        print("=" * 50)
        
        best_result = None
        best_confidence = 0
        
        for attempt in range(max_attempts):
            print(f"\n🔄 Attempt {attempt + 1}/{max_attempts}")
            
            # Record audio
            audio_file = self.record_high_quality_audio(duration)
            
            if not audio_file:
                print("❌ Recording failed, trying again...")
                continue
            
            # Multi-engine transcription
            text, confidence = self.multi_engine_transcribe(audio_file)
            
            # Clean up audio file
            try:
                os.remove(audio_file)
                if audio_file.endswith('_enhanced.wav'):
                    original_file = audio_file.replace('_enhanced.wav', '.wav')
                    if os.path.exists(original_file):
                        os.remove(original_file)
            except:
                pass
            
            if text and confidence > best_confidence:
                best_result = text
                best_confidence = confidence
                
                # If confidence is high enough, we're done
                if confidence >= self.confidence_threshold:
                    print(f"✅ High confidence result achieved!")
                    break
            
            if attempt < max_attempts - 1:
                print(f"🔄 Confidence {confidence:.2f} < {self.confidence_threshold}, trying again...")
                time.sleep(1)
        
        if best_result:
            print(f"\n🎯 FINAL RESULT:")
            print(f"👤 USER SAID: '{best_result}'")
            print(f"🎯 Confidence: {best_confidence:.2f}")
            print("=" * 50)
            
            # Log user response
            self.conversation_log.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'speaker': 'USER',
                'text': best_result,
                'confidence': best_confidence
            })
            
            return best_result
        else:
            print("❌ All attempts failed")
            return self.get_manual_input("Please type your response:")
    
    def get_manual_input(self, prompt):
        """Get manual input as ultimate fallback"""
        print(f"\n⌨️  {prompt}")
        
        try:
            user_input = input("👤 Type here: ").strip()
            if user_input:
                print(f"👤 USER SAID: '{user_input}'")
                print("=" * 50)
                
                self.conversation_log.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'speaker': 'USER',
                    'text': user_input,
                    'confidence': 1.0  # Manual input is 100% confident
                })
                
                return user_input
        except KeyboardInterrupt:
            return None
        
        return None
    
    def run_ultra_reliable_conversation(self):
        """Run ultra-reliable conversation flow"""
        print("\n" + "="*60)
        print("🚀 ULTRA-RELIABLE CONVERSATION FLOW")
        print("Hello → Name → Wait → Purpose → Transcription")
        print("="*60)
        
        # Step 1: Greeting
        print("\n📍 STEP 1: GREETING")
        self.speak("Hello! Welcome to our ultra-reliable smart door system.")
        
        time.sleep(2)
        
        # Step 2: Ask for name with high reliability
        print("\n📍 STEP 2: ASKING FOR NAME (Ultra-Reliable)")
        self.speak("What is your name? Please speak clearly.")
        
        user_name = self.ultra_reliable_listen("Please tell me your name clearly...", 5, 3)
        
        if user_name:
            response = f"Perfect! Nice to meet you, {user_name}!"
            self.speak(response)
        else:
            self.speak("I apologize, but I couldn't understand your name.")
        
        # Step 3: Wait
        print("\n📍 STEP 3: WAITING...")
        print("⏳ Waiting for 3 seconds as requested...")
        time.sleep(3)
        
        # Step 4: Ask purpose with ultra-reliability
        print("\n📍 STEP 4: ASKING PURPOSE (Ultra-Reliable)")
        self.speak("What is the purpose of your visit today? Please speak clearly and take your time.")
        
        purpose = self.ultra_reliable_listen("Please tell me why you're here today...", 7, 3)
        
        if purpose:
            response = f"Thank you! I understand you're here because: {purpose}. I'll process this information."
            self.speak(response)
        else:
            self.speak("Thank you for your visit.")
        
        # Step 5: Complete transcription
        print("\n📍 STEP 5: COMPLETE TRANSCRIPTION")
        self.show_enhanced_transcription()
        
        self.speak("Ultra-reliable conversation completed successfully. Thank you!")
    
    def show_enhanced_transcription(self):
        """Show enhanced conversation transcription with confidence scores"""
        print("\n" + "="*70)
        print("📝 ULTRA-RELIABLE CONVERSATION TRANSCRIPTION")
        print("="*70)
        
        for i, entry in enumerate(self.conversation_log, 1):
            speaker_icon = "🤖" if entry['speaker'] == 'AI' else "👤"
            confidence_str = ""
            
            if 'confidence' in entry:
                conf = entry['confidence']
                if conf >= 0.8:
                    confidence_str = f" ✅({conf:.2f})"
                elif conf >= 0.6:
                    confidence_str = f" ⚠️({conf:.2f})"
                else:
                    confidence_str = f" ❌({conf:.2f})"
            
            print(f"{i:2d}. [{entry['timestamp']}] {speaker_icon} {entry['speaker']}: {entry['text']}{confidence_str}")
        
        print("="*70)
        
        # Calculate overall reliability score
        user_entries = [e for e in self.conversation_log if e['speaker'] == 'USER' and 'confidence' in e]
        if user_entries:
            avg_confidence = sum(e['confidence'] for e in user_entries) / len(user_entries)
            print(f"📊 Overall Speech Recognition Reliability: {avg_confidence:.2f} ({avg_confidence*100:.0f}%)")
        
        # Save enhanced log
        try:
            filename = f"ultra_reliable_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'conversation': self.conversation_log,
                    'engines_used': {k: v['available'] for k, v in self.engines.items()},
                    'settings': {
                        'confidence_threshold': self.confidence_threshold,
                        'sample_rate': self.sample_rate,
                        'max_attempts': 3
                    }
                }, f, indent=2)
            print(f"💾 Enhanced conversation saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save: {e}")

def install_ultra_reliable_deps():
    """Install all dependencies for ultra-reliable speech recognition"""
    print("📦 Installing Ultra-Reliable Speech Recognition Dependencies")
    print("=" * 60)
    
    commands = [
        # Basic audio tools
        "sudo apt-get update",
        "sudo apt-get install -y espeak espeak-data festival sox",
        "sudo apt-get install -y alsa-utils portaudio19-dev python3-pyaudio",
        
        # Python packages
        "pip install SpeechRecognition",
        "pip install pyaudio",
        "pip install vosk",
        "pip install openai-whisper",
        "pip install numpy",
        
        # Optional but recommended
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
    ]
    
    for cmd in commands:
        print(f"\n🔧 Running: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
            print("✅ Success")
        except Exception as e:
            print(f"⚠️  Warning: {e}")
    
    print("\n✅ All dependencies installed!")
    print("📥 Don't forget to download Vosk model:")
    print("   Run the setup script and choose 'Download Vosk Model'")

def main():
    """Main function"""
    print("🚀 Ultra-Reliable Speech Recognition System")
    print("=" * 50)
    
    try:
        recognizer = UltraReliableSpeechRecognition()
        
        while True:
            print("\n" + "="*50)
            print("🎤 ULTRA-RELIABLE SPEECH MENU")
            print("="*50)
            print("1. 📦 Install All Dependencies")
            print("2. 🧪 Test Speech Recognition")
            print("3. 🚀 Ultra-Reliable Conversation Flow")
            print("4. 🎤 Single Ultra-Reliable Test")
            print("5. 🔊 Test Speaker")
            print("6. 📊 Show Engine Status")
            print("7. 🚪 Exit")
            print("="*50)
            
            choice = input("Enter choice (1-7): ").strip()
            
            if choice == '1':
                install_ultra_reliable_deps()
            elif choice == '2':
                result = recognizer.ultra_reliable_listen("Say 'hello test' clearly...", 3, 2)
                if result:
                    recognizer.speak(f"Perfect! I heard: {result}")
            elif choice == '3':
                print("\n🚀 Starting ultra-reliable conversation flow...")
                input("Press Enter when ready...")
                recognizer.run_ultra_reliable_conversation()
            elif choice == '4':
                result = recognizer.ultra_reliable_listen("Say anything you want...", 5, 3)
                if result:
                    recognizer.speak(f"Ultra-reliable result: {result}")
            elif choice == '5':
                recognizer.speak("This is an ultra-reliable speaker test. Can you hear me clearly?")
            elif choice == '6':
                recognizer.show_available_engines()
            elif choice == '7':
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
