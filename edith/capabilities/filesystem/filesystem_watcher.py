from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

class IFileWatcher(ABC):
    """
    Optional interface for Directory Watching.
    Architecture reserved for future capabilities.
    """
    
    @abstractmethod
    def watch(self, path: Path, on_event: Callable[[str, Path], None]) -> str:
        """Start watching a directory and return a watcher_id."""
        pass
        
    @abstractmethod
    def stop(self, watcher_id: str) -> None:
        """Stop a specific watcher."""
        pass
