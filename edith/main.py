import time
import threading
from edith.utils.logger import logger

# Core
from edith.core.state_machine import StateMachine
from edith.core.telemetry import TelemetryTracker
from edith.core.lifecycle import BootstrapManager
from edith.core.events import event_bus, AppEvent
from edith.core.dispatcher import Dispatcher
from edith.core.orchestrator import Orchestrator
from edith.core.resolver import CapabilityResolver
from edith.core.response import DefaultResponseGenerator
from edith.core.session import VoiceSessionController

# Subsystems
from edith.voice.manager import voice_manager
from edith.ai.planner import Planner
from edith.wake.engine import WakeEngine
from edith.ui.window import UIManager

# SDK
from edith.sdk.capability import CapabilityLoader, capability_registry

# Ecosystem
from edith.permission.permission_manager import PermissionManager
from edith.interaction.context.context_manager import context_manager
from edith.memory import memory_manager


def build_app():
    """
    Assembles every subsystem into a fully wired EDITH application.
    No mocks. No shortcuts. Production-ready.
    """
    # 1. Core Infrastructure
    state_machine = StateMachine()
    telemetry = TelemetryTracker()
    bootstrap = BootstrapManager(state_machine)

    # 2. Hardware Subsystems
    wake_engine = WakeEngine()
    ui_manager = UIManager()

    # 3. AI Layer
    planner = Planner()

    # 4. Permission Layer
    permission = PermissionManager()

    # 5. Capability Pipeline
    resolver = CapabilityResolver(default_executor=None)
    dispatcher = Dispatcher(resolver, permission, memory_manager, context_manager)
    response_gen = DefaultResponseGenerator()

    # 6. Core Orchestrator (fully wired)
    orchestrator = Orchestrator(
        voice_manager=voice_manager,
        planner=planner,
        dispatcher=dispatcher,
        response_generator=response_gen,
        bootstrap_manager=bootstrap,
        state_machine=state_machine,
        telemetry=telemetry,
        memory_manager=memory_manager,
        context_manager=context_manager
    )

    # 7. Voice Session Controller
    session_controller = VoiceSessionController(voice_manager, orchestrator)

    # 8. Capability Loader
    loader = CapabilityLoader(capability_registry)

    # 9. Register subsystems for lifecycle management
    bootstrap.register_subsystem(voice_manager)
    bootstrap.register_subsystem(wake_engine)
    bootstrap.register_subsystem(ui_manager)
    bootstrap.register_subsystem(session_controller)
    bootstrap.register_subsystem(loader)

    return orchestrator, ui_manager


def main():
    logger.info("Starting EDITH v1.0...")
    orchestrator, ui_manager = build_app()

    try:
        orchestrator.start()

        # pywebview MUST run on the main thread
        logger.info("Handing off main thread to UI loop.")
        ui_manager.start()

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        logger.info("Shutting down EDITH...")
        orchestrator.stop()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
