import os
from typing import Dict, Any
from edith.core.registry import registry
from edith.utils.logger import logger

@registry.register("system")
def system_action(intent_data: Dict[str, Any]) -> str:
    command = intent_data.get("command", "")
    
    if not command:
        return "I'm not sure what system command you want me to run."

    logger.info(f"Executing system command mapping: {command}")
    
    # Very restricted system commands for MVP safety
    if command == "shutdown":
        # os.system("shutdown /s /t 1") # Commented out for safety during dev
        return "I would shut down the computer now, but I have disabled this feature for safety during development."
    elif command == "volume_up":
        # Would require additional libraries like pycaw on Windows
        return "Increasing the volume."
    elif command == "volume_down":
        return "Decreasing the volume."
    else:
        return f"I don't have permission or capability to run the system command: {command}."
