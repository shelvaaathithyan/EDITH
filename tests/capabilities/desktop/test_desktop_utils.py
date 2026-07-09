import pytest
from edith.capabilities.desktop.desktop_utils import resolve_alias
from edith.config.settings import settings

def test_resolve_alias():
    # Setup aliases
    settings.app_aliases = {
        "vscode": "Code.exe",
        "cursor": "Cursor.exe",
        "music": "Spotify.exe",
        "discord": "Update.exe --processStart Discord.exe"
    }
    
    # Test configured aliases (case insensitive)
    assert resolve_alias("vscode") == "Code.exe"
    assert resolve_alias("VSCode") == "Code.exe"
    assert resolve_alias("music") == "Spotify.exe"
    assert resolve_alias("Discord") == "Update.exe --processStart Discord.exe"
    
    # Test guessing (not in aliases)
    assert resolve_alias("paint") == "paint.exe"
    assert resolve_alias("calc") == "calc.exe"
    
    # Test already ends in .exe
    assert resolve_alias("notepad.exe") == "notepad.exe"
