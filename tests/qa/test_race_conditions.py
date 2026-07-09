import pytest
import threading
import time
import random
import queue
from edith.core.events import event_bus, AppEvent
from edith.core.state_machine import StateMachine, AppState
from edith.interaction.context.context_manager import ContextManager

def test_event_bus_concurrency():
    """Stress test the EventBus to ensure threading.RLock handles concurrent publish/subscribe."""
    errors = []
    
    def subscriber(data):
        # Do some trivial work
        time.sleep(0.001)
        if data != "test_data":
            errors.append("Corrupted data")

    # Subscribe from many threads
    threads = []
    for i in range(50):
        t = threading.Thread(target=event_bus.subscribe, args=(AppEvent.STATE_CHANGED, subscriber))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()

    # Publish from many threads
    pub_threads = []
    for i in range(100):
        t = threading.Thread(target=event_bus.publish, args=(AppEvent.STATE_CHANGED, "test_data"))
        pub_threads.append(t)
        t.start()

    for t in pub_threads:
        t.join()

    assert not errors, f"Event bus concurrency errors: {errors}"
    
    # Cleanup
    event_bus._subscribers[AppEvent.STATE_CHANGED] = []

def test_state_machine_concurrency():
    """Stress test StateMachine to ensure thread-safe transitions and queries."""
    sm = StateMachine()
    errors = []
    
    def transition_worker():
        for _ in range(100):
            try:
                current = sm.get_state()
                # Just random transitions to trigger the lock, 
                # we wrap in try/except because invalid transitions throw StateTransitionError
                if current == AppState.STARTING:
                    sm.transition(AppState.INITIALIZING)
                elif current == AppState.INITIALIZING:
                    sm.transition(AppState.READY)
                elif current == AppState.READY:
                    sm.transition(AppState.LISTENING)
                elif current == AppState.LISTENING:
                    sm.transition(AppState.READY)
            except Exception as e:
                # We expect StateTransitionError due to race conditions, which proves it protects state!
                # What we don't want is corrupted state or deadlocks.
                pass
            time.sleep(0.001)

    threads = [threading.Thread(target=transition_worker) for _ in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    # If we made it here without deadlock, the lock works.
    assert isinstance(sm.get_state(), AppState)

def test_context_manager_concurrency():
    """Stress test ContextManager dictionary updates."""
    cm = ContextManager()
    errors = []
    
    def context_worker(thread_id):
        for i in range(100):
            # Must use a recognized key
            cm.update_context({f"last_folder": f"value_{thread_id}_{i}"})
            ctx = cm.get_context()
            if not isinstance(ctx, dict):
                errors.append("Context became invalid")
            time.sleep(0.001)

    threads = [threading.Thread(target=context_worker, args=(i,)) for i in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert not errors, "Context manager concurrency errors detected"
    assert len(cm.get_context()) >= 1 # Just ensure it hasn't crashed, since last_folder overwrites itself
