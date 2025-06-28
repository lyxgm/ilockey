#!/usr/bin/env python3
import os
import subprocess

def backup_and_remove_asoundrc():
    """Backup and remove problematic .asoundrc file"""
    asoundrc_path = os.path.expanduser("~/.asoundrc")
    
    if os.path.exists(asoundrc_path):
        print("🔧 Found problematic .asoundrc file")
        
        # Backup the file
        backup_path = asoundrc_path + ".backup"
        try:
            os.rename(asoundrc_path, backup_path)
            print(f"✅ Backed up to {backup_path}")
            print("✅ Removed problematic .asoundrc")
        except Exception as e:
            print(f"❌ Failed to backup: {e}")
            # Try to just remove it
            try:
                os.remove(asoundrc_path)
                print("✅ Removed problematic .asoundrc")
            except Exception as e2:
                print(f"❌ Failed to remove: {e2}")
    else:
        print("ℹ️  No .asoundrc file found")

def test_audio_devices():
    """Test each audio device to find working ones"""
    print("\n🎧 Testing Audio Devices...")
    print("=" * 30)
    
    # List available cards
    try:
        result = subprocess.run("aplay -l", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 Available Playback Devices:")
            print(result.stdout)
        
        result = subprocess.run("arecord -l", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 Available Recording Devices:")
            print(result.stdout)
            
    except Exception as e:
        print(f"❌ Error listing devices: {e}")

def test_specific_device(card_num, device_num=0):
    """Test a specific audio card"""
    print(f"\n🎤 Testing Card {card_num}, Device {device_num}...")
    
    # Test recording
    cmd = f"arecord -D hw:{card_num},{device_num} -f S16_LE -r 16000 -d 3 /tmp/test_card_{card_num}.wav"
    print(f"🔧 Command: {cmd}")
    print("Say something for 3 seconds...")
    
    result = os.system(cmd)
    
    if result == 0:
        print(f"✅ Recording successful on card {card_num}!")
        
        # Test playback
        play_cmd = f"aplay -D hw:{card_num},{device_num} /tmp/test_card_{card_num}.wav"
        print(f"🔊 Playing back... Command: {play_cmd}")
        
        play_result = os.system(play_cmd)
        if play_result == 0:
            print(f"✅ Playback successful on card {card_num}!")
            return True
        else:
            print(f"⚠️  Playback failed on card {card_num}")
            return False
    else:
        print(f"❌ Recording failed on card {card_num}")
        return False

def find_working_audio_card():
    """Find which audio card works"""
    print("\n🔍 Finding Working Audio Card...")
    print("=" * 35)
    
    working_cards = []
    
    # Test cards 0-3 (based on your device list)
    for card in range(4):
        if os.path.exists(f"/dev/snd/controlC{card}"):
            print(f"\n📡 Testing Card {card}...")
            if test_specific_device(card):
                working_cards.append(card)
                print(f"✅ Card {card} works!")
            else:
                print(f"❌ Card {card} doesn't work")
        else:
            print(f"⚠️  Card {card} not found")
    
    return working_cards

def create_working_mic_test(working_card):
    """Create a mic test using the working card"""
    print(f"\n🎤 Creating Mic Test for Card {working_card}...")
    
    mic_test = f'''#!/usr/bin/env python3
import os
import sys

def test_microphone():
    """Test microphone using working card {working_card}"""
    print("🎤 Microphone Test - Card {working_card}")
    print("=" * 30)
    
    # Record using the working card
    print("🎧 Recording 5 seconds of audio...")
    print("Say something now!")
    
    record_cmd = "arecord -D hw:{working_card},0 -f S16_LE -r 16000 -d 5 /tmp/mic_test.wav"
    print(f"Command: {{record_cmd}}")
    
    result = os.system(record_cmd)
    
    if result == 0:
        print("✅ Recording successful!")
        
        # Play it back
        print("🔊 Playing back your recording...")
        play_cmd = "aplay -D hw:{working_card},0 /tmp/mic_test.wav"
        play_result = os.system(play_cmd)
        
        if play_result == 0:
            print("✅ Playback successful!")
            print("🎉 Your microphone is working!")
        else:
            print("⚠️  Playback had issues")
        
        # Clean up
        os.system("rm -f /tmp/mic_test.wav")
        return True
    else:
        print("❌ Recording failed")
        return False

def test_with_python():
    """Test with Python speech recognition"""
    print("\\n🐍 Testing with Python...")
    
    try:
        import speech_recognition as sr
        
        r = sr.Recognizer()
        
        # Use the specific device
        mic = sr.Microphone(device_index=None)  # Let it auto-detect
        
        print("🔧 Calibrating microphone...")
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=2)
        
        print("🎧 Say something (5 seconds):")
        with mic as source:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        
        print("🔄 Processing speech...")
        try:
            text = r.recognize_google(audio)
            print(f"✅ I heard: '{{text}}'")
            return True
        except sr.UnknownValueError:
            print("⚠️  Could not understand audio")
            return False
        except sr.RequestError as e:
            print(f"❌ Speech service error: {{e}}")
            return False
            
    except ImportError:
        print("⚠️  speech_recognition not installed")
        print("   Install with: pip install SpeechRecognition")
        return False
    except Exception as e:
        print(f"❌ Python test failed: {{e}}")
        return False

if __name__ == "__main__":
    print("🚀 Starting microphone test...")
    
    # Test basic recording first
    if test_microphone():
        # If basic works, try Python
        test_with_python()
    else:
        print("❌ Basic microphone test failed")
        print("🔧 Try running the audio fix tool again")
'''
    
    try:
        with open(f"working_mic_test_card{working_card}.py", "w") as f:
            f.write(mic_test)
        os.chmod(f"working_mic_test_card{working_card}.py", 0o755)
        print(f"✅ Created working_mic_test_card{working_card}.py")
        return f"working_mic_test_card{working_card}.py"
    except Exception as e:
        print(f"❌ Failed to create test: {e}")
        return None

def main():
    """Main function"""
    print("🔧 ALSA Configuration Fix")
    print("=" * 30)
    
    # Step 1: Remove problematic config
    backup_and_remove_asoundrc()
    
    # Step 2: Test devices
    test_audio_devices()
    
    # Step 3: Find working card
    working_cards = find_working_audio_card()
    
    if working_cards:
        print(f"\n🎉 Found working audio cards: {working_cards}")
        
        # Use the first working card
        best_card = working_cards[0]
        print(f"✅ Using card {best_card} as primary")
        
        # Create a working mic test
        test_file = create_working_mic_test(best_card)
        
        if test_file:
            print(f"\n🚀 Now run: python3 {test_file}")
            print("This should work without ALSA errors!")
        
    else:
        print("\n❌ No working audio cards found")
        print("🔧 Try these commands manually:")
        print("   sudo apt-get install pulseaudio-utils")
        print("   pulseaudio --kill && pulseaudio --start")

if __name__ == "__main__":
    main()
