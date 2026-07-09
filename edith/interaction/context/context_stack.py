from typing import List, Optional, Iterator
from edith.interaction.context.context_models import ContextNode

class ContextStack:
    """
    A hierarchical stack representing the current conversational context.
    Provides methods to query nodes chronologically.
    """
    def __init__(self):
        self._nodes: List[ContextNode] = []

    def push(self, node: ContextNode):
        """Adds a new node or updates an existing one, moving it to the top."""
        # Remove if exists to re-append at the end (top of stack)
        self._nodes = [n for n in self._nodes if n.id != node.id]
        self._nodes.append(node)

    def remove(self, node_id: str):
        """Removes a node by ID."""
        self._nodes = [n for n in self._nodes if n.id != node_id]

    def clear(self):
        self._nodes.clear()

    def get_top(self) -> Optional[ContextNode]:
        """Returns the most recently accessed node."""
        if not self._nodes:
            return None
        return self._nodes[-1]

    def get_all(self) -> List[ContextNode]:
        """Returns all nodes, ordered from oldest to newest."""
        return list(self._nodes)

    def iter_top_down(self) -> Iterator[ContextNode]:
        """Yields nodes from newest to oldest."""
        for node in reversed(self._nodes):
            yield node
