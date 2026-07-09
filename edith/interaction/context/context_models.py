from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import time
import uuid

class ContextNode(BaseModel):
    """
    Represents a distinct entity in the short-term working memory.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(description="The type of context (e.g. 'application', 'browser', 'file', 'website', 'search')")
    value: Any = Field(description="The actual value or name of the context entity")
    parent_id: Optional[str] = Field(default=None, description="The ID of the parent context node, if any")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional properties associated with this node")
    
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    last_accessed_at: float = Field(default_factory=time.time)
    
    # Expiration in seconds, default to 15 minutes
    ttl: float = Field(default=900.0)

    @property
    def is_expired(self) -> bool:
        return time.time() - self.last_accessed_at > self.ttl

    def touch(self):
        self.last_accessed_at = time.time()
        self.updated_at = time.time()
