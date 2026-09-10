"""Small command-line entry point for inspecting a completed model run."""

from __future__ import annotations

import json
from pathlib import Path

import typer


app = typer.Typer(help="China PPI nowcast research pipeline")


@app.command()
def status(
    project_root: Path = typer.Option(Path.cwd(), exists=True, file_okay=False),
) -> None:
    """Print the preferred model and latest development nowcast."""

    summary_path = project_root / "data/processed/forecasts/run_summary.json"
    if not summary_path.exists():
        raise typer.BadParameter(f"run summary not found: {summary_path}")
    typer.echo(json.dumps(json.loads(summary_path.read_text()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
