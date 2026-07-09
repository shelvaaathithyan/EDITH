from typing import List, Any
from edith.utils.logger import logger
from edith.core.state_machine import StateMachine, AppState

class BootstrapManager:
    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine
        self.subsystems: List[Any] = []

    def register_subsystem(self, subsystem: Any):
        self.subsystems.append(subsystem)

    def startup(self) -> bool:
        """Initializes all registered subsystems. Returns True if successful."""
        try:
            self.state_machine.transition(AppState.INITIALIZING)
            
            for subsystem in self.subsystems:
                name = subsystem.__class__.__name__
                logger.info(f"Initializing subsystem: {name}")
                
                # Check health if supported
                if hasattr(subsystem, 'health_check'):
                    health = subsystem.health_check()
                    if health and getattr(health, 'status', 'unhealthy') != 'healthy':
                        logger.error(f"Health check failed for {name}: {getattr(health, 'error', 'Unknown Error')}")
                        self.state_machine.transition(AppState.ERROR)
                        return False
                
                # Initialize
                if hasattr(subsystem, 'initialize'):
                    subsystem.initialize()
                    
            self.state_machine.transition(AppState.READY)
            logger.info("All subsystems initialized successfully. System READY.")
            return True
            
        except Exception as e:
            logger.error(f"Startup failed during initialization: {e}")
            try:
                self.state_machine.transition(AppState.ERROR)
            except Exception:
                pass
            return False

    def shutdown(self):
        """Shuts down all registered subsystems in reverse order."""
        try:
            self.state_machine.transition(AppState.SHUTTING_DOWN)
        except Exception:
            pass
            
        for subsystem in reversed(self.subsystems):
            if hasattr(subsystem, 'shutdown'):
                try:
                    subsystem.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down {subsystem.__class__.__name__}: {e}")
