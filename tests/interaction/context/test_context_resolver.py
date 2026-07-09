import pytest
from edith.interaction.context.context_store import ContextStore
from edith.interaction.context.context_models import ContextNode
from edith.interaction.context.context_resolver import ContextResolver
from edith.interaction.context.context_exceptions import ContextResolutionError

def test_resolve_it():
    store = ContextStore()
    resolver = ContextResolver(store)
    
    store.push(ContextNode(type="browser", value="chrome"))
    store.push(ContextNode(type="application", value="vscode"))
    
    # "it" resolves to the absolute top of the stack
    node = resolver.resolve("it")
    assert node.value == "vscode"

def test_resolve_specific_type():
    store = ContextStore()
    resolver = ContextResolver(store)
    
    store.push(ContextNode(type="browser", value="chrome"))
    store.push(ContextNode(type="application", value="vscode"))
    
    # "the browser" resolves to chrome
    node = resolver.resolve("the browser")
    assert node.value == "chrome"

def test_resolve_previous():
    store = ContextStore()
    resolver = ContextResolver(store)
    
    store.push(ContextNode(type="application", value="vscode"))
    store.push(ContextNode(type="application", value="spotify"))
    
    # "previous application" skips the top one
    node = resolver.resolve("previous application")
    assert node.value == "vscode"
    
def test_resolve_expected_type():
    store = ContextStore()
    resolver = ContextResolver(store)
    
    store.push(ContextNode(type="browser", value="chrome"))
    store.push(ContextNode(type="application", value="vscode"))
    
    # "it" with expected type application -> vscode
    node = resolver.resolve("it", expected_type="application")
    assert node.value == "vscode"
    
    # "it" with expected type browser -> chrome
    node = resolver.resolve("it", expected_type="browser")
    assert node.value == "chrome"

def test_resolve_unresolvable():
    store = ContextStore()
    resolver = ContextResolver(store)
    
    store.push(ContextNode(type="browser", value="chrome"))
    
    with pytest.raises(ContextResolutionError):
        resolver.resolve("previous application")
