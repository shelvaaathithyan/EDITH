from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from edith.permission.permission_models import RiskLevel
from edith.sdk.capability.capability_health import CapabilityHealth

class CapabilityManifest(BaseModel):
    id: str
    name: str
    version: str
    author: str
    description: str
    supported_platforms: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    supported_actions: List[str] = Field(default_factory=list)
    risk_matrix: Dict[str, RiskLevel] = Field(default_factory=dict)
    required_permissions: List[str] = Field(default_factory=list)
    min_python_version: str = "3.10"

class CapabilityResult(BaseModel):
    success: bool
    capability: str
    action: str
    execution_time: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    message: str = ""
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
