"""
Data Models for the Long-Term Memory Subsystem.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from edith.memory.memory_constants import MemoryCategory, MemorySource

class MemoryRelationship(BaseModel):
    source_id: str
    target_id: str
    relation_type: str

class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: MemoryCategory
    title: str
    value: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    importance: float = Field(ge=0.0, le=1.0, default=0.5)
    
    created_time: datetime = Field(default_factory=datetime.now)
    updated_time: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    
    access_count: int = Field(default=0)
    embedding_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    ttl: Optional[datetime] = None
    source: MemorySource = Field(default=MemorySource.SYSTEM)
    
    # Non-persisted computed fields
    relevance_score: float = Field(default=0.0, exclude=True)

class MemoryQuery(BaseModel):
    """Encapsulates a search query for memory retrieval."""
    query: str
    categories: Optional[List[MemoryCategory]] = None
    tags: Optional[List[str]] = None
    min_confidence: float = 0.5
    min_importance: float = 0.0
    limit: int = 10
    
    # Hybrid search parameters
    use_embeddings: bool = True
    semantic_weight: float = 0.5
