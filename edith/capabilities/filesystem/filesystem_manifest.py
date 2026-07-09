from edith.permission.permission_models import RiskLevel

MANIFEST = {
    "capability_id": "core.filesystem",
    "name": "Filesystem Capability",
    "version": "1.0",
    "author": "EDITH Core Team",
    "description": "Secure local filesystem operations supporting files, folders, zip archives, and comprehensive batch management.",
    "dependencies": ["send2trash", "winshell"],
    "supported_platforms": ["Windows"],
    "minimum_python_version": "3.11",
    "supported_actions": [
        "create_folder", "create_file", "open_folder", "open_file", "rename", "move", "copy",
        "delete", "recycle", "restore", "read_text", "append_text", "write_text", "search",
        "compress_zip", "extract_zip", "list_directory", "watch_directory", "preview"
    ],
    "risk_matrix": {
        "create_folder": RiskLevel.LOW,
        "create_file": RiskLevel.LOW,
        "open_folder": RiskLevel.LOW,
        "open_file": RiskLevel.LOW,
        "list_directory": RiskLevel.LOW,
        "search": RiskLevel.LOW,
        "read_text": RiskLevel.LOW,
        "preview": RiskLevel.LOW,
        "rename": RiskLevel.MEDIUM,
        "move": RiskLevel.MEDIUM,
        "copy": RiskLevel.MEDIUM,
        "compress_zip": RiskLevel.MEDIUM,
        "extract_zip": RiskLevel.MEDIUM,
        "append_text": RiskLevel.MEDIUM,
        "recycle": RiskLevel.MEDIUM,
        "restore": RiskLevel.MEDIUM,
        "write_text": RiskLevel.HIGH, # Overwrite is high risk
        "delete": RiskLevel.HIGH,     # Explicit deletion
        "empty_recycle_bin": RiskLevel.CRITICAL
    }
}
