import json
import pytest
from edith.ai.planner import Planner
from edith.ai.models import ChatResponse, ExecutionPlan, ErrorResponse
from edith.ai.providers.base_provider import LLMProvider

class MockProvider(LLMProvider):
    def __init__(self, raw_response=""):
        self.model = "mock-model"
        self.raw_response = raw_response
        self.call_count = 0

    def initialize(self):
        pass

    def plan(self, user_prompt: str, system_prompt: str) -> str:
        self.call_count += 1
        return self.raw_response

    def chat(self, messages):
        return ""

    def health_check(self):
        return None

    def shutdown(self):
        pass

def test_planner_success_chat(monkeypatch):
    mock_json = json.dumps({"type": "chat", "response": "Hi!"})
    
    # Mock ProviderFactory to return our MockProvider
    from edith.ai.providers.factory import ProviderFactory
    monkeypatch.setattr(ProviderFactory, "get_provider", lambda: MockProvider(mock_json))
    
    planner = Planner()
    result = planner.plan("Say hi")
    
    assert isinstance(result.data, ChatResponse)
    assert result.data.response == "Hi!"
    assert result.metadata.provider == "MockProvider"

def test_planner_retry_on_invalid_json(monkeypatch):
    # We will simulate a failure on the first call, and success on the second call.
    # To do this cleanly, we make the mock provider return different strings.
    class RetryMockProvider(MockProvider):
        def plan(self, user_prompt: str, system_prompt: str) -> str:
            self.call_count += 1
            if self.call_count == 1:
                return "Not JSON at all"
            else:
                return json.dumps({"type": "chat", "response": "Recovered!"})

    from edith.ai.providers.factory import ProviderFactory
    monkeypatch.setattr(ProviderFactory, "get_provider", lambda: RetryMockProvider())
    
    planner = Planner()
    result = planner.plan("Say hi")
    
    # Should have recovered
    assert isinstance(result.data, ChatResponse)
    assert result.data.response == "Recovered!"
    assert planner.provider.call_count == 2

def test_planner_max_retries_exhausted(monkeypatch):
    from edith.ai.providers.factory import ProviderFactory
    monkeypatch.setattr(ProviderFactory, "get_provider", lambda: MockProvider("Still not JSON"))
    
    planner = Planner()
    result = planner.plan("Fail me")
    
    # Max retries is 2, so it should try 3 times total (initial + 2 retries)
    assert isinstance(result.data, ErrorResponse)
    assert "Failed to generate valid JSON" in result.data.message
    assert planner.provider.call_count == 3
