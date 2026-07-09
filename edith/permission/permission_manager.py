from typing import Union
from edith.core.interfaces.permission import IPermissionManager
from edith.ai.models import ExecutionPlan, ResolvedExecutionPlan
from edith.permission.permission_store import PermissionStore
from edith.permission.permission_policy import policy_engine
from edith.permission.permission_models import RiskLevel, PermissionAction, PendingAction, PendingActionStatus
from edith.core.events import event_bus
from edith.permission.permission_events import PermissionEvent
from edith.utils.logger import logger

class PermissionManager(IPermissionManager):
    def __init__(self):
        self.store = PermissionStore()
        
        # Capability risk declarations
        # In a larger system, capabilities might register themselves.
        # For now, we use a simple matrix to map tool/actions to RiskLevels.
        self._risk_matrix = {
            "browser.launch": RiskLevel.LOW,
            "browser.close": RiskLevel.LOW,
            "desktop.launch": RiskLevel.LOW,
            "desktop.focus": RiskLevel.LOW,
            "desktop.close": RiskLevel.MEDIUM,
            "filesystem.delete": RiskLevel.HIGH,
            "filesystem.write_text": RiskLevel.HIGH,
            "system.shutdown": RiskLevel.CRITICAL
        }
        
        # Load filesystem manifest risks
        try:
            from edith.capabilities.filesystem.filesystem_manifest import MANIFEST
            for action, risk in MANIFEST["risk_matrix"].items():
                self._risk_matrix[f"filesystem.{action}"] = risk
        except ImportError:
            pass

    def _determine_risk(self, plan: Union[ExecutionPlan, ResolvedExecutionPlan]) -> RiskLevel:
        """Determines the overall risk level for a given plan."""
        highest_risk = RiskLevel.LOW
        
        for step in plan.steps:
            action = step.arguments.get("action", "")
            tool_name = step.tool.lower()
            
            from edith.sdk.capability import capability_registry
            cap = capability_registry.get_capability(tool_name)
            
            if cap:
                risk = cap.get_risk(action)
            else:
                key = f"{step.tool}.{action}" if action else step.tool
                risk = self._risk_matrix.get(key, RiskLevel.MEDIUM) # Fallback
            
            if risk.value > highest_risk.value:
                highest_risk = risk
                
        return highest_risk

    def evaluate_plan(self, plan: Union[ExecutionPlan, ResolvedExecutionPlan]) -> bool:
        """
        Evaluates a plan and dictates if it can execute immediately.
        Returns False if the pipeline must halt for confirmation.
        """
        # If there's an active pending action that we just confirmed, we wouldn't be evaluating it again.
        # The dispatcher handles resumption. This method is for NEW plans.
        
        risk = self._determine_risk(plan)
        action = policy_engine.evaluate(risk)
        
        if action == PermissionAction.EXECUTE:
            return True
            
        elif action in [PermissionAction.OPTIONAL_CONFIRM, PermissionAction.REQUIRE_CONFIRM, PermissionAction.REQUIRE_EXPLICIT_CONFIRM]:
            logger.info(f"PermissionManager: Plan halted for confirmation. Risk={risk.name}, PolicyAction={action.name}")
            
            pending = PendingAction(plan=plan, risk_level=risk)
            self.store.store_action(pending)
            
            # Integrate with Interaction Context
            from edith.interaction.context.context_manager import context_manager
            context_manager.update_context({
                "pending_action": pending.id,
                "risk_level": risk.name,
                "permission_action": action.name
            })
            
            event_bus.publish(PermissionEvent.PERMISSION_REQUESTED, pending)
            return False
            
        elif action == PermissionAction.DENY:
            logger.warning(f"PermissionManager: Action denied due to risk policy. Risk={risk.name}")
            event_bus.publish(PermissionEvent.PERMISSION_DENIED, plan)
            return False
            
        return False
        
    def resolve_confirmation(self, confirmed: bool) -> Union[ExecutionPlan, ResolvedExecutionPlan, None]:
        """
        Called when a simple confirmation is detected.
        If confirmed=True, grants the active pending action and returns it.
        If False, cancels it.
        Returns the plan to resume if granted, None otherwise.
        """
        active = self.store.get_active_action()
        if not active:
            return None
            
        if confirmed:
            active.status = PendingActionStatus.GRANTED
            event_bus.publish(PermissionEvent.PERMISSION_GRANTED, active)
            self.store.remove_action(active.id)
            return active.plan
        else:
            active.status = PendingActionStatus.DENIED
            event_bus.publish(PermissionEvent.PERMISSION_CANCELLED, active)
            self.store.remove_action(active.id)
            return None

# Global instance
permission_manager = PermissionManager()
