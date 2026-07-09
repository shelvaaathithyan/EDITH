from typing import Dict, Any
from edith.core.interfaces.context import IContextManager
from edith.interaction.context.context_store import ContextStore
from edith.interaction.context.context_resolver import ContextResolver
from edith.interaction.context.context_models import ContextNode
from edith.core.events import event_bus, AppEvent

class ContextManager(IContextManager):
    """
    Implements the core interface but routes structured updates into the ContextStack.
    """
    def __init__(self):
        self.store = ContextStore()
        self.resolver = ContextResolver(self.store)
        
        # Subscribe to Vision updates
        event_bus.subscribe(AppEvent.SCREEN_CAPTURED, lambda data: self.update_context({"last_screenshot": data.get("path")}))
        event_bus.subscribe(AppEvent.OCR_COMPLETED, lambda data: self.update_context({"last_ocr_result": data.get("text")}))
        event_bus.subscribe(AppEvent.UI_DETECTED, lambda data: self.update_context({"detected_ui_elements": data.get("count")}))
        event_bus.subscribe(AppEvent.VISION_ANALYZED, lambda data: self.update_context({
            "last_vision_result": data.get("summary"),
            "detected_windows": data.get("detected_windows", []),
            "detected_errors": data.get("detected_errors", [])
        }))
        
        # Subscribe to Media updates
        event_bus.subscribe(AppEvent.PLAYBACK_STARTED, lambda data: self.update_context({"media_session": data.get("track")}))
        event_bus.subscribe(AppEvent.TRACK_CHANGED, lambda data: self.update_context({"media_session": data.get("track")}))
        event_bus.subscribe(AppEvent.PLAYBACK_PAUSED, lambda _: self.update_context({"playback_state": "PAUSED"}))
        event_bus.subscribe(AppEvent.PLAYBACK_STOPPED, lambda _: self.update_context({"playback_state": "STOPPED"}))

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
            elif key in ["last_screenshot", "image_path", "screenshot"]:
                node_type = "screenshot"
            elif key in ["last_ocr_result", "ocr_text", "detected_text"]:
                node_type = "ocr_result"
            elif key in ["last_vision_result", "vision_summary", "summary"]:
                node_type = "vision_result"
            elif key in ["detected_windows", "windows"]:
                node_type = "detected_windows"
            elif key in ["detected_ui_elements", "ui_elements"]:
                node_type = "detected_ui_elements"
            elif key in ["detected_errors", "errors"]:
                node_type = "detected_errors"
            elif key in ["media_session", "track"]:
                node_type = "media_session"
            elif key in ["playback_state", "playing_status"]:
                node_type = "playback_state"
                
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
