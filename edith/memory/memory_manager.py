"""
Memory Manager.
Provides the high-level API for remembering, recalling, consolidating, and relating memories.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from edith.memory.memory_models import Memory, MemoryCategory, MemorySource, MemoryQuery, MemoryRelationship
from edith.memory.memory_repository import MemoryRepository
from edith.memory.memory_search import MemorySearch
from edith.memory.memory_classifier import MemoryClassifier, ExtractedMemory
from edith.memory.memory_constants import MAX_CONFIDENCE
from edith.core.events import event_bus, AppEvent
from edith.utils.logger import logger

class MemoryManager:
    def __init__(self, repository: MemoryRepository):
        self.repo = repository
        self.search_engine = MemorySearch(self.repo)
        self.classifier = MemoryClassifier()
        
        # Subscribe to Orchestrator completion to extract memories from interactions
        event_bus.subscribe(AppEvent.REQUEST_COMPLETED, self._on_request_completed)

    def _on_request_completed(self, data: Dict[str, Any]) -> None:
        context = data.get("context")
        if context and context.user_input:
            # We can run memory classification on user input
            # In a full implementation, we might also analyze the tool executions or context modifications
            self.remember(context.user_input, source=MemorySource.IMPLICIT)

    def _consolidate_memory(self, extracted: ExtractedMemory) -> Memory:
        """
        Consolidates a new memory with existing ones to prevent duplicates.
        If a similar memory exists in the same category, it updates the value and boosts confidence.
        """
        # Find existing memory by title/category
        existing = self.repo.list_by_category(extracted.category)
        
        for mem in existing:
            # Simple heuristic for consolidation: if titles match closely
            if mem.title.lower() == extracted.title.lower():
                logger.info(f"Consolidating memory: {mem.title}")
                
                # If value changed, update it and preserve old in metadata
                if mem.value != extracted.value:
                    if "historical_values" not in mem.metadata:
                        mem.metadata["historical_values"] = []
                    mem.metadata["historical_values"].append({
                        "value": mem.value,
                        "changed_at": datetime.now().isoformat()
                    })
                    mem.value = extracted.value
                
                # Dynamic Confidence Increase
                mem.confidence = min(MAX_CONFIDENCE, mem.confidence + (extracted.confidence * 0.2))
                mem.updated_time = datetime.now()
                
                # Merge tags
                mem.tags = list(set(mem.tags + extracted.tags))
                return mem
                
        # No existing memory found, create a new one
        return Memory(
            category=extracted.category,
            title=extracted.title,
            value=extracted.value,
            confidence=extracted.confidence,
            importance=extracted.importance,
            source=extracted.source,
            tags=extracted.tags
        )

    def remember(self, text: str, source: MemorySource = MemorySource.EXPLICIT) -> Optional[Memory]:
        """
        Processes text and saves it if it qualifies as a memory.
        """
        extracted = None
        if source == MemorySource.EXPLICIT:
            extracted = self.classifier.classify_explicit(text)
        else:
            extracted = self.classifier.classify_implicit(text)
            
        if not extracted:
            return None
            
        memory = self._consolidate_memory(extracted)
        self.repo.save(memory)
        
        event_bus.publish(
            AppEvent.MEMORY_UPDATED if hasattr(memory, '_consolidation') else AppEvent.MEMORY_CREATED, 
            memory
        )
        return memory

    def save_memory_direct(self, memory: Memory) -> None:
        """Saves a fully formed memory object directly."""
        self.repo.save(memory)
        event_bus.publish(AppEvent.MEMORY_CREATED, memory)

    def recall(self, query_text: str, limit: int = 5, categories: Optional[List[MemoryCategory]] = None) -> List[Memory]:
        """
        Retrieves top memories matching the query.
        Updates access count and last_accessed for retrieved memories.
        """
        query = MemoryQuery(query=query_text, limit=limit, categories=categories)
        results = self.search_engine.search(query)
        
        now = datetime.now()
        for mem in results:
            mem.access_count += 1
            mem.last_accessed = now
            self.repo.save(mem)
            event_bus.publish(AppEvent.MEMORY_ACCESSED, mem)
            
        event_bus.publish(AppEvent.MEMORY_SEARCHED, {"query": query_text, "results_count": len(results)})
        return results
        
    def link_memories(self, source_id: str, target_id: str, relation_type: str) -> None:
        """Creates a relationship between two memories."""
        rel = MemoryRelationship(source_id=source_id, target_id=target_id, relation_type=relation_type)
        self.repo.save_relationship(rel)

    def forget(self, memory_id: str) -> None:
        """Deletes a memory permanently."""
        self.repo.delete(memory_id)
        event_bus.publish(AppEvent.MEMORY_DELETED, memory_id)
