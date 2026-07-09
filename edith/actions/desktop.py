import subprocess
import os
from typing import Dict, Any
from edith.core.registry import registry
from edith.utils.logger import logger

@registry.register("launch_app")
def launch_app(intent_data: Dict[str, Any]) -> str:
    app_name = intent_data.get("app_name", "").lower()
    
    if not app_name:
        return "I didn't catch the name of the application you want to open."

    logger.info(f"Attempting to launch app: {app_name}")
    
    # Common Windows mappings
    app_map = {
        "chrome": "start chrome",
        "google chrome": "start chrome",
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "notepad": "notepad",
        "calculator": "calc",
        "spotify": "start spotify",
        "explorer": "explorer"
    }

    command = app_map.get(app_name)
    
    if command:
        try:
            # Using shell=True for 'start' commands on Windows
            subprocess.Popen(command, shell=True)
            return f"Opening {app_name}."
        except Exception as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            return f"I tried to open {app_name}, but something went wrong."
    else:
        # Fallback to try and run it directly
        try:
            subprocess.Popen(f"start {app_name}", shell=True)
            return f"Trying to open {app_name}."
        except Exception:
            return f"I couldn't find an application called {app_name} on your system."
