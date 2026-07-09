from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from edith.ai.models import PlannerResponse

@dataclass
class OrchestrationContext:
    """The generic payload that flows through the execution pipeline."""
    user_input: str
    planner_response: Optional[PlannerResponse] = None
    execution_result: Optional[str] = None
    final_response: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Flags to control pipeline flow
    halt_pipeline: bool = False
    error: Optional[Exception] = None
