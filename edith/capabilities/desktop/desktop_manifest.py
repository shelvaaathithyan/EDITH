from edith.permission.permission_models import RiskLevel

MANIFEST = {
    "id": "desktop",
    "name": "Desktop Control",
    "version": "1.0.0",
    "author": "EDITH Core",
    "description": "Manages windows and applications on the local desktop.",
    "supported_platforms": ["Windows"],
    "dependencies": ["psutil", "pywin32"],
    "supported_actions": [
        "launch",
        "close",
        "focus",
        "minimize",
        "maximize",
        "restore"
    ],
    "risk_matrix": {
        "launch": RiskLevel.LOW,
        "close": RiskLevel.MEDIUM,
        "focus": RiskLevel.LOW,
        "minimize": RiskLevel.LOW,
        "maximize": RiskLevel.LOW,
        "restore": RiskLevel.LOW
    },
    "required_permissions": []
}
