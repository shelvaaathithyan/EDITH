from edith.permission.permission_models import RiskLevel

MANIFEST = {
    "id": "browser",
    "name": "Browser Control",
    "version": "1.0.0",
    "author": "EDITH Core",
    "description": "Launches the user's default browser and performs web navigation/search.",
    "supported_platforms": ["Windows", "macOS", "Linux"],
    "dependencies": [],
    "supported_actions": [
        "search",
        "navigate",
        "launch"
    ],
    "risk_matrix": {
        "search": RiskLevel.LOW,
        "navigate": RiskLevel.LOW,
        "launch": RiskLevel.LOW
    },
    "required_permissions": []
}
