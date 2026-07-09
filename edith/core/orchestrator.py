import queue
import threading
from typing import Optional
from edith.utils.logger import logger
from edith.core.interfaces.voice import IVoiceManager
from edith.core.interfaces.planner import IPlanner
from edith.core.interfaces.response import IResponseGenerator
from edith.core.state_machine import StateMachine, AppState
from edith.core.events import event_bus, AppEvent
from edith.core.telemetry import TelemetryTracker
from edith.core.dispatcher import Dispatcher
from edith.core.models import OrchestrationContext
from edith.core.lifecycle import BootstrapManager
from edith.core.interfaces.context import IContextManager
from edith.memory.memory_manager import MemoryManager

class Orchestrator:
    def __init__(
        self,
        voice_manager: IVoiceManager,
        planner: IPlanner,
        dispatcher: Dispatcher,
        response_generator: IResponseGenerator,
        bootstrap_manager: BootstrapManager,
        state_machine: StateMachine,
        telemetry: TelemetryTracker,
        memory_manager: MemoryManager,
        context_manager: IContextManager
    ):
        self.voice = voice_manager
        self.planner = planner
        self.dispatcher = dispatcher
        self.response_gen = response_generator
        self.bootstrap = bootstrap_manager
        self.state_machine = state_machine
        self.telemetry = telemetry
        self.memory = memory_manager
        self.context = context_manager
        
        self._input_queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        """Starts the orchestrator worker thread."""
        logger.info("Starting Core Orchestrator...")
        self.bootstrap.startup()
        
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._process_loop, daemon=True, name="OrchestratorWorker")
        self._worker_thread.start()
        event_bus.publish(AppEvent.APPLICATION_STARTED)

    def stop(self):
        """Stops the worker thread."""
        logger.info("Stopping Core Orchestrator...")
        self._stop_event.set()
        # Wake up queue
        self._input_queue.put(None)
        if self._worker_thread:
            self._worker_thread.join()
            
        self.bootstrap.shutdown()
        event_bus.publish(AppEvent.APPLICATION_STOPPED)

    def process_input(self, text: str):
        """
        Receives input from any source (Voice, CLI, GUI) and queues it for processing.
        Returns immediately, freeing the caller thread.
        """
        if not text or not text.strip():
            return
            
        if self.state_machine.get_state() != AppState.READY and self.state_machine.get_state() != AppState.IDLE:
            logger.warning(f"Ignored input '{text}' while in state {self.state_machine.get_state().name}")
            return
            
        self._input_queue.put(text)

    def _process_loop(self):
        while not self._stop_event.is_set():
            text = self._input_queue.get()
            if text is None or self._stop_event.is_set():
                break
                
            try:
                self.telemetry.start("total_request_duration")
                self._handle_request(text)
            except Exception as e:
                logger.error(f"Orchestrator unhandled exception: {e}")
                self.state_machine.transition(AppState.ERROR)
                self.voice.speak(f"A critical system error occurred: {str(e)}")
            finally:
                self.telemetry.end("total_request_duration")
                self._input_queue.task_done()
                
                # Reset to READY
                if not self._stop_event.is_set() and self.state_machine.get_state() != AppState.READY:
                    try:
                        self.state_machine.transition(AppState.READY)
                    except Exception:
                        pass

    def _handle_request(self, text: str):
        logger.info(f"Orchestrator processing request: '{text}'")
        self.state_machine.transition(AppState.UNDERSTANDING)
        
        context = OrchestrationContext(user_input=text)
        
        # 0. Check for hybrid confirmations
        from edith.permission.confirmation_detector import confirmation_detector
        from edith.permission.permission_manager import permission_manager
        
        if permission_manager.store.get_active_action():
            confirmed = confirmation_detector.detect(text)
            if confirmed is not None:
                # It is a simple yes/no response
                resolved_plan = permission_manager.resolve_confirmation(confirmed)
                if resolved_plan:
                    # User said yes: inject resolved plan and jump to dispatch
                    from edith.ai.models import PlannerResponse, ExecutionPlan, ResponseMetadata
                    # Wrap the resolved plan
                    context.planner_response = PlannerResponse(
                        data=ExecutionPlan(goal="resume pending action", steps=[]), 
                        metadata=ResponseMetadata(provider="system", model="permission_manager", latency=0.0, created_at="N/A")
                    )
                    context.resolved_plan = resolved_plan
                    context.skip_permission_check = True
                    # Skip planning
                    self.telemetry.start("pipeline_duration")
                    self.state_machine.transition(AppState.EXECUTING)
                    self.dispatcher.dispatch(context)
                    self.telemetry.end("pipeline_duration")
                else:
                    # User said no: cancel
                    context.final_response = "Action cancelled."
                    
                # Skip to response voice output
                self._finish_request(context)
                return

        # 1. Planning with Memory Retrieval
        self.telemetry.start("planner_duration")
        self.state_machine.transition(AppState.PLANNING)
        event_bus.publish(AppEvent.PLANNER_STARTED, text)
        
        # Retrieval Pipeline: Interaction Context -> Long-Term Memory
        interaction_context_data = self.context.get_context()
        memories = self.memory.recall(text, limit=5)
        
        prompt_with_context = text
        if interaction_context_data or memories:
            context_str = "CURRENT CONTEXT:\n"
            for k, v in interaction_context_data.items():
                context_str += f"- {k}: {v}\n"
                
            if memories:
                context_str += "\nLONG-TERM MEMORY:\n"
                for m in memories:
                    context_str += f"- {m.title}: {m.value} (Confidence: {m.confidence:.2f})\n"
                    
            prompt_with_context = f"{context_str}\nUSER REQUEST:\n{text}"
        
        planner_response = self.planner.plan(prompt_with_context)
        context.planner_response = planner_response
        
        event_bus.publish(AppEvent.PLANNER_COMPLETED, planner_response)
        self.telemetry.end("planner_duration")
        
        # 2. Dispatch
        if not context.halt_pipeline:
            self.telemetry.start("pipeline_duration")
            self.state_machine.transition(AppState.EXECUTING)
            self.dispatcher.dispatch(context)
            self.telemetry.end("pipeline_duration")
            
        self._finish_request(context)

    def _finish_request(self, context: OrchestrationContext):
        # 3. Response Generation
        self.state_machine.transition(AppState.RESPONDING)
        # Only generate a response if one wasn't explicitly set (like in cancellation)
        if not context.final_response:
            final_text = self.response_gen.generate(context)
            context.final_response = final_text
        else:
            final_text = context.final_response
        
        # 4. Voice Output
        if final_text:
            self.telemetry.start("voice_duration")
            self.voice.speak(final_text)
            self.telemetry.end("voice_duration")
            
        logger.info(f"Request complete. Telemetry: {self.telemetry.get_metrics()}")
        
        event_bus.publish(AppEvent.REQUEST_COMPLETED, {
            "context": context,
            "telemetry": self.telemetry.get_metrics()
        })
        
        self.telemetry.clear()
