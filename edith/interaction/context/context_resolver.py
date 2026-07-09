import re
from typing import Optional
from edith.interaction.context.context_store import ContextStore
from edith.interaction.context.context_models import ContextNode
from edith.interaction.context.context_exceptions import ContextResolutionError
from edith.core.events import event_bus
from edith.interaction.context.context_events import ContextEvent

class ContextResolver:
    """
    Resolves natural language references (e.g. "it", "previous application") into concrete ContextNodes.
    """
    def __init__(self, store: ContextStore):
        self.store = store
        
        # Lists of words that indicate relative positioning
        self.current_keywords = {"it", "this", "that", "current", "same", "selected", "opened", "focused", "running", "there", "here"}
        self.previous_keywords = {"previous", "last", "again"}

    def resolve(self, reference: str, expected_type: Optional[str] = None) -> ContextNode:
        """
        Attempts to resolve an ambiguous string to a ContextNode.
        Raises ContextResolutionError if it cannot be resolved.
        """
        if not reference:
            raise ContextResolutionError("Empty reference cannot be resolved.")
            
        ref_lower = reference.lower().strip()
        
        # Check if it's a simple exact pronoun match
        if ref_lower in self.current_keywords:
            node = self.store.find_by_type(expected_type) if expected_type else self.store.find_any()
            if node:
                event_bus.publish(ContextEvent.CONTEXT_RESOLVED, node)
                return node
            raise ContextResolutionError(f"Could not resolve '{reference}' - no active context found.")
            
        # Parse complex phrases like "previous search" or "the browser"
        tokens = ref_lower.split()
        
        skip_count = 0
        target_type = expected_type
        
        for token in tokens:
            if token in self.previous_keywords:
                skip_count = 1
            elif token in ["browser", "application", "file", "folder", "website", "search"]:
                target_type = token
                
        # Attempt resolution
        if target_type:
            node = self.store.find_by_type(target_type, skip_count=skip_count)
        else:
            node = self.store.find_any(skip_count=skip_count)
            
        if node:
            event_bus.publish(ContextEvent.CONTEXT_RESOLVED, node)
            return node
            
        # If we couldn't resolve it via pronouns, it might just be a hardcoded string that doesn't need resolution
        # However, if expected_type was enforced and we didn't find it, we should throw.
        raise ContextResolutionError(f"Could not resolve reference '{reference}' to any known context.")
