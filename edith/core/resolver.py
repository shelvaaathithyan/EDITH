from typing import Optional, Union
from edith.ai.models import ExecutionPlan, ResolvedExecutionPlan, ToolResult
from edith.core.interfaces.executor import IToolExecutor
from edith.utils.logger import logger
from edith.sdk.capability import capability_registry, CapabilityResult

class CapabilityResolver:
    def __init__(self, default_executor: Optional[IToolExecutor] = None):
        self.default_executor = default_executor

    def resolve_and_execute(self, plan: Union[ExecutionPlan, ResolvedExecutionPlan]) -> ToolResult:
        """
        Determines the correct capability provider via CapabilityRegistry and executes.
        """
        logger.debug("CapabilityResolver routing execution plan...")
        
        tool_name = plan.steps[0].tool.lower() if plan.steps else ""
        
        capability = capability_registry.get_capability(tool_name)
        if capability:
            # Execute through the SDK capability
            cap_result: CapabilityResult = capability.execute(plan)
            # Map SDK CapabilityResult back to core ToolResult
            return ToolResult(
                success=cap_result.success,
                message=cap_result.message,
                data=cap_result.structured_data
            )
        
        if self.default_executor:
            return self.default_executor.execute(plan)
            
        return ToolResult(success=False, message=f"No capability resolver found for the requested tool: {tool_name}")
