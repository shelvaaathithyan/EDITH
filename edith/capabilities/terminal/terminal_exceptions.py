"""
Terminal Capability — Exception Hierarchy

All exceptions are isolated from core edith.core exceptions.
"""


class TerminalException(Exception):
    """Base exception for all Terminal Capability errors."""
    pass


class CommandBlockedError(TerminalException):
    """
    Raised when a command matches the security block-list.
    The Permission Manager will escalate this to CRITICAL risk.
    """
    def __init__(self, command: str, pattern: str):
        self.command = command
        self.pattern = pattern
        super().__init__(
            f"Command blocked by security policy. "
            f"Matched pattern: '{pattern}' in: '{command}'"
        )


class ExecutableNotFoundError(TerminalException):
    """Raised when the requested executable is not found on PATH."""
    def __init__(self, executable: str):
        self.executable = executable
        super().__init__(f"Executable not found: '{executable}'. Is it installed and on PATH?")


class WorkingDirectoryError(TerminalException):
    """Raised when the working directory does not exist or is not accessible."""
    def __init__(self, path: str, reason: str = "does not exist"):
        self.path = path
        super().__init__(f"Working directory '{path}' {reason}.")


class WorkspaceError(TerminalException):
    """Raised when workspace operations fail (open, switch, detect)."""
    def __init__(self, path: str, reason: str):
        self.path = path
        super().__init__(f"Workspace error for '{path}': {reason}")


class SessionNotFoundError(TerminalException):
    """Raised when a referenced session_id does not exist."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session '{session_id}' not found.")


class ProcessGroupError(TerminalException):
    """Raised when a process group operation fails."""
    def __init__(self, group_id: str, reason: str):
        self.group_id = group_id
        super().__init__(f"Process group '{group_id}': {reason}")


class ProcessAlreadyRunningError(TerminalException):
    """Raised when attempting to start an already-running session."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session '{session_id}' is already running.")


class InteractiveInputError(TerminalException):
    """Raised when stdin input cannot be sent to a process."""
    def __init__(self, session_id: str, reason: str):
        self.session_id = session_id
        super().__init__(f"Cannot send input to session '{session_id}': {reason}")


class ShellNotFoundError(TerminalException):
    """Raised when the requested shell profile cannot be resolved to an executable."""
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        super().__init__(
            f"Shell profile '{profile_id}' could not be resolved. "
            f"Is the shell installed?"
        )


class WorkflowError(TerminalException):
    """Raised when a developer workflow fails during expansion or execution."""
    def __init__(self, workflow_id: str, step: int, reason: str):
        self.workflow_id = workflow_id
        self.step = step
        super().__init__(
            f"Workflow '{workflow_id}' failed at step {step}: {reason}"
        )


class EnvironmentDetectionError(TerminalException):
    """Raised when environment detection fails critically."""
    def __init__(self, tool: str, reason: str):
        self.tool = tool
        super().__init__(f"Failed to detect environment for '{tool}': {reason}")
