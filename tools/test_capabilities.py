import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from edith.sdk.capability import CapabilityLoader, capability_registry

def test_capabilities():
    print("=== EDITH Capability Diagnostic ===")
    
    loader = CapabilityLoader(capability_registry)
    loader.discover_and_load()
    
    caps = capability_registry.get_all()
    if not caps:
        print("[WARN] No capabilities loaded.")
        return
        
    print(f"\nLoaded {len(caps)} capabilities. Running health checks...\n")
    
    health_summary = capability_registry.get_health_summary()
    
    for cap_id, status in health_summary.items():
        icon = "[OK]" if status.lower() == "healthy" else ("[WARN]" if status.lower() == "degraded" else "[FAIL]")
        print(f"{icon} {cap_id.ljust(20)} : {status}")

if __name__ == "__main__":
    test_capabilities()
