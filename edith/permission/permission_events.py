from enum import Enum, auto

class PermissionEvent(Enum):
    PERMISSION_REQUESTED = auto()
    PERMISSION_GRANTED = auto()
    PERMISSION_DENIED = auto()
    PERMISSION_EXPIRED = auto()
    PERMISSION_CANCELLED = auto()
