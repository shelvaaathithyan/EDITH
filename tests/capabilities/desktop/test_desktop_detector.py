import pytest
from unittest.mock import patch, MagicMock
from edith.capabilities.desktop.desktop_detector import DesktopDetector

@pytest.fixture
def detector():
    d = DesktopDetector()
    d._cache.clear()
    d._is_loaded = False
    return d

@patch('edith.capabilities.desktop.desktop_detector.winreg')
@patch('edith.capabilities.desktop.desktop_detector.os.path.exists')
def test_load_index(mock_exists, mock_winreg, detector):
    # Setup mock registry
    mock_exists.return_value = True
    
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
    mock_winreg.QueryInfoKey.return_value = (1, 0, 0)
    mock_winreg.EnumKey.return_value = "Code.exe"
    mock_winreg.QueryValueEx.return_value = (r"C:\Program Files\VSCode\Code.exe", 1)
    
    # Execute
    detector.load_index()
    
    # Verify cache
    assert "code.exe" in detector._cache
    assert detector._cache["code.exe"].path == r"C:\Program Files\VSCode\Code.exe"

@patch('edith.capabilities.desktop.desktop_detector.shutil.which')
def test_find_executable_path(mock_which, detector):
    # Setup mock path
    mock_which.return_value = r"C:\Windows\System32\calc.exe"
    
    # Execute
    path = detector.find_executable("calc.exe")
    
    # Verify
    assert path == r"C:\Windows\System32\calc.exe"

def test_find_executable_with_args(detector):
    # Should not attempt to resolve absolute path for command with args
    cmd = "Update.exe --processStart Discord.exe"
    path = detector.find_executable(cmd)
    assert path == cmd
