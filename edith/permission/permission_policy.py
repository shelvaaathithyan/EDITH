from typing import Dict
from edith.permission.permission_models import RiskLevel, PermissionAction

class PermissionPolicy:
    """
    Configuration-driven engine mapping RiskLevels to required PermissionActions.
    """
    def __init__(self):
        # Default policy mapping
        self.policy: Dict[RiskLevel, PermissionAction] = {
            RiskLevel.LOW: PermissionAction.EXECUTE,
            RiskLevel.MEDIUM: PermissionAction.OPTIONAL_CONFIRM,
            RiskLevel.HIGH: PermissionAction.REQUIRE_CONFIRM,
            RiskLevel.CRITICAL: PermissionAction.REQUIRE_EXPLICIT_CONFIRM
        }

    def evaluate(self, risk_level: RiskLevel) -> PermissionAction:
        """Determines the required action for a given risk level."""
        return self.policy.get(risk_level, PermissionAction.REQUIRE_CONFIRM)

policy_engine = PermissionPolicy()
