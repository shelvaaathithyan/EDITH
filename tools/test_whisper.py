from edith.voice.stt import stt

model = stt.model

print("Speak...", flush=True)
audio = stt.capture_audio()

if audio:
    print("Starting transcription via unified STT module...")
    text = stt.transcribe(audio)

if text:
    print("\nTranscribed text:")
    print(text)
else:
    print("\nNo speech detected or transcription failed.")

print("Done")