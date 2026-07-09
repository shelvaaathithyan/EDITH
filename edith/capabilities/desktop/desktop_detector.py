import os
import winreg
import shutil
from typing import Dict, Optional
from edith.utils.logger import logger

class AppIndex:
    """Represents a cached application entry."""
    def __init__(self, executable: str, path: str):
        self.executable = executable
        self.path = path

class DesktopDetector:
    """
    Scans and caches installed desktop applications to avoid slow Registry lookups.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DesktopDetector, cls).__new__(cls)
            cls._instance._cache: Dict[str, AppIndex] = {}
            cls._instance._is_loaded = False
        return cls._instance

    def load_index(self):
        """Scans the system for applications and builds the cache."""
        if self._is_loaded:
            return
            
        logger.info("Building Application Index from Windows Registry...")
        
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]
        
        for hkey, reg_path in registry_paths:
            try:
                with winreg.OpenKey(hkey, reg_path) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            app_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, app_key_name) as app_key:
                                path, _ = winreg.QueryValueEx(app_key, "")
                                if path and os.path.exists(path):
                                    exe_name = app_key_name.lower()
                                    self._cache[exe_name] = AppIndex(exe_name, path)
                        except Exception:
                            continue
            except FileNotFoundError:
                pass
                
        self._is_loaded = True
        logger.info(f"Application Index built. Found {len(self._cache)} executables.")

    def refresh(self):
        """Forces a rebuild of the Application Index."""
        self._cache.clear()
        self._is_loaded = False
        self.load_index()

    def find_executable(self, exe_name: str) -> Optional[str]:
        """
        Attempts to find the absolute path for an executable using:
        1. Cache (Registry App Paths)
        2. PATH environment (shutil.which)
        """
        if not self._is_loaded:
            self.load_index()
            
        exe_lower = exe_name.lower()
        
        # Some aliases map to commands with arguments (e.g. "Update.exe --processStart Discord.exe")
        # In this case we just return the full command, we don't try to resolve it to an absolute path directly if it has args
        if " " in exe_name and not exe_name.startswith('"'):
            # Just return the raw command, the controller will split it or pass it to shell
            return exe_name
            
        # 1. Check Cache
        if exe_lower in self._cache:
            return self._cache[exe_lower].path
            
        # 2. Check PATH
        path_result = shutil.which(exe_name)
        if path_result:
            return path_result
            
        return None

detector = DesktopDetector()
