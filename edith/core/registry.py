from typing import Callable, Dict, Any
from edith.utils.logger import logger

class ActionRegistry:
    def __init__(self):
        self._actions: Dict[str, Callable[[Dict[str, Any]], str]] = {}

    def register(self, intent_name: str):
        """Decorator to register an action handler for a specific intent."""
        def decorator(func: Callable[[Dict[str, Any]], str]):
            self._actions[intent_name] = func
            return func
        return decorator

    def execute(self, intent_data: Dict[str, Any]) -> str:
        intent = intent_data.get("intent")
        if not intent:
            return "No intent found to execute."

        handler = self._actions.get(intent)
        if handler:
            try:
                return handler(intent_data)
            except Exception as e:
                logger.error(f"Error executing action {intent}: {e}")
                return f"I encountered an error while trying to perform the action: {e}"
        
        logger.warning(f"No action registered for intent: {intent}")
        return f"I understand you want me to perform a {intent} action, but I don't know how to do that yet."

registry = ActionRegistry()
