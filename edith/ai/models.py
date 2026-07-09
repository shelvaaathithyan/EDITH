from typing import Dict, List, Any, Union, Optional
from pydantic import BaseModel, Field

class ExecutionStep(BaseModel):
    tool: str = Field(description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(description="Arguments for the tool")

class ExecutionPlan(BaseModel):
    type: str = Field(default="execution", description="Type of response")
    goal: str = Field(description="The high-level goal of this plan")
    steps: List[ExecutionStep] = Field(description="List of steps to execute")
    requires_confirmation: bool = Field(default=False, description="Whether user confirmation is required before execution")
    confidence: float = Field(default=1.0, description="Confidence score from 0.0 to 1.0")

class ChatResponse(BaseModel):
    type: str = Field(default="chat", description="Type of response")
    response: str = Field(description="The natural language response")

class ErrorResponse(BaseModel):
    type: str = Field(default="error", description="Type of response")
    message: str = Field(description="The error message to convey to the user")

class ResponseMetadata(BaseModel):
    provider: str
    model: str
    latency: float
    tokens: Optional[int] = None
    created_at: str

class PlannerResponse(BaseModel):
    """Wrapper that contains the typed response and reasoning metadata."""
    data: Union[ExecutionPlan, ChatResponse, ErrorResponse]
    metadata: ResponseMetadata

class HealthStatus(BaseModel):
    status: str = Field(description="'healthy' or 'unhealthy'")
    provider: str
    model: str
    latency: Optional[float] = None
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional health details like 'ollama_running', 'model_installed', etc.")
