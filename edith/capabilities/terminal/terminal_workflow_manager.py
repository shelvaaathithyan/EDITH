"""
Terminal Capability — Developer Workflow Manager

Sits between the Planner and TerminalCapability. Converts high-level
workflow actions (e.g. 'deploy_project') into ordered sequences of
terminal commands + capability actions.

NOT a capability itself — it is a plan transformer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from edith.capabilities.terminal.terminal_workspace import workspace_manager
from edith.utils.logger import logger


@dataclass
class WorkflowStep:
    """A single step in a developer workflow."""
    capability: str                     # "terminal" or "browser"
    action: str                         # action name
    args: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None     # e.g. "workspace.has_docker"
    on_failure: str = "stop"            # "stop" | "continue" | "rollback"
    label: Optional[str] = None         # Human-readable step name


@dataclass
class WorkflowDefinition:
    """A named, ordered sequence of WorkflowSteps."""
    id: str
    display_name: str
    steps: List[WorkflowStep]
    requires_workspace: bool = True
    creates_group: bool = True          # Whether to wrap steps in a ProcessGroup


# ---------------------------------------------------------------------------
# Built-in workflow definitions
# ---------------------------------------------------------------------------

BUILTIN_WORKFLOWS: Dict[str, WorkflowDefinition] = {
    "deploy_project": WorkflowDefinition(
        id="deploy_project",
        display_name="Deploy Project",
        creates_group=True,
        steps=[
            WorkflowStep("terminal", "run_command", {"command": "git pull"}, label="Pull latest"),
            WorkflowStep("terminal", "install_dependencies", label="Install dependencies"),
            WorkflowStep("terminal", "build_project", label="Build"),
            WorkflowStep("terminal", "run_command", {"command": "docker compose up -d"},
                         condition="workspace.has_docker", label="Start containers"),
            WorkflowStep("browser", "navigate", {"query": "http://localhost:3000"},
                         on_failure="continue", label="Open browser"),
        ],
    ),
    "run_full_test_suite": WorkflowDefinition(
        id="run_full_test_suite",
        display_name="Run Full Test Suite",
        creates_group=False,
        steps=[
            WorkflowStep("terminal", "install_dependencies", label="Install dependencies"),
            WorkflowStep("terminal", "lint", label="Lint"),
            WorkflowStep("terminal", "run_tests", label="Run tests"),
        ],
    ),
    "clean_and_rebuild": WorkflowDefinition(
        id="clean_and_rebuild",
        display_name="Clean and Rebuild",
        creates_group=False,
        steps=[
            WorkflowStep("terminal", "clean", label="Clean"),
            WorkflowStep("terminal", "install_dependencies", label="Install dependencies"),
            WorkflowStep("terminal", "build_project", label="Build"),
        ],
    ),
    "start_dev_environment": WorkflowDefinition(
        id="start_dev_environment",
        display_name="Start Development Environment",
        creates_group=True,
        steps=[
            WorkflowStep("terminal", "install_dependencies", label="Install dependencies"),
            WorkflowStep("terminal", "start_project", label="Start project"),
            WorkflowStep("browser", "navigate", {"query": "http://localhost:3000"},
                         on_failure="continue", label="Open browser"),
        ],
    ),
}


class DeveloperWorkflowManager:
    """
    Expands a workflow ID into an ordered list of WorkflowStep objects.
    Evaluates step conditions against the active workspace.
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = dict(BUILTIN_WORKFLOWS)

    def register(self, workflow: WorkflowDefinition) -> None:
        """Register a custom workflow at runtime."""
        self._workflows[workflow.id] = workflow
        logger.info(f"Workflow registered: {workflow.id}")

    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def is_workflow(self, action: str) -> bool:
        return action in self._workflows

    def expand(self, workflow_id: str) -> List[WorkflowStep]:
        """
        Return the filtered, condition-evaluated list of steps for a workflow.
        """
        definition = self._workflows.get(workflow_id)
        if not definition:
            raise ValueError(f"Unknown workflow: '{workflow_id}'")

        workspace = workspace_manager.get_active_workspace()
        active_steps: List[WorkflowStep] = []

        for step in definition.steps:
            if step.condition and not self._eval_condition(step.condition, workspace):
                logger.debug(
                    f"Workflow '{workflow_id}': skipping step '{step.label}' "
                    f"(condition not met: {step.condition})"
                )
                continue
            active_steps.append(step)

        logger.info(
            f"Workflow '{workflow_id}' expanded to {len(active_steps)} steps."
        )
        return active_steps

    def list_workflows(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())

    @staticmethod
    def _eval_condition(condition: str, workspace) -> bool:
        """Evaluate a simple condition string against the workspace state."""
        if workspace is None:
            return False

        if condition == "workspace.has_docker":
            return workspace.docker_compose_path is not None
        if condition == "workspace.has_git":
            return workspace.git_root is not None
        if condition == "workspace.has_venv":
            return workspace.venv_path is not None
        if condition.startswith("workspace.has_tool:"):
            tool = condition.split(":", 1)[1]
            return tool in workspace.environment.available_tools

        logger.warning(f"Unknown workflow condition: '{condition}'")
        return True  # Unknown conditions pass by default


# Global singleton
workflow_manager = DeveloperWorkflowManager()
