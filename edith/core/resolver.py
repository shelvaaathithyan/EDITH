from edith.core.interfaces.executor import IToolExecutor
from edith.ai.models import ExecutionPlan, ToolResult
from edith.utils.logger import logger

class CapabilityResolver:
    def __init__(self, default_executor: IToolExecutor):
        self.default_executor = default_executor

    def resolve_and_execute(self, plan: ExecutionPlan) -> ToolResult:
        """
        Determines the correct capability provider (Local Tool, Plugin, Remote Service)
        and executes the plan.
        """
        logger.debug(f"CapabilityResolver routing execution plan...")
        
        # Check if the tool is "browser" and if we have a registered browser capability
        # For now we will handle this explicitly, but later we should use a generic registry
        tool_name = plan.steps[0].tool.lower() if plan.steps else ""
        
        if tool_name == "browser":
            try:
                from edith.capabilities.browser.browser_capability import browser_capability
                return browser_capability.execute(plan)
            except ImportError as e:
                logger.error(f"Failed to load browser capability: {e}")
                return ToolResult(success=False, message="Browser capability is not installed or failed to load.")
                
        if tool_name == "desktop":
            try:
                from edith.capabilities.desktop.desktop_capability import desktop_capability
                return desktop_capability.execute(plan)
            except ImportError as e:
                logger.error(f"Failed to load desktop capability: {e}")
                return ToolResult(success=False, message="Desktop capability is not installed or failed to load.")
        
        if self.default_executor:
            return self.default_executor.execute(plan)
            
        return ToolResult(success=False, message="No capability resolver found for the requested tool.")
