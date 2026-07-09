from enum import Enum
from typing import Callable, Dict, List, Any
from dataclasses import dataclass

class VoiceState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    UNDERSTANDING = "UNDERSTANDING"
    THINKING = "THINKING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"

class VoiceEvent(Enum):
    VOICE_STARTED = "VOICE_STARTED"
    VOICE_STOPPED = "VOICE_STOPPED"
    LISTENING_STARTED = "LISTENING_STARTED"
    LISTENING_FINISHED = "LISTENING_FINISHED"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    STATE_CHANGED = "STATE_CHANGED"

@dataclass
class VoiceMessage:
    text: str
    priority: str = "normal"  # normal, high, critical
    interruptible: bool = True

class VoiceEventBus:
    """Simple pub/sub event bus for voice events."""
    def __init__(self):
        self._subscribers: Dict[VoiceEvent, List[Callable[[Any], None]]] = {
            event: [] for event in VoiceEvent
        }

    def subscribe(self, event: VoiceEvent, callback: Callable[[Any], None]):
        if callback not in self._subscribers[event]:
            self._subscribers[event].append(callback)

    def unsubscribe(self, event: VoiceEvent, callback: Callable[[Any], None]):
        if callback in self._subscribers[event]:
            self._subscribers[event].remove(callback)

    def publish(self, event: VoiceEvent, data: Any = None):
        for callback in self._subscribers[event]:
            try:
                callback(data)
            except Exception as e:
                # Local import to prevent circular dependency
                from edith.utils.logger import logger
                logger.error(f"Error in VoiceEventBus callback for {event}: {e}")

event_bus = VoiceEventBus()
