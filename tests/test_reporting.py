from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from invest_a_bull.reporting import build_readme_latest_results_section, build_report_markdown


class ReportingTests(unittest.TestCase):
    def test_readme_section_uses_dynamic_selection_count_and_paths(self) -> None:
        top_selection = pd.DataFrame(
            {
                "rank": [1, 2, 3],
                "symbol": ["AAA", "BBB", "CCC"],
                "name": ["A", "B", "C"],
                "trend_score": [0.7, 0.6, 0.5],
                "return_21d": [0.1, 0.09, 0.08],
                "return_63d": [0.2, 0.18, 0.16],
            }
        )
        portfolio_summary = pd.DataFrame(
            {
                "metric": [
                    "Portfolio total return (lookback)",
                    "Portfolio Sharpe ratio",
                    "Portfolio max drawdown",
                ],
                "value": [0.25, 1.5, -0.1],
            }
        )
        mc_summary = pd.Series({"mean": 1.2, "95% CI Lower": 0.9, "95% CI Upper": 1.5})

        section = build_readme_latest_results_section(
            generated_at=datetime(2026, 5, 5, tzinfo=timezone.utc),
            data_as_of="2026-05-04",
            selection_source="unit_test_source",
            top_selection=top_selection,
            portfolio_summary=portfolio_summary,
            monte_carlo_summary=mc_summary,
        )

        self.assertIn("Top 3 trending stocks", section)
        self.assertIn("Current top-3 snapshot", section)
        self.assertIn("reports/latest_top3_stock_report.md", section)
        self.assertIn("data/processed/latest_top3_selection.csv", section)

    def test_report_markdown_uses_dynamic_selection_count(self) -> None:
        top_selection = pd.DataFrame(
            {
                "rank": [1, 2, 3],
                "symbol": ["AAA", "BBB", "CCC"],
                "name": ["A", "B", "C"],
                "screens": ["s1", "s1", "s2"],
                "trend_score": [0.7, 0.6, 0.5],
                "day_change_pct": [1.1, 0.9, 0.7],
                "return_5d": [0.03, 0.02, 0.01],
                "return_21d": [0.1, 0.09, 0.08],
                "return_63d": [0.2, 0.18, 0.16],
                "market_cap": [100_000_000_000, 90_000_000_000, 80_000_000_000],
                "avg_volume_3m": [1_000_000, 900_000, 800_000],
                "history_rows": [80, 80, 80],
            }
        )
        portfolio_summary = pd.DataFrame(
            {
                "metric": ["Portfolio total return (lookback)", "SPY total return (lookback)", "Portfolio Sharpe ratio"],
                "value": [0.22, 0.12, 1.6],
            }
        )
        mc_summary = pd.Series({"mean": 1.2, "95% CI Lower": 0.9, "95% CI Upper": 1.5})

        report = build_report_markdown(
            generated_at=datetime(2026, 5, 5, tzinfo=timezone.utc),
            data_as_of="2026-05-04",
            selection_source="unit_test_source",
            candidate_count=50,
            min_history_days=21,
            screener_queries=("most_actives", "day_gainers"),
            top_selection=top_selection,
            portfolio_summary=portfolio_summary,
            monte_carlo_summary=mc_summary,
            figures={
                "normalized_prices": "reports/figures/top3_normalized_performance.png",
                "correlation_heatmap": "reports/figures/top3_correlation_heatmap.png",
            },
        )

        self.assertIn("top 3 trending U.S. stocks", report)
        self.assertIn("## Top 3 trending stocks", report)
        self.assertIn("keep the top 3.", report)
        self.assertIn("at least 21 trading days of lookback", report)


if __name__ == "__main__":
    unittest.main()

