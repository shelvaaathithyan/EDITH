from typing import Any, Dict, List
from pathlib import Path
import logging

from edith.sdk.capability import (
    BaseCapability,
    CapabilityManifest,
    CapabilityResult,
    CapabilityValidationError
)
from edith.permission.permission_models import RiskLevel
from edith.capabilities.filesystem.filesystem_controller import FilesystemController
from edith.capabilities.filesystem.filesystem_utils import PathResolver
from edith.capabilities.filesystem.filesystem_search import SearchService
from edith.capabilities.filesystem.filesystem_manifest import MANIFEST

logger = logging.getLogger(__name__)

class FilesystemCapability(BaseCapability):
    def get_manifest(self) -> CapabilityManifest:
        # Convert raw dict manifest to typed Manifest
        return CapabilityManifest(
            id="filesystem",
            name=MANIFEST.get("name", "Filesystem"),
            version=MANIFEST.get("version", "1.0"),
            author=MANIFEST.get("author", "EDITH"),
            description=MANIFEST.get("description", ""),
            supported_platforms=MANIFEST.get("supported_platforms", []),
            dependencies=MANIFEST.get("dependencies", []),
            supported_actions=MANIFEST.get("supported_actions", []),
            risk_matrix=MANIFEST.get("risk_matrix", {}),
            required_permissions=MANIFEST.get("required_permissions", [])
        )

    def _do_initialize(self) -> None:
        self.controller = FilesystemController()
        
        # Register Actions
        self.register_action("create_folder", self._action_create_folder)
        self.register_action("create_file", self._action_create_file)
        self.register_action("delete", self._action_delete)
        self.register_action("rename", self._action_rename)
        self.register_action("move", self._action_move)
        self.register_action("copy", self._action_copy)
        self.register_action("read_text", self._action_read_text)
        self.register_action("write_text", self._action_write_text)
        self.register_action("append_text", self._action_append_text)
        self.register_action("compress_zip", self._action_compress_zip)
        self.register_action("extract_zip", self._action_extract_zip)
        self.register_action("list_directory", self._action_list_directory)
        self.register_action("search", self._action_search)
        self.register_action("restore", self._action_restore)

    def _resolve_paths(self, raw_paths) -> list[Path]:
        if not raw_paths:
            return []
        if isinstance(raw_paths, str):
            raw_paths = [raw_paths]
            
        # Get active folder from context using BaseCapability.context
        active_folder = self.context.get("last_folder")
        
        return [PathResolver.resolve(p, current_context=active_folder) for p in raw_paths]

    # --- ACTION HANDLERS ---

    def _action_create_folder(self, args: Dict[str, Any]) -> CapabilityResult:
        preview = args.get("preview", False)
        paths = self._resolve_paths(args.get("paths", args.get("path")))
        result = self.controller.create_folder(paths, preview=preview)
        if not preview and result:
            self.context.update({"last_folder": result[-1].path})
        return CapabilityResult(success=True, capability=self._manifest.id, action="create_folder", message=f"Created {len(paths)} folders.", structured_data={"result": [r.model_dump() for r in result]})

    def _action_create_file(self, args: Dict[str, Any]) -> CapabilityResult:
        preview = args.get("preview", False)
        paths = self._resolve_paths(args.get("paths", args.get("path")))
        result = self.controller.create_file(paths, preview=preview)
        if not preview and result:
            self.context.update({"last_file": result[-1].path})
        return CapabilityResult(success=True, capability=self._manifest.id, action="create_file", message=f"Created {len(paths)} files.", structured_data={"result": [r.model_dump() for r in result]})

    def _action_delete(self, args: Dict[str, Any]) -> CapabilityResult:
        preview = args.get("preview", False)
        paths = self._resolve_paths(args.get("paths", args.get("path")))
        permanent = args.get("permanent", False)
        result = self.controller.delete(paths, permanent=permanent, preview=preview)
        msg = f"{'Permanently deleted' if permanent else 'Recycled'} {len(paths)} items."
        return CapabilityResult(success=True, capability=self._manifest.id, action="delete", message=msg, structured_data={"result": result if preview else result})

    def _action_rename(self, args: Dict[str, Any]) -> CapabilityResult:
        preview = args.get("preview", False)
        paths = self._resolve_paths(args.get("paths", args.get("path")))
        new_names = args.get("new_names") or [args.get("new_name")]
        result = self.controller.rename(paths, new_names, preview=preview)
        if not preview and result:
            self.context.update({"last_file" if result[-1].model_dump().get("extension") else "last_folder": result[-1].path})
        return CapabilityResult(success=True, capability=self._manifest.id, action="rename", message=f"Renamed {len(paths)} items.", structured_data={"result": [r.model_dump() for r in result] if not preview else result.model_dump()})

    def _action_move(self, args: Dict[str, Any]) -> CapabilityResult:
        preview = args.get("preview", False)
        paths = self._resolve_paths(args.get("paths", args.get("path")))
        dest_raw = args.get("dest")
        if not dest_raw: raise CapabilityValidationError("Destination path required.")
        dest = self._resolve_paths(dest_raw)[0]
        result = self.controller.move(paths, dest, preview=preview)
        if not preview and result:
            self.context.update({"last_folder": str(dest)})
        return CapabilityResult(success=True, capability=self._manifest.id, action="move", message=f"Moved {len(paths)} items.", structured_data={"result": [r.model_dump() for r in result] if not preview else result.model_dump()})

    def _action_copy(self, args: Dict[str, Any]) -> CapabilityResult:
        preview = args.get("preview", False)
        paths = self._resolve_paths(args.get("paths", args.get("path")))
        dest_raw = args.get("dest")
        if not dest_raw: raise CapabilityValidationError("Destination path required.")
        dest = self._resolve_paths(dest_raw)[0]
        result = self.controller.copy(paths, dest, preview=preview)
        return CapabilityResult(success=True, capability=self._manifest.id, action="copy", message=f"Copied {len(paths)} items.", structured_data={"result": [r.model_dump() for r in result] if not preview else result.model_dump()})

    def _action_read_text(self, args: Dict[str, Any]) -> CapabilityResult:
        path = self._resolve_paths(args.get("path"))[0]
        text = self.controller.read_text(path)
        return CapabilityResult(success=True, capability=self._manifest.id, action="read_text", message="File read successfully.", structured_data={"text": text})

    def _action_write_text(self, args: Dict[str, Any]) -> CapabilityResult:
        path = self._resolve_paths(args.get("path"))[0]
        text = args.get("text", "")
        result = self.controller.write_text(path, text)
        return CapabilityResult(success=True, capability=self._manifest.id, action="write_text", message="File written successfully.", structured_data={"result": result.model_dump()})

    def _action_append_text(self, args: Dict[str, Any]) -> CapabilityResult:
        path = self._resolve_paths(args.get("path"))[0]
        text = args.get("text", "")
        result = self.controller.append_text(path, text)
        return CapabilityResult(success=True, capability=self._manifest.id, action="append_text", message="File appended successfully.", structured_data={"result": result.model_dump()})

    def _action_compress_zip(self, args: Dict[str, Any]) -> CapabilityResult:
        preview = args.get("preview", False)
        paths = self._resolve_paths(args.get("paths", args.get("path")))
        dest_raw = args.get("dest")
        if not dest_raw: raise CapabilityValidationError("Destination zip path required.")
        dest = self._resolve_paths(dest_raw)[0]
        result = self.controller.compress_zip(paths, dest, preview=preview)
        if not preview:
            self.context.update({"last_file": result.path})
        return CapabilityResult(success=True, capability=self._manifest.id, action="compress_zip", message="Compressed successfully.", structured_data={"result": result.model_dump()})

    def _action_extract_zip(self, args: Dict[str, Any]) -> CapabilityResult:
        preview = args.get("preview", False)
        path = self._resolve_paths(args.get("path"))[0]
        dest_raw = args.get("dest")
        if not dest_raw: raise CapabilityValidationError("Destination path required.")
        dest = self._resolve_paths(dest_raw)[0]
        result = self.controller.extract_zip(path, dest, preview=preview)
        if not preview:
            self.context.update({"last_folder": result.path})
        return CapabilityResult(success=True, capability=self._manifest.id, action="extract_zip", message="Extracted successfully.", structured_data={"result": result.model_dump()})

    def _action_list_directory(self, args: Dict[str, Any]) -> CapabilityResult:
        path = self._resolve_paths(args.get("path"))[0]
        result = self.controller.list_directory(path)
        return CapabilityResult(success=True, capability=self._manifest.id, action="list_directory", message="Directory listed.", structured_data={"result": result.model_dump()})

    def _action_search(self, args: Dict[str, Any]) -> CapabilityResult:
        base = self._resolve_paths(args.get("base_dir", "here"))[0]
        query = args.get("query")
        if not query: raise CapabilityValidationError("Search query required.")
        match_ext = args.get("match_extension")
        result = SearchService.search(base, query, match_extension=match_ext)
        return CapabilityResult(success=True, capability=self._manifest.id, action="search", message=f"Found {len(result.matches)} matches.", structured_data={"result": result.model_dump()})

    def _action_restore(self, args: Dict[str, Any]) -> CapabilityResult:
        path_str = args.get("path")
        if not path_str: raise CapabilityValidationError("Path to restore required.")
        success = self.controller.restore(path_str)
        return CapabilityResult(success=success, capability=self._manifest.id, action="restore", message="Restore " + ("successful" if success else "failed"))
