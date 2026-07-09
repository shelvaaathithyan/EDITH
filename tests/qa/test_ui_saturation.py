import pytest
import time
from edith.core.events import event_bus, AppEvent
from edith.ui.window import UIManager

def test_ui_event_saturation():
    """
    Spam the event bus with thousands of events to ensure subscribers 
    (like UI window updates) don't lock up or crash.
    """
    ui = UIManager()
    
    # We won't call ui.start() because it blocks the main thread in pywebview,
    # but we can simulate the event bus hooks that UI sets up.
    # UIManager automatically registers to STATE_CHANGED and ERROR_OCCURRED in its real implementation?
    # Actually, UIManager in current architecture doesn't subscribe to EventBus natively yet for state.
    # Ah wait, in our app.js we have a push mechanism. 
    # Let's just test raw event bus throughput for now.
    
    received_count = [0]
    
    def dummy_subscriber(data):
        received_count[0] += 1
        
    event_bus.subscribe(AppEvent.STATE_CHANGED, dummy_subscriber)
    
    start_time = time.time()
    TOTAL_EVENTS = 5000
    
    for i in range(TOTAL_EVENTS):
        event_bus.publish(AppEvent.STATE_CHANGED, {"input": f"Spam {i}"})
        
    end_time = time.time()
    
    duration = end_time - start_time
    assert received_count[0] == TOTAL_EVENTS
    assert duration < 2.0, f"Event bus took too long to process {TOTAL_EVENTS} events: {duration:.2f}s"
    
    event_bus.unsubscribe(AppEvent.STATE_CHANGED, dummy_subscriber)
