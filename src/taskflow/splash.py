"""Splash screen display for TaskFlow."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from taskflow import __app_name__, __version__

LOGO = r"""
  _____         _    _____ _
 |_   _|_ _ ___| | _|  ___| | _____      __
   | |/ _` / __| |/ / |_  | |/ _ \ \ /\ / /
   | | (_| \__ \   <|  _| | | (_) \ V  V /
   |_|\__,_|___/_|\_\_|   |_|\___/ \_/\_/
"""


def display_splash(console: Console) -> None:
    """Display the application splash screen."""
    logo_text = Text(LOGO, style="bold cyan")
    version_text = Text(f"\nVersion {__version__}", style="dim white")
    tagline = Text("\nAsync Task Runner with Beautiful Progress Tracking", style="italic green")

    content = Text()
    content.append_text(logo_text)
    content.append_text(version_text)
    content.append_text(tagline)

    panel = Panel(
        content,
        title=f"[bold magenta]{__app_name__}[/bold magenta]",
        subtitle="[dim]Press Ctrl+C to cancel[/dim]",
        border_style="bright_blue",
        padding=(1, 4),
    )

    console.print()
    console.print(panel)
    console.print()
