import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from edith.voice.audio import AudioPlayer

def test_runtime_audio():
    print("=== EDITH Runtime Audio Test ===")
    wav_path = "s:/EDITH/temp/last_tts.wav"
    
    player = AudioPlayer()
    
    try:
        player.play_wav(wav_path, block=True)
        print("[OK] Playback completed.")
    except Exception as e:
        print(f"\n[FAIL] Runtime Audio test error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_runtime_audio()
