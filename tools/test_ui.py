import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from edith.ui.window import UIBridge

def test_ui():
    print("=== EDITH UI Bridge Diagnostic ===")
    
    bridge = UIBridge()
    
    print("\n[1] Testing get_health_report()...")
    report = bridge.get_health_report()
    print(f"Overall Status: {report.get('overall_status')}")
    print(f"Subsystems Count: {len(report.get('subsystems', []))}")
    print(f"Capabilities Count: {len(report.get('capabilities', {}))}")
    
    print("\n[2] Testing get_runtime_diagnostics()...")
    diagnostics = bridge.get_runtime_diagnostics()
    print(f"Lifecycle: {diagnostics.get('lifecycle')}")
    print(f"Ollama: {diagnostics.get('ollama')}")
    
    print("\n[3] Testing get_system_metrics()...")
    metrics = bridge.get_system_metrics()
    print(f"CPU: {metrics.get('cpu_percent')}%")
    print(f"RAM: {metrics.get('ram_mb')} MB")
    print(f"Threads: {metrics.get('thread_count')}")
    
    print("\n[OK] UI Bridge methods executed successfully.")

if __name__ == "__main__":
    test_ui()
