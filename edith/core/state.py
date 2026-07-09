class AppState:
    def __init__(self):
        self.is_listening = False
        self.is_processing = False
        self.last_intent = None

state = AppState()
