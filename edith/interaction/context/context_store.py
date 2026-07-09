import threading
from typing import List, Optional
from edith.core.events import event_bus
from edith.interaction.context.context_events import ContextEvent
from edith.interaction.context.context_models import ContextNode
from edith.interaction.context.context_stack import ContextStack

class ContextStore:
    """
    Thread-safe store that manages the ContextStack and handles lazy eviction of expired contexts.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._stack = ContextStack()

    def _evict_expired(self):
        """Removes expired nodes. Must be called with lock acquired."""
        expired_nodes = []
        for node in self._stack.get_all():
            if node.is_expired:
                expired_nodes.append(node)
                
        for node in expired_nodes:
            self._stack.remove(node.id)
            event_bus.publish(ContextEvent.CONTEXT_EXPIRED, node)

    def push(self, node: ContextNode):
        with self._lock:
            self._evict_expired()
            self._stack.push(node)
            event_bus.publish(ContextEvent.CONTEXT_CREATED, node)

    def remove(self, node_id: str):
        with self._lock:
            self._stack.remove(node_id)

    def clear(self):
        with self._lock:
            self._stack.clear()
            event_bus.publish(ContextEvent.CONTEXT_CLEARED, None)

    def get_top(self) -> Optional[ContextNode]:
        with self._lock:
            self._evict_expired()
            return self._stack.get_top()

    def get_all(self) -> List[ContextNode]:
        with self._lock:
            self._evict_expired()
            return self._stack.get_all()

    def find_by_type(self, context_type: str, skip_count: int = 0) -> Optional[ContextNode]:
        """
        Finds the most recent node of a given type.
        skip_count allows skipping the most recent N matches (e.g. for "previous").
        """
        with self._lock:
            self._evict_expired()
            matches = 0
            for node in self._stack.iter_top_down():
                if node.type == context_type:
                    if matches == skip_count:
                        node.touch()
                        event_bus.publish(ContextEvent.CONTEXT_UPDATED, node)
                        return node
                    matches += 1
            return None

    def find_any(self, skip_count: int = 0) -> Optional[ContextNode]:
        """Finds the most recent node regardless of type, with optional skipping."""
        with self._lock:
            self._evict_expired()
            matches = 0
            for node in self._stack.iter_top_down():
                if matches == skip_count:
                    node.touch()
                    event_bus.publish(ContextEvent.CONTEXT_UPDATED, node)
                    return node
                matches += 1
            return None
