import typer
from rich.console import Console
from edith.core.assistant import assistant
from edith.voice.manager import voice_manager
from edith.voice.providers.piper_provider import PiperProvider
from edith.voice.models import event_bus, VoiceEvent, VoiceState
from edith.utils.logger import logger

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
    """Starts EDITH in a single listening session."""
    logger.info("EDITH Session Started via CLI.")
    voice_manager.initialize()
    assistant.start_session()
    voice_manager.shutdown()

if __name__ == "__main__":
    app()
