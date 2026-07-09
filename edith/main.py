import time
import threading
from edith.utils.logger import logger

# Import all core components
from edith.core.state_machine import StateMachine
from edith.core.telemetry import TelemetryTracker
from edith.core.lifecycle import BootstrapManager
from edith.core.events import event_bus, AppEvent
from edith.core.dispatcher import Dispatcher
from edith.core.orchestrator import Orchestrator
from edith.core.resolver import CapabilityResolver
from edith.core.response import DefaultResponseGenerator

# Import concrete subsystems
from edith.voice.manager import voice_manager
from edith.ai.planner import Planner
from edith.ai.providers.factory import ProviderFactory
from edith.wake.engine import WakeEngine
from edith.ui.window import UIManager
from edith.core.session import VoiceSessionController

# Mock components for Phase 2
class MockCapabilityResolver(CapabilityResolver):
    def resolve_and_execute(self, plan):
        logger.info(f"Dummy execution of plan: {plan.goal}")
        return "I understood your request."

class MockPermission:
    def request_permission(self, plan):
        return True

class MockMemory:
    def store(self, role, content): pass
    def get_history(self): return ""

class MockContext:
    def update_context(self, data): pass
    def get_context(self): return {}

def build_app():
    # 1. Base Core
    state_machine = StateMachine()
    telemetry = TelemetryTracker()
    bootstrap = BootstrapManager(state_machine)
    
    # 2. Subsystems
    wake_engine = WakeEngine()
    ui_manager = UIManager()
    
    # 3. AI & Tools
    planner = Planner(ProviderFactory.get_provider("ollama"))
    permission = MockPermission()
    memory = MockMemory()
    context = MockContext()
    
    # 4. Pipeline & Dispatcher (with Dummy Execution)
    resolver = MockCapabilityResolver(default_executor=None)
    dispatcher = Dispatcher(resolver, permission, memory, context)
    response_gen = DefaultResponseGenerator()
    
    # 5. Core Orchestrator
    orchestrator = Orchestrator(
        voice_manager=voice_manager,
        planner=planner,
        dispatcher=dispatcher,
        response_generator=response_gen,
        bootstrap_manager=bootstrap,
        state_machine=state_machine,
        telemetry=telemetry
    )
    
    # 6. Session Controller
    session_controller = VoiceSessionController(voice_manager, orchestrator)
    
    # Register subsystems for lifecycle
    bootstrap.register_subsystem(voice_manager)
    bootstrap.register_subsystem(wake_engine)
    bootstrap.register_subsystem(ui_manager)
    bootstrap.register_subsystem(session_controller)
    
    return orchestrator, ui_manager

def main():
    logger.info("Starting EDITH Application (Phase 2)...")
    orchestrator, ui_manager = build_app()
    
    try:
        orchestrator.start() # Starts worker thread and bootstraps subsystems
        
        # This MUST run on the main thread for pywebview
        logger.info("Handing off main thread to UI loop.")
        ui_manager.start()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        logger.info("Shutting down...")
        orchestrator.stop()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    main()
