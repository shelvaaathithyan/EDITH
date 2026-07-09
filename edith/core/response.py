from edith.core.interfaces.response import IResponseGenerator
from edith.core.models import OrchestrationContext
from edith.ai.models import ChatResponse, ErrorResponse, ExecutionPlan

class DefaultResponseGenerator(IResponseGenerator):
    def generate(self, context: OrchestrationContext) -> str:
        """Determines the final spoken response based on pipeline context."""
        
        # If there's a hard error
        if context.error:
            return f"An error occurred: {str(context.error)}"

        # If we have a planner response
        if context.planner_response:
            resp_data = context.planner_response.data
            
            if isinstance(resp_data, ErrorResponse):
                return resp_data.message
                
            if isinstance(resp_data, ChatResponse):
                return resp_data.response
                
            if isinstance(resp_data, ExecutionPlan):
                # If execution yielded a specific result
                if context.execution_result:
                    from edith.ai.models import ToolResult
                    if isinstance(context.execution_result, ToolResult):
                        return context.execution_result.message
                    return str(context.execution_result)
                # Fallback to narrating the goal
                return f"I have completed the task: {resp_data.goal}"

        return "I'm not sure how to respond to that."
