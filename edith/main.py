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

# Classes (NOT singletons)
from edith.voice.audio import AudioPlayer
from edith.voice.microphone import MicrophoneManager
from edith.voice.sounds import SoundManager
from edith.voice.scheduler import SpeechScheduler
from edith.voice.stt import STTProvider
from edith.voice.ptt import PTTController
from edith.voice.manager import VoiceManager
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
    All runtime objects are created HERE — no import-time singletons.
    
    MANDATORY BOOTSTRAP ORDER:
    1. Configuration    (already loaded via settings import)
    2. Logger           (already loaded via logger import)
    3. EventBus         (already loaded — stateless, OK)
    4. Memory           (memory_manager — imported above)
    5. Telemetry
    6. Ollama Provider  (via Planner.initialize())
    7. Planner
    8. Capability Registry
    9. Dispatcher
    10. Orchestrator
    11. VoiceManager
    12. Wake Engine
    13. UIManager
    """

    logger.info("=" * 60)
    logger.info("EDITH v2.0 — Building Application")
    logger.info("=" * 60)

    # ── 1-3. Configuration, Logger, EventBus ──────────────────
    # Already loaded at import time (stateless / config-only — acceptable)

    # ── 4. Memory ─────────────────────────────────────────────
    # memory_manager is imported from edith.memory (module-level OK for data layer)
    logger.info("[Bootstrap] 4/13 Memory Manager ready")

    # ── 5. Telemetry ──────────────────────────────────────────
    telemetry = TelemetryTracker()
    logger.info("[Bootstrap] 5/13 Telemetry ready")

    # ── State Machine ─────────────────────────────────────────
    state_machine = StateMachine()

    # ── 6-7. Planner (creates + initializes Ollama Provider) ──
    planner = Planner()
    logger.info("[Bootstrap] 6-7/13 Planner created (will initialize during bootstrap)")

    # ── 8. Capability Registry ────────────────────────────────
    loader = CapabilityLoader(capability_registry)
    logger.info("[Bootstrap] 8/13 Capability Loader created")

    # ── 9. Dispatcher ─────────────────────────────────────────
    permission = PermissionManager()
    resolver = CapabilityResolver(default_executor=None)
    dispatcher = Dispatcher(resolver, permission, memory_manager, context_manager)
    logger.info("[Bootstrap] 9/13 Dispatcher wired")

    # ── 10. Orchestrator ──────────────────────────────────────
    response_gen = DefaultResponseGenerator()

    # ── 11. Voice Subsystem ───────────────────────────────────
    # Build the voice dependency graph bottom-up
    audio_player = AudioPlayer()
    microphone_mgr = MicrophoneManager()
    sound_mgr = SoundManager(audio_player)
    stt_provider = STTProvider(microphone_manager=microphone_mgr)
    scheduler = SpeechScheduler(sound_manager=sound_mgr)
    ptt = PTTController()
    voice_mgr = VoiceManager(
        stt_provider=stt_provider,
        scheduler=scheduler,
        sound_manager=sound_mgr,
        ptt_controller=ptt,
        audio_player=audio_player
    )
    logger.info("[Bootstrap] 11/13 Voice Manager assembled")

    # ── 12. Wake Engine ───────────────────────────────────────
    wake_engine = WakeEngine()
    logger.info("[Bootstrap] 12/13 Wake Engine created")

    # ── 13. UI Manager ────────────────────────────────────────
    ui_manager = UIManager()
    logger.info("[Bootstrap] 13/13 UI Manager created")

    # ── Wire Orchestrator ─────────────────────────────────────
    bootstrap = BootstrapManager(state_machine)
    orchestrator = Orchestrator(
        voice_manager=voice_mgr,
        planner=planner,
        dispatcher=dispatcher,
        response_generator=response_gen,
        bootstrap_manager=bootstrap,
        state_machine=state_machine,
        telemetry=telemetry,
        memory_manager=memory_manager,
        context_manager=context_manager
    )

    # ── Voice Session Controller ──────────────────────────────
    session_controller = VoiceSessionController(voice_mgr, orchestrator)

    # ── Register subsystems for lifecycle management ──────────
    # ORDER MATTERS: subsystems initialize in registration order.
    # Planner MUST initialize before voice/wake so the provider
    # is resolved before any voice input can reach the planner.
    bootstrap.register_subsystem(planner)           # 6-7: Provider + Planner init
    bootstrap.register_subsystem(loader)            # 8: Capabilities
    bootstrap.register_subsystem(voice_mgr)         # 11: TTS + PTT
    bootstrap.register_subsystem(wake_engine)       # 12: Wake word
    bootstrap.register_subsystem(session_controller)# Voice session
    bootstrap.register_subsystem(ui_manager)        # 13: UI event subscriptions

    logger.info("=" * 60)
    logger.info("EDITH v2.0 — Application Assembly Complete")
    logger.info("=" * 60)

    return orchestrator, ui_manager


def main():
    logger.info("Starting EDITH v2.0...")
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
