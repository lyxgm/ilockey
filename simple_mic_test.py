#!/usr/bin/env python3

print("🚀 Starting Simple Microphone Test...")
print("=" * 40)

def check_dependencies():
    """Check if required packages are installed"""
    print("📦 Checking dependencies...")
    
    missing = []
    
    try:
        import speech_recognition
        print("✅ speech_recognition: OK")
    except ImportError:
        print("❌ speech_recognition: MISSING")
        missing.append("SpeechRecognition")
    
    try:
        import pyaudio
        print("✅ pyaudio: OK")
    except ImportError:
        print("❌ pyaudio: MISSING")
        missing.append("pyaudio")
    
    try:
        import pyttsx3
        print("✅ pyttsx3: OK")
    except ImportError:
        print("❌ pyttsx3: MISSING")
        missing.append("pyttsx3")
    
    if missing:
        print(f"\n🔧 Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        print("\n🐧 On Raspberry Pi also run:")
        print("   sudo apt-get install portaudio19-dev python3-pyaudio")
        return False
    
    return True

def test_microphone():
    """Simple microphone test"""
    print("\n🎤 Testing Microphone...")
    
    try:
        import speech_recognition as sr
        
        r = sr.Recognizer()
        mic = sr.Microphone()
        
        print("🔧 Calibrating microphone...")
        with mic as source:
            print("   Please be quiet for 2 seconds...")
            r.adjust_for_ambient_noise(source, duration=2)
        
        print("✅ Microphone calibrated!")
        print("\n🎧 Say something (you have 5 seconds):")
        
        with mic as source:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        
        print("🔄 Processing your speech...")
        
        try:
            text = r.recognize_google(audio)
            print(f"✅ I heard: '{text}'")
            return True
        except sr.UnknownValueError:
            print("⚠️  Could not understand the audio")
            return False
        except sr.RequestError as e:
            print(f"❌ Speech service error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        return False

def test_speaker():
    """Simple speaker test"""
    print("\n🔊 Testing Speaker...")
    
    try:
        import pyttsx3
        
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        
        text = "Hello! This is a speaker test. Can you hear me?"
        print(f"🤖 Speaking: {text}")
        
        engine.say(text)
        engine.runAndWait()
        
        print("✅ Speaker test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Speaker test failed: {e}")
        return False

def list_audio_devices():
    """List available audio devices"""
    print("\n🎧 Audio Devices:")
    
    try:
        import pyaudio
        
        p = pyaudio.PyAudio()
        
        print("Input Devices (Microphones):")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  🎤 {i}: {info['name']}")
        
        print("\nOutput Devices (Speakers):")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                print(f"  🔊 {i}: {info['name']}")
        
        p.terminate()
        
    except Exception as e:
        print(f"❌ Could not list devices: {e}")

def simple_conversation():
    """Simple voice conversation"""
    print("\n💬 Starting Simple Conversation...")
    print("Say 'hello' and I'll respond!")
    
    try:
        import speech_recognition as sr
        import pyttsx3
        
        r = sr.Recognizer()
        mic = sr.Microphone()
        engine = pyttsx3.init()
        
        # Calibrate
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=1)
        
        for i in range(3):  # 3 attempts
            print(f"\n🎧 Listening (attempt {i+1}/3)...")
            print("   Say something now!")
            
            try:
                with mic as source:
                    audio = r.listen(source, timeout=5, phrase_time_limit=5)
                
                text = r.recognize_google(audio)
                print(f"👤 You said: '{text}'")
                
                # Simple response
                if 'hello' in text.lower():
                    response = "Hello there! Nice to meet you!"
                elif 'delivery' in text.lower():
                    response = "I understand you have a delivery. Let me help you."
                elif 'help' in text.lower():
                    response = "I'm here to help! What do you need?"
                else:
                    response = f"I heard you say: {text}. How can I help you?"
                
                print(f"🤖 AI Response: {response}")
                engine.say(response)
                engine.runAndWait()
                
                break
                
            except sr.WaitTimeoutError:
                print("⏰ No speech detected, trying again...")
            except sr.UnknownValueError:
                print("⚠️  Could not understand, trying again...")
            except Exception as e:
                print(f"❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Conversation failed: {e}")

def main():
    """Main function with simple menu"""
    
    # Always show the menu first
    while True:
        print("\n" + "="*40)
        print("🎤 SIMPLE MICROPHONE TEST")
        print("="*40)
        print("1. 📦 Check Dependencies")
        print("2. 🎧 List Audio Devices") 
        print("3. 🎤 Test Microphone")
        print("4. 🔊 Test Speaker")
        print("5. 💬 Simple Conversation")
        print("6. 🚪 Exit")
        print("="*40)
        
        try:
            choice = input("Enter choice (1-6): ").strip()
            
            if choice == '1':
                check_dependencies()
            elif choice == '2':
                list_audio_devices()
            elif choice == '3':
                test_microphone()
            elif choice == '4':
                test_speaker()
            elif choice == '5':
                simple_conversation()
            elif choice == '6':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice! Please enter 1-6")
                
        except KeyboardInterrupt:
            print("\n🛑 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# Run the program
if __name__ == "__main__":
    main()
