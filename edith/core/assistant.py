from edith.core.state import state
from edith.core.orchestrator import orchestrator
from edith.voice.manager import voice_manager
from edith.utils.logger import logger
from rich.console import Console
from rich.panel import Panel

console = Console()

class Assistant:
    def start_session(self):
        """Starts a single interaction session when triggered."""
        state.is_listening = True
        
        text = voice_manager.wake()
        state.is_listening = False
        
        if text:
            console.print(f"[bold cyan]You:[/bold cyan] {text}")
            state.is_processing = True
            orchestrator.process_text(text)
            state.is_processing = False
        else:
            logger.info("No speech detected.")
            voice_manager.speak("I didn't catch that.", priority="high")
            console.print("[dim]No speech detected.[/dim]")

assistant = Assistant()
