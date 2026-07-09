from typing import Dict, Any
from edith.ai.models import PlannerResponse, ResponseMetadata, ExecutionPlan, ChatResponse, ErrorResponse

class ResponseParser:
    def parse(self, validated_data: Dict[str, Any], metadata: ResponseMetadata) -> PlannerResponse:
        """Parses validated dictionary into strongly-typed Pydantic models."""
        resp_type = validated_data.get("type")
        
        if resp_type == "execution":
            data_obj = ExecutionPlan(**validated_data)
        elif resp_type == "chat":
            data_obj = ChatResponse(**validated_data)
        elif resp_type == "error":
            data_obj = ErrorResponse(**validated_data)
        else:
            # Should not be reachable if validator is used properly
            data_obj = ErrorResponse(type="error", message=f"Unknown type: {resp_type}")
            
        return PlannerResponse(data=data_obj, metadata=metadata)
