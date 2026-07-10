import threading
from enum import Enum, auto
from typing import Callable, Dict, List, Any

class AppEvent(Enum):
    # Lifecycle
    APPLICATION_STARTED = auto()
    APPLICATION_STOPPED = auto()
    STATE_CHANGED = auto()
    
    # Voice Events
    VOICE_STARTED = auto()
    VOICE_STOPPED = auto()
    WAKE_WORD_DETECTED = auto()
    
    # Pipeline Events
    PLANNER_STARTED = auto()
    PLANNER_COMPLETED = auto()
    PIPELINE_STARTED = auto()
    PIPELINE_COMPLETED = auto()
    REQUEST_COMPLETED = auto()
    STT_STARTED = auto()
    STT_FINISHED = auto()
    TTS_STARTED = auto()
    TTS_FINISHED = auto()
    CAPABILITY_RESOLVER_STARTED = auto()
    CAPABILITY_RESOLVER_FINISHED = auto()
    GENERATOR_STARTED = auto()
    GENERATOR_FINISHED = auto()
    
    # Execution
    EXECUTION_STARTED = auto()
    EXECUTION_COMPLETED = auto()
    TOOL_EXECUTED = auto()
    CAPABILITY_STARTED = auto()
    CAPABILITY_FINISHED = auto()
    
    # Browser Capability
    BROWSER_LAUNCH_STARTED = auto()
    BROWSER_LAUNCH_COMPLETED = auto()
    BROWSER_SEARCH_STARTED = auto()
    BROWSER_SEARCH_COMPLETED = auto()
    BROWSER_NAVIGATION_STARTED = auto()
    BROWSER_NAVIGATION_COMPLETED = auto()
    BROWSER_LAUNCH_FAILED = auto()
    
    # Desktop Capability
    APPLICATION_LOOKUP_STARTED = auto()
    APPLICATION_LOOKUP_COMPLETED = auto()
    APPLICATION_FOUND = auto()
    APPLICATION_NOT_FOUND = auto()
    APPLICATION_LAUNCH_STARTED = auto()
    APPLICATION_LAUNCH_COMPLETED = auto()
    APPLICATION_ALREADY_RUNNING = auto()
    APPLICATION_FOCUSED = auto()
    APPLICATION_MINIMIZED = auto()
    APPLICATION_MAXIMIZED = auto()
    APPLICATION_RESTORED = auto()
    APPLICATION_CLOSED = auto()
    APPLICATION_ERROR = auto()
    
    # Terminal / Developer Execution Engine
    TERMINAL_OPENED = auto()
    TERMINAL_CLOSED = auto()
    COMMAND_STARTED = auto()
    COMMAND_OUTPUT = auto()
    COMMAND_FINISHED = auto()
    COMMAND_FAILED = auto()
    COMMAND_CANCELLED = auto()
    PROCESS_KILLED = auto()
    WORKING_DIRECTORY_CHANGED = auto()
    WORKSPACE_OPENED = auto()
    WORKSPACE_SWITCHED = auto()
    PROJECT_DETECTED = auto()
    ENV_DETECTED = auto()
    PROCESS_GROUP_CREATED = auto()
    PROCESS_GROUP_STOPPED = auto()
    VENV_ACTIVATED = auto()
    VENV_DEACTIVATED = auto()
    WORKFLOW_STARTED = auto()
    WORKFLOW_STEP_COMPLETED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_FAILED = auto()

    # Permissions
    PERMISSION_REQUESTED = auto()
    PERMISSION_GRANTED = auto()
    PERMISSION_DENIED = auto()

    # Error Recovery
    ERROR_OCCURRED = auto()

    # Memory Subsystem
    MEMORY_CREATED = auto()
    MEMORY_UPDATED = auto()
    MEMORY_DELETED = auto()
    MEMORY_ACCESSED = auto()
    MEMORY_EXPIRED = auto()
    MEMORY_SEARCHED = auto()

    # Vision Subsystem
    SCREEN_CAPTURED = auto()
    OCR_COMPLETED = auto()
    VISION_ANALYZED = auto()
    PDF_PARSED = auto()
    WINDOW_CAPTURED = auto()
    IMAGE_CAPTURED = auto()
    REGION_CAPTURED = auto()
    UI_DETECTED = auto()

    # Media & Spotify Subsystem
    SPOTIFY_STARTED = auto()
    SPOTIFY_CONNECTED = auto()
    PLAYBACK_STARTED = auto()
    PLAYBACK_PAUSED = auto()
    PLAYBACK_STOPPED = auto()
    TRACK_CHANGED = auto()
    PLAYLIST_STARTED = auto()
    ARTIST_STARTED = auto()
    ALBUM_STARTED = auto()
    VOLUME_CHANGED = auto()
    SHUFFLE_CHANGED = auto()
    REPEAT_CHANGED = auto()
    TRACK_LIKED = auto()
    TRACK_UNLIKED = auto()
    SPOTIFY_CLOSED = auto()

class EventBus:
    def __init__(self):
        self._subscribers: Dict[AppEvent, List[Callable]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_type: AppEvent, callback: Callable):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: AppEvent, callback: Callable):
        with self._lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def publish(self, event_type: AppEvent, data: Any = None):
        """Dispatches an event synchronously. 
        Callbacks should be lightweight or offload work to a separate thread."""
        with self._lock:
            callbacks = self._subscribers.get(event_type, []).copy()
        
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                import logging
                logging.getLogger("EventBus").error(f"Error in callback for {event_type}: {e}")

# Global singleton Event Bus
event_bus = EventBus()
