from abc import ABC, abstractmethod
from typing import List
from edith.core.models import OrchestrationContext
from edith.utils.logger import logger
from edith.core.events import event_bus, AppEvent

class PipelineStage(ABC):
    @abstractmethod
    def process(self, context: OrchestrationContext) -> None:
        """Processes the context. Implementations may mutate the context.
        To halt the pipeline (e.g., error or permission denied), set context.halt_pipeline = True."""
        pass

class Pipeline:
    def __init__(self):
        self.stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage):
        self.stages.append(stage)

    def execute(self, context: OrchestrationContext) -> None:
        event_bus.publish(AppEvent.PIPELINE_STARTED, context)
        
        for stage in self.stages:
            if context.halt_pipeline:
                logger.info("Pipeline execution halted.")
                break
                
            try:
                stage_name = stage.__class__.__name__
                logger.debug(f"Executing pipeline stage: {stage_name}")
                stage.process(context)
            except Exception as e:
                logger.error(f"Error in pipeline stage {stage_name}: {e}")
                context.halt_pipeline = True
                context.error = e
                break
                
        event_bus.publish(AppEvent.PIPELINE_COMPLETED, context)
