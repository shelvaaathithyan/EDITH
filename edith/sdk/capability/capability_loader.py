import pkgutil
import importlib
import inspect
from edith.utils.logger import logger
from edith.sdk.capability.base_capability import BaseCapability
from edith.sdk.capability.capability_registry import CapabilityRegistry

class CapabilityLoader:
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def initialize(self) -> None:
        """Lifecycle hook called by BootstrapManager."""
        self.discover_and_load()

    def discover_and_load(self, package_name: str = "edith.capabilities") -> None:
        """
        Scans a package for classes inheriting from BaseCapability and registers them.
        """
        logger.info(f"Scanning for capabilities in '{package_name}'...")
        try:
            package = importlib.import_module(package_name)
        except ImportError as e:
            logger.error(f"Failed to import capability package '{package_name}': {e}")
            return

        if not hasattr(package, "__path__"):
            logger.warning(f"Package '{package_name}' has no __path__. Cannot scan.")
            return

        for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            try:
                module = importlib.import_module(module_name)
                self._register_capabilities_from_module(module)
            except Exception as e:
                logger.error(f"Error loading capability module '{module_name}': {e}")

    def _register_capabilities_from_module(self, module) -> None:
        """Finds BaseCapability subclasses in a module and registers them."""
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseCapability) and obj is not BaseCapability:
                # To prevent re-registering if imported elsewhere
                if getattr(obj, "__module__", "") != module.__name__:
                    continue
                    
                try:
                    # Instantiate and register
                    instance = obj()
                    self.registry.register(instance)
                except Exception as e:
                    logger.error(f"Failed to instantiate and register capability '{name}': {e}")
