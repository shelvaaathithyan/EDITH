import sys
import argparse
from edith.utils.logger import logger
from edith.sdk.capability import CapabilityLoader, capability_registry

def _setup_registry():
    loader = CapabilityLoader(capability_registry)
    loader.discover_and_load()

def cmd_doctor(args):
    _setup_registry()
    print("\n🩺 EDITH Doctor: Capability Health Check")
    print("-" * 50)
    health_summary = capability_registry.get_health_summary()
    if not health_summary:
        print("No capabilities registered.")
        return
        
    for cap_id, status in health_summary.items():
        icon = "✅" if status == "healthy" else ("⚠️" if status == "degraded" else "❌")
        print(f"{icon} {cap_id.ljust(20)} : {status}")
    print("-" * 50)

def cmd_list(args):
    _setup_registry()
    print("\n📦 Registered Capabilities")
    print("-" * 60)
    caps = capability_registry.get_all()
    for cap in caps:
        m = cap.get_manifest()
        print(f"• {m.id} (v{m.version}) - {m.name}")
    print(f"\nTotal capabilities: {len(caps)}")
    print("-" * 60)

def cmd_inspect(args):
    _setup_registry()
    cap_id = args.capability
    cap = capability_registry.get_capability(cap_id)
    if not cap:
        print(f"❌ Capability '{cap_id}' not found.")
        return
        
    m = cap.get_manifest()
    print(f"\n🔍 Inspecting: {m.id} (v{m.version})")
    print("=" * 60)
    print(f"Name:          {m.name}")
    print(f"Author:        {m.author}")
    print(f"Description:   {m.description}")
    print(f"Platforms:     {', '.join(m.supported_platforms)}")
    print(f"Dependencies:  {', '.join(m.dependencies) if m.dependencies else 'None'}")
    print(f"\nActions:       {', '.join(m.supported_actions)}")
    print("\nRisk Matrix:")
    for action, risk in m.risk_matrix.items():
        print(f"  - {action.ljust(15)} : {risk.name}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="EDITH Developer Tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # edith doctor
    subparsers.add_parser("doctor", help="Run health checks on all capabilities")

    # edith capabilities
    subparsers.add_parser("capabilities", help="List all registered capabilities")

    # edith inspect <capability>
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a specific capability manifest")
    inspect_parser.add_argument("capability", help="ID of the capability to inspect")

    args = parser.parse_args()

    # Suppress verbose logs for CLI tools
    logger.setLevel(logging.WARNING if not args else logging.CRITICAL)

    if args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "capabilities":
        cmd_list(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    import logging
    main()
