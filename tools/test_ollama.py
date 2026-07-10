import sys
import time

# Ensure s:\EDITH is in python path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from edith.config.settings import settings
from edith.ai.providers.ollama_provider import OllamaProvider

def test_ollama():
    print("=== EDITH Ollama Diagnostic ===")
    
    provider = OllamaProvider()
    print(f"Checking health...")
    health = provider.health_check()
    
    print("\n--- Diagnostic Results ---")
    print(f"Ollama Running: {health.details.get('ollama_running')}")
    print(f"Configured Model (from settings): {settings.ai_model}")
    print(f"Resolved Model (from provider): {provider.model}")
    print(f"Model Installed: {health.details.get('model_installed')}")
    print(f"Generate Endpoint: {provider.client.base_url}generate (appended to OLLAMA_API_URL)")
    print(f"Inference Test Passed: {health.details.get('inference_test')}")
    print(f"Overall Status: {health.status}")
    if health.error:
        print(f"Error: {health.error}")
        sys.exit(1)
        
    print("\n--- Live Inference Test ---")
    prompt = "Reply with exactly the word 'SUCCESS' in JSON format like {\"status\": \"SUCCESS\"}."
    print(f"Test Prompt: {prompt}")
    
    start = time.time()
    try:
        response = provider.plan(prompt, system_prompt="You are a JSON assistant.")
        latency = time.time() - start
        print(f"Planner Response: {response}")
        print(f"Latency: {latency:.2f}s")
    except Exception as e:
        print(f"Inference Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_ollama()
