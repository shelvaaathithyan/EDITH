"""
Search Resolver.
Translates natural language intents into structured search commands.
"""

from edith.capabilities.spotify.spotify_models import Track

class SearchResolver:
    def resolve_track(self, query: str) -> Track:
        # Simple stub: in reality this might hit an API or use NLP
        return Track(title=query, artist="Unknown")
        
    def resolve_album(self, query: str) -> str:
        return query
        
    def resolve_artist(self, query: str) -> str:
        return query
        
    def resolve_playlist(self, query: str) -> str:
        return query
