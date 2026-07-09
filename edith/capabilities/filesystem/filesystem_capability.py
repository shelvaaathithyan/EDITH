from typing import Any, Dict
from pathlib import Path
import logging

from edith.core.interfaces.executor import IToolExecutor
from edith.ai.models import ResolvedExecutionPlan, ToolResult
from edith.capabilities.filesystem.filesystem_controller import FilesystemController
from edith.capabilities.filesystem.filesystem_utils import PathResolver
from edith.capabilities.filesystem.filesystem_search import SearchService
from edith.interaction.context.context_manager import context_manager

logger = logging.getLogger(__name__)

class FilesystemCapability(IToolExecutor):
    def __init__(self):
        self.controller = FilesystemController()
        
    def get_manifest(self) -> Dict[str, Any]:
        from edith.capabilities.filesystem.filesystem_manifest import MANIFEST
        return MANIFEST
        
    def _resolve_paths(self, raw_paths) -> list[Path]:
        if not raw_paths:
            return []
        if isinstance(raw_paths, str):
            raw_paths = [raw_paths]
            
        # Get active folder from context for relative path resolution
        ctx_data = context_manager.get_context()
        active_folder = ctx_data.get("last_folder")
        
        return [PathResolver.resolve(p, current_context=active_folder) for p in raw_paths]

    def execute(self, plan: ResolvedExecutionPlan) -> ToolResult:
        if not plan.steps:
            return ToolResult(success=False, message="No execution steps provided.")
            
        step = plan.steps[0]
        args = step.arguments
        action = args.get("action")
        
        try:
            # We intercept "preview" flags
            preview = args.get("preview", False)
            
            if action == "create_folder":
                paths = self._resolve_paths(args.get("paths", args.get("path")))
                result = self.controller.create_folder(paths, preview=preview)
                if not preview and result:
                    context_manager.update_context({"last_folder": result[-1].path})
                return ToolResult(success=True, message=f"Created {len(paths)} folders.", data={"result": [r.model_dump() for r in result]})
                
            elif action == "create_file":
                paths = self._resolve_paths(args.get("paths", args.get("path")))
                result = self.controller.create_file(paths, preview=preview)
                if not preview and result:
                    context_manager.update_context({"last_file": result[-1].path})
                return ToolResult(success=True, message=f"Created {len(paths)} files.", data={"result": [r.model_dump() for r in result]})
                
            elif action == "delete":
                paths = self._resolve_paths(args.get("paths", args.get("path")))
                permanent = args.get("permanent", False)
                result = self.controller.delete(paths, permanent=permanent, preview=preview)
                msg = f"{'Permanently deleted' if permanent else 'Recycled'} {len(paths)} items."
                return ToolResult(success=True, message=msg, data={"result": result if preview else result})
                
            elif action == "rename":
                paths = self._resolve_paths(args.get("paths", args.get("path")))
                new_names = args.get("new_names") or [args.get("new_name")]
                result = self.controller.rename(paths, new_names, preview=preview)
                if not preview and result:
                    context_manager.update_context({"last_file" if result[-1].model_dump().get("extension") else "last_folder": result[-1].path})
                return ToolResult(success=True, message=f"Renamed {len(paths)} items.", data={"result": [r.model_dump() for r in result] if not preview else result.model_dump()})

            elif action == "move":
                paths = self._resolve_paths(args.get("paths", args.get("path")))
                dest = self._resolve_paths(args.get("dest"))[0]
                result = self.controller.move(paths, dest, preview=preview)
                if not preview and result:
                    context_manager.update_context({"last_folder": str(dest)})
                return ToolResult(success=True, message=f"Moved {len(paths)} items.", data={"result": [r.model_dump() for r in result] if not preview else result.model_dump()})

            elif action == "copy":
                paths = self._resolve_paths(args.get("paths", args.get("path")))
                dest = self._resolve_paths(args.get("dest"))[0]
                result = self.controller.copy(paths, dest, preview=preview)
                return ToolResult(success=True, message=f"Copied {len(paths)} items.", data={"result": [r.model_dump() for r in result] if not preview else result.model_dump()})

            elif action == "read_text":
                path = self._resolve_paths(args.get("path"))[0]
                text = self.controller.read_text(path)
                return ToolResult(success=True, message="File read successfully.", data={"text": text})

            elif action == "write_text":
                path = self._resolve_paths(args.get("path"))[0]
                text = args.get("text", "")
                result = self.controller.write_text(path, text)
                return ToolResult(success=True, message="File written successfully.", data={"result": result.model_dump()})

            elif action == "append_text":
                path = self._resolve_paths(args.get("path"))[0]
                text = args.get("text", "")
                result = self.controller.append_text(path, text)
                return ToolResult(success=True, message="File appended successfully.", data={"result": result.model_dump()})

            elif action == "compress_zip":
                paths = self._resolve_paths(args.get("paths", args.get("path")))
                dest = self._resolve_paths(args.get("dest"))[0]
                result = self.controller.compress_zip(paths, dest, preview=preview)
                if not preview:
                    context_manager.update_context({"last_file": result.path})
                return ToolResult(success=True, message="Compressed successfully.", data={"result": result.model_dump()})

            elif action == "extract_zip":
                path = self._resolve_paths(args.get("path"))[0]
                dest = self._resolve_paths(args.get("dest"))[0]
                result = self.controller.extract_zip(path, dest, preview=preview)
                if not preview:
                    context_manager.update_context({"last_folder": result.path})
                return ToolResult(success=True, message="Extracted successfully.", data={"result": result.model_dump()})

            elif action == "list_directory":
                path = self._resolve_paths(args.get("path"))[0]
                result = self.controller.list_directory(path)
                return ToolResult(success=True, message="Directory listed.", data={"result": result.model_dump()})

            elif action == "search":
                base = self._resolve_paths(args.get("base_dir", "here"))[0]
                query = args.get("query")
                match_ext = args.get("match_extension")
                result = SearchService.search(base, query, match_extension=match_ext)
                return ToolResult(success=True, message=f"Found {len(result.matches)} matches.", data={"result": result.model_dump()})

            elif action == "restore":
                path_str = args.get("path")
                success = self.controller.restore(path_str)
                return ToolResult(success=success, message="Restore " + ("successful" if success else "failed"))

            return ToolResult(success=False, message=f"Unknown filesystem action: {action}")
            
        except Exception as e:
            logger.exception(f"Filesystem error: {e}")
            return ToolResult(success=False, message=f"Error: {str(e)}")
