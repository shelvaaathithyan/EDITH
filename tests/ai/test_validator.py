import json
import pytest
from edith.ai.validator import ResponseValidator
from edith.ai.exceptions import JSONValidationError

@pytest.fixture
def validator():
    return ResponseValidator()

def test_validate_execution_plan_success(validator):
    raw_json = json.dumps({
        "type": "execution",
        "goal": "Open Chrome",
        "steps": [
            {
                "tool": "launch_app",
                "arguments": {"app_name": "chrome"}
            }
        ],
        "requires_confirmation": False,
        "confidence": 0.95
    })
    result = validator.validate_raw(raw_json)
    assert result["type"] == "execution"
    assert len(result["steps"]) == 1

def test_validate_execution_plan_missing_fields(validator):
    # Missing 'confidence' and 'requires_confirmation'
    raw_json = json.dumps({
        "type": "execution",
        "goal": "Open Chrome",
        "steps": []
    })
    with pytest.raises(JSONValidationError):
        validator.validate_raw(raw_json)

def test_validate_chat_success(validator):
    raw_json = json.dumps({
        "type": "chat",
        "response": "Hello there!"
    })
    result = validator.validate_raw(raw_json)
    assert result["type"] == "chat"
    assert result["response"] == "Hello there!"

def test_validate_unknown_type(validator):
    raw_json = json.dumps({
        "type": "unknown_type"
    })
    with pytest.raises(JSONValidationError):
        validator.validate_raw(raw_json)

def test_validate_malformed_json(validator):
    raw_json = "This is not JSON at all."
    with pytest.raises(JSONValidationError):
        validator.validate_raw(raw_json)
