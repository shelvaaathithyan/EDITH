"""
Memory Classifier.
Analyzes text or interactions to extract memory candidates and assign confidence.
"""

from typing import Optional, Dict, Any
import re
from dataclasses import dataclass

from edith.memory.memory_constants import MemorySource, MemoryCategory, AUTO_SAVE_THRESHOLD
from edith.utils.logger import logger

@dataclass
class ExtractedMemory:
    category: MemoryCategory
    title: str
    value: str
    confidence: float
    importance: float
    source: MemorySource
    tags: list[str]

class MemoryClassifier:
    """Classifies inputs into memory categories and extracts facts."""
    
    # Very basic regex heuristics for demonstration/fallback
    EXPLICIT_REGEX = re.compile(r"(?i)^(remember|store|save)\s+(that\s+)?(.+)")
    PREF_REGEX = re.compile(r"(?i)^my\s+(favorite|preferred)\s+(.+?)\s+is\s+(.+)")

    def __init__(self, ai_planner=None):
        # We can inject the IPlanner here if we want LLM-based classification in the future.
        self.planner = ai_planner

    def classify_explicit(self, text: str) -> Optional[ExtractedMemory]:
        """Fast-path classification for explicit 'Remember that...' commands."""
        match = self.EXPLICIT_REGEX.search(text.strip())
        if not match:
            return None
            
        statement = match.group(3).strip()
        
        # Determine category heuristically
        category = MemoryCategory.FACT
        if "project" in statement.lower() or "workspace" in statement.lower():
            category = MemoryCategory.WORKSPACE
        elif "prefer" in statement.lower() or "favorite" in statement.lower():
            category = MemoryCategory.PREFERENCE
            
        return ExtractedMemory(
            category=category,
            title="Explicit Fact",
            value=statement,
            confidence=1.0,      # Explicit commands have 1.0 confidence
            importance=0.8,      # High importance
            source=MemorySource.EXPLICIT,
            tags=["explicit"]
        )

    def classify_implicit(self, text: str, context_metadata: Dict[str, Any] = None) -> Optional[ExtractedMemory]:
        """Analyzes behavior/statements for implicit habits or preferences."""
        
        match = self.PREF_REGEX.search(text.strip())
        if match:
            item = match.group(2).strip()
            value = match.group(3).strip()
            return ExtractedMemory(
                category=MemoryCategory.PREFERENCE,
                title=f"Preferred {item.title()}",
                value=value,
                confidence=0.6,      # Implicit starts lower
                importance=0.5,
                source=MemorySource.IMPLICIT,
                tags=[item.lower()]
            )
            
        return None
