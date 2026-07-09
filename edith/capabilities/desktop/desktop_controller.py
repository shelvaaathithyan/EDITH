import subprocess
import psutil
import win32gui
import win32con
import win32process
from typing import Optional, List, Dict, Any

from edith.utils.logger import logger
from edith.capabilities.desktop.desktop_exceptions import ApplicationLaunchError, WindowFocusError
from edith.capabilities.desktop.desktop_constants import (
    SW_RESTORE, SW_MINIMIZE, SW_MAXIMIZE, SW_SHOW, WM_CLOSE
)

class DesktopController:
    """
    Handles OS-level process management and Window API interactions using psutil and pywin32.
    """

    def _get_hwnds_for_pid(self, pid: int) -> List[int]:
        """Finds all top-level window handles associated with a given Process ID."""
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    hwnds.append(hwnd)
            return True
            
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds

    def _find_running_process(self, exe_name: str) -> Optional[psutil.Process]:
        """Finds a running process by its executable name."""
        exe_lower = exe_name.lower()
        # Some aliases have args like "Update.exe --processStart Discord.exe"
        if " " in exe_lower:
            # Try to extract the actual target if it's a known pattern
            parts = exe_lower.split()
            exe_lower = parts[-1]
            
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == exe_lower:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None

    def check_running(self, exe_name: str) -> bool:
        return self._find_running_process(exe_name) is not None

    def launch(self, path: str) -> bool:
        """Launches the executable at the given path."""
        try:
            # Check if it's a command with arguments
            if " " in path and not path.startswith('"'):
                subprocess.Popen(path, shell=True, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                subprocess.Popen([path], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True)
            return True
        except Exception as e:
            logger.error(f"Failed to launch application at {path}: {e}")
            raise ApplicationLaunchError(f"System error launching application: {e}")

    def _execute_window_action(self, exe_name: str, action: str) -> Dict[str, Any]:
        """Core method to find a process's window and apply a win32 API action."""
        proc = self._find_running_process(exe_name)
        if not proc:
            return {"success": False, "message": "Application is not currently running."}

        hwnds = self._get_hwnds_for_pid(proc.pid)
        if not hwnds:
            # Sometimes applications spawn child processes that own the window.
            # Look through children
            try:
                for child in proc.children(recursive=True):
                    hwnds.extend(self._get_hwnds_for_pid(child.pid))
            except psutil.Error:
                pass
                
        if not hwnds:
            return {"success": False, "message": "Application is running but has no visible windows."}
            
        # Prioritize the largest or first window
        hwnd = hwnds[0]
        window_title = win32gui.GetWindowText(hwnd)

        try:
            if action == "focus" or action == "restore":
                # If minimized, restore it first
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement[1] == win32con.SW_SHOWMINIMIZED:
                    win32gui.ShowWindow(hwnd, SW_RESTORE)
                    
                win32gui.SetForegroundWindow(hwnd)
                return {"success": True, "message": f"Focused {window_title}.", "window_title": window_title}
                
            elif action == "minimize":
                win32gui.ShowWindow(hwnd, SW_MINIMIZE)
                return {"success": True, "message": f"Minimized {window_title}.", "window_title": window_title}
                
            elif action == "maximize":
                win32gui.ShowWindow(hwnd, SW_MAXIMIZE)
                return {"success": True, "message": f"Maximized {window_title}.", "window_title": window_title}
                
            elif action == "close":
                # Graceful close
                win32gui.PostMessage(hwnd, WM_CLOSE, 0, 0)
                return {"success": True, "message": f"Closed {window_title}.", "window_title": window_title}
                
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Window API error for {action} on {exe_name}: {e}")
            raise WindowFocusError(f"Failed to perform {action} on window: {e}")

    def focus(self, exe_name: str) -> Dict[str, Any]:
        return self._execute_window_action(exe_name, "focus")

    def close(self, exe_name: str) -> Dict[str, Any]:
        return self._execute_window_action(exe_name, "close")

    def minimize(self, exe_name: str) -> Dict[str, Any]:
        return self._execute_window_action(exe_name, "minimize")

    def maximize(self, exe_name: str) -> Dict[str, Any]:
        return self._execute_window_action(exe_name, "maximize")

    def restore(self, exe_name: str) -> Dict[str, Any]:
        return self._execute_window_action(exe_name, "restore")
