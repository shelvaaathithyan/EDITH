import pytest
import time
from edith.permission.permission_models import RiskLevel, PermissionAction, PendingAction, PendingActionStatus
from edith.permission.permission_policy import PermissionPolicy
from edith.permission.permission_store import PermissionStore
from edith.permission.confirmation_detector import ConfirmationDetector
from edith.ai.models import ResolvedExecutionPlan, ResolvedExecutionStep

def test_permission_policy():
    policy = PermissionPolicy()
    assert policy.evaluate(RiskLevel.LOW) == PermissionAction.EXECUTE
    assert policy.evaluate(RiskLevel.HIGH) == PermissionAction.REQUIRE_CONFIRM

def test_permission_store_and_expiration():
    store = PermissionStore()
    plan = ResolvedExecutionPlan(steps=[ResolvedExecutionStep(tool="test", arguments={})])
    
    # Action with short TTL
    action = PendingAction(plan=plan, risk_level=RiskLevel.MEDIUM, ttl_seconds=0.1)
    store.store_action(action)
    
    assert store.get_active_action() is not None
    assert store.get_active_action().id == action.id
    
    time.sleep(0.2)
    # Should lazily evict on next access
    assert store.get_active_action() is None
    
def test_confirmation_detector():
    detector = ConfirmationDetector()
    assert detector.detect("Yes") is True
    assert detector.detect("yeah") is True
    assert detector.detect("proceed") is True
    
    assert detector.detect("No") is False
    assert detector.detect("cancel") is False
    
    # Complex responses
    assert detector.detect("Yes, but only delete the screenshots folder") is None
    assert detector.detect("No move it instead") is None
    
