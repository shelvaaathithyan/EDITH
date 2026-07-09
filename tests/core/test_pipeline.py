import pytest
from unittest.mock import MagicMock
from edith.core.models import OrchestrationContext
from edith.core.pipeline import Pipeline, PipelineStage

class MockStage1(PipelineStage):
    def process(self, context: OrchestrationContext) -> None:
        context.metadata["stage1"] = True

class MockStage2(PipelineStage):
    def process(self, context: OrchestrationContext) -> None:
        context.metadata["stage2"] = True
        context.halt_pipeline = True # Halt here

class MockStage3(PipelineStage):
    def process(self, context: OrchestrationContext) -> None:
        context.metadata["stage3"] = True

def test_pipeline_execution():
    pipeline = Pipeline()
    pipeline.add_stage(MockStage1())
    pipeline.add_stage(MockStage2())
    pipeline.add_stage(MockStage3())
    
    context = OrchestrationContext(user_input="test")
    pipeline.execute(context)
    
    assert context.metadata.get("stage1") is True
    assert context.metadata.get("stage2") is True
    # Stage 3 should not have run because stage 2 halted
    assert context.metadata.get("stage3") is None
    assert context.halt_pipeline is True
