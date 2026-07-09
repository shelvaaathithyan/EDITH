import time
from edith.ai.models import ExecutionPlan, ToolResult
from edith.utils.logger import logger
from edith.core.events import event_bus, AppEvent

from edith.capabilities.desktop.desktop_models import DesktopActionArgs
from edith.capabilities.desktop.desktop_exceptions import ApplicationNotFoundError, ApplicationLaunchError, WindowFocusError
from edith.capabilities.desktop.desktop_controller import DesktopController
from edith.capabilities.desktop.desktop_detector import detector
from edith.capabilities.desktop.desktop_utils import resolve_alias

class DesktopCapability:
    """
    Main interface for the Desktop capability.
    Acts as an Executor for desktop-related ExecutionPlans.
    """
    def __init__(self):
        self.controller = DesktopController()
        # Initialize detector cache asynchronously if possible, or trigger it early
        detector.load_index()

    def execute(self, plan: ExecutionPlan) -> ToolResult:
        """Parses the execution plan, runs the desktop action, and returns a ToolResult."""
        if not plan.steps:
            return ToolResult(success=False, message="No steps provided in the execution plan.")
            
        step = plan.steps[0]
        try:
            args = DesktopActionArgs(**step.arguments)
        except Exception as e:
            logger.error(f"Invalid desktop arguments: {e}")
            return ToolResult(success=False, message=f"I couldn't understand the desktop arguments: {e}")
            
        action = args.action.lower()
        raw_app_name = args.application
        
        start_time = time.time()
        
        # Resolve natural language to executable
        event_bus.publish(AppEvent.APPLICATION_LOOKUP_STARTED, raw_app_name)
        exe_name = resolve_alias(raw_app_name)
        
        # Check if running
        is_running = self.controller.check_running(exe_name)
        
        # Default data payload
        result_data = {
            "application": raw_app_name,
            "action": action,
            "executable": exe_name,
            "already_running": is_running,
            "window_found": False
        }
        
        try:
            if action == 'launch':
                if is_running:
                    # Bring to foreground instead of launching another
                    event_bus.publish(AppEvent.APPLICATION_ALREADY_RUNNING, exe_name)
                    logger.info(f"{exe_name} is already running. Attempting to focus.")
                    action_result = self.controller.focus(exe_name)
                    
                    if action_result["success"]:
                        result_data.update({"action_changed_to": "focus", "window_title": action_result.get("window_title"), "window_found": True})
                        event_bus.publish(AppEvent.APPLICATION_FOCUSED, result_data)
                        msg = f"{raw_app_name} is already running. I've brought it to the front."
                    else:
                        msg = f"{raw_app_name} is already running, but I couldn't bring it to the front."
                        
                else:
                    # Need to launch. Find the path
                    app_path = detector.find_executable(exe_name)
                    if not app_path:
                        event_bus.publish(AppEvent.APPLICATION_NOT_FOUND, exe_name)
                        return ToolResult(success=False, message=f"I couldn't find {raw_app_name} installed on your system.")
                    
                    event_bus.publish(AppEvent.APPLICATION_FOUND, app_path)
                    result_data["application_path"] = app_path
                    
                    event_bus.publish(AppEvent.APPLICATION_LAUNCH_STARTED, result_data)
                    self.controller.launch(app_path)
                    
                    event_bus.publish(AppEvent.APPLICATION_LAUNCH_COMPLETED, result_data)
                    msg = f"Opened {raw_app_name}."
                    
            elif action in ['close', 'focus', 'minimize', 'maximize', 'restore']:
                if not is_running:
                    return ToolResult(success=False, message=f"{raw_app_name} is not currently running.")
                
                # Execute specific action
                if action == 'close':
                    action_result = self.controller.close(exe_name)
                    success_event = AppEvent.APPLICATION_CLOSED
                    msg = f"Closed {raw_app_name}."
                elif action == 'focus':
                    action_result = self.controller.focus(exe_name)
                    success_event = AppEvent.APPLICATION_FOCUSED
                    msg = f"Focused {raw_app_name}."
                elif action == 'minimize':
                    action_result = self.controller.minimize(exe_name)
                    success_event = AppEvent.APPLICATION_MINIMIZED
                    msg = f"Minimized {raw_app_name}."
                elif action == 'maximize':
                    action_result = self.controller.maximize(exe_name)
                    success_event = AppEvent.APPLICATION_MAXIMIZED
                    msg = f"Maximized {raw_app_name}."
                else: # restore
                    action_result = self.controller.restore(exe_name)
                    success_event = AppEvent.APPLICATION_RESTORED
                    msg = f"Restored {raw_app_name}."
                    
                if action_result["success"]:
                    result_data.update({"window_title": action_result.get("window_title"), "window_found": True})
                    event_bus.publish(success_event, result_data)
                else:
                    return ToolResult(success=False, message=f"I couldn't {action} {raw_app_name}. {action_result['message']}")
                    
            else:
                return ToolResult(success=False, message=f"Desktop action '{action}' is not supported yet.")

            duration = time.time() - start_time
            result_data["duration"] = duration
            
            return ToolResult(
                success=True,
                message=msg,
                data=result_data
            )
            
        except ApplicationLaunchError as e:
            logger.error(f"Application launch failed: {e}")
            event_bus.publish(AppEvent.APPLICATION_ERROR, str(e))
            return ToolResult(success=False, message=f"I couldn't launch {raw_app_name} due to a system error.")
        except WindowFocusError as e:
            logger.error(f"Window focus failed: {e}")
            event_bus.publish(AppEvent.APPLICATION_ERROR, str(e))
            return ToolResult(success=False, message=f"I couldn't manage the window for {raw_app_name}.")
        except Exception as e:
            logger.error(f"Unexpected error in desktop capability: {e}")
            event_bus.publish(AppEvent.APPLICATION_ERROR, str(e))
            return ToolResult(success=False, message=f"An unexpected error occurred: {e}")

# Singleton instance exported for the resolver
desktop_capability = DesktopCapability()
