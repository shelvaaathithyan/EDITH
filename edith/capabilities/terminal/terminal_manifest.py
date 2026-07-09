"""
Terminal Capability — Static Manifest

Defines the capability's contract: supported actions, risk matrix,
dependencies, and supported platforms.
"""

from edith.permission.permission_models import RiskLevel

MANIFEST = {
    "id": "terminal",
    "name": "Developer Execution Engine",
    "version": "1.0.0",
    "author": "EDITH Core",
    "description": (
        "Production-grade terminal execution engine. Supports shell command execution, "
        "long-running process management, developer workflows, project-aware workspaces, "
        "interactive stdin, process groups, and streaming output."
    ),
    "supported_platforms": ["Windows", "Linux", "macOS"],
    "dependencies": [],
    "supported_shells": [
        "powershell", "powershell5", "cmd", "wt", "gitbash", "wsl", "wsl-ubuntu",
        "bash", "zsh",
    ],
    "supported_actions": [
        # Core execution
        "run_command",
        "run_script",
        # Workspace
        "open_workspace",
        "set_working_directory",
        "switch_workspace",
        # Shell
        "open_terminal",
        # Process lifecycle
        "stop_process",
        "restart_process",
        "kill_process",
        "list_processes",
        # Interactive I/O
        "send_input",
        "send_ctrl_c",
        "send_ctrl_break",
        # Process groups
        "create_process_group",
        "stop_group",
        "list_groups",
        # Developer commands
        "install_dependencies",
        "run_tests",
        "build_project",
        "start_project",
        "stop_project",
        "lint",
        "format",
        "clean",
        # Workflows
        "deploy_project",
        "run_full_test_suite",
        "clean_and_rebuild",
        "start_dev_environment",
        # Environment
        "activate_venv",
        "deactivate_venv",
        "detect_environment",
        # Misc
        "clear_terminal",
        "get_session_output",
    ],
    "risk_matrix": {
        # Low risk — read-only or non-destructive
        "open_terminal":          RiskLevel.LOW,
        "open_workspace":         RiskLevel.LOW,
        "set_working_directory":  RiskLevel.LOW,
        "switch_workspace":       RiskLevel.LOW,
        "list_processes":         RiskLevel.LOW,
        "list_groups":            RiskLevel.LOW,
        "run_tests":              RiskLevel.LOW,
        "build_project":          RiskLevel.LOW,
        "start_project":          RiskLevel.LOW,
        "lint":                   RiskLevel.LOW,
        "format":                 RiskLevel.LOW,
        "activate_venv":          RiskLevel.LOW,
        "deactivate_venv":        RiskLevel.LOW,
        "detect_environment":     RiskLevel.LOW,
        "clear_terminal":         RiskLevel.LOW,
        "get_session_output":     RiskLevel.LOW,
        "send_input":             RiskLevel.LOW,
        "send_ctrl_c":            RiskLevel.LOW,
        "send_ctrl_break":        RiskLevel.LOW,
        # Medium risk — initiates I/O, downloads, or modifies state
        "run_command":            RiskLevel.MEDIUM,
        "install_dependencies":   RiskLevel.MEDIUM,
        "stop_process":           RiskLevel.MEDIUM,
        "restart_process":        RiskLevel.MEDIUM,
        "stop_project":           RiskLevel.MEDIUM,
        "stop_group":             RiskLevel.MEDIUM,
        "create_process_group":   RiskLevel.MEDIUM,
        "clean":                  RiskLevel.MEDIUM,
        "deploy_project":         RiskLevel.MEDIUM,
        "start_dev_environment":  RiskLevel.MEDIUM,
        "run_full_test_suite":    RiskLevel.MEDIUM,
        "clean_and_rebuild":      RiskLevel.MEDIUM,
        # High risk — arbitrary file execution or forceful termination
        "run_script":             RiskLevel.HIGH,
        "kill_process":           RiskLevel.HIGH,
    },
    "required_permissions": [],
}
