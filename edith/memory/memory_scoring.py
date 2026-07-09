"""
Memory Scoring algorithms.
Computes relevance scores based on Recency, Frequency, Decay, Importance, and Confidence.
"""

from typing import List
from datetime import datetime
import math

from edith.memory.memory_models import Memory
from edith.memory.memory_constants import DECAY_RATE_DAYS

class MemoryScoring:
    """Calculates dynamic memory relevance."""
    
    @staticmethod
    def _calculate_decay_multiplier(last_accessed: datetime, now: datetime) -> float:
        """Applies exponential decay based on days since last access."""
        days_passed = (now - last_accessed).total_seconds() / 86400.0
        if days_passed <= 0:
            return 1.0
        # Decay formula: e^(-lambda * t)
        decay = math.exp(-DECAY_RATE_DAYS * days_passed)
        # Ensure it doesn't drop to absolute 0, keeping a floor of 0.1
        return max(0.1, decay)

    @staticmethod
    def _calculate_frequency_multiplier(access_count: int) -> float:
        """Logarithmic scaling for access frequency."""
        if access_count <= 0:
            return 1.0
        return 1.0 + math.log10(access_count + 1)

    @staticmethod
    def score_memory(memory: Memory, now: datetime = None) -> float:
        """
        Calculates the relevance score for a memory.
        Score = (Confidence * Importance) * Decay * Frequency
        """
        if now is None:
            now = datetime.now()
            
        base_score = memory.confidence * memory.importance
        
        decay_multiplier = MemoryScoring._calculate_decay_multiplier(memory.last_accessed, now)
        freq_multiplier = MemoryScoring._calculate_frequency_multiplier(memory.access_count)
        
        # Calculate raw score
        final_score = base_score * decay_multiplier * freq_multiplier
        
        # Normalize slightly but allow it to exceed 1.0 for highly accessed memories
        memory.relevance_score = final_score
        return final_score

    @staticmethod
    def rank_memories(memories: List[Memory]) -> List[Memory]:
        """Scores and sorts memories by relevance (descending)."""
        now = datetime.now()
        for mem in memories:
            MemoryScoring.score_memory(mem, now)
            
        return sorted(memories, key=lambda m: m.relevance_score, reverse=True)
