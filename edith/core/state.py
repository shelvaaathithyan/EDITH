"""
DEPRECATED: Legacy state object. Replaced by StateMachine with AppState enum.
Scheduled for removal after integration tests confirm it is unused.
"""
import warnings
warnings.warn("edith.core.state is deprecated. Use StateMachine instead.", DeprecationWarning, stacklevel=2)

class AppState:
    def __init__(self):
        self.is_listening = False
        self.is_processing = False
        self.last_intent = None

state = AppState()
