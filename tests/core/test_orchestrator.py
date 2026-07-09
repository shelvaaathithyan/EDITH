import pytest
from unittest.mock import MagicMock

from edith.core.state_machine import StateMachine, AppState
from edith.core.telemetry import TelemetryTracker
from edith.core.lifecycle import BootstrapManager
from edith.core.dispatcher import Dispatcher
from edith.core.orchestrator import Orchestrator
from edith.core.models import OrchestrationContext
from edith.core.response import DefaultResponseGenerator
from edith.ai.models import PlannerResponse, ChatResponse, ResponseMetadata

@pytest.fixture
def mock_voice():
    voice = MagicMock()
    return voice

@pytest.fixture
def mock_planner():
    planner = MagicMock()
    metadata = ResponseMetadata(provider="mock", model="mock", latency=0.1, created_at="now")
    planner.plan.return_value = PlannerResponse(data=ChatResponse(response="Hello!"), metadata=metadata)
    return planner

@pytest.fixture
def orchestrator(mock_voice, mock_planner):
    state_machine = StateMachine()
    telemetry = TelemetryTracker()
    bootstrap = BootstrapManager(state_machine)
    dispatcher = MagicMock()
    response_gen = DefaultResponseGenerator()
    
    return Orchestrator(
        voice_manager=mock_voice,
        planner=mock_planner,
        dispatcher=dispatcher,
        response_generator=response_gen,
        bootstrap_manager=bootstrap,
        state_machine=state_machine,
        telemetry=telemetry
    )

def test_orchestrator_initial_state(orchestrator):
    assert orchestrator.state_machine.get_state() == AppState.STARTING

def test_orchestrator_startup_shutdown(orchestrator):
    orchestrator.start()
    # Assuming no subsystems registered, it should immediately go to READY
    assert orchestrator.state_machine.get_state() == AppState.READY
    orchestrator.stop()
    assert orchestrator.state_machine.get_state() == AppState.SHUTTING_DOWN
    
def test_orchestrator_process_input(orchestrator, mock_voice):
    orchestrator.start()
    assert orchestrator.state_machine.get_state() == AppState.READY
    
    # Process a simple input
    orchestrator.process_input("Say hello")
    
    # Wait for queue to process
    orchestrator._input_queue.join()
    
    # Verify planner was called
    orchestrator.planner.plan.assert_called_with("Say hello")
    
    # Verify voice was spoken to via ResponseGenerator
    mock_voice.speak.assert_called_with("Hello!")
    
    # Stop
    orchestrator.stop()
