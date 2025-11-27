"""Configuration and constants for TaskFlow."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LoopConfig:
    """Configuration for loop iterations."""

    outer_min: int = 0
    outer_max: int = 1000
    middle_min: int = 0
    middle_max: int = 10
    inner_min: int = 1
    inner_max: int = 20


@dataclass
class TaskConfig:
    """Runtime configuration for task execution."""

    outer_iterations: int
    middle_iterations: int
    inner_iterations: int
    short_circuit_probability: float = 0.3
    sleep_min: float = 0.01
    sleep_max: float = 0.05
    report_path: Path = field(default_factory=lambda: Path("report.md"))

    def __post_init__(self) -> None:
        """Validate configuration values."""
        loop_config = LoopConfig()

        if not loop_config.outer_min <= self.outer_iterations <= loop_config.outer_max:
            msg = f"outer_iterations must be between {loop_config.outer_min} and {loop_config.outer_max}"
            raise ValueError(msg)

        if not loop_config.middle_min <= self.middle_iterations <= loop_config.middle_max:
            msg = f"middle_iterations must be between {loop_config.middle_min} and {loop_config.middle_max}"
            raise ValueError(msg)

        if not loop_config.inner_min <= self.inner_iterations <= loop_config.inner_max:
            msg = f"inner_iterations must be between {loop_config.inner_min} and {loop_config.inner_max}"
            raise ValueError(msg)


@dataclass
class TaskStats:
    """Statistics collected during task execution."""

    total_outer_iterations: int = 0
    total_middle_iterations: int = 0
    total_inner_iterations: int = 0
    short_circuit_count: int = 0
    total_elapsed_seconds: float = 0.0
    messages: list[str] = field(default_factory=list)

    def add_message(self, message: str) -> None:
        """Add a message to the stats log."""
        self.messages.append(message)
