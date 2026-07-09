from typing import Optional
from pydantic import BaseModel, Field

class BrowserActionArgs(BaseModel):
    """Strongly typed arguments for the browser tool."""
    action: str = Field(description="'launch', 'search', 'navigate'")
    browser: Optional[str] = Field(default=None, description="'chrome', 'edge', 'firefox', 'brave', or None for default")
    query: Optional[str] = Field(default=None, description="Search query or URL")
