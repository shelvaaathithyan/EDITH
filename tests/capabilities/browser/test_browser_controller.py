import pytest
from unittest.mock import patch, MagicMock
from edith.capabilities.browser.browser_controller import BrowserController
from edith.capabilities.browser.browser_exceptions import BrowserLaunchError

@pytest.fixture
def controller():
    return BrowserController()

@patch('edith.capabilities.browser.browser_controller.subprocess.Popen')
@patch('edith.capabilities.browser.browser_controller.BrowserController._get_browser_path')
def test_launch_subprocess(mock_get_path, mock_popen, controller):
    # Setup mock
    mock_get_path.return_value = r"C:\Path\To\chrome.exe"
    
    # Execute
    result = controller.launch("https://github.com", browser="chrome")
    
    # Verify
    assert result["browser"] == "chrome"
    assert result["url"] == "https://github.com"
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert args[0] == [r"C:\Path\To\chrome.exe", "https://github.com"]

@patch('edith.capabilities.browser.browser_controller.webbrowser.open')
@patch('edith.capabilities.browser.browser_controller.BrowserController._get_browser_path')
def test_launch_fallback(mock_get_path, mock_webbrowser, controller):
    # Setup mock to simulate browser not found in registry
    mock_get_path.return_value = None
    mock_webbrowser.return_value = True
    
    # Execute
    result = controller.launch("https://github.com", browser="chrome")
    
    # Verify
    assert result["browser"] == "system default"
    mock_webbrowser.assert_called_once_with("https://github.com")

@patch('edith.capabilities.browser.browser_controller.webbrowser.open')
def test_launch_failure(mock_webbrowser, controller):
    # Setup mock to simulate default browser failure
    mock_webbrowser.return_value = False
    
    # Execute and verify exception
    with pytest.raises(BrowserLaunchError):
        controller.launch("https://github.com")
