"""Async task execution with nested loops."""

import random
from datetime import datetime

import anyio

from taskflow.config import TaskConfig, TaskStats
from taskflow.progress import ProgressManager


async def inner_loop(
    config: TaskConfig,
    stats: TaskStats,
    progress: ProgressManager,
    outer_idx: int,
    middle_idx: int,
) -> int:
    """
    Execute the innermost loop.

    Can short-circuit randomly before completing all iterations.
    Returns the actual number of iterations completed.
    """
    progress.add_message(
        f"[cyan]Starting inner loop[/cyan] (outer={outer_idx}, middle={middle_idx})"
    )

    completed = 0
    for i in range(config.inner_iterations):
        # Random short-circuit check
        if i > 0 and random.random() < config.short_circuit_probability:
            progress.add_message(
                f"[yellow]Short-circuit[/yellow] at inner iteration {i} "
                f"(outer={outer_idx}, middle={middle_idx})"
            )
            stats.short_circuit_count += 1
            stats.add_message(
                f"Short-circuit at outer={outer_idx}, middle={middle_idx}, inner={i}"
            )
            break

        # Simulate work
        sleep_time = random.uniform(config.sleep_min, config.sleep_max)
        await anyio.sleep(sleep_time)

        completed = i + 1
        stats.total_inner_iterations += 1

        if completed % 5 == 0 or completed == config.inner_iterations:
            progress.add_message(
                f"[dim]Inner progress:[/dim] {completed}/{config.inner_iterations} "
                f"(outer={outer_idx}, middle={middle_idx})"
            )

    return completed


async def middle_loop(
    config: TaskConfig,
    stats: TaskStats,
    progress: ProgressManager,
    outer_idx: int,
) -> None:
    """
    Execute the middle loop.

    Tracks combined progress with inner loop on the second progress bar.
    """
    progress.add_message(f"[blue]Starting middle loop[/blue] (outer={outer_idx})")

    # Calculate total expected iterations for inner progress bar
    # This is middle_iterations * inner_iterations (max possible)
    total_inner_steps = config.middle_iterations * config.inner_iterations
    progress.reset_inner(total_inner_steps)

    cumulative_inner = 0

    for j in range(config.middle_iterations):
        progress.add_message(
            f"[green]Middle iteration {j + 1}/{config.middle_iterations}[/green] "
            f"(outer={outer_idx})"
        )

        # Execute inner loop
        inner_completed = await inner_loop(config, stats, progress, outer_idx, j)
        cumulative_inner += inner_completed
        stats.total_middle_iterations += 1

        # Update inner progress bar with cumulative progress
        progress.advance_inner(cumulative_inner, total_inner_steps)

        # Small delay between middle iterations
        await anyio.sleep(config.sleep_min)

    # Mark inner progress complete for this outer iteration
    progress.complete_inner(cumulative_inner)
    progress.add_message(
        f"[green]Completed middle loop[/green] (outer={outer_idx}, "
        f"inner_steps={cumulative_inner}/{total_inner_steps})"
    )


async def outer_loop(
    config: TaskConfig,
    stats: TaskStats,
    progress: ProgressManager,
) -> None:
    """
    Execute the outermost loop.

    Tracks progress on the first progress bar.
    """
    progress.add_message("[bold magenta]Starting outer loop execution[/bold magenta]")
    stats.add_message(f"Execution started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for i in range(config.outer_iterations):
        progress.add_message(
            f"[bold cyan]Outer iteration {i + 1}/{config.outer_iterations}[/bold cyan]"
        )
        stats.add_message(f"Outer iteration {i + 1} started")

        # Execute middle and inner loops
        await middle_loop(config, stats, progress, i)

        stats.total_outer_iterations += 1

        # Update outer progress
        progress.advance_outer(i + 1)

    # Mark outer progress complete
    progress.complete_outer()
    progress.add_message("[bold green]All loops completed successfully![/bold green]")
    stats.add_message(f"Execution completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def run_tasks(config: TaskConfig, stats: TaskStats, progress: ProgressManager) -> None:
    """Main entry point for task execution."""
    stats.add_message("TaskFlow execution initialized")
    stats.add_message(f"Configuration: outer={config.outer_iterations}, "
                      f"middle={config.middle_iterations}, inner={config.inner_iterations}")

    await outer_loop(config, stats, progress)

    stats.total_elapsed_seconds = progress.get_outer_elapsed()
    stats.add_message(f"Total elapsed time: {stats.total_elapsed_seconds:.2f} seconds")
