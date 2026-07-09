import pytest
from edith.sdk.capability import (
    BaseCapability, 
    CapabilityManifest, 
    CapabilityResult,
    CapabilityRegistry,
    CapabilityActionNotFoundError,
    CapabilityValidationError
)
from edith.permission.permission_models import RiskLevel

class DummyCapability(BaseCapability):
    def get_manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            id="dummy",
            name="Dummy",
            version="1.0",
            author="Test",
            description="A dummy capability for testing",
            supported_platforms=["Windows"],
            dependencies=[],
            supported_actions=["ping", "echo"],
            risk_matrix={"ping": RiskLevel.LOW, "echo": RiskLevel.LOW},
            required_permissions=[]
        )
        
    def _do_initialize(self) -> None:
        self.register_action("ping", self._action_ping)
        self.register_action("echo", self._action_echo)
        
    def _action_ping(self, args) -> CapabilityResult:
        return CapabilityResult(success=True, capability="dummy", action="ping", message="pong")
        
    def _action_echo(self, args) -> CapabilityResult:
        if "text" not in args:
            raise CapabilityValidationError("text argument is missing")
        return CapabilityResult(success=True, capability="dummy", action="echo", message=args["text"])

def test_capability_registry():
    registry = CapabilityRegistry()
    dummy = DummyCapability()
    
    registry.register(dummy)
    
    cap = registry.get_capability("dummy")
    assert cap is not None
    assert cap.get_manifest().name == "Dummy"
    assert len(registry.get_all()) == 1

def test_capability_action_execution():
    dummy = DummyCapability()
    dummy.initialize()
    
    from edith.ai.models import ResolvedExecutionPlan, ResolvedExecutionStep
    
    # Test valid action
    plan = ResolvedExecutionPlan(
        goal="Ping",
        steps=[ResolvedExecutionStep(tool="dummy", arguments={"action": "ping"})]
    )
    result = dummy.execute(plan)
    assert result.success is True
    assert result.message == "pong"
    
    # Test invalid action
    plan2 = ResolvedExecutionPlan(
        goal="Invalid",
        steps=[ResolvedExecutionStep(tool="dummy", arguments={"action": "nonexistent"})]
    )
    result = dummy.execute(plan2)
    assert result.success is False
    assert "is not supported by dummy" in result.message
        
def test_capability_validation_error():
    dummy = DummyCapability()
    dummy.initialize()
    
    from edith.ai.models import ResolvedExecutionPlan, ResolvedExecutionStep
    
    # Test validation error
    plan = ResolvedExecutionPlan(
        goal="Echo",
        steps=[ResolvedExecutionStep(tool="dummy", arguments={"action": "echo"})] # missing 'text'
    )
    
    # Base capability catches CapabilityValidationError and returns failed result
    result = dummy.execute(plan)
    assert result.success is False
    assert "text argument is missing" in result.message
