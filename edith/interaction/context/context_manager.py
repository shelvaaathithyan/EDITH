from typing import Dict, Any
from edith.core.interfaces.context import IContextManager
from edith.interaction.context.context_store import ContextStore
from edith.interaction.context.context_resolver import ContextResolver
from edith.interaction.context.context_models import ContextNode

class ContextManager(IContextManager):
    """
    Implements the core interface but routes structured updates into the ContextStack.
    """
    def __init__(self):
        self.store = ContextStore()
        self.resolver = ContextResolver(self.store)

    def update_context(self, context_data: Dict[str, Any]) -> None:
        """
        Translates flat dictionary updates from Orchestrator into ContextNodes.
        """
        # Look for well-known types in the result data
        # For example: last_application, last_browser, last_url
        
        for key, value in context_data.items():
            if not value:
                continue
                
            node_type = None
            if key in ["last_application", "application"]:
                node_type = "application"
            elif key in ["last_browser", "browser"]:
                node_type = "browser"
            elif key in ["last_url", "url"]:
                node_type = "website"
            elif key in ["last_search", "query"]:
                node_type = "search"
            elif key in ["last_folder", "folder"]:
                node_type = "folder"
            elif key in ["last_file", "file"]:
                node_type = "file"
            elif key in ["last_cwd", "terminal_cwd"]:
                node_type = "cwd"
            elif key in ["last_session_id", "terminal_session"]:
                node_type = "session_id"
            elif key in ["last_workspace_id", "terminal_workspace"]:
                node_type = "workspace_id"
            elif key in ["last_group_id", "terminal_group"]:
                node_type = "group_id"
            elif key in ["last_command", "terminal_command"]:
                node_type = "command"
            elif key in ["last_shell", "terminal_shell"]:
                node_type = "shell"
                
            if node_type:
                node = ContextNode(type=node_type, value=value, metadata=context_data)
                self.store.push(node)

    def get_context(self) -> Dict[str, Any]:
        """
        Returns a flat representation of the top nodes for legacy compatibility
        or state inspection.
        """
        out = {}
        for node in self.store.get_all():
            out[f"last_{node.type}"] = node.value
        return out
        
    def get_store(self) -> ContextStore:
        return self.store
        
    def get_resolver(self) -> ContextResolver:
        return self.resolver

# Global instance
context_manager = ContextManager()
