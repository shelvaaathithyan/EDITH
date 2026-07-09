import pytest
import time
from edith.interaction.context.context_models import ContextNode
from edith.interaction.context.context_store import ContextStore

def test_context_stack_hierarchy():
    store = ContextStore()
    
    node1 = ContextNode(type="browser", value="chrome")
    node2 = ContextNode(type="application", value="vscode")
    
    store.push(node1)
    store.push(node2)
    
    assert store.get_top().value == "vscode"
    
    # Touch node1
    store.find_by_type("browser")
    
    # Actually finding it calls touch, but it doesn't automatically move it to top of stack unless we push. 
    # Wait, our `push` moves it to top. find_by_type touches it (updates last_accessed_at).
    # Since our resolver relies on `iter_top_down` which traverses list order, 
    # if we want 'touched' to move to top, we should push it again.
    # For now, let's just check expiration logic.
    assert len(store.get_all()) == 2

def test_context_expiration():
    store = ContextStore()
    
    node1 = ContextNode(type="browser", value="chrome", ttl=0.1)
    store.push(node1)
    
    assert store.get_top() is not None
    
    time.sleep(0.2)
    
    # Should be evicted on next read
    assert store.get_top() is None
    assert len(store.get_all()) == 0
