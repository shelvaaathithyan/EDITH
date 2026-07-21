import os
import threading
import webview
from edith.utils.logger import logger
from edith.core.events import event_bus, AppEvent
from edith.core.state_machine import AppState
import psutil
import json

class UIBridge:
    """
    Exposes Python methods to JavaScript for the Developer Control Center.
    """
    def __init__(self):
        self._window = None

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

    def get_runtime_diagnostics(self):
        """Returns a comprehensive diagnostic dictionary for Phase 11."""
        # 1. Provider details
        # The OllamaProvider instance is inside Planner
        import inspect
        from edith.ai.planner import Planner
        from edith.voice.manager import VoiceManager
        from edith.wake.engine import WakeEngine
        from edith.voice.stt import STTProvider
        from edith.core.dispatcher import Dispatcher
        from edith.sdk.capability import capability_registry
        from edith.core.health_dashboard import health_dashboard
        from edith.core.state_machine import AppState
        from edith.main import build_app
        
        # We need to find the live instances.
        # However, they are all passed to Orchestrator in main.py.
        # But `health_dashboard` already polls everything.
        # For provider specific details, let's grab the provider from the health dashboard if possible,
        # or we just get the health report and augment it.
        report = health_dashboard.get_report_dict()
        
        diagnostics = {
            "lifecycle": {
                "planner_initialized": False,
                "provider_initialized": False
            },
            "ollama": {
                "configured_model": None,
                "resolved_model": None,
                "installed_models": [],
                "inference_test": False
            },
            "subsystems": report["subsystems"],
            "capabilities": report["capabilities"]
        }
        
        # We need to find the Planner instance and OllamaProvider
        import gc
        for obj in gc.get_objects():
            if isinstance(obj, Planner):
                diagnostics["lifecycle"]["planner_initialized"] = obj._initialized
                if hasattr(obj, "provider"):
                    p = obj.provider
                    diagnostics["lifecycle"]["provider_initialized"] = getattr(p, "_initialized", False)
                    diagnostics["ollama"]["configured_model"] = getattr(p, "configured_model", None)
                    diagnostics["ollama"]["resolved_model"] = getattr(p, "resolved_model", None)
                    diagnostics["ollama"]["installed_models"] = getattr(p, "installed_models", [])
                break

        # Check inference test from the health dashboard's provider check if available
        for sub in report["subsystems"]:
            if sub["name"] == "OllamaProvider":
                diagnostics["ollama"]["inference_test"] = sub.get("status") == "healthy"
                
        return diagnostics

    def get_interaction_context(self):
        """Returns the current Interaction Context state."""
        from edith.interaction.context.context_manager import context_manager
        return context_manager.get_context()

    def get_telemetry(self):
        """Returns latest latency metrics from the last request."""
        # Telemetry is request-scoped; we expose the last snapshot via event data
        return getattr(self, '_last_telemetry', {})

    def get_system_metrics(self):
        process = psutil.Process()
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_mb": process.memory_info().rss / (1024 * 1024),
            "thread_count": process.num_threads()
        }

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
        # Ensure it is a valid file URI for PyWebView reliability
        self.index_html = "file:///" + os.path.join(self.web_dir, "index.html").replace('\\', '/')

    def initialize(self):
        """Lifecycle init"""
        # Subscribe to ALL events to forward to JS
        for event_type in AppEvent:
            def make_handler(et=event_type):
                return lambda data=None: self._on_any_event(et, data)
            event_bus.subscribe(event_type, make_handler())

        from edith.voice.models import VoiceEvent
        for event_type in VoiceEvent:
            def make_handler(et=event_type):
                return lambda data=None: self._on_any_event(et, data)
            event_bus.subscribe(event_type, make_handler())
        
    def start(self):
        """
        Starts the pywebview loop.
        WARNING: This MUST be called on the main thread.
        It blocks until the window is destroyed.
        """
        if self._is_running:
            return
            
        logger.info(f"Creating UI window on thread: {threading.current_thread().name}...")
        from edith.config.settings import settings
        logger.info(f"Resolved HTML path: {self.index_html}")
        self.window = webview.create_window(
            'EDITH Developer Control Center v2.0', 
            url=self.index_html,
            js_api=self.bridge,
            width=1600,
            height=950,
            min_size=(1200, 750),
            frameless=False,  # User wants a desktop IDE feel, standard window frame is fine unless specified
            easy_drag=True,
            on_top=settings.ui_on_top,
            hidden=settings.ui_start_hidden,
            background_color='#09090b'
        )
        self.bridge._window = self.window
        logger.info("UI window created.")
        
        # Handle close event to hide instead of destroy, or just let it close
        # Closing the window will just hide it if we can intercept, 
        # but pywebview closed event cannot cancel destruction easily.
        # We will just let it close, but the background daemon threads will keep running.
        # Wait, if pywebview.start() returns, the main thread might exit if no other non-daemon threads exist.
        self.window.events.closed += self._on_closed
        
        self._is_running = True
        
        # Start blocking loop
        logger.info("Calling webview.start()...")
        webview.start(debug=False)
        logger.info("webview.start() returned. EDITH UI successfully initialized.")

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

    def _on_any_event(self, event_type: AppEvent, data: any):
        """Generic event forwarder to JS."""
        if not self.window or not self._is_running:
            return
            
        # Handle specific native wake behavior
        if event_type == AppEvent.WAKE_WORD_DETECTED:
            try:
                self.window.restore()
                self.window.show()
            except Exception:
                pass
                
        # Serialize data
        payload = {}
        try:
            if data is not None:
                if hasattr(data, "model_dump"):
                    payload = data.model_dump(mode='json')
                elif hasattr(data, "to_dict"):
                    payload = data.to_dict()
                elif isinstance(data, dict):
                    # stringify non-serializable items
                    payload = {k: str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v for k, v in data.items()}
                else:
                    payload = {"value": str(data)}
        except Exception:
            payload = {"error": "unserializable"}

        # Add timestamp and format
        import time
        event_obj = {
            "time": time.strftime("%H:%M:%S"),
            "event": event_type.name,
            "data": payload
        }
        
        try:
            escaped_json = json.dumps(event_obj).replace("'", "\\'")
            self.window.evaluate_js(f"if (window.onAppEvent) window.onAppEvent('{escaped_json}');")
        except Exception as e:
            logger.debug(f"Failed to push event to UI: {e}")
