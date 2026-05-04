from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nbformat
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from invest_a_bull.automation import refresh_project_assets
from invest_a_bull.config import AnalysisConfig


class AutomationTests(unittest.TestCase):
    def _write_pipeline_outputs(self, root: Path) -> dict[str, Path]:
        data_dir = root / "data" / "processed"
        reports_dir = root / "reports"
        data_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = data_dir / "latest_run_metadata.json"
        metadata_path.write_text(
            json.dumps(
                {
                    "generated_at_utc": "2026-05-04T00:00:00+00:00",
                    "data_as_of": "2026-05-01",
                    "selection_source": "unit_test_source",
                    "selected_tickers": ["AAA", "BBB", "CCC", "DDD", "EEE"],
                }
            ),
            encoding="utf-8",
        )

        top_selection_path = data_dir / "latest_top5_selection.csv"
        pd.DataFrame(
            {
                "rank": [1, 2, 3, 4, 5],
                "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE"],
                "name": ["A", "B", "C", "D", "E"],
                "trend_score": [0.5, 0.4, 0.3, 0.2, 0.1],
                "return_21d": [0.1, 0.09, 0.08, 0.07, 0.06],
                "return_63d": [0.2, 0.18, 0.16, 0.14, 0.12],
            }
        ).to_csv(top_selection_path, index=False)

        portfolio_summary_path = data_dir / "latest_portfolio_summary.csv"
        pd.DataFrame(
            {
                "metric": [
                    "Portfolio total return (lookback)",
                    "Portfolio Sharpe ratio",
                    "Portfolio max drawdown",
                ],
                "value": [0.25, 1.5, -0.1],
            }
        ).to_csv(portfolio_summary_path, index=False)

        monte_carlo_summary_path = data_dir / "latest_monte_carlo_summary.csv"
        pd.Series({"mean": 1.2, "95% CI Lower": 0.8, "95% CI Upper": 1.6}, name="value").to_csv(
            monte_carlo_summary_path,
            header=True,
        )

        report_path = reports_dir / "latest_top5_stock_report.md"
        report_path.write_text("report", encoding="utf-8")
        dq_path = reports_dir / "data_quality_report.md"
        dq_path.write_text("dq", encoding="utf-8")

        return {
            "top_selection": top_selection_path,
            "portfolio_summary": portfolio_summary_path,
            "monte_carlo_summary": monte_carlo_summary_path,
            "metadata": metadata_path,
            "report": report_path,
            "data_quality_report": dq_path,
        }

    def test_refresh_project_assets_updates_readme_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            outputs = self._write_pipeline_outputs(root)
            config = AnalysisConfig(project_root=root)

            with (
                patch("invest_a_bull.automation.run_pipeline", return_value=outputs),
                patch("invest_a_bull.automation.build_readme_latest_results_section", return_value="section") as build_section,
                patch("invest_a_bull.automation.update_readme_with_latest_results") as update_readme,
            ):
                refreshed = refresh_project_assets(config=config, execute_master_notebook=False, update_readme=True)

            self.assertIn("readme", refreshed)
            self.assertNotIn("notebook", refreshed)
            build_section.assert_called_once()
            update_readme.assert_called_once_with(root / "README.md", "section")

    def test_refresh_project_assets_executes_notebook_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            notebook_path = root / "MasterAnalysisFinal.ipynb"
            nbformat.write(nbformat.v4.new_notebook(), notebook_path)
            outputs = self._write_pipeline_outputs(root)
            config = AnalysisConfig(project_root=root)

            with patch("invest_a_bull.automation.run_pipeline", return_value=outputs), patch(
                "invest_a_bull.automation.execute_notebook",
                return_value=notebook_path,
            ) as execute_notebook:
                refreshed = refresh_project_assets(config=config, execute_master_notebook=True, update_readme=False)

            self.assertIn("notebook", refreshed)
            execute_notebook.assert_called_once_with(
                notebook_path,
                working_directory=root,
                timeout=config.notebook_timeout_seconds,
            )


if __name__ == "__main__":
    unittest.main()

