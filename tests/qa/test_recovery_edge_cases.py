import pytest
from unittest.mock import MagicMock
from edith.main import build_app
from edith.core.state_machine import AppState
from edith.core.events import event_bus, AppEvent

def test_planner_exception_recovery():
    orchestrator, _ = build_app()
    
    # Mock WakeEngine to prevent bootstrap failure in test env
    from edith.ai.models import HealthStatus
    for sub in orchestrator.bootstrap.subsystems:
        if sub.__class__.__name__ == "WakeEngine":
            sub.health_check = MagicMock(return_value=HealthStatus(status="healthy", provider="openwakeword", model="hey_jarvis"))
            sub.start = MagicMock()
            
    # Inject catastrophic exception
    orchestrator.planner.plan = MagicMock(side_effect=MemoryError("Simulated OOM inside Planner"))
    orchestrator.voice = MagicMock()
    
    # Hook into event bus to verify ERROR_OCCURRED is fired
    error_event_fired = []
    def on_error(data):
        error_event_fired.append(data)
    
    event_bus.subscribe(AppEvent.ERROR_OCCURRED, on_error)
    
    # Process request (will raise MemoryError inside _handle_request, caught by _process_loop)
    orchestrator.start()
    orchestrator.process_input("test")
    
    # Wait for queue to clear
    orchestrator._input_queue.join()
    
    # Check state before stop() because stop() goes to SHUTTING_DOWN
    state_after_error = orchestrator.state_machine.get_state()
    orchestrator.stop()
    
    # Validate
    assert len(error_event_fired) == 1
    assert "Simulated OOM" in error_event_fired[0]["error"]
    
    # The orchestrator MUST have recovered to READY, not stuck in PLANNING or ERROR
    assert state_after_error == AppState.READY
    
    event_bus.unsubscribe(AppEvent.ERROR_OCCURRED, on_error)

def test_capability_exception_recovery():
    orchestrator, _ = build_app()
    
    # Mock WakeEngine to prevent bootstrap failure in test env
    from edith.ai.models import HealthStatus
    for sub in orchestrator.bootstrap.subsystems:
        if sub.__class__.__name__ == "WakeEngine":
            sub.health_check = MagicMock(return_value=HealthStatus(status="healthy", provider="openwakeword", model="hey_jarvis"))
            sub.start = MagicMock()
            
    # We want the planner to succeed, but the Dispatcher to blow up
    from edith.ai.models import PlannerResponse, ExecutionPlan, ExecutionStep, ResponseMetadata
    orchestrator.planner.plan = MagicMock(return_value=PlannerResponse(
        data=ExecutionPlan(goal="crash", steps=[ExecutionStep(tool="dummy", arguments={})]),
        metadata=ResponseMetadata(provider="mock", model="mock", latency=0.0, created_at="now")
    ))
    
    orchestrator.dispatcher.dispatch = MagicMock(side_effect=RecursionError("Stack overflow in dispatcher"))
    orchestrator.voice = MagicMock()
    
    orchestrator.start()
    orchestrator.process_input("do a capability")
    orchestrator._input_queue.join()
    
    state_after_error = orchestrator.state_machine.get_state()
    orchestrator.stop()
    
    assert state_after_error == AppState.READY
