"""
Memory Search engine.
Orchestrates querying, filtering, and relevance ranking.
"""

from typing import List, Optional
from edith.memory.memory_models import Memory, MemoryQuery
from edith.memory.memory_repository import MemoryRepository
from edith.memory.memory_scoring import MemoryScoring
from edith.utils.logger import logger

class MemorySearch:
    def __init__(self, repository: MemoryRepository):
        self.repo = repository

    def _matches_query(self, memory: Memory, query_text: str) -> bool:
        """Basic fuzzy text matching on title/value/tags."""
        if not query_text:
            return True
            
        q = query_text.lower()
        if q in memory.title.lower() or q in memory.value.lower():
            return True
            
        for tag in memory.tags:
            if q in tag.lower():
                return True
                
        # Semantic search would go here via embeddings if used.
        return False

    def search(self, query: MemoryQuery) -> List[Memory]:
        """
        Executes a memory search using criteria, fuzzy matching, and ranking.
        """
        candidates: List[Memory] = []
        
        # 1. Fetch Candidates
        if query.categories:
            for cat in query.categories:
                candidates.extend(self.repo.list_by_category(cat))
        else:
            candidates = self.repo.list_by_category(None)
            
        # 2. Filter Candidates
        filtered: List[Memory] = []
        for mem in candidates:
            # Filter by confidence/importance thresholds
            if mem.confidence < query.min_confidence:
                continue
            if mem.importance < query.min_importance:
                continue
                
            # Filter by Tags
            if query.tags and not any(tag in mem.tags for tag in query.tags):
                continue
                
            # Filter by Text query
            if query.query and not self._matches_query(mem, query.query):
                continue
                
            filtered.append(mem)
            
        # 3. Score and Rank
        ranked = MemoryScoring.rank_memories(filtered)
        
        # 4. Limit
        return ranked[:query.limit]
