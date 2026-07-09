import pytest
import tracemalloc
import time
from unittest.mock import MagicMock
from edith.main import build_app
from edith.core.state_machine import AppState
from edith.ai.models import PlannerResponse, ChatResponse, ResponseMetadata

def test_endurance_memory_leak():
    """
    Simulates 10,000 orchestration cycles to measure memory footprint growth.
    Target: <2% growth. Max acceptable: 5%.
    """
    # 1. Build app (without starting UI or daemon threads)
    orchestrator, _ = build_app()
    
    # 2. Fast Mocking to isolate EDITH internals from slow ML inference
    mock_planner = MagicMock()
    mock_planner.plan.return_value = PlannerResponse(
        data=ChatResponse(response="Mock response"),
        metadata=ResponseMetadata(provider="mock", model="mock", latency=0.0, created_at="now")
    )
    orchestrator.planner = mock_planner
    orchestrator.voice = MagicMock()
    
    # Optional: Mock embedding so we don't spam Ollama with 10k requests, 
    # but still hit SQLite and Memory Manager
    mock_embedding = MagicMock()
    mock_embedding.generate_embedding.return_value = [0.1] * 768
    orchestrator.memory.repo.embedding_provider = mock_embedding
    
    orchestrator.state_machine._state = AppState.READY
    
    # 3. Warm-up (populate caches, JIT, etc.)
    for _ in range(100):
        try:
            orchestrator._handle_request("warmup")
        except Exception:
            pass
        finally:
            orchestrator.state_machine._state = AppState.READY
            
    
    # 4. Baseline Memory Snapshot
    tracemalloc.start()
    time.sleep(0.5)
    baseline_snapshot = tracemalloc.take_snapshot()
    baseline_size = sum(stat.size for stat in baseline_snapshot.statistics("filename"))
    
    # 5. Stress Test - 10,000 cycles
    ITERATIONS = 10000
    for i in range(ITERATIONS):
        try:
            # Pass a unique string so memory saves unique entries and context grows
            orchestrator._handle_request(f"stress_test_input_{i}")
        except Exception:
            pass
        finally:
            orchestrator.state_machine._state = AppState.READY
        
    # 6. Final Memory Snapshot
    time.sleep(0.5)
    final_snapshot = tracemalloc.take_snapshot()
    final_size = sum(stat.size for stat in final_snapshot.statistics("filename"))
    
    tracemalloc.stop()
    
    # Calculate metrics
    growth_bytes = final_size - baseline_size
    growth_percent = (growth_bytes / baseline_size) * 100 if baseline_size > 0 else 0
    
    print(f"\n[Endurance Test] Iterations: {ITERATIONS}")
    print(f"[Endurance Test] Baseline Memory: {baseline_size / 1024 / 1024:.2f} MB")
    print(f"[Endurance Test] Final Memory: {final_size / 1024 / 1024:.2f} MB")
    print(f"[Endurance Test] Memory Growth: {growth_percent:.2f}% ({growth_bytes / 1024 / 1024:.2f} MB)")
    
    # The requirement is max 5%, target < 2%
    assert growth_percent <= 5.0, f"Memory growth {growth_percent:.2f}% exceeds 5% threshold!"
