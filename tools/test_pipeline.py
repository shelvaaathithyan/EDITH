import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from edith.main import build_app
from edith.core.events import event_bus, AppEvent

# Event tracking
events_fired = []

def _on_event(event_type, data):
    events_fired.append(event_type)
    print(f"[EVENT] {event_type.name}")

def test_pipeline():
    print("=== EDITH End-to-End Pipeline Diagnostic ===")
    
    # Subscribe to all events
    for et in AppEvent:
        event_bus.subscribe(et, lambda d, e=et: _on_event(e, d))
        
    print("\n[1] Building Application (Bootstrap)...")
    try:
        orchestrator, _ = build_app()
    except Exception as e:
        print(f"\n[FAIL] Bootstrap Failed: {e}")
        sys.exit(1)
        
    print("\n[2] Starting Orchestrator Worker...")
    orchestrator.start()
    
    # Give it a moment to spin up
    time.sleep(1)
    
    test_input = "Hello! Please reply briefly."
    print(f"\n[3] Injecting test input into Orchestrator: '{test_input}'")
    
    orchestrator.process_input(test_input)
    
    # Wait for pipeline to finish
    print("\n[4] Waiting for REQUEST_COMPLETED...")
    timeout = 30
    start = time.time()
    
    while AppEvent.REQUEST_COMPLETED not in events_fired and time.time() - start < timeout:
        time.sleep(0.5)
        
    orchestrator.stop()
    
    if AppEvent.REQUEST_COMPLETED in events_fired:
        print("\n[OK] Pipeline completed successfully!")
    else:
        print(f"\n[FAIL] Pipeline timed out after {timeout} seconds.")
        print(f"Events captured: {[e.name for e in events_fired]}")
        sys.exit(1)

if __name__ == "__main__":
    test_pipeline()
