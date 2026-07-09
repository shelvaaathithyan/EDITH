import os
import subprocess
import webbrowser
import winreg
from typing import Optional, Dict

from edith.utils.logger import logger
from edith.capabilities.browser.browser_exceptions import BrowserLaunchError

class BrowserController:
    """
    Stateless controller for launching and navigating web browsers on Windows.
    Uses registry checks to find executable paths and subprocess/webbrowser to launch.
    """
    
    # Common browser registry paths
    BROWSER_REGISTRY = {
        "chrome": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        "edge": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
        "firefox": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe",
        "brave": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe"
    }

    def _get_browser_path(self, browser_name: str) -> Optional[str]:
        """Locates the absolute path to the browser executable using the Windows Registry."""
        browser_name = browser_name.lower()
        if browser_name not in self.BROWSER_REGISTRY:
            return None
            
        reg_path = self.BROWSER_REGISTRY[browser_name]
        try:
            # Try Current User
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                path, _ = winreg.QueryValueEx(key, "")
                if path and os.path.exists(path):
                    return path
        except FileNotFoundError:
            pass
            
        try:
            # Try Local Machine
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                path, _ = winreg.QueryValueEx(key, "")
                if path and os.path.exists(path):
                    return path
        except FileNotFoundError:
            pass
            
        return None

    def launch(self, url: str, browser: Optional[str] = None) -> Dict[str, str]:
        """
        Launches the specified URL in the given browser.
        Returns a dict with 'browser' used and 'url' opened.
        """
        browser_used = "system default"
        
        # Try specific browser via subprocess if requested
        if browser:
            exe_path = self._get_browser_path(browser)
            if exe_path:
                try:
                    # Detached process so it doesn't block EDITH
                    # CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS
                    creationflags = 0x00000200 | 0x00000008
                    subprocess.Popen([exe_path, url], creationflags=creationflags, close_fds=True)
                    logger.info(f"Launched {browser} at {url} via subprocess.")
                    return {"browser": browser, "url": url}
                except Exception as e:
                    logger.error(f"Failed to launch {browser} via subprocess: {e}")
                    # Fallback
            else:
                logger.warning(f"Browser '{browser}' requested but executable not found. Falling back.")
        
        # Fallback to python's standard webbrowser
        try:
            logger.info(f"Launching {url} via default webbrowser module.")
            success = webbrowser.open(url)
            if not success:
                raise BrowserLaunchError("webbrowser.open returned False.")
        except Exception as e:
            logger.error(f"Failed to launch default browser: {e}")
            raise BrowserLaunchError(f"Could not launch browser: {e}")
            
        return {"browser": browser_used, "url": url}
