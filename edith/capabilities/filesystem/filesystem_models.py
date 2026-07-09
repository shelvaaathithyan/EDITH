from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from pathlib import Path

class FileObject(BaseModel):
    name: str
    path: str
    extension: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    is_readonly: bool

class FolderObject(BaseModel):
    name: str
    path: str
    created_at: datetime
    modified_at: datetime
    item_count: Optional[int] = None

class ZipObject(BaseModel):
    name: str
    path: str
    size_bytes: int
    created_at: datetime
    item_count: int

class DirectoryListing(BaseModel):
    path: str
    folders: List[FolderObject]
    files: List[FileObject]

class SearchResult(BaseModel):
    query: str
    matches: List[FileObject | FolderObject]

class PreviewStats(BaseModel):
    file_count: int = 0
    folder_count: int = 0
    total_size_bytes: int = 0
    action: str
