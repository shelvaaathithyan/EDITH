import os
import sys
import sounddevice as sd
import soundfile as sf
import time

def test_audio():
    print("=== EDITH Direct Audio Test ===")
    wav_path = "s:/EDITH/temp/last_tts.wav"
    
    if not os.path.exists(wav_path):
        print(f"[FAIL] File not found: {wav_path}")
        print("Please run EDITH and trigger a voice response first to generate the file.")
        sys.exit(1)
        
    try:
        data, fs = sf.read(wav_path)
        duration = len(data) / fs
        channels = data.ndim if len(data.shape) > 1 else 1
        print(f"File loaded successfully: {wav_path}")
        print(f"Duration: {duration:.3f}s")
        print(f"Sample Rate: {fs}Hz")
        print(f"Channels: {channels}")
        
        # Output devices
        devices = sd.query_devices()
        default_device_idx = sd.default.device[1]
        
        print("\n--- Output Devices ---")
        for idx, dev in enumerate(devices):
            if dev['max_output_channels'] > 0:
                is_default = (idx == default_device_idx)
                marker = "[DEFAULT/SELECTED]" if is_default else ""
                print(f"[{idx}] {dev['name']} {marker} | SR: {dev['default_samplerate']}")
        
        print(f"\nPlaying on device [{default_device_idx}] for {duration:.3f}s...")
        sd.play(data, fs, device=default_device_idx, blocking=True)
        print("[OK] Playback completed.")
        
    except Exception as e:
        print(f"\n[FAIL] Audio test error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_audio()
