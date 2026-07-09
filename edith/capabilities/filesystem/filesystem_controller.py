import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Optional, Union
from datetime import datetime
from send2trash import send2trash
import winshell

from edith.core.events import event_bus
from edith.capabilities.filesystem.filesystem_models import (
    FileObject, FolderObject, ZipObject, DirectoryListing, PreviewStats
)
from edith.capabilities.filesystem.filesystem_events import FilesystemEvent
from edith.capabilities.filesystem.filesystem_validator import FilesystemValidator

class FilesystemController:
    """Core execution engine for EDITH Filesystem Capability."""
    
    def _to_file_object(self, path: Path) -> FileObject:
        stat = path.stat()
        return FileObject(
            name=path.name,
            path=str(path.resolve()),
            extension=path.suffix,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            is_readonly=not os.access(path, os.W_OK)
        )
        
    def _to_folder_object(self, path: Path, count_items: bool = False) -> FolderObject:
        stat = path.stat()
        item_count = len(list(path.iterdir())) if count_items else None
        return FolderObject(
            name=path.name,
            path=str(path.resolve()),
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            item_count=item_count
        )

    def create_folder(self, paths: List[Path], preview: bool = False) -> Union[PreviewStats, List[FolderObject]]:
        if preview:
            return PreviewStats(folder_count=len(paths), action="create_folder")
            
        results = []
        for path in paths:
            FilesystemValidator.validate_name(path.name)
            path.mkdir(parents=True, exist_ok=True)
            folder = self._to_folder_object(path)
            results.append(folder)
            event_bus.publish(FilesystemEvent.FOLDER_CREATED, {"folder": folder.model_dump()})
        return results

    def create_file(self, paths: List[Path], preview: bool = False) -> Union[PreviewStats, List[FileObject]]:
        if preview:
            return PreviewStats(file_count=len(paths), action="create_file")
            
        results = []
        for path in paths:
            FilesystemValidator.validate_name(path.name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
            file_obj = self._to_file_object(path)
            results.append(file_obj)
            event_bus.publish(FilesystemEvent.FILE_CREATED, {"file": file_obj.model_dump()})
        return results

    def delete(self, paths: List[Path], permanent: bool = False, preview: bool = False) -> Union[PreviewStats, List[str]]:
        if preview:
            files, folders, size = 0, 0, 0
            for path in paths:
                if path.is_file():
                    files += 1
                    size += path.stat().st_size
                elif path.is_dir():
                    for item in path.rglob('*'):
                        if item.is_file():
                            files += 1
                            size += item.stat().st_size
                        elif item.is_dir():
                            folders += 1
                    folders += 1
            return PreviewStats(file_count=files, folder_count=folders, total_size_bytes=size, action="delete" if permanent else "recycle")
            
        deleted_paths = []
        for path in paths:
            FilesystemValidator.validate_exists(path)
            FilesystemValidator.validate_writable(path)
            FilesystemValidator.validate_lock(path)
            
            str_path = str(path.resolve())
            is_folder = path.is_dir()
            
            if permanent:
                if is_folder:
                    shutil.rmtree(path)
                else:
                    path.unlink()
            else:
                send2trash(str_path)
                
            deleted_paths.append(str_path)
            event = FilesystemEvent.FOLDER_DELETED if is_folder else FilesystemEvent.FILE_DELETED
            event_bus.publish(event, {"path": str_path, "permanent": permanent})
            
        return deleted_paths

    def rename(self, src_paths: List[Path], new_names: List[str], preview: bool = False) -> Union[PreviewStats, List[Union[FileObject, FolderObject]]]:
        if preview:
            return PreviewStats(file_count=len([p for p in src_paths if p.is_file()]), folder_count=len([p for p in src_paths if p.is_dir()]), action="rename")
            
        if len(src_paths) != len(new_names):
            raise ValueError("Number of sources must match number of new names.")
            
        results = []
        for src, name in zip(src_paths, new_names):
            FilesystemValidator.validate_exists(src)
            FilesystemValidator.validate_name(name)
            
            dst = src.parent / name
            FilesystemValidator.validate_not_exists(dst)
            FilesystemValidator.validate_writable(src)
            FilesystemValidator.validate_lock(src)
            
            src.rename(dst)
            
            is_folder = dst.is_dir()
            obj = self._to_folder_object(dst) if is_folder else self._to_file_object(dst)
            results.append(obj)
            
            event_bus.publish(FilesystemEvent.FILE_RENAMED, {"src": str(src), "dst": str(dst)})
            
        return results

    def move(self, src_paths: List[Path], dest_dir: Path, preview: bool = False) -> Union[PreviewStats, List[Union[FileObject, FolderObject]]]:
        if preview:
            return PreviewStats(file_count=len([p for p in src_paths if p.is_file()]), folder_count=len([p for p in src_paths if p.is_dir()]), action="move")
            
        dest_dir.mkdir(parents=True, exist_ok=True)
        event_bus.publish(FilesystemEvent.MOVE_STARTED, {"count": len(src_paths), "dest": str(dest_dir)})
        
        results = []
        for src in src_paths:
            FilesystemValidator.validate_exists(src)
            FilesystemValidator.validate_move(src, dest_dir)
            FilesystemValidator.validate_writable(src)
            FilesystemValidator.validate_lock(src)
            
            dst = dest_dir / src.name
            shutil.move(str(src), str(dst))
            
            obj = self._to_folder_object(dst) if dst.is_dir() else self._to_file_object(dst)
            results.append(obj)
            event_bus.publish(FilesystemEvent.FILE_MOVED, {"src": str(src), "dst": str(dst)})
            
        event_bus.publish(FilesystemEvent.MOVE_COMPLETED, {"count": len(src_paths), "dest": str(dest_dir)})
        return results

    def copy(self, src_paths: List[Path], dest_dir: Path, preview: bool = False) -> Union[PreviewStats, List[Union[FileObject, FolderObject]]]:
        if preview:
            return PreviewStats(file_count=len([p for p in src_paths if p.is_file()]), folder_count=len([p for p in src_paths if p.is_dir()]), action="copy")
            
        dest_dir.mkdir(parents=True, exist_ok=True)
        event_bus.publish(FilesystemEvent.COPY_STARTED, {"count": len(src_paths), "dest": str(dest_dir)})
        
        results = []
        for src in src_paths:
            FilesystemValidator.validate_exists(src)
            FilesystemValidator.validate_move(src, dest_dir)
            
            dst = dest_dir / src.name
            if src.is_dir():
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
                obj = self._to_folder_object(dst)
            else:
                shutil.copy2(str(src), str(dst))
                obj = self._to_file_object(dst)
                
            results.append(obj)
            event_bus.publish(FilesystemEvent.FILE_COPIED, {"src": str(src), "dst": str(dst)})
            
        event_bus.publish(FilesystemEvent.COPY_COMPLETED, {"count": len(src_paths), "dest": str(dest_dir)})
        return results

    def read_text(self, path: Path) -> str:
        FilesystemValidator.validate_exists(path)
        return path.read_text(encoding='utf-8', errors='ignore')

    def write_text(self, path: Path, text: str) -> FileObject:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            FilesystemValidator.validate_writable(path)
        path.write_text(text, encoding='utf-8')
        return self._to_file_object(path)

    def append_text(self, path: Path, text: str) -> FileObject:
        FilesystemValidator.validate_exists(path)
        FilesystemValidator.validate_writable(path)
        with path.open("a", encoding="utf-8") as f:
            f.write(text)
        return self._to_file_object(path)

    def compress_zip(self, src_paths: List[Path], dest_zip: Path, preview: bool = False) -> Union[PreviewStats, ZipObject]:
        if preview:
            files, size = 0, 0
            for p in src_paths:
                if p.is_file(): files += 1; size += p.stat().st_size
                elif p.is_dir():
                    for item in p.rglob('*'):
                        if item.is_file(): files += 1; size += item.stat().st_size
            return PreviewStats(file_count=files, total_size_bytes=size, action="compress")
            
        dest_zip.parent.mkdir(parents=True, exist_ok=True)
        FilesystemValidator.validate_not_exists(dest_zip)
        
        with zipfile.ZipFile(dest_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for src in src_paths:
                FilesystemValidator.validate_exists(src)
                if src.is_file():
                    zipf.write(src, src.name)
                elif src.is_dir():
                    for file_path in src.rglob('*'):
                        if file_path.is_file():
                            zipf.write(file_path, file_path.relative_to(src.parent))
                            
        event_bus.publish(FilesystemEvent.ZIP_CREATED, {"zip": str(dest_zip)})
        return ZipObject(
            name=dest_zip.name,
            path=str(dest_zip.resolve()),
            size_bytes=dest_zip.stat().st_size,
            created_at=datetime.fromtimestamp(dest_zip.stat().st_ctime),
            item_count=len(zipfile.ZipFile(dest_zip, 'r').infolist())
        )

    def extract_zip(self, zip_path: Path, dest_dir: Path, preview: bool = False) -> Union[PreviewStats, FolderObject]:
        FilesystemValidator.validate_exists(zip_path)
        if preview:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                return PreviewStats(file_count=len(zipf.infolist()), action="extract")
                
        dest_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(dest_dir)
            
        event_bus.publish(FilesystemEvent.ZIP_EXTRACTED, {"zip": str(zip_path), "dest": str(dest_dir)})
        return self._to_folder_object(dest_dir, count_items=True)
        
    def restore(self, path_str: str) -> bool:
        """Attempt to undelete using winshell (Windows only)."""
        import winshell
        try:
            recycle_bin = winshell.recycle_bin()
            for item in recycle_bin:
                if str(path_str).lower() in str(item.original_filename()).lower():
                    item.undelete()
                    return True
        except Exception:
            pass
        return False
        
    def list_directory(self, path: Path) -> DirectoryListing:
        FilesystemValidator.validate_exists(path)
        files = []
        folders = []
        for item in path.iterdir():
            try:
                if item.is_file():
                    files.append(self._to_file_object(item))
                elif item.is_dir():
                    folders.append(self._to_folder_object(item))
            except PermissionError:
                continue
        return DirectoryListing(path=str(path.resolve()), folders=folders, files=files)
