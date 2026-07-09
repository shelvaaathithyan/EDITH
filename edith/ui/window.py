import os
import threading
import webview
from edith.utils.logger import logger
from edith.core.events import event_bus, AppEvent
from edith.core.state_machine import AppState

class UIBridge:
    """
    Exposes Python methods to JavaScript for the Developer Control Center.
    """
    def __init__(self):
        self.window = None

    def log_from_js(self, message):
        logger.debug(f"[UI] {message}")
        
    def get_memories(self, category=None):
        from edith.memory import memory_manager
        from edith.memory.memory_constants import MemoryCategory
        cat_enum = MemoryCategory(category) if category else None
        
        memories = memory_manager.repo.list_by_category(cat_enum)
        return [mem.model_dump(mode='json') for mem in memories]
        
    def forget_memory(self, memory_id):
        from edith.memory import memory_manager
        try:
            memory_manager.forget(memory_id)
            return True
        except Exception as e:
            logger.error(f"UI failed to forget memory: {e}")
            return False

    def get_health_report(self):
        """Returns the full system health dashboard."""
        from edith.core.health_dashboard import health_dashboard
        return health_dashboard.get_report_dict()

    def get_interaction_context(self):
        """Returns the current Interaction Context state."""
        from edith.interaction.context.context_manager import context_manager
        return context_manager.get_context()

    def get_telemetry(self):
        """Returns latest latency metrics from the last request."""
        # Telemetry is request-scoped; we expose the last snapshot via event data
        return getattr(self, '_last_telemetry', {})

    def get_event_log(self):
        """Returns recent events from the Event Bus."""
        return getattr(self, '_event_log', [])

class UIManager:
    def __init__(self):
        self.bridge = UIBridge()
        self.window = None
        self._is_running = False
        
        # Determine paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.web_dir = os.path.join(base_dir, "web")
        self.index_html = os.path.join(self.web_dir, "index.html")

    def initialize(self):
        """Lifecycle init"""
        # Subscribe to events
        event_bus.subscribe(AppEvent.WAKE_WORD_DETECTED, self._on_wake)
        event_bus.subscribe(AppEvent.STATE_CHANGED, self._on_state_change)
        event_bus.subscribe(AppEvent.REQUEST_COMPLETED, self._on_request_completed)
        
    def start(self):
        """
        Starts the pywebview loop.
        WARNING: This MUST be called on the main thread.
        It blocks until the window is destroyed.
        """
        if self._is_running:
            return
            
        logger.info("Starting EDITH UI...")
        from edith.config.settings import settings
        self.window = webview.create_window(
            'EDITH', 
            url=self.index_html,
            js_api=self.bridge,
            width=settings.ui_width,
            height=settings.ui_height,
            frameless=settings.ui_frameless,
            easy_drag=True,
            on_top=settings.ui_on_top,
            hidden=True,
            background_color='#000000'
        )
        self.bridge.window = self.window
        
        # Handle close event to hide instead of destroy, or just let it close
        # Closing the window will just hide it if we can intercept, 
        # but pywebview closed event cannot cancel destruction easily.
        # We will just let it close, but the background daemon threads will keep running.
        # Wait, if pywebview.start() returns, the main thread might exit if no other non-daemon threads exist.
        self.window.events.closed += self._on_closed
        
        self._is_running = True
        
        # Start blocking loop
        # Note: In production, we might want to start this right away but keep it hidden
        webview.start(debug=False)

    def stop(self):
        if self.window and self._is_running:
            try:
                self.window.destroy()
            except Exception:
                pass
        self._is_running = False

    def shutdown(self):
        self.stop()

    def _on_closed(self):
        logger.info("UI Window closed by user.")
        self._is_running = False
        self.window = None

    def _on_wake(self, _data=None):
        """Called when wake word is detected."""
        if self.window and self._is_running:
            logger.info("Waking UI...")
            # Restore and show window
            self.window.restore()
            self.window.show()

    def _on_state_change(self, state: AppState):
        """Push state transitions to the web frontend."""
        if self.window and self._is_running:
            try:
                # Call JS function updateState(newState)
                self.window.evaluate_js(f"if (window.updateState) window.updateState('{state.name}');")
            except Exception as e:
                logger.debug(f"Failed to push state to UI: {e}")

    def _on_request_completed(self, data: dict):
        """Pushes debug information to the frontend."""
        if not self.window or not self._is_running:
            return
            
        import json
        context = data.get("context")
        telemetry = data.get("telemetry", {})
        
        if not context:
            return
            
        planner_resp = context.planner_response
        
        payload = {
            "transcription": context.user_input,
            "goal": planner_resp.goal if planner_resp else "N/A",
            "type": planner_resp.type if planner_resp else "N/A",
            "confidence": f"{planner_resp.confidence:.2f}" if planner_resp else "N/A",
            "latency": round(telemetry.get("planner_duration", 0), 2),
            "pipeline_duration": round(telemetry.get("total_request_duration", 0), 2),
            "response": context.final_response or "N/A",
            "json_dump": planner_resp.model_dump_json(indent=2) if planner_resp else "{}"
        }
        
        try:
            escaped_json = json.dumps(payload).replace("'", "\\'")
            self.window.evaluate_js(f"if (window.updateDebug) window.updateDebug('{escaped_json}');")
        except Exception as e:
            logger.error(f"Failed to push debug payload to UI: {e}")
