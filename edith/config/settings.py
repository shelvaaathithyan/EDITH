import json
from pathlib import Path
from pydantic import BaseModel, Field

CONFIG_DIR = Path("edith/config")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "settings.json"

class VoiceProfile(BaseModel):
    model_name: str = Field(description="Name of the ONNX model file (without .onnx)")

class Settings(BaseModel):
    api_key: str = Field(default="", description="OpenAI API Key")
    browser: str = Field(default="chrome", description="Preferred browser")
    theme: str = Field(default="dark", description="CLI Theme")
    
    # Voice Engine settings
    voice_engine: str = Field(default="piper", description="TTS engine to use")
    voice_profile: str = Field(default="edith_default", description="Current voice profile")
    voice_profiles: dict[str, VoiceProfile] = Field(
        default={
            "edith_default": VoiceProfile(model_name="en_US-lessac-medium")
        },
        description="Mapping of profile names to model configurations"
    )
    interrupt_keywords: list[str] = Field(
        default=["stop", "cancel", "wait", "hold on", "enough"], 
        description="Keywords to trigger barge-in/interruption"
    )
    wake_responses: list[str] = Field(
        default=["Yes?"], 
        description="Responses played immediately after wake word"
    )
    speech_speed: float = Field(default=1.0, description="Playback speed multiplier")
    volume: float = Field(default=1.0, description="Playback volume multiplier")
    microphone_index: int | None = Field(default=None, description="PyAudio/SoundDevice microphone index")
    enable_sound_effects: bool = Field(default=True, description="Play UI notification sounds")
    ambient_noise_calibration: bool = Field(default=True, description="Auto-calibrate mic for noise")
    record_timeout: int = Field(default=8, description="Max recording time before cutting off")
    silence_timeout: int = Field(default=2, description="Seconds of silence before stopping recording")
    wake_word_model: str = Field(default="hey_jarvis", description="OpenWakeWord model name or path")

    # AI Engine settings
    ai_provider: str = Field(default="ollama", description="LLM provider")
    ai_model: str = Field(default="qwen2.5:latest", description="LLM model name (e.g., qwen2.5)")
    ai_temperature: float = Field(default=0.2, description="Temperature for generation")
    ai_max_tokens: int = Field(default=2048, description="Max tokens for generation")
    ai_timeout: int = Field(default=60, description="Request timeout in seconds")

    # Browser Capability settings
    default_search_engine: str = Field(default="google", description="google, bing, duckduckgo, etc")
    quick_sites: dict[str, str] = Field(
        default={
            "github": "https://github.com",
            "youtube": "https://youtube.com",
            "gmail": "https://mail.google.com",
            "chatgpt": "https://chat.openai.com",
            "localhost": "http://localhost:3000"
        },
        description="Quick site aliases mapping word to URL"
    )

    # Desktop Capability settings
    app_aliases: dict[str, str] = Field(
        default={
            "vscode": "Code.exe",
            "visual studio code": "Code.exe",
            "visual studio": "Code.exe",
            "code": "Code.exe",
            "cursor": "Cursor.exe",
            "cursor ai": "Cursor.exe",
            "spotify": "Spotify.exe",
            "music": "Spotify.exe",
            "terminal": "wt.exe",
            "discord": "Update.exe --processStart Discord.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "firefox": "firefox.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "notepad": "notepad.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "file explorer": "explorer.exe",
            "task manager": "taskmgr.exe"
        },
        description="Aliases mapping natural language to executables or commands"
    )

    # UI settings
    ui_width: int = Field(default=400, description="Window width in pixels")
    ui_height: int = Field(default=600, description="Window height in pixels")
    ui_frameless: bool = Field(default=True, description="Use frameless window")
    ui_on_top: bool = Field(default=True, description="Keep window on top")
    ui_start_hidden: bool = Field(default=True, description="Start the UI hidden until wake word")

    # Timeouts
    planner_retry_count: int = Field(default=2, description="Max planner retries on JSON validation failure")
    capability_timeout: int = Field(default=30, description="Max seconds for a capability execution")

    # Vision settings
    vision_model: str = Field(default="qwen2.5-vl", description="Default multimodal vision model")
    ocr_provider: str = Field(default="easyocr", description="Default OCR provider")
    vision_max_resolution: int = Field(default=1920, description="Max image resolution before downscaling")

    # Spotify settings
    spotify_default_provider: str = Field(default="desktop", description="Default Spotify provider backend")

    # Logging
    log_rotation_size_mb: int = Field(default=5, description="Max log file size in MB before rotation")
    log_backup_count: int = Field(default=3, description="Number of rotated log backups to keep")

    # Embedding
    embedding_model: str = Field(default="nomic-embed-text", description="Ollama embedding model for LTM semantic search")
    embedding_dimensions: int = Field(default=768, description="Embedding vector dimension size")

def load_settings() -> Settings:
    if not CONFIG_FILE.exists():
        default_settings = Settings()
        save_settings(default_settings)
        return default_settings
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return Settings(**data)

def save_settings(settings: Settings):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(), f, indent=4)

# Global settings instance
settings = load_settings()
