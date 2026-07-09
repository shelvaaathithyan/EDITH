from edith.core.interfaces.executor import IToolExecutor
from edith.ai.models import ExecutionPlan
from edith.utils.logger import logger

class CapabilityResolver:
    def __init__(self, default_executor: IToolExecutor):
        self.default_executor = default_executor

    def resolve_and_execute(self, plan: ExecutionPlan) -> str:
        """
        Determines the correct capability provider (Local Tool, Plugin, Remote Service)
        and executes the plan.
        """
        # For MVP, we route everything to the default local Tool Executor.
        # Future additions will inspect `plan` and dispatch dynamically.
        logger.debug(f"CapabilityResolver routing execution plan...")
        return self.default_executor.execute(plan)
