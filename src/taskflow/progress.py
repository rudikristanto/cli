"""Progress bar management for TaskFlow."""

from dataclasses import dataclass, field
from time import perf_counter
from typing import TYPE_CHECKING

from rich.console import Console, ConsoleOptions, Group, RenderResult
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

if TYPE_CHECKING:
    from rich.console import Console as ConsoleType


class DynamicLayout:
    """Wrapper that recalculates elapsed times on each render."""

    def __init__(self, progress_manager: "ProgressManager") -> None:
        self._progress_manager = progress_manager

    def __rich_console__(
        self, console: "ConsoleType", options: ConsoleOptions
    ) -> RenderResult:
        """Render the layout with updated elapsed times."""
        self._progress_manager._refresh_time_displays()
        yield self._progress_manager._create_layout()


def format_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


@dataclass
class ProgressManager:
    """Manages dual progress bars for task tracking."""

    console: Console
    outer_total: int
    inner_total: int
    _outer_progress: Progress = field(init=False)
    _inner_progress: Progress = field(init=False)
    _outer_task: TaskID = field(init=False)
    _inner_task: TaskID = field(init=False)
    _live: Live = field(init=False)
    _messages: list[str] = field(default_factory=list)
    _outer_start_time: float = field(default=0.0)
    _inner_start_time: float = field(default=0.0)
    _current_outer_step: int = field(default=0)
    _current_inner_step: int = field(default=0)
    _inner_completed_steps: int = field(default=0)

    def __post_init__(self) -> None:
        """Initialize progress bars."""
        self._outer_progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Outer Loop[/bold blue]"),
            BarColumn(bar_width=40, complete_style="green", finished_style="bright_green"),
            TextColumn("[progress.percentage]{task.percentage:>6.1f}%"),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[time_display]}[/cyan]"),
            TextColumn("•"),
            TextColumn("[dim]{task.fields[status]}[/dim]"),
            console=self.console,
            expand=False,
        )

        self._inner_progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold yellow]Inner Loop[/bold yellow]"),
            BarColumn(bar_width=40, complete_style="yellow", finished_style="bright_yellow"),
            TextColumn("[progress.percentage]{task.percentage:>6.1f}%"),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[time_display]}[/cyan]"),
            TextColumn("•"),
            TextColumn("[dim]{task.fields[status]}[/dim]"),
            console=self.console,
            expand=False,
        )

    def _refresh_time_displays(self) -> None:
        """Refresh the elapsed time displays for both progress bars."""
        if self._outer_start_time > 0:
            outer_elapsed = perf_counter() - self._outer_start_time
            self._outer_progress.update(
                self._outer_task,
                time_display=format_time(outer_elapsed),
            )
        if self._inner_start_time > 0:
            inner_elapsed = perf_counter() - self._inner_start_time
            self._inner_progress.update(
                self._inner_task,
                time_display=format_time(inner_elapsed),
            )

    def _create_layout(self) -> Panel:
        """Create the combined layout with progress bars and messages."""
        progress_table = Table.grid(expand=True)
        progress_table.add_row(self._outer_progress)
        progress_table.add_row(self._inner_progress)

        message_table = Table.grid(expand=True)
        recent_messages = self._messages[-10:] if self._messages else ["Waiting for tasks..."]
        for msg in recent_messages:
            message_table.add_row(f"  [dim]>[/dim] {msg}")

        layout = Table.grid(expand=True, padding=(0, 0))
        layout.add_row(
            Panel(
                progress_table,
                title="[bold]Progress[/bold]",
                border_style="bright_blue",
                padding=(0, 1),
            )
        )
        layout.add_row(
            Panel(
                message_table,
                title="[bold]Activity Log[/bold]",
                border_style="dim",
                padding=(0, 1),
            )
        )

        return Panel(
            layout,
            title="[bold magenta]TaskFlow Execution[/bold magenta]",
            border_style="magenta",
        )

    async def __aenter__(self) -> "ProgressManager":
        """Start the live display."""
        self._outer_task = self._outer_progress.add_task(
            "outer",
            total=self.outer_total,
            time_display="00:00:00",
            status=f"0/{self.outer_total}",
        )
        self._inner_task = self._inner_progress.add_task(
            "inner",
            total=self.inner_total,
            time_display="00:00:00",
            status=f"0/{self.inner_total}",
        )

        self._outer_start_time = perf_counter()
        self._inner_start_time = perf_counter()

        # Use DynamicLayout to ensure elapsed times update on each render cycle
        self._live = Live(
            DynamicLayout(self),
            console=self.console,
            refresh_per_second=10,
            transient=False,
        )
        self._live.__enter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Stop the live display."""
        self._live.__exit__(*args)

    def add_message(self, message: str) -> None:
        """Add a message to the activity log."""
        self._messages.append(message)
        self._update_display()

    def advance_outer(self, step: int) -> None:
        """Advance the outer progress bar."""
        self._current_outer_step = step
        elapsed = perf_counter() - self._outer_start_time
        self._outer_progress.update(
            self._outer_task,
            completed=step,
            time_display=format_time(elapsed),
            status=f"{step}/{self.outer_total}",
        )
        self._update_display()

    def reset_inner(self, new_total: int) -> None:
        """Reset the inner progress bar for a new outer iteration."""
        self._inner_start_time = perf_counter()
        self._inner_completed_steps = 0
        self._inner_progress.update(
            self._inner_task,
            completed=0,
            total=new_total,
            time_display="00:00:00",
            status=f"0/{new_total}",
        )
        self._update_display()

    def advance_inner(self, step: int, total: int) -> None:
        """Advance the inner progress bar."""
        self._inner_completed_steps = step
        elapsed = perf_counter() - self._inner_start_time
        self._inner_progress.update(
            self._inner_task,
            completed=step,
            total=total,
            time_display=format_time(elapsed),
            status=f"{step}/{total}",
        )
        self._update_display()

    def complete_outer(self) -> None:
        """Mark outer progress as complete."""
        elapsed = perf_counter() - self._outer_start_time
        self._outer_progress.update(
            self._outer_task,
            completed=self.outer_total,
            time_display=format_time(elapsed),
            status="Complete!",
        )
        self._update_display()

    def complete_inner(self, total: int) -> None:
        """Mark inner progress as complete for current iteration."""
        elapsed = perf_counter() - self._inner_start_time
        self._inner_progress.update(
            self._inner_task,
            completed=total,
            total=total,
            time_display=format_time(elapsed),
            status="Complete!",
        )
        self._update_display()

    def _update_display(self) -> None:
        """Update the live display.

        Note: With DynamicLayout, the display auto-refreshes 10 times per second,
        so this method is now a no-op. Updates to progress/messages will be
        picked up on the next render cycle.
        """
        pass

    def get_outer_elapsed(self) -> float:
        """Get elapsed time for outer loop."""
        return perf_counter() - self._outer_start_time
