from abc import ABC, abstractmethod
import time
import traceback
from typing import Dict, Any, Callable, List
from edith.ai.models import ResolvedExecutionPlan, ResolvedExecutionStep, ToolResult
from edith.utils.logger import logger
from edith.core.events import event_bus
from edith.core.telemetry import TelemetryTracker
from edith.permission.permission_models import RiskLevel

from edith.sdk.capability.capability_models import CapabilityManifest, CapabilityResult
from edith.sdk.capability.capability_health import CapabilityHealth
from edith.sdk.capability.capability_events import CapabilityEvents
from edith.sdk.capability.capability_context import CapabilityContext
from edith.sdk.capability.capability_exceptions import (
    CapabilityInitializationError,
    CapabilityExecutionError,
    CapabilityValidationError,
    CapabilityActionNotFoundError,
    CapabilityUnavailableError
)

class BaseCapability(ABC):
    def __init__(self):
        self._manifest: CapabilityManifest = self.get_manifest()
        self.context = CapabilityContext(self._manifest.id)
        self._actions: Dict[str, Callable] = {}
        self._health: CapabilityHealth = CapabilityHealth.UNAVAILABLE
        self.telemetry = TelemetryTracker()

    @abstractmethod
    def get_manifest(self) -> CapabilityManifest:
        """Returns the static capability manifest."""
        pass

    def register_action(self, action_name: str, handler: Callable):
        """Registers a handler function for a specific action."""
        if action_name not in self._manifest.supported_actions:
            logger.warning(f"Registering action '{action_name}' which is not in the manifest's supported_actions for {self._manifest.id}.")
        self._actions[action_name] = handler

    def supported_actions(self) -> List[str]:
        return self._manifest.supported_actions

    def get_risk(self, action: str) -> RiskLevel:
        return self._manifest.risk_matrix.get(action, RiskLevel.MEDIUM)

    def initialize(self) -> None:
        """Lifecycle: Set up the capability. Can be overridden."""
        try:
            self._do_initialize()
            self._health = CapabilityHealth.HEALTHY
            event_bus.publish(CapabilityEvents.CAPABILITY_INITIALIZED, {"capability": self._manifest.id})
            event_bus.publish(CapabilityEvents.CAPABILITY_READY, {"capability": self._manifest.id})
        except Exception as e:
            self._health = CapabilityHealth.ERROR
            event_bus.publish(CapabilityEvents.CAPABILITY_FAILED, {"capability": self._manifest.id, "error": str(e)})
            raise CapabilityInitializationError(f"Failed to initialize {self._manifest.id}: {str(e)}") from e

    def _do_initialize(self) -> None:
        """Subclasses can override this instead of initialize() to ensure health is set."""
        pass

    def shutdown(self) -> None:
        """Lifecycle: Tear down."""
        self._do_shutdown()
        self._health = CapabilityHealth.UNAVAILABLE
        event_bus.publish(CapabilityEvents.CAPABILITY_SHUTDOWN, {"capability": self._manifest.id})

    def _do_shutdown(self) -> None:
        pass

    def health_check(self) -> CapabilityHealth:
        """Returns the current health status of the capability."""
        return self._health

    def validate(self, action: str, args: Dict[str, Any]) -> None:
        """
        Validates the arguments for an action.
        Subclasses should override this and raise CapabilityValidationError if invalid.
        """
        if action not in self._actions:
            raise CapabilityActionNotFoundError(f"Action '{action}' is not supported by {self._manifest.id}.")

    def before_execute(self, action: str, args: Dict[str, Any]) -> None:
        """Hook called before execution."""
        pass

    def after_execute(self, action: str, result: CapabilityResult) -> None:
        """Hook called after execution."""
        pass

    def rollback(self, action: str, args: Dict[str, Any], error: Exception) -> None:
        """Optional hook to clean up if execution fails."""
        pass

    def execute(self, plan: ResolvedExecutionPlan) -> CapabilityResult:
        """
        The main entrypoint for the Orchestrator/Dispatcher.
        Routes to the specific registered action.
        """
        if self.health_check() in [CapabilityHealth.UNAVAILABLE, CapabilityHealth.ERROR]:
            return CapabilityResult(
                success=False,
                capability=self._manifest.id,
                action="unknown",
                message=f"Capability {self._manifest.id} is {self.health_check().value}.",
                errors=[f"Capability is not healthy."]
            )

        if not plan.steps:
            return CapabilityResult(
                success=False, capability=self._manifest.id, action="unknown",
                message="No steps provided."
            )

        step = plan.steps[0]
        args = step.arguments
        action = args.get("action", "")

        start_time = time.time()
        result = CapabilityResult(
            success=False,
            capability=self._manifest.id,
            action=action,
            risk_level=self.get_risk(action)
        )

        try:
            self.validate(action, args)
            self.before_execute(action, args)
            
            # Execute action
            handler = self._actions[action]
            action_result = handler(args)
            
            # Process result
            if isinstance(action_result, CapabilityResult):
                result = action_result
            else:
                # Wrap it if handler returned dict or bool
                result.success = True
                result.message = "Action executed successfully."
                if isinstance(action_result, dict):
                    result.structured_data = action_result

        except CapabilityActionNotFoundError as e:
            result.success = False
            result.message = str(e)
            result.errors.append(str(e))
        except CapabilityValidationError as e:
            result.success = False
            result.message = f"Validation Error: {str(e)}"
            result.errors.append(traceback.format_exc())
        except Exception as e:
            logger.error(f"Execution error in {self._manifest.id}.{action}: {e}")
            result.success = False
            result.message = f"Execution Error: {str(e)}"
            result.errors.append(traceback.format_exc())
            try:
                self.rollback(action, args, e)
            except Exception as re:
                logger.error(f"Rollback failed in {self._manifest.id}.{action}: {re}")

        result.execution_time = time.time() - start_time
        
        try:
            self.after_execute(action, result)
        except Exception as e:
            logger.error(f"after_execute failed in {self._manifest.id}.{action}: {e}")

        event_bus.publish(CapabilityEvents.CAPABILITY_EXECUTED, {"capability": self._manifest.id, "action": action, "success": result.success})
        
        return result
