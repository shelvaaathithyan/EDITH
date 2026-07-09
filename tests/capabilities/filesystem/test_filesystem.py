import pytest
from pathlib import Path
from edith.capabilities.filesystem.filesystem_controller import FilesystemController
from edith.capabilities.filesystem.filesystem_utils import PathResolver
from edith.capabilities.filesystem.filesystem_exceptions import InvalidPathError, DirectoryTraversalError

def test_path_resolver():
    assert PathResolver.resolve(".").resolve() == Path.cwd().resolve()
    with pytest.raises(InvalidPathError):
        PathResolver.resolve("")
        
def test_create_and_delete(tmp_path):
    controller = FilesystemController()
    test_file = tmp_path / "test.txt"
    
    controller.create_file([test_file])
    assert test_file.exists()
    
    # Write and append
    controller.write_text(test_file, "Hello ")
    controller.append_text(test_file, "EDITH")
    
    assert controller.read_text(test_file) == "Hello EDITH"
    
    # Delete permanent
    controller.delete([test_file], permanent=True)
    assert not test_file.exists()

def test_rename(tmp_path):
    controller = FilesystemController()
    folder = tmp_path / "AI"
    controller.create_folder([folder])
    
    result = controller.rename([folder], ["EDITH"])[0]
    
    assert result.name == "EDITH"
    assert (tmp_path / "EDITH").exists()
    assert not folder.exists()

def test_validation_traversal(tmp_path):
    from edith.capabilities.filesystem.filesystem_validator import FilesystemValidator
    
    base = tmp_path / "allowed"
    base.mkdir()
    
    malicious = base / ".." / "system32"
    
    with pytest.raises(DirectoryTraversalError):
        FilesystemValidator.validate_traversal(base, malicious)
