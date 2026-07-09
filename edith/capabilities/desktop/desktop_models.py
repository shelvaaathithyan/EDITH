from typing import Optional
from pydantic import BaseModel, Field

class DesktopActionArgs(BaseModel):
    """Strongly typed arguments for the desktop tool."""
    action: str = Field(description="'launch', 'close', 'focus', 'minimize', 'maximize', 'restore'")
    application: str = Field(description="Name or alias of the application (e.g. 'vscode', 'spotify', 'chrome')")
