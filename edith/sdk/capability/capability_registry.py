from typing import Dict, List, Optional
from edith.utils.logger import logger
from edith.sdk.capability.base_capability import BaseCapability
from edith.sdk.capability.capability_health import CapabilityHealth
from edith.sdk.capability.capability_exceptions import CapabilityUnavailableError

class CapabilityRegistry:
    def __init__(self):
        self._capabilities: Dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability) -> None:
        """Registers a single capability instance."""
        manifest = capability.get_manifest()
        
        if manifest.id in self._capabilities:
            logger.warning(f"Capability {manifest.id} is already registered. Overwriting.")
            
        try:
            capability.initialize()
            self._capabilities[manifest.id] = capability
            logger.info(f"Registered capability: {manifest.id} v{manifest.version}")
        except Exception as e:
            logger.error(f"Failed to register capability {manifest.id}: {e}")

    def get_capability(self, capability_id: str) -> Optional[BaseCapability]:
        """Retrieves a capability by ID."""
        return self._capabilities.get(capability_id)

    def get_all(self) -> List[BaseCapability]:
        """Returns all registered capabilities."""
        return list(self._capabilities.values())

    def get_health_summary(self) -> Dict[str, str]:
        """Returns a summary of all capability health statuses."""
        return {
            cap_id: cap.health_check().value
            for cap_id, cap in self._capabilities.items()
        }

    def shutdown_all(self) -> None:
        """Shuts down all registered capabilities."""
        for cap_id, cap in self._capabilities.items():
            try:
                cap.shutdown()
                logger.info(f"Shutdown capability: {cap_id}")
            except Exception as e:
                logger.error(f"Error shutting down capability {cap_id}: {e}")
                
# Global instance
capability_registry = CapabilityRegistry()
