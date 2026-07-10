import keyboard
import threading
import time
from edith.utils.logger import logger
from edith.core.events import event_bus, AppEvent

class PTTController:
    """
    Manages the Push-to-Talk functionality (Key: 7).
    We run this as a background listener. When 7 is pressed, we alert the voice manager.
    """
    def __init__(self, key="7"):
        self.key = key
        self.is_running = False
        self._thread = None
        
    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._listener_loop, daemon=True, name="PTTController")
        self._thread.start()
        logger.info(f"PTT Controller started listening for '{self.key}' key.")

    def stop(self):
        self.is_running = False
        
    def _listener_loop(self):
        while self.is_running:
            try:
                # Wait until key is pressed
                while not keyboard.is_pressed(self.key) and self.is_running:
                    time.sleep(0.05)
                
                if not self.is_running:
                    break
                    
                # Key is pressed
                logger.info(f"PTT key '{self.key}' pressed.")
                event_bus.publish(AppEvent.WAKE_WORD_DETECTED, "PTT")
                
                # Wait until key is released
                while keyboard.is_pressed(self.key) and self.is_running:
                    time.sleep(0.05)
                    
                # Key is released
                logger.info(f"PTT key '{self.key}' released.")
                
            except ImportError:
                logger.error("keyboard library not installed, disabling PTT.")
                break
            except Exception as e:
                logger.error(f"PTT Controller error: {e}")
                time.sleep(1)

ptt_controller = PTTController()
