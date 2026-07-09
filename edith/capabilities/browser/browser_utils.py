import re
from typing import Optional
from edith.config.settings import settings
from urllib.parse import urlparse

# Common TLDs for matching
TLD_REGEX = re.compile(r'\.(com|org|net|edu|gov|io|co|ai|dev|app|uk|us|ca|au)$', re.IGNORECASE)

# IPv4 address matching
IP_REGEX = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?::[0-9]{1,5})?$')

def is_url(query: str) -> bool:
    """
    Robustly determines if a string is intended to be a URL.
    """
    query = query.strip()
    
    # Explicit schemes
    if query.startswith(('http://', 'https://', 'file://')):
        return True
        
    # Localhost
    if query.startswith('localhost'):
        return True
        
    # IP Addresses (e.g. 127.0.0.1, 192.168.1.1:8080)
    if IP_REGEX.match(query):
        return True
        
    # Look for domain.tld structure
    # Check if there is a known TLD
    domain_part = query.split('/')[0].split(':')[0]
    if TLD_REGEX.search(domain_part):
        return True
        
    return False

def format_url(url_or_query: str) -> str:
    """
    Takes an input that has been identified as a URL or an alias and formats it correctly.
    """
    # Check aliases first
    lower_query = url_or_query.strip().lower()
    if lower_query in settings.quick_sites:
        return settings.quick_sites[lower_query]
        
    url_or_query = url_or_query.strip()
    
    if url_or_query.startswith(('http://', 'https://', 'file://')):
        return url_or_query
        
    return f"https://{url_or_query}"
