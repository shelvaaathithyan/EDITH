from typing import Any, Dict
import logging

from edith.sdk.capability import (
    BaseCapability,
    CapabilityManifest,
    CapabilityResult,
    CapabilityValidationError
)
from edith.core.events import event_bus, AppEvent
from edith.capabilities.desktop.desktop_controller import DesktopController
from edith.capabilities.desktop.desktop_detector import detector
from edith.capabilities.desktop.desktop_utils import resolve_alias
from edith.capabilities.desktop.desktop_manifest import MANIFEST
from edith.capabilities.desktop.desktop_models import DesktopActionArgs

logger = logging.getLogger(__name__)

class DesktopCapability(BaseCapability):
    def get_manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            id=MANIFEST["id"],
            name=MANIFEST["name"],
            version=MANIFEST["version"],
            author=MANIFEST["author"],
            description=MANIFEST["description"],
            supported_platforms=MANIFEST["supported_platforms"],
            dependencies=MANIFEST["dependencies"],
            supported_actions=MANIFEST["supported_actions"],
            risk_matrix=MANIFEST["risk_matrix"],
            required_permissions=MANIFEST["required_permissions"]
        )

    def _do_initialize(self) -> None:
        self.controller = DesktopController()
        detector.load_index()
        
        # Register Actions
        self.register_action("launch", self._action_launch)
        self.register_action("close", self._action_close)
        self.register_action("focus", self._action_focus)
        self.register_action("minimize", self._action_minimize)
        self.register_action("maximize", self._action_maximize)
        self.register_action("restore", self._action_restore)

    def validate(self, action: str, args: Dict[str, Any]) -> None:
        super().validate(action, args)
        if "application" not in args:
            raise CapabilityValidationError("Missing 'application' argument.")

    def _prepare_app_context(self, args: Dict[str, Any]) -> dict:
        raw_app_name = args.get("application")
        exe_name = resolve_alias(raw_app_name)
        is_running = self.controller.check_running(exe_name)
        return {
            "raw_name": raw_app_name,
            "exe": exe_name,
            "is_running": is_running,
            "result_data": {
                "application": raw_app_name,
                "executable": exe_name,
                "already_running": is_running,
                "window_found": False
            }
        }

    # --- ACTION HANDLERS ---

    def _action_launch(self, args: Dict[str, Any]) -> CapabilityResult:
        ctx = self._prepare_app_context(args)
        raw_name, exe, is_running, rdata = ctx["raw_name"], ctx["exe"], ctx["is_running"], ctx["result_data"]
        
        event_bus.publish(AppEvent.APPLICATION_LOOKUP_STARTED, raw_name)
        
        if is_running:
            event_bus.publish(AppEvent.APPLICATION_ALREADY_RUNNING, exe)
            action_result = self.controller.focus(exe)
            if action_result["success"]:
                rdata.update({"action_changed_to": "focus", "window_title": action_result.get("window_title"), "window_found": True})
                event_bus.publish(AppEvent.APPLICATION_FOCUSED, rdata)
                return CapabilityResult(success=True, capability=self._manifest.id, action="launch", message=f"{raw_name} is already running. I've brought it to the front.", structured_data=rdata)
            else:
                return CapabilityResult(success=False, capability=self._manifest.id, action="launch", message=f"{raw_name} is already running, but I couldn't bring it to the front.", structured_data=rdata)
        else:
            app_path = detector.find_executable(exe)
            if not app_path:
                event_bus.publish(AppEvent.APPLICATION_NOT_FOUND, exe)
                return CapabilityResult(success=False, capability=self._manifest.id, action="launch", message=f"I couldn't find {raw_name} installed on your system.")
            
            event_bus.publish(AppEvent.APPLICATION_FOUND, app_path)
            rdata["application_path"] = app_path
            
            event_bus.publish(AppEvent.APPLICATION_LAUNCH_STARTED, rdata)
            self.controller.launch(app_path)
            event_bus.publish(AppEvent.APPLICATION_LAUNCH_COMPLETED, rdata)
            return CapabilityResult(success=True, capability=self._manifest.id, action="launch", message=f"Opened {raw_name}.", structured_data=rdata)

    def _action_close(self, args: Dict[str, Any]) -> CapabilityResult:
        ctx = self._prepare_app_context(args)
        if not ctx["is_running"]:
            return CapabilityResult(success=False, capability=self._manifest.id, action="close", message=f"{ctx['raw_name']} is not currently running.")
        
        action_result = self.controller.close(ctx["exe"])
        if action_result["success"]:
            ctx["result_data"].update({"window_title": action_result.get("window_title"), "window_found": True})
            event_bus.publish(AppEvent.APPLICATION_CLOSED, ctx["result_data"])
            return CapabilityResult(success=True, capability=self._manifest.id, action="close", message=f"Closed {ctx['raw_name']}.", structured_data=ctx["result_data"])
        return CapabilityResult(success=False, capability=self._manifest.id, action="close", message=f"I couldn't close {ctx['raw_name']}. {action_result['message']}")

    def _action_focus(self, args: Dict[str, Any]) -> CapabilityResult:
        ctx = self._prepare_app_context(args)
        if not ctx["is_running"]:
            return CapabilityResult(success=False, capability=self._manifest.id, action="focus", message=f"{ctx['raw_name']} is not currently running.")
            
        action_result = self.controller.focus(ctx["exe"])
        if action_result["success"]:
            ctx["result_data"].update({"window_title": action_result.get("window_title"), "window_found": True})
            event_bus.publish(AppEvent.APPLICATION_FOCUSED, ctx["result_data"])
            return CapabilityResult(success=True, capability=self._manifest.id, action="focus", message=f"Focused {ctx['raw_name']}.", structured_data=ctx["result_data"])
        return CapabilityResult(success=False, capability=self._manifest.id, action="focus", message=f"I couldn't focus {ctx['raw_name']}. {action_result['message']}")

    def _action_minimize(self, args: Dict[str, Any]) -> CapabilityResult:
        ctx = self._prepare_app_context(args)
        if not ctx["is_running"]:
            return CapabilityResult(success=False, capability=self._manifest.id, action="minimize", message=f"{ctx['raw_name']} is not currently running.")
            
        action_result = self.controller.minimize(ctx["exe"])
        if action_result["success"]:
            ctx["result_data"].update({"window_title": action_result.get("window_title"), "window_found": True})
            event_bus.publish(AppEvent.APPLICATION_MINIMIZED, ctx["result_data"])
            return CapabilityResult(success=True, capability=self._manifest.id, action="minimize", message=f"Minimized {ctx['raw_name']}.", structured_data=ctx["result_data"])
        return CapabilityResult(success=False, capability=self._manifest.id, action="minimize", message=f"I couldn't minimize {ctx['raw_name']}. {action_result['message']}")

    def _action_maximize(self, args: Dict[str, Any]) -> CapabilityResult:
        ctx = self._prepare_app_context(args)
        if not ctx["is_running"]:
            return CapabilityResult(success=False, capability=self._manifest.id, action="maximize", message=f"{ctx['raw_name']} is not currently running.")
            
        action_result = self.controller.maximize(ctx["exe"])
        if action_result["success"]:
            ctx["result_data"].update({"window_title": action_result.get("window_title"), "window_found": True})
            event_bus.publish(AppEvent.APPLICATION_MAXIMIZED, ctx["result_data"])
            return CapabilityResult(success=True, capability=self._manifest.id, action="maximize", message=f"Maximized {ctx['raw_name']}.", structured_data=ctx["result_data"])
        return CapabilityResult(success=False, capability=self._manifest.id, action="maximize", message=f"I couldn't maximize {ctx['raw_name']}. {action_result['message']}")

    def _action_restore(self, args: Dict[str, Any]) -> CapabilityResult:
        ctx = self._prepare_app_context(args)
        if not ctx["is_running"]:
            return CapabilityResult(success=False, capability=self._manifest.id, action="restore", message=f"{ctx['raw_name']} is not currently running.")
            
        action_result = self.controller.restore(ctx["exe"])
        if action_result["success"]:
            ctx["result_data"].update({"window_title": action_result.get("window_title"), "window_found": True})
            event_bus.publish(AppEvent.APPLICATION_RESTORED, ctx["result_data"])
            return CapabilityResult(success=True, capability=self._manifest.id, action="restore", message=f"Restored {ctx['raw_name']}.", structured_data=ctx["result_data"])
        return CapabilityResult(success=False, capability=self._manifest.id, action="restore", message=f"I couldn't restore {ctx['raw_name']}. {action_result['message']}")

