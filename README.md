# TaskFlow

A beautiful async CLI task runner with dual progress tracking, built with Python 3.13.

## Features

- Splash screen with application branding
- Dual progress bars tracking nested loop execution
- Async/await programming model
- Real-time activity logging
- Markdown report generation
- Interactive report viewer with scrolling
- Configurable loop iterations and short-circuit probability

## Requirements

- Python 3.13+
- Poetry (package manager)

## Installation

### 1. Install Poetry (if not already installed)

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Clone and Install Dependencies

```bash
cd poc22
poetry install
```

## How to Run

### Using Poetry

```bash
# Run with default settings
poetry run taskflow run

# Run with custom parameters
poetry run taskflow run --outer 10 --middle 5 --inner 15 --report my-report.md

# Run with all options
poetry run taskflow run \
    --outer 20 \
    --middle 8 \
    --inner 12 \
    --short-circuit 0.25 \
    --report my-report.md

# Skip splash screen
poetry run taskflow run --no-splash

# View help
poetry run taskflow --help
poetry run taskflow run --help
```

### Using the Installed Command

After `poetry install`, you can also use:

```bash
# Activate virtual environment first
poetry shell

# Then run directly
taskflow run
taskflow run --outer 10 --middle 5 --inner 15
```

### View a Report

```bash
# View an existing report
poetry run taskflow view report.md

# Or after activating shell
taskflow view report.md
```

## CLI Options

### `taskflow run`

| Option | Short | Description | Default | Range |
|--------|-------|-------------|---------|-------|
| `--outer` | `-o` | Outer loop iterations | 5 | 0-1000 |
| `--middle` | `-m` | Middle loop iterations | 3 | 0-10 |
| `--inner` | `-i` | Inner loop iterations (max) | 10 | 1-20 |
| `--short-circuit` | `-s` | Short-circuit probability | 0.3 | 0.0-1.0 |
| `--report` | `-r` | Report output path | report.md | - |
| `--no-splash` | - | Skip splash screen | false | - |
| `--version` | `-v` | Show version | - | - |

### `taskflow view`

```bash
taskflow view <report_path>
```

Opens the markdown report in an interactive viewer with:
- Arrow keys / Page Up/Down for scrolling
- 'q' to quit

## Example Session

```bash
# Run a quick test with small iteration counts
poetry run taskflow run -o 3 -m 2 -i 5

# Run a longer session
poetry run taskflow run -o 50 -m 5 -i 10 -s 0.2 -r detailed-report.md
```

## Project Structure

```
poc22/
├── pyproject.toml
├── README.md
└── src/
    └── taskflow/
        ├── __init__.py      # Package metadata
        ├── cli.py           # CLI entry point (Typer)
        ├── config.py        # Configuration dataclasses
        ├── progress.py      # Dual progress bar management
        ├── report.py        # Report generation and viewer
        ├── splash.py        # Splash screen display
        └── tasks.py         # Async task execution loops
```

## Architecture

### Progress Bars

1. **Outer Progress Bar** (Blue): Tracks the outermost loop iterations
2. **Inner Progress Bar** (Yellow): Tracks combined middle + inner loop progress, resets on each outer iteration

### Loop Structure

```
Outer Loop (0-1000 iterations)
└── Middle Loop (0-10 iterations)
    └── Inner Loop (1-20 iterations, may short-circuit)
```

### Short-Circuiting

The inner loop can terminate early based on a configurable probability. This simulates real-world scenarios where tasks may complete early or be skipped.

## License

MIT
