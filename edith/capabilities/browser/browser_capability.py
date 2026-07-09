import time
from edith.ai.models import ExecutionPlan, ToolResult
from edith.utils.logger import logger
from edith.core.events import event_bus, AppEvent

from edith.capabilities.browser.browser_models import BrowserActionArgs
from edith.capabilities.browser.browser_exceptions import BrowserLaunchError
from edith.capabilities.browser.browser_controller import BrowserController
from edith.capabilities.browser.browser_constants import get_search_url
from edith.capabilities.browser.browser_utils import is_url, format_url

class BrowserCapability:
    """
    Main interface for the Browser capability.
    Acts as an Executor for browser-related ExecutionPlans.
    """
    def __init__(self):
        self.controller = BrowserController()

    def execute(self, plan: ExecutionPlan) -> ToolResult:
        """Parses the execution plan, runs the browser action, and returns a ToolResult."""
        if not plan.steps:
            return ToolResult(success=False, message="No steps provided in the execution plan.")
            
        step = plan.steps[0]
        try:
            args = BrowserActionArgs(**step.arguments)
        except Exception as e:
            logger.error(f"Invalid browser arguments: {e}")
            return ToolResult(success=False, message=f"I couldn't understand the browser arguments: {e}")
            
        action = args.action.lower()
        browser_req = args.browser.lower() if args.browser else None
        query = args.query

        start_time = time.time()
        
        try:
            if action == 'search':
                event_bus.publish(AppEvent.BROWSER_SEARCH_STARTED, args.model_dump())
                
                # Check if the user said "search github.com" instead of "search github"
                if query and is_url(query):
                    target_url = format_url(query)
                else:
                    target_url = get_search_url(None, query or "") # Will use default engine
                    
                result = self.controller.launch(target_url, browser=browser_req)
                
                event_bus.publish(AppEvent.BROWSER_SEARCH_COMPLETED, result)
                msg = f"Searched for {query} in {result['browser']}." if query else f"Opened search in {result['browser']}."
                
            elif action == 'navigate' or action == 'launch':
                event_bus.publish(AppEvent.BROWSER_NAVIGATION_STARTED, args.model_dump())
                
                if query:
                    target_url = format_url(query) if is_url(query) or action == 'navigate' else get_search_url(None, query)
                else:
                    # Just launch default blank or new tab
                    target_url = "about:blank"
                    
                result = self.controller.launch(target_url, browser=browser_req)
                
                event_bus.publish(AppEvent.BROWSER_NAVIGATION_COMPLETED, result)
                if target_url == "about:blank":
                    msg = f"Opened {result['browser']}."
                else:
                    msg = f"Opened {query} in {result['browser']}."
                    
            else:
                return ToolResult(success=False, message=f"Browser action '{action}' is not supported yet.")

            duration = time.time() - start_time
            result["duration"] = duration
            
            return ToolResult(
                success=True,
                message=msg,
                data=result
            )
            
        except BrowserLaunchError as e:
            logger.error(f"Browser launch failed: {e}")
            event_bus.publish(AppEvent.BROWSER_LAUNCH_FAILED, str(e))
            return ToolResult(success=False, message="I couldn't launch the browser due to a system error.")
        except Exception as e:
            logger.error(f"Unexpected error in browser capability: {e}")
            event_bus.publish(AppEvent.BROWSER_LAUNCH_FAILED, str(e))
            return ToolResult(success=False, message=f"An unexpected error occurred: {e}")

# Singleton instance exported for the resolver
browser_capability = BrowserCapability()
