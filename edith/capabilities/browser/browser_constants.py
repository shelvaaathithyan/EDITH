from typing import Dict
from edith.config.settings import settings

SEARCH_ENGINES: Dict[str, str] = {
    "google": "https://www.google.com/search?q={query}",
    "bing": "https://www.bing.com/search?q={query}",
    "duckduckgo": "https://duckduckgo.com/?q={query}",
    "youtube": "https://www.youtube.com/results?search_query={query}",
    "github": "https://github.com/search?q={query}",
    "stackoverflow": "https://stackoverflow.com/search?q={query}",
    "reddit": "https://www.reddit.com/search/?q={query}",
    "chatgpt": "https://chat.openai.com/?q={query}"
}

def get_search_url(engine: str, query: str) -> str:
    engine = engine.lower() if engine else settings.default_search_engine
    template = SEARCH_ENGINES.get(engine, SEARCH_ENGINES.get(settings.default_search_engine))
    from urllib.parse import quote_plus
    return template.format(query=quote_plus(query))
