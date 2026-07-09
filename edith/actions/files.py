import os
import shutil
from pathlib import Path
from typing import Dict, Any
from edith.core.registry import registry
from edith.utils.logger import logger

@registry.register("filesystem")
def filesystem_action(intent_data: Dict[str, Any]) -> str:
    operation = intent_data.get("operation")
    path_str = intent_data.get("path")
    
    if not operation or not path_str:
        return "I need to know the operation and the file path to do that."

    # Using the current user's home directory as the base for safety in MVP
    base_dir = Path.home()
    target_path = base_dir / path_str

    try:
        if operation == "create_folder":
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {target_path}")
            return f"I have created the folder {path_str} in your home directory."
            
        elif operation == "delete_folder":
            if target_path.exists() and target_path.is_dir():
                shutil.rmtree(target_path)
                logger.info(f"Deleted folder: {target_path}")
                return f"I have deleted the folder {path_str}."
            return f"I couldn't find a folder named {path_str}."
            
        else:
            return f"I don't know how to perform the filesystem operation: {operation}."
            
    except Exception as e:
        logger.error(f"Filesystem error: {e}")
        return f"An error occurred while trying to modify the file system."
