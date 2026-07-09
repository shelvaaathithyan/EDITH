import pytest
from edith.ai.parser import ResponseParser
from edith.ai.models import ExecutionPlan, ChatResponse, ErrorResponse, ResponseMetadata

@pytest.fixture
def parser():
    return ResponseParser()

@pytest.fixture
def metadata():
    return ResponseMetadata(
        provider="TestProvider",
        model="test-model",
        latency=0.1,
        created_at="2026-07-09T00:00:00Z"
    )

def test_parse_execution_plan(parser, metadata):
    validated_dict = {
        "type": "execution",
        "goal": "Test goal",
        "steps": [
            {"tool": "test_tool", "arguments": {}}
        ],
        "requires_confirmation": False,
        "confidence": 0.99
    }
    response = parser.parse(validated_dict, metadata)
    assert isinstance(response.data, ExecutionPlan)
    assert response.data.goal == "Test goal"
    assert response.metadata.provider == "TestProvider"

def test_parse_chat_response(parser, metadata):
    validated_dict = {
        "type": "chat",
        "response": "Hello"
    }
    response = parser.parse(validated_dict, metadata)
    assert isinstance(response.data, ChatResponse)
    assert response.data.response == "Hello"

def test_parse_error_response(parser, metadata):
    validated_dict = {
        "type": "error",
        "message": "Something went wrong"
    }
    response = parser.parse(validated_dict, metadata)
    assert isinstance(response.data, ErrorResponse)
    assert response.data.message == "Something went wrong"
