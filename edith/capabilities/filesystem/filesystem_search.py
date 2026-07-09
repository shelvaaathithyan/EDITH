import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from edith.capabilities.filesystem.filesystem_models import FileObject, FolderObject, SearchResult

class SearchService:
    """Advanced search engine for EDITH Filesystem Capability."""
    
    @staticmethod
    def search(
        base_dir: Path,
        query: str,
        match_extension: Optional[str] = None,
        use_regex: bool = False,
        use_wildcard: bool = False,
        modified_after: Optional[datetime] = None,
        min_size_bytes: Optional[int] = None
    ) -> SearchResult:
        
        matches = []
        if not base_dir.exists() or not base_dir.is_dir():
            return SearchResult(query=query, matches=matches)
            
        regex_pattern = None
        if use_regex:
            regex_pattern = re.compile(query)
        elif use_wildcard:
            import fnmatch
            regex_pattern = re.compile(fnmatch.translate(query))
        else:
            query_lower = query.lower()

        for item in base_dir.rglob('*'):
            try:
                # Filter by name
                matched = False
                if regex_pattern:
                    if regex_pattern.search(item.name):
                        matched = True
                else:
                    if query_lower in item.name.lower():
                        matched = True
                        
                if not matched:
                    continue
                    
                # Filter by extension
                if match_extension and item.is_file():
                    if item.suffix.lower() != match_extension.lower():
                        continue
                        
                stat = item.stat()
                
                # Filter by modified date
                if modified_after:
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    if mtime < modified_after:
                        continue
                        
                # Filter by size
                if min_size_bytes is not None and item.is_file():
                    if stat.st_size < min_size_bytes:
                        continue

                # Build object
                if item.is_file():
                    matches.append(FileObject(
                        name=item.name,
                        path=str(item.resolve()),
                        extension=item.suffix,
                        size_bytes=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime),
                        is_readonly=not os.access(item, os.W_OK)
                    ))
                elif item.is_dir():
                    matches.append(FolderObject(
                        name=item.name,
                        path=str(item.resolve()),
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime)
                    ))
            except (PermissionError, FileNotFoundError):
                # Skip inaccessible files during deep search
                continue
                
        return SearchResult(query=query, matches=matches)

import os # Needed above
