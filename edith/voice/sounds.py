import threading
from pathlib import Path
from edith.config.settings import settings

# Assume sounds are placed in edith/assets/sounds/
SOUNDS_DIR = Path("edith/assets/sounds")

class SoundManager:
    def __init__(self, audio_player):
        self._audio_player = audio_player

    def _play(self, sound_name: str):
        if not settings.enable_sound_effects:
            return
            
        sound_path = SOUNDS_DIR / f"{sound_name}.wav"
        if sound_path.exists():
            # Play sounds in a background thread so they don't block
            t = threading.Thread(target=self._audio_player.play_wav, args=(str(sound_path), True), daemon=True)
            t.start()

    def play_listening_start(self):
        self._play("start")

    def play_listening_end(self):
        self._play("stop")

    def play_task_complete(self):
        self._play("complete")

    def play_error(self):
        self._play("error")

# NO MODULE-LEVEL SINGLETON — created in build_app()
