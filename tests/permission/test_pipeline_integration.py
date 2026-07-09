import pytest
from edith.core.dispatcher import Dispatcher, PermissionStage, ContextResolutionStage, ExecutionStage
from edith.core.models import OrchestrationContext
from edith.ai.models import ExecutionPlan, ExecutionStep, PlannerResponse, ToolResult
from edith.permission.permission_manager import permission_manager
from edith.permission.permission_models import RiskLevel
from edith.interaction.context.context_manager import ContextManager
from edith.core.resolver import CapabilityResolver
from edith.core.interfaces.memory import IMemoryManager

class MockMemoryManager(IMemoryManager):
    def store(self, role, content): pass
    def get_recent(self, limit): return []
    def get_history(self): return []
    def clear(self): pass

class MockCapabilityResolver(CapabilityResolver):
    def __init__(self):
        pass
    def resolve_and_execute(self, plan):
        return ToolResult(success=True, message="mock message", data={"result": "mock executed"})

@pytest.fixture
def clean_pipeline():
    permission_manager.store.clear()
    
    ctx_manager = ContextManager()
    memory_manager = MockMemoryManager()
    resolver = MockCapabilityResolver()
    
    dispatcher = Dispatcher(resolver, permission_manager, memory_manager, ctx_manager)
    return dispatcher, permission_manager

def test_pipeline_interception(clean_pipeline):
    dispatcher, pm = clean_pipeline
    
    # 1. Dispatch a high-risk action
    step = ExecutionStep(tool="filesystem", arguments={"action": "delete_folder", "path": "test"})
    plan = ExecutionPlan(goal="delete", steps=[step])
    from edith.ai.models import ResponseMetadata
    metadata = ResponseMetadata(provider="test", model="test", latency=0.0, created_at="2026")
    response = PlannerResponse(data=plan, metadata=metadata)
    
    ctx = OrchestrationContext(user_input="delete folder", planner_response=response)
    dispatcher.dispatch(ctx)
    
    # Assert it was halted
    assert ctx.halt_pipeline is True
    assert ctx.final_response == "This action requires confirmation. Do you want me to continue?"
    assert pm.store.get_active_action() is not None
    assert pm.store.get_active_action().risk_level == RiskLevel.HIGH
    
    # 2. Simulate User confirming it
    resolved_plan = pm.resolve_confirmation(True)
    assert resolved_plan is not None
    assert pm.store.get_active_action() is None
    
    # In real orchestrator, we would dispatch again
    ctx_resume = OrchestrationContext(
        user_input="yes", 
        planner_response=PlannerResponse(data=ExecutionPlan(goal="resume pending action", steps=[]), metadata=metadata)
    )
    ctx_resume.resolved_plan = resolved_plan
    ctx_resume.skip_permission_check = True
    
    dispatcher.dispatch(ctx_resume)
    
    # It should have executed this time
    assert ctx_resume.halt_pipeline is False
    assert ctx_resume.execution_result.success is True
    assert ctx_resume.execution_result.data["result"] == "mock executed"
