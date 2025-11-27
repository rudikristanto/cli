"""CLI entry point for TaskFlow."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Confirm

from taskflow import __app_name__, __version__
from taskflow.config import LoopConfig, TaskConfig, TaskStats
from taskflow.progress import ProgressManager
from taskflow.report import (
    display_summary,
    generate_report,
    save_report,
    view_report_interactive,
)
from taskflow.splash import display_splash
from taskflow.tasks import run_tasks

app = typer.Typer(
    name=__app_name__,
    help="A beautiful async CLI task runner with progress tracking.",
    rich_markup_mode="rich",
    add_completion=False,
)

console = Console()
loop_config = LoopConfig()


def version_callback(value: bool) -> None:
    """Display version and exit."""
    if value:
        console.print(f"{__app_name__} version {__version__}")
        raise typer.Exit()


def validate_outer(value: int) -> int:
    """Validate outer iteration count."""
    if not loop_config.outer_min <= value <= loop_config.outer_max:
        raise typer.BadParameter(
            f"Must be between {loop_config.outer_min} and {loop_config.outer_max}"
        )
    return value


def validate_middle(value: int) -> int:
    """Validate middle iteration count."""
    if not loop_config.middle_min <= value <= loop_config.middle_max:
        raise typer.BadParameter(
            f"Must be between {loop_config.middle_min} and {loop_config.middle_max}"
        )
    return value


def validate_inner(value: int) -> int:
    """Validate inner iteration count."""
    if not loop_config.inner_min <= value <= loop_config.inner_max:
        raise typer.BadParameter(
            f"Must be between {loop_config.inner_min} and {loop_config.inner_max}"
        )
    return value


def validate_report_path(value: Path) -> Path:
    """Validate report path."""
    if value.suffix.lower() != ".md":
        raise typer.BadParameter("Report file must have .md extension")
    return value


@app.command()
def run(
    outer: Annotated[
        int,
        typer.Option(
            "--outer",
            "-o",
            help=f"Number of outer loop iterations ({loop_config.outer_min}-{loop_config.outer_max})",
            callback=validate_outer,
            show_default=True,
        ),
    ] = 5,
    middle: Annotated[
        int,
        typer.Option(
            "--middle",
            "-m",
            help=f"Number of middle loop iterations ({loop_config.middle_min}-{loop_config.middle_max})",
            callback=validate_middle,
            show_default=True,
        ),
    ] = 3,
    inner: Annotated[
        int,
        typer.Option(
            "--inner",
            "-i",
            help=f"Max inner loop iterations ({loop_config.inner_min}-{loop_config.inner_max})",
            callback=validate_inner,
            show_default=True,
        ),
    ] = 10,
    report: Annotated[
        Path,
        typer.Option(
            "--report",
            "-r",
            help="Path for the output report file (.md)",
            callback=validate_report_path,
            show_default=True,
        ),
    ] = Path("report.md"),
    short_circuit_prob: Annotated[
        float,
        typer.Option(
            "--short-circuit",
            "-s",
            help="Probability of short-circuiting inner loop (0.0-1.0)",
            min=0.0,
            max=1.0,
            show_default=True,
        ),
    ] = 0.3,
    no_splash: Annotated[
        bool,
        typer.Option(
            "--no-splash",
            help="Skip the splash screen",
        ),
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """
    Run the TaskFlow task execution with progress tracking.

    This command executes three nested loops with configurable iteration counts.
    Progress is displayed using two progress bars - one for the outer loop and
    one for the combined middle/inner loops.

    [bold]Example:[/bold]
        taskflow run --outer 10 --middle 5 --inner 15

    The inner loop may short-circuit randomly based on the probability setting.
    """
    # Display splash screen
    if not no_splash:
        display_splash(console)

    # Create configuration
    try:
        config = TaskConfig(
            outer_iterations=outer,
            middle_iterations=middle,
            inner_iterations=inner,
            short_circuit_probability=short_circuit_prob,
            report_path=report,
        )
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1) from e

    stats = TaskStats()

    # Display configuration
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Outer iterations:  [cyan]{outer}[/cyan]")
    console.print(f"  Middle iterations: [cyan]{middle}[/cyan]")
    console.print(f"  Inner iterations:  [cyan]{inner}[/cyan] (max)")
    console.print(f"  Short circuit:     [cyan]{short_circuit_prob:.0%}[/cyan]")
    console.print(f"  Report path:       [cyan]{report}[/cyan]")
    console.print()

    # Calculate total inner steps for progress bar
    total_inner_steps = middle * inner

    # Run the async task execution
    async def execute() -> None:
        async with ProgressManager(
            console=console,
            outer_total=outer,
            inner_total=total_inner_steps,
        ) as progress:
            await run_tasks(config, stats, progress)

    try:
        asyncio.run(execute())
    except KeyboardInterrupt:
        console.print("\n[yellow]Execution cancelled by user.[/yellow]")
        raise typer.Exit(130) from None

    # Display summary
    display_summary(console, config, stats)

    # Generate and save report
    report_content = generate_report(config, stats)
    save_report(report_content, report)
    console.print(f"[green]Report saved to:[/green] {report.absolute()}")
    console.print()

    # Ask if user wants to view the report
    console.print("[bold]Commands:[/bold]")
    console.print(f"  View report: [cyan]taskflow view {report}[/cyan]")
    console.print()

    if Confirm.ask("Would you like to view the report now?", default=True):
        view_report_interactive(console, report)


@app.command()
def view(
    report_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the markdown report file to view",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
) -> None:
    """
    View a markdown report in an interactive viewer.

    Use arrow keys or Page Up/Down to scroll through the report.
    Press 'q' to quit the viewer and exit the program.

    [bold]Example:[/bold]
        taskflow view report.md
    """
    if report_path.suffix.lower() != ".md":
        console.print("[red]Error:[/red] File must be a markdown (.md) file")
        raise typer.Exit(1)

    view_report_interactive(console, report_path)
    console.print("[dim]Viewer closed.[/dim]")


if __name__ == "__main__":
    app()
