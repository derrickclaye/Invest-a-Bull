from __future__ import annotations

import asyncio
import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import nbformat
import pandas as pd
from nbclient import NotebookClient

from .config import AnalysisConfig
from .pipeline import run_pipeline
from .reporting import build_readme_latest_results_section, update_readme_with_latest_results


if os.name == "nt" and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def execute_notebook(notebook_path: Path, *, working_directory: Path, timeout: int) -> Path:
    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(working_directory)}},
    )
    executed = client.execute()
    nbformat.write(executed, notebook_path)
    return notebook_path


def refresh_project_assets(
    config: AnalysisConfig | None = None,
    *,
    execute_master_notebook: bool = True,
    update_readme: bool = True,
) -> dict[str, Path]:
    resolved_config = config or AnalysisConfig()
    outputs = run_pipeline(resolved_config)

    metadata = json.loads(outputs["metadata"].read_text(encoding="utf-8"))
    top_selection = pd.read_csv(outputs["top_selection"])
    portfolio_summary = pd.read_csv(outputs["portfolio_summary"])
    monte_carlo_summary = pd.read_csv(outputs["monte_carlo_summary"], index_col=0).iloc[:, 0]
    generated_at = datetime.fromisoformat(metadata["generated_at_utc"])

    if execute_master_notebook:
        notebook_path = resolved_config.project_root / "MasterAnalysisFinal.ipynb"
        previous_flag = os.environ.get("INVEST_A_BULL_NOTEBOOK_REFRESH")
        os.environ["INVEST_A_BULL_NOTEBOOK_REFRESH"] = "0"
        try:
            execute_notebook(
                notebook_path,
                working_directory=resolved_config.project_root,
                timeout=resolved_config.notebook_timeout_seconds,
            )
        finally:
            if previous_flag is None:
                os.environ.pop("INVEST_A_BULL_NOTEBOOK_REFRESH", None)
            else:
                os.environ["INVEST_A_BULL_NOTEBOOK_REFRESH"] = previous_flag
        outputs["notebook"] = notebook_path

    # Defer README update until all other steps have succeeded so that a
    # notebook failure never leaves the repository partially refreshed.
    if update_readme:
        readme_path = resolved_config.project_root / "README.md"
        summary_section = build_readme_latest_results_section(
            generated_at=generated_at,
            data_as_of=metadata["data_as_of"],
            selection_source=metadata["selection_source"],
            top_selection=top_selection,
            portfolio_summary=portfolio_summary,
            monte_carlo_summary=monte_carlo_summary,
        )
        update_readme_with_latest_results(readme_path, summary_section)
        outputs["readme"] = readme_path

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Invest-a-Bull reports, README, and notebook outputs.")
    parser.add_argument("--skip-notebook", action="store_true", help="Skip executing MasterAnalysisFinal.ipynb.")
    parser.add_argument("--skip-readme", action="store_true", help="Skip updating the README latest-results section.")
    args = parser.parse_args()

    outputs = refresh_project_assets(
        execute_master_notebook=not args.skip_notebook,
        update_readme=not args.skip_readme,
    )
    print("Invest-a-Bull automation completed successfully.")
    for label, path in outputs.items():
        print(f"- {label}: {path}")


