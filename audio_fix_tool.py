#!/usr/bin/env python3
import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and show the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"⚠️  {description} - WARNING")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - FAILED: {e}")
        return False

def check_audio_devices():
    """Check what audio devices are available"""
    print("\n🎧 Checking Audio Devices...")
    print("=" * 30)
    
    # Check ALSA devices
    print("📋 ALSA Audio Cards:")
    run_command("cat /proc/asound/cards", "List ALSA cards")
    
    print("\n📋 Audio Devices:")
    run_command("ls -la /dev/snd/", "List sound devices")
    
    print("\n📋 USB Audio Devices:")
    run_command("lsusb | grep -i audio", "Check USB audio devices")

def fix_alsa_config():
    """Fix ALSA configuration"""
    print("\n🔧 Fixing ALSA Configuration...")
    print("=" * 35)
    
    # Create a simple ALSA config
    alsa_config = """
# Simple ALSA configuration for Raspberry Pi
pcm.!default {
    type pulse
    fallback "sysdefault"
    hint {
        show on
        description "Default ALSA Output (currently PulseAudio Sound Server)"
    }
}

ctl.!default {
    type pulse
    fallback "sysdefault"
}

# Fallback to hardware if PulseAudio is not available
pcm.sysdefault {
    type hw
    card 0
}

ctl.sysdefault {
    type hw
    card 0
}
"""
    
    try:
        with open(os.path.expanduser("~/.asoundrc"), "w") as f:
            f.write(alsa_config)
        print("✅ Created ~/.asoundrc configuration")
    except Exception as e:
        print(f"❌ Failed to create ALSA config: {e}")

def install_audio_packages():
    """Install necessary audio packages"""
    print("\n📦 Installing Audio Packages...")
    print("=" * 35)
    
    packages = [
        "pulseaudio",
        "pulseaudio-utils", 
        "alsa-utils",
        "portaudio19-dev",
        "python3-pyaudio"
    ]
    
    for package in packages:
        run_command(f"sudo apt-get install -y {package}", f"Install {package}")

def start_audio_services():
    """Start audio services"""
    print("\n🚀 Starting Audio Services...")
    print("=" * 30)
    
    # Kill any existing pulseaudio
    run_command("pulseaudio --kill", "Kill existing PulseAudio")
    
    # Start pulseaudio
    run_command("pulseaudio --start", "Start PulseAudio")
    
    # Check if it's running
    run_command("pulseaudio --check", "Check PulseAudio status")

def test_audio_simple():
    """Simple audio test without complex libraries"""
    print("\n🧪 Simple Audio Test...")
    print("=" * 25)
    
    # Test speaker with aplay
    print("🔊 Testing speaker with system beep...")
    run_command("speaker-test -t sine -f 1000 -l 1 -s 1", "Test speaker")
    
    # Test microphone with arecord
    print("\n🎤 Testing microphone recording...")
    print("   Recording 3 seconds of audio...")
    
    if run_command("timeout 3s arecord -f cd -t wav /tmp/test_recording.wav", "Record audio test"):
        print("✅ Audio recording successful!")
        
        # Play it back
        if run_command("aplay /tmp/test_recording.wav", "Play back recording"):
            print("✅ Audio playback successful!")
        
        # Clean up
        run_command("rm -f /tmp/test_recording.wav", "Clean up test file")
    else:
        print("❌ Audio recording failed")

def create_simple_mic_test():
    """Create a very simple microphone test"""
    print("\n🎤 Creating Simple Microphone Test...")
    
    simple_test = '''#!/usr/bin/env python3
import os
import sys

def test_basic_audio():
    """Test basic audio without complex libraries"""
    print("🎤 Basic Audio Test")
    print("=" * 20)
    
    # Test if we can access audio devices
    if os.path.exists("/dev/snd/"):
        devices = os.listdir("/dev/snd/")
        print(f"✅ Found audio devices: {devices}")
    else:
        print("❌ No audio devices found")
        return False
    
    # Try to record with arecord
    print("\\n🎧 Testing microphone with arecord...")
    print("Say something for 3 seconds...")
    
    cmd = "arecord -f S16_LE -r 16000 -d 3 /tmp/mic_test.wav"
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Recording successful!")
        
        # Play it back
        print("🔊 Playing back your recording...")
        play_result = os.system("aplay /tmp/mic_test.wav")
        
        if play_result == 0:
            print("✅ Playback successful!")
        else:
            print("⚠️  Playback had issues")
        
        # Clean up
        os.system("rm -f /tmp/mic_test.wav")
        return True
    else:
        print("❌ Recording failed")
        return False

if __name__ == "__main__":
    test_basic_audio()
'''
    
    try:
        with open("basic_audio_test.py", "w") as f:
            f.write(simple_test)
        os.chmod("basic_audio_test.py", 0o755)
        print("✅ Created basic_audio_test.py")
        print("   Run with: python3 basic_audio_test.py")
    except Exception as e:
        print(f"❌ Failed to create test: {e}")

def show_audio_info():
    """Show current audio configuration"""
    print("\n📊 Current Audio Configuration:")
    print("=" * 35)
    
    run_command("aplay -l", "List playback devices")
    run_command("arecord -l", "List recording devices")
    run_command("amixer", "Show mixer settings")

def main():
    """Main audio fix tool"""
    print("🔧 Raspberry Pi Audio Fix Tool")
    print("=" * 35)
    
    while True:
        print("\n" + "="*40)
        print("🔧 AUDIO FIX TOOL")
        print("="*40)
        print("1. 📊 Check Current Audio Setup")
        print("2. 📦 Install Audio Packages")
        print("3. 🔧 Fix ALSA Configuration")
        print("4. 🚀 Start Audio Services")
        print("5. 🧪 Test Audio (Simple)")
        print("6. 🎤 Create Basic Mic Test")
        print("7. 🔄 Full Audio Fix (All Steps)")
        print("8. 🚪 Exit")
        print("="*40)
        
        try:
            choice = input("Enter choice (1-8): ").strip()
            
            if choice == '1':
                check_audio_devices()
                show_audio_info()
            elif choice == '2':
                install_audio_packages()
            elif choice == '3':
                fix_alsa_config()
            elif choice == '4':
                start_audio_services()
            elif choice == '5':
                test_audio_simple()
            elif choice == '6':
                create_simple_mic_test()
            elif choice == '7':
                print("🔄 Running full audio fix...")
                install_audio_packages()
                fix_alsa_config()
                start_audio_services()
                test_audio_simple()
                create_simple_mic_test()
                print("✅ Full audio fix completed!")
            elif choice == '8':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice!")
                
        except KeyboardInterrupt:
            print("\n🛑 Exiting...")
            break

if __name__ == "__main__":
    main()
