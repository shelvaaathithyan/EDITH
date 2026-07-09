from typing import Dict, Any, Optional
from edith.interaction.context.context_manager import context_manager

class CapabilityContext:
    """
    A wrapper around the global context manager that capabilities use.
    Provides standard helper methods for reading, updating, and publishing context.
    """
    def __init__(self, capability_id: str):
        self.capability_id = capability_id

    def get_context(self) -> Dict[str, Any]:
        """Read the global context state."""
        return context_manager.get_context()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific context value."""
        return self.get_context().get(key, default)

    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update the context with the provided key/value pairs.
        These are typically mapped to ContextNodes internally.
        """
        context_manager.update_context(updates)

    def publish_event(self, event_type: str, data: Any) -> None:
        """
        Publish a specific context event related to this capability.
        """
        # We can route this to the global event bus
        from edith.core.events import event_bus
        event_bus.publish(event_type, {"capability": self.capability_id, "data": data})
