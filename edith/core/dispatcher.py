from edith.core.models import OrchestrationContext
from edith.ai.models import ExecutionPlan, ChatResponse, ErrorResponse
from edith.core.pipeline import Pipeline, PipelineStage
from edith.core.resolver import CapabilityResolver
from edith.core.interfaces.permission import IPermissionManager
from edith.core.interfaces.memory import IMemoryManager
from edith.core.interfaces.context import IContextManager
from edith.core.response import DefaultResponseGenerator
from edith.utils.logger import logger
from edith.core.events import event_bus, AppEvent

class PermissionStage(PipelineStage):
    def __init__(self, permission_manager: IPermissionManager):
        self.permission_manager = permission_manager

    def process(self, context: OrchestrationContext) -> None:
        plan = context.planner_response.data
        if isinstance(plan, ExecutionPlan):
            if plan.requires_confirmation:
                event_bus.publish(AppEvent.PERMISSION_REQUESTED, plan)
                granted = self.permission_manager.request_permission(plan)
                if granted:
                    event_bus.publish(AppEvent.PERMISSION_GRANTED, plan)
                else:
                    event_bus.publish(AppEvent.PERMISSION_DENIED, plan)
                    context.halt_pipeline = True
                    context.error = Exception("Permission denied by user.")

class ExecutionStage(PipelineStage):
    def __init__(self, resolver: CapabilityResolver, context_manager: IContextManager):
        self.resolver = resolver
        self.context_manager = context_manager

    def process(self, context: OrchestrationContext) -> None:
        plan = context.planner_response.data
        if isinstance(plan, ExecutionPlan):
            event_bus.publish(AppEvent.EXECUTION_STARTED, plan)
            result = self.resolver.resolve_and_execute(plan)
            context.execution_result = result
            
            # Extract ToolResult data to the global context
            from edith.ai.models import ToolResult
            if isinstance(result, ToolResult) and result.success:
                update_data = {
                    "last_tool": plan.steps[0].tool if plan.steps else None,
                }
                # Inject specific tool data like last_browser, last_url
                for k, v in result.data.items():
                    update_data[f"last_{k}"] = v
                self.context_manager.update_context(update_data)
                
            event_bus.publish(AppEvent.EXECUTION_COMPLETED, result)

class MemoryStage(PipelineStage):
    def __init__(self, memory_manager: IMemoryManager, context_manager: IContextManager):
        self.memory_manager = memory_manager
        self.context_manager = context_manager

    def process(self, context: OrchestrationContext) -> None:
        # Update user message
        self.memory_manager.store("user", context.user_input)
        
        # Update system/assistant message
        if context.execution_result:
            self.memory_manager.store("assistant", context.execution_result)
        elif context.planner_response and isinstance(context.planner_response.data, ChatResponse):
            self.memory_manager.store("assistant", context.planner_response.data.response)
            
        # Update context
        self.context_manager.update_context({"last_input": context.user_input})

class Dispatcher:
    def __init__(
        self,
        resolver: CapabilityResolver,
        permission_manager: IPermissionManager,
        memory_manager: IMemoryManager,
        context_manager: IContextManager
    ):
        # We can construct different pipelines based on the response type.
        self.execution_pipeline = Pipeline()
        self.execution_pipeline.add_stage(PermissionStage(permission_manager))
        self.execution_pipeline.add_stage(ExecutionStage(resolver, context_manager))
        self.execution_pipeline.add_stage(MemoryStage(memory_manager, context_manager))

        self.chat_pipeline = Pipeline()
        self.chat_pipeline.add_stage(MemoryStage(memory_manager, context_manager))

    def dispatch(self, context: OrchestrationContext) -> None:
        """Inspects context and runs the appropriate pipeline."""
        if not context.planner_response:
            logger.error("Dispatcher received empty planner response.")
            context.error = Exception("No planner response to dispatch.")
            return

        resp_data = context.planner_response.data

        if isinstance(resp_data, ExecutionPlan):
            logger.info("Dispatching Execution Pipeline...")
            self.execution_pipeline.execute(context)
            
        elif isinstance(resp_data, ChatResponse):
            logger.info("Dispatching Chat Pipeline...")
            self.chat_pipeline.execute(context)
            
        elif isinstance(resp_data, ErrorResponse):
            logger.warning(f"Dispatching Error: {resp_data.message}")
            context.error = Exception(resp_data.message)
            
        else:
            context.error = Exception("Unknown PlannerResponse type.")
