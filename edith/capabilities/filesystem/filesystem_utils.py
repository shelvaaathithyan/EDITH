import os
from pathlib import Path
from edith.capabilities.filesystem.filesystem_exceptions import InvalidPathError

class PathResolver:
    """Intelligent path resolver for EDITH Filesystem Capability."""
    
    @staticmethod
    def resolve(path_str: str, current_context: Path | str | None = None) -> Path:
        """
        Resolves natural language or shorthand paths to an absolute pathlib.Path.
        """
        if not path_str:
            raise InvalidPathError("Path string cannot be empty.")
            
        path_str = path_str.strip()
        
        # Windows environment variables
        if "%" in path_str:
            path_str = os.path.expandvars(path_str)
            
        # Tilde expansion
        if "~" in path_str:
            path_str = os.path.expanduser(path_str)
            
        # Natural aliases
        user_home = Path.home()
        aliases = {
            "desktop": user_home / "Desktop",
            "downloads": user_home / "Downloads",
            "documents": user_home / "Documents",
            "pictures": user_home / "Pictures",
            "music": user_home / "Music",
            "videos": user_home / "Videos",
            "home": user_home,
            "temp": Path(os.environ.get("TEMP", "C:/Temp"))
        }
        
        lower_path = path_str.lower()
        if lower_path in aliases:
            return aliases[lower_path]
            
        p = Path(path_str)
        
        # Absolute path check
        if p.is_absolute():
            return p.resolve()
            
        # Relative to current_context or current working directory
        base_dir = Path(current_context).resolve() if current_context else Path.cwd()
        
        if path_str == "." or lower_path == "here":
            return base_dir
        if path_str == "..":
            return base_dir.parent
            
        return (base_dir / p).resolve()
