from enum import Enum

class CapabilityHealth(Enum):
    HEALTHY = "Healthy"
    WARNING = "Warning"
    UNAVAILABLE = "Unavailable"
    ERROR = "Error"
