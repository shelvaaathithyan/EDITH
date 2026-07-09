from edith.voice.stt import stt
import speech_recognition as sr

model = stt.model

r = sr.Recognizer()

with sr.Microphone() as source:
    print("Speak...", flush=True)
    audio = r.listen(source)
    print("Recording finished", flush=True)

print("Starting transcription via STT module...")
text = stt.transcribe(audio)

if text:
    print("\nTranscribed text:")
    print(text)
else:
    print("\nNo speech detected or transcription failed.")

print("Done")