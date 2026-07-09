"""
Memory Repository enforcing the Repository Pattern.
Abstracts data access logic from the domain models.
"""

from typing import List, Optional
from edith.memory.memory_models import Memory, MemoryRelationship, MemoryCategory
from edith.memory.providers.sqlite_provider import ISqliteProvider
from edith.memory.providers.embedding_provider import IEmbeddingProvider
from edith.utils.logger import logger

class MemoryRepository:
    def __init__(self, db: ISqliteProvider, embeddings: IEmbeddingProvider):
        self.db = db
        self.embeddings = embeddings
        self.db.initialize()

    def get(self, memory_id: str) -> Optional[Memory]:
        """Retrieves a single memory by ID."""
        return self.db.get_memory(memory_id)

    def save(self, memory: Memory) -> None:
        """Saves a memory to both SQLite and the Embedding provider."""
        # 1. Update Embeddings if value/title changed
        text_representation = f"{memory.title}: {memory.value}"
        try:
            emb_vector = self.embeddings.generate_embedding(text_representation)
            memory.embedding_id = self.embeddings.store_embedding(memory.id, emb_vector)
        except Exception as e:
            logger.warning(f"Failed to generate embedding for memory {memory.id}: {e}")
            
        # 2. Save relational data
        self.db.save_memory(memory)

    def delete(self, memory_id: str) -> None:
        """Deletes a memory completely."""
        mem = self.db.get_memory(memory_id)
        if mem and mem.embedding_id:
            try:
                self.embeddings.delete_embedding(mem.embedding_id)
            except Exception as e:
                logger.warning(f"Failed to delete embedding for memory {memory_id}: {e}")
                
        self.db.delete_memory(memory_id)

    def list_by_category(self, category: Optional[MemoryCategory] = None) -> List[Memory]:
        """Lists all memories, optionally filtered by category."""
        return self.db.list_memories(category)
        
    def save_relationship(self, relationship: MemoryRelationship) -> None:
        self.db.save_relationship(relationship)
        
    def get_relationships(self, source_id: str) -> List[MemoryRelationship]:
        return self.db.get_relationships(source_id)
