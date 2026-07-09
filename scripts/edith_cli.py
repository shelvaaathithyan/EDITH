import sys
import argparse
from edith.utils.logger import logger
from edith.sdk.capability import CapabilityLoader, capability_registry
from edith.memory import memory_manager
from edith.memory.memory_constants import MemoryCategory

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

def cmd_memory(args):
    action = args.mem_action
    
    if action == "list":
        category = MemoryCategory(args.category) if args.category else None
        memories = memory_manager.repo.list_by_category(category)
        
        print(f"\n🧠 EDITH Long-Term Memory (Total: {len(memories)})")
        print("-" * 80)
        for m in sorted(memories, key=lambda x: x.relevance_score, reverse=True):
            tags = f"[{', '.join(m.tags)}]" if m.tags else ""
            print(f"{m.id[:8]} | {m.category.value[:10].ljust(10)} | Conf: {m.confidence:.2f} | {m.title.ljust(25)} | {m.value[:20]} {tags}")
        print("-" * 80)
        
    elif action == "forget":
        try:
            memory_manager.forget(args.id)
            print(f"✅ Memory {args.id} forgotten.")
        except Exception as e:
            print(f"❌ Failed to forget memory: {e}")
            
    elif action == "remember":
        mem = memory_manager.remember(args.text)
        if mem:
            print(f"✅ Learned: {mem.title} -> {mem.value}")
        else:
            print("❌ Could not extract a memory from the text.")

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

    # edith memory
    mem_parser = subparsers.add_parser("memory", help="Inspect and manage Long-Term Memory")
    mem_subparsers = mem_parser.add_subparsers(dest="mem_action")
    
    list_mem = mem_subparsers.add_parser("list", help="List memories")
    list_mem.add_argument("--category", "-c", help="Filter by category")
    
    forget_mem = mem_subparsers.add_parser("forget", help="Forget a specific memory")
    forget_mem.add_argument("id", help="Memory ID")
    
    remember_mem = mem_subparsers.add_parser("remember", help="Explicitly tell EDITH to remember something")
    remember_mem.add_argument("text", help="Text to remember")

    args = parser.parse_args()

    # Suppress verbose logs for CLI tools
    logger.setLevel(logging.WARNING if not args else logging.CRITICAL)

    if args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "capabilities":
        cmd_list(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "memory":
        cmd_memory(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    import logging
    main()
