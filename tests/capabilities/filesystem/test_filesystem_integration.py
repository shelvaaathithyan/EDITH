import pytest
from pathlib import Path
from edith.core.dispatcher import Dispatcher, ContextResolutionStage, ExecutionStage
from edith.core.models import OrchestrationContext
from edith.ai.models import ExecutionPlan, ExecutionStep, PlannerResponse, ToolResult
from edith.interaction.context.context_manager import context_manager
from edith.core.resolver import CapabilityResolver
from edith.capabilities.filesystem.filesystem_capability import FilesystemCapability
from edith.core.interfaces.memory import IMemoryManager

class MockMemoryManager(IMemoryManager):
    def store(self, role, content): pass
    def get_recent(self, limit): return []
    def get_history(self): return []
    def clear(self): pass

@pytest.fixture
def integration_pipeline():
    context_manager.update_context({"last_folder": None, "last_file": None})
    resolver = CapabilityResolver()
    
    # We will register filesystem explicitly for the test instead of relying on default executor
    from edith.permission.permission_policy import policy_engine
    from edith.permission.permission_models import RiskLevel, PermissionAction
    policy_engine.policy[RiskLevel.MEDIUM] = PermissionAction.EXECUTE
    
    from edith.permission.permission_manager import permission_manager
    pipeline = Dispatcher(
        resolver=resolver,
        permission_manager=permission_manager,
        memory_manager=MockMemoryManager(),
        context_manager=context_manager
    )
    # The CapabilityResolver instantiates FilesystemCapability by tool name "filesystem"
    return pipeline

def test_full_filesystem_conversational_flow(integration_pipeline, tmp_path):
    dispatcher = integration_pipeline
    
    ai_folder = str(tmp_path / "AI")
    
    from edith.ai.models import ResponseMetadata
    metadata = ResponseMetadata(provider="test", model="test", latency=0.0, created_at="2026")
    
    # 1. Create folder AI
    plan = ExecutionPlan(goal="Create AI folder", steps=[
        ExecutionStep(tool="filesystem", arguments={"action": "create_folder", "path": ai_folder})
    ])
    ctx = OrchestrationContext(user_input="Create folder AI", planner_response=PlannerResponse(data=plan, metadata=metadata))
    dispatcher.dispatch(ctx)
    assert ctx.execution_result.success is True
    
    # Context should now track "last_folder": ai_folder
    assert context_manager.get_context().get("last_folder") == ai_folder
    
    # 2. Rename it
    plan = ExecutionPlan(goal="Rename it", steps=[
        ExecutionStep(tool="filesystem", arguments={"action": "rename", "path": "it", "new_name": "EDITH_CORE"})
    ])
    ctx = OrchestrationContext(user_input="Rename it to EDITH_CORE", planner_response=PlannerResponse(data=plan, metadata=metadata))
    dispatcher.dispatch(ctx)
    
    edith_folder = str(tmp_path / "EDITH_CORE")
    assert ctx.execution_result.success is True
    assert context_manager.get_context().get("last_folder") == edith_folder
    
    # 3. Move it
    dest_dir = tmp_path / "Desktop"
    plan = ExecutionPlan(goal="Move it", steps=[
        ExecutionStep(tool="filesystem", arguments={"action": "move", "path": "it", "dest": str(dest_dir)})
    ])
    ctx = OrchestrationContext(user_input="Move it to Desktop", planner_response=PlannerResponse(data=plan, metadata=metadata))
    dispatcher.dispatch(ctx)
    
    moved_folder = str(dest_dir / "EDITH_CORE")
    assert ctx.execution_result.success is True
    assert context_manager.get_context().get("last_folder") == str(dest_dir) # Context becomes the destination directory currently
    
    # Let's explicitly set the context back to the moved folder to simulate what a real context resolver might do
    context_manager.update_context({"last_folder": moved_folder})
    
    # 4. Compress it
    zip_path = str(tmp_path / "backup.zip")
    plan = ExecutionPlan(goal="Compress it", steps=[
        ExecutionStep(tool="filesystem", arguments={"action": "compress_zip", "path": "it", "dest": zip_path})
    ])
    ctx = OrchestrationContext(user_input="Compress it", planner_response=PlannerResponse(data=plan, metadata=metadata))
    dispatcher.dispatch(ctx)
    
    assert ctx.execution_result.success is True
    assert Path(zip_path).exists()
    assert context_manager.get_context().get("last_file") == zip_path
    
    # 5. Extract it
    extract_path = str(tmp_path / "extracted")
    plan = ExecutionPlan(goal="Extract it", steps=[
        ExecutionStep(tool="filesystem", arguments={"action": "extract_zip", "path": "it", "dest": extract_path})
    ])
    ctx = OrchestrationContext(user_input="Extract it", planner_response=PlannerResponse(data=plan, metadata=metadata))
    dispatcher.dispatch(ctx)
    
    assert ctx.execution_result.success is True
    assert Path(extract_path).exists()
    assert context_manager.get_context().get("last_folder") == extract_path
    
    # 6. Delete it (Recycle)
    plan = ExecutionPlan(goal="Delete it", steps=[
        ExecutionStep(tool="filesystem", arguments={"action": "delete", "path": "it", "permanent": False})
    ])
    ctx = OrchestrationContext(user_input="Delete it", planner_response=PlannerResponse(data=plan, metadata=metadata))
    dispatcher.dispatch(ctx)
    
    # Permission manager should halt this!
    assert ctx.halt_pipeline is True
    assert ctx.final_response == "This action requires confirmation. Do you want me to continue?"
    
    # 7. Simulate "Yes"
    from edith.permission.permission_manager import permission_manager
    resolved_plan = permission_manager.resolve_confirmation(True)
    assert resolved_plan is not None
    
    ctx_resume = OrchestrationContext(user_input="Yes", planner_response=PlannerResponse(data=ExecutionPlan(goal="resume", steps=[]), metadata=metadata))
    ctx_resume.resolved_plan = resolved_plan
    ctx_resume.skip_permission_check = True
    dispatcher.dispatch(ctx_resume)
    
    assert ctx_resume.execution_result.success is True
    assert not Path(extract_path).exists()
