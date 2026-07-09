import pytest
from edith.capabilities.browser.browser_utils import is_url, format_url
from edith.config.settings import settings

def test_is_url():
    # Valid URLs
    assert is_url("https://github.com") == True
    assert is_url("github.com") == True
    assert is_url("localhost") == True
    assert is_url("localhost:3000") == True
    assert is_url("127.0.0.1") == True
    assert is_url("192.168.1.100:8080") == True
    assert is_url("file:///C:/Users/test/index.html") == True
    assert is_url("domain.ai") == True
    
    # Search queries
    assert is_url("how to bake a cake") == False
    assert is_url("github") == False
    assert is_url("123 test street") == False

def test_format_url():
    # Aliases
    settings.quick_sites = {"github": "https://github.com", "localhost": "http://localhost:3000"}
    assert format_url("github") == "https://github.com"
    assert format_url("GITHUB") == "https://github.com"
    
    # Direct URLs
    assert format_url("example.com") == "https://example.com"
    assert format_url("http://example.com") == "http://example.com"
    assert format_url("127.0.0.1") == "https://127.0.0.1" # Browser might fallback to http if https fails, but prepending https is standard.
