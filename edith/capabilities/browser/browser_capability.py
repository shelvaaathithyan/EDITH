from typing import Any, Dict
import logging

from edith.sdk.capability import (
    BaseCapability,
    CapabilityManifest,
    CapabilityResult,
    CapabilityValidationError
)
from edith.core.events import event_bus, AppEvent
from edith.capabilities.browser.browser_controller import BrowserController
from edith.capabilities.browser.browser_constants import get_search_url
from edith.capabilities.browser.browser_utils import is_url, format_url
from edith.capabilities.browser.browser_manifest import MANIFEST
from edith.capabilities.browser.browser_models import BrowserActionArgs

logger = logging.getLogger(__name__)

class BrowserCapability(BaseCapability):
    def get_manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            id=MANIFEST["id"],
            name=MANIFEST["name"],
            version=MANIFEST["version"],
            author=MANIFEST["author"],
            description=MANIFEST["description"],
            supported_platforms=MANIFEST["supported_platforms"],
            dependencies=MANIFEST["dependencies"],
            supported_actions=MANIFEST["supported_actions"],
            risk_matrix=MANIFEST["risk_matrix"],
            required_permissions=MANIFEST["required_permissions"]
        )

    def _do_initialize(self) -> None:
        self.controller = BrowserController()
        
        # Register Actions
        self.register_action("search", self._action_search)
        self.register_action("navigate", self._action_navigate)
        self.register_action("launch", self._action_navigate) # alias

    def _action_search(self, args: Dict[str, Any]) -> CapabilityResult:
        query = args.get("query")
        browser_req = args.get("browser", "").lower() if args.get("browser") else None
        
        event_bus.publish(AppEvent.BROWSER_SEARCH_STARTED, args)
        
        if query and is_url(query):
            target_url = format_url(query)
        else:
            target_url = get_search_url(None, query or "")
            
        result = self.controller.launch(target_url, browser=browser_req)
        event_bus.publish(AppEvent.BROWSER_SEARCH_COMPLETED, result)
        
        msg = f"Searched for {query} in {result.get('browser', 'browser')}." if query else f"Opened search in {result.get('browser', 'browser')}."
        return CapabilityResult(success=True, capability=self._manifest.id, action="search", message=msg, structured_data=result)

    def _action_navigate(self, args: Dict[str, Any]) -> CapabilityResult:
        query = args.get("query")
        browser_req = args.get("browser", "").lower() if args.get("browser") else None
        
        event_bus.publish(AppEvent.BROWSER_NAVIGATION_STARTED, args)
        
        if query:
            target_url = format_url(query) if is_url(query) or args.get("action") == "navigate" else get_search_url(None, query)
        else:
            target_url = "about:blank"
            
        result = self.controller.launch(target_url, browser=browser_req)
        event_bus.publish(AppEvent.BROWSER_NAVIGATION_COMPLETED, result)
        
        if target_url == "about:blank":
            msg = f"Opened {result.get('browser', 'browser')}."
        else:
            msg = f"Opened {query} in {result.get('browser', 'browser')}."
            
        return CapabilityResult(success=True, capability=self._manifest.id, action="navigate", message=msg, structured_data=result)

