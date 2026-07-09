from edith.config.settings import settings

def resolve_alias(app_name: str) -> str:
    """
    Resolves a natural language application name into its executable alias using settings.
    Falls back to trying to guess the executable name (e.g. app_name.exe) if not found.
    """
    if not app_name:
        return ""
        
    lower_name = app_name.strip().lower()
    
    # Check aliases
    if lower_name in settings.app_aliases:
        return settings.app_aliases[lower_name]
        
    # If it already ends in .exe, return as is
    if lower_name.endswith('.exe'):
        return app_name
        
    # Otherwise, guess .exe
    # E.g. "paint" -> "paint.exe"
    return f"{app_name}.exe"
