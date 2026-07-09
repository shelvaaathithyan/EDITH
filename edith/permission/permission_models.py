from enum import Enum, auto
from pydantic import BaseModel, Field
import time
import uuid
from edith.ai.models import ResolvedExecutionPlan

class RiskLevel(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

class PermissionAction(Enum):
    EXECUTE = auto()
    OPTIONAL_CONFIRM = auto()
    REQUIRE_CONFIRM = auto()
    REQUIRE_EXPLICIT_CONFIRM = auto()
    DENY = auto()

class PendingActionStatus(Enum):
    PENDING = auto()
    GRANTED = auto()
    DENIED = auto()
    EXPIRED = auto()

class PendingAction(BaseModel):
    """Represents an execution plan that is paused awaiting user confirmation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan: ResolvedExecutionPlan
    risk_level: RiskLevel
    status: PendingActionStatus = Field(default=PendingActionStatus.PENDING)
    
    created_at: float = Field(default_factory=time.time)
    ttl_seconds: float = Field(default=60.0)
    
    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds
