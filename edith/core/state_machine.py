import threading
from enum import Enum, auto
from edith.core.events import event_bus, AppEvent
from edith.utils.logger import logger

class AppState(Enum):
    STARTING = auto()
    INITIALIZING = auto()
    READY = auto()
    LISTENING = auto()
    UNDERSTANDING = auto()
    PLANNING = auto()
    EXECUTING = auto()
    RESPONDING = auto()
    IDLE = auto()
    ERROR = auto()
    SHUTTING_DOWN = auto()

class StateTransitionError(Exception):
    pass

class StateMachine:
    def __init__(self):
        self._state = AppState.STARTING
        self._lock = threading.RLock()
        
        # Valid transitions mapping
        self._valid_transitions = {
            AppState.STARTING: [AppState.INITIALIZING, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.INITIALIZING: [AppState.READY, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.READY: [AppState.LISTENING, AppState.UNDERSTANDING, AppState.IDLE, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.IDLE: [AppState.LISTENING, AppState.UNDERSTANDING, AppState.READY, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.LISTENING: [AppState.UNDERSTANDING, AppState.READY, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.UNDERSTANDING: [AppState.PLANNING, AppState.READY, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.PLANNING: [AppState.EXECUTING, AppState.RESPONDING, AppState.READY, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.EXECUTING: [AppState.RESPONDING, AppState.READY, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.RESPONDING: [AppState.READY, AppState.IDLE, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.ERROR: [AppState.READY, AppState.SHUTTING_DOWN],
            AppState.SHUTTING_DOWN: []
        }

    def get_state(self) -> AppState:
        with self._lock:
            return self._state

    def transition(self, new_state: AppState) -> None:
        with self._lock:
            if new_state not in self._valid_transitions[self._state]:
                # In a robust system, we might log and ignore instead of crashing, but let's be strict internally
                error_msg = f"Invalid state transition from {self._state.name} to {new_state.name}"
                logger.error(error_msg)
                raise StateTransitionError(error_msg)
            
            logger.debug(f"State transition: {self._state.name} -> {new_state.name}")
            self._state = new_state
            
            # Fire event outside of lock ideally, or just synchronously here if callbacks are safe
            # But the event_bus itself has a lock.
            
        # Fire event
        event_bus.publish(AppEvent.STATE_CHANGED, self._state)
