from enum import auto, Enum

class ContextEvent(Enum):
    CONTEXT_CREATED = auto()
    CONTEXT_UPDATED = auto()
    CONTEXT_RESOLVED = auto()
    CONTEXT_EXPIRED = auto()
    CONTEXT_CLEARED = auto()
