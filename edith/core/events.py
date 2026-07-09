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
    
    # Execution
    EXECUTION_STARTED = auto()
    EXECUTION_COMPLETED = auto()
    TOOL_EXECUTED = auto()
    
    # Permissions
    PERMISSION_REQUESTED = auto()
    PERMISSION_GRANTED = auto()
    PERMISSION_DENIED = auto()

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
