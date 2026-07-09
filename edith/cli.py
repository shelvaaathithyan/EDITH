import typer
from rich.console import Console
from edith.core.assistant import assistant
from edith.voice.manager import voice_manager
from edith.voice.providers.piper_provider import PiperProvider
from edith.voice.models import event_bus, VoiceEvent, VoiceState
from edith.utils.logger import logger
from edith.sdk.capability import CapabilityLoader, capability_registry
from edith.memory import memory_manager
from edith.memory.memory_constants import MemoryCategory

app = typer.Typer(help="EDITH: AI Desktop Voice Assistant")
console = Console()

def _on_state_changed(state: VoiceState):
    state_messages = {
        VoiceState.LISTENING: "[bold green]🎤 Listening...[/bold green]",
        VoiceState.UNDERSTANDING: "[bold yellow]🧠 Understanding...[/bold yellow]",
        VoiceState.THINKING: "[bold yellow]🤔 Thinking...[/bold yellow]",
        VoiceState.EXECUTING: "[bold cyan]⚙ Executing...[/bold cyan]",
        VoiceState.SPEAKING: "[bold magenta]🔊 Speaking...[/bold magenta]",
        VoiceState.INTERRUPTED: "[bold red]🛑 Interrupted.[/bold red]",
        VoiceState.ERROR: "[bold red]❌ Error occurred.[/bold red]",
    }
    msg = state_messages.get(state)
    if msg:
        console.print(msg)

event_bus.subscribe(VoiceEvent.STATE_CHANGED, _on_state_changed)

@app.command()
def setup():
    """Sets up EDITH by downloading necessary voice models."""
    console.print("[bold cyan]Setting up EDITH Voice Engine...[/bold cyan]")
    # Initialize downloads models if missing
    provider = PiperProvider()
    provider.initialize()
    console.print("[bold green]Setup complete![/bold green]")

@app.command()
def start():
    """Starts a lightweight Voice CLI session (no UI, no orchestrator). For full EDITH run: python edith/main.py"""
    logger.info("Lightweight Voice CLI Session Started. (For full app, run python edith/main.py)")
    voice_manager.initialize()
    assistant.start_session()
    voice_manager.shutdown()

def _setup_registry():
    loader = CapabilityLoader(capability_registry)
    loader.discover_and_load()

@app.command()
def doctor():
    """Run health checks on all capabilities"""
    _setup_registry()
    console.print("\n[bold]--- EDITH Doctor: Capability Health Check ---[/bold]")
    console.print("-" * 50)
    health_summary = capability_registry.get_health_summary()
    if not health_summary:
        console.print("No capabilities registered.")
        return
        
    for cap_id, status in health_summary.items():
        icon = "[OK]" if status.lower() == "healthy" else ("[WARN]" if status.lower() == "degraded" else "[FAIL]")
        console.print(f"{icon} {cap_id.ljust(20)} : {status}")
    console.print("-" * 50)

@app.command()
def capabilities():
    """List all registered capabilities"""
    _setup_registry()
    console.print("\n[bold]--- Registered Capabilities ---[/bold]")
    console.print("-" * 60)
    caps = capability_registry.get_all()
    for cap in caps:
        m = cap.get_manifest()
        console.print(f"- {m.id} (v{m.version}) - {m.name}")
    console.print(f"\nTotal capabilities: {len(caps)}")
    console.print("-" * 60)

@app.command()
def inspect(capability: str):
    """Inspect a specific capability manifest"""
    _setup_registry()
    cap = capability_registry.get_capability(capability)
    if not cap:
        console.print(f"[bold red][FAIL] Capability '{capability}' not found.[/bold red]")
        return
        
    m = cap.get_manifest()
    console.print(f"\n[bold]--- Inspecting: {m.id} (v{m.version}) ---[/bold]")
    console.print("=" * 60)
    console.print(f"Name:          {m.name}")
    console.print(f"Author:        {m.author}")
    console.print(f"Description:   {m.description}")
    console.print(f"Platforms:     {', '.join(m.supported_platforms)}")
    console.print(f"Dependencies:  {', '.join(m.dependencies) if m.dependencies else 'None'}")
    console.print(f"\nActions:       {', '.join(m.supported_actions)}")
    console.print("\nRisk Matrix:")
    for action, risk in m.risk_matrix.items():
        console.print(f"  - {action.ljust(15)} : {risk.name}")
    console.print("=" * 60)

# Memory sub-app
memory_app = typer.Typer(help="Inspect and manage Long-Term Memory")
app.add_typer(memory_app, name="memory")

@memory_app.command("list")
def memory_list(category: str = None):
    """List memories"""
    cat_enum = MemoryCategory(category) if category else None
    memories = memory_manager.repo.list_by_category(cat_enum)
    
    console.print(f"\n[bold]--- EDITH Long-Term Memory (Total: {len(memories)}) ---[/bold]")
    console.print("-" * 80)
    for m in sorted(memories, key=lambda x: x.relevance_score, reverse=True):
        tags = f"[{', '.join(m.tags)}]" if m.tags else ""
        console.print(f"{m.id[:8]} | {m.category.value[:10].ljust(10)} | Conf: {m.confidence:.2f} | {m.title.ljust(25)} | {m.value[:20]} {tags}")
    console.print("-" * 80)

@memory_app.command("forget")
def memory_forget(memory_id: str):
    """Forget a specific memory"""
    try:
        memory_manager.forget(memory_id)
        console.print(f"[bold green][OK] Memory {memory_id} forgotten.[/bold green]")
    except Exception as e:
        console.print(f"[bold red][FAIL] Failed to forget memory: {e}[/bold red]")

@memory_app.command("remember")
def memory_remember(text: str):
    """Explicitly tell EDITH to remember something"""
    mem = memory_manager.remember(text)
    if mem:
        console.print(f"[bold green][OK] Learned: {mem.title} -> {mem.value}[/bold green]")
    else:
        console.print("[bold red][FAIL] Could not extract a memory from the text.[/bold red]")

if __name__ == "__main__":
    app()
