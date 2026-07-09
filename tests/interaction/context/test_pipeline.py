import pytest
from edith.ai.models import ExecutionPlan, ExecutionStep, ResolvedExecutionPlan
from edith.core.dispatcher import ContextResolutionStage
from edith.core.models import OrchestrationContext
from edith.ai.models import PlannerResponse
from edith.interaction.context.context_manager import context_manager

@pytest.fixture
def clean_context():
    context_manager.get_store().clear()
    return context_manager

def test_pipeline_resolution(clean_context):
    # Setup some previous state
    clean_context.update_context({"last_application": "vscode", "last_action": "launch"})
    
    # Simulate a new plan using "it"
    step = ExecutionStep(tool="desktop", arguments={"action": "close", "application": "it"})
    plan = ExecutionPlan(goal="test", steps=[step])
    from edith.ai.models import ResponseMetadata
    metadata = ResponseMetadata(provider="test", model="test", latency=0.0, created_at="2026")
    response = PlannerResponse(data=plan, metadata=metadata)
    
    orch_ctx = OrchestrationContext(user_input="test", planner_response=response)
    
    # Run resolution stage
    stage = ContextResolutionStage(clean_context)
    stage.process(orch_ctx)
    
    resolved_plan = orch_ctx.resolved_plan
    assert isinstance(resolved_plan, ResolvedExecutionPlan)
    assert resolved_plan.steps[0].arguments["application"] == "vscode"

def test_pipeline_resolution_unresolvable(clean_context):
    # No state
    
    step = ExecutionStep(tool="desktop", arguments={"action": "close", "application": "it"})
    plan = ExecutionPlan(goal="test", steps=[step])
    from edith.ai.models import ResponseMetadata
    metadata = ResponseMetadata(provider="test", model="test", latency=0.0, created_at="2026")
    response = PlannerResponse(data=plan, metadata=metadata)
    
    orch_ctx = OrchestrationContext(user_input="test", planner_response=response)
    
    # Run resolution stage
    stage = ContextResolutionStage(clean_context)
    stage.process(orch_ctx)
    
    resolved_plan = orch_ctx.resolved_plan
    assert isinstance(resolved_plan, ResolvedExecutionPlan)
    # Should fallback to raw "it" because resolution threw error
    assert resolved_plan.steps[0].arguments["application"] == "it"
