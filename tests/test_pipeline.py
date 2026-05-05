from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from invest_a_bull.config import AnalysisConfig
from invest_a_bull.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_run_pipeline_falls_back_to_best_available_shared_history_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = AnalysisConfig(
                project_root=root,
                top_n=3,
                min_history_days=5,
                monte_carlo_simulations=4,
                monte_carlo_days=5,
            )

            candidate_rows = pd.DataFrame({"screen": ["most_actives"], "symbol": ["AAA"]})
            candidate_universe = pd.DataFrame(
                {
                    "symbol": ["AAA", "BBB", "CCC"],
                    "name": ["A", "B", "C"],
                    "screen_hits": [2, 2, 1],
                    "screens": ["s1, s2", "s1, s2", "s2"],
                    "price": [100.0, 90.0, 15.0],
                    "day_change_pct": [1.0, 0.8, 0.6],
                    "market_cap": [500_000_000_000, 400_000_000_000, 20_000_000_000],
                    "avg_volume_3m": [5_000_000, 4_000_000, 2_000_000],
                }
            )
            candidate_prices = pd.DataFrame(
                {
                    "AAA": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
                    "BBB": [90.0, 91.0, 92.0, 93.0, 94.0, 95.0],
                    "CCC": [np.nan, np.nan, 15.0, 15.5, 16.0, 16.5],
                },
                index=pd.date_range("2025-01-01", periods=6, freq="B"),
                dtype=float,
            )
            metrics = pd.DataFrame(
                {
                    "symbol": ["AAA", "BBB", "CCC"],
                    "name": ["A", "B", "C"],
                    "screen_hits": [2, 2, 1],
                    "screens": ["s1, s2", "s1, s2", "s2"],
                    "price": [100.0, 90.0, 15.0],
                    "day_change_pct": [1.0, 0.8, 0.6],
                    "market_cap": [500_000_000_000, 400_000_000_000, 20_000_000_000],
                    "avg_volume_3m": [5_000_000, 4_000_000, 2_000_000],
                    "latest_close": [105.0, 95.0, 16.5],
                    "return_5d": [0.05, 0.055, 0.10],
                    "return_21d": [0.10, 0.09, 0.14],
                    "return_63d": [0.14, 0.13, 0.18],
                    "ann_volatility": [0.20, 0.18, 0.35],
                    "max_drawdown": [-0.05, -0.04, -0.10],
                    "dollar_volume": [525_000_000, 380_000_000, 33_000_000],
                    "history_rows": [6, 6, 4],
                    "history_start": ["2025-01-01", "2025-01-01", "2025-01-03"],
                    "history_end": ["2025-01-08", "2025-01-08", "2025-01-08"],
                }
            )
            benchmark = pd.Series(
                [100.0, 100.5, 101.0, 101.5, 102.0, 102.5],
                index=candidate_prices.index,
                name="SPY",
            )

            with (
                patch("invest_a_bull.pipeline.fetch_screener_candidates", return_value=(candidate_rows, "unit_test_source")),
                patch("invest_a_bull.pipeline.aggregate_candidates", return_value=candidate_universe),
                patch("invest_a_bull.pipeline.download_adjusted_close", return_value=candidate_prices),
                patch("invest_a_bull.pipeline.compute_security_metrics", return_value=metrics),
                patch("invest_a_bull.pipeline.download_benchmark_close", return_value=benchmark),
                patch("invest_a_bull.pipeline.plot_normalized_prices"),
                patch("invest_a_bull.pipeline.plot_correlation_heatmap"),
            ):
                outputs = run_pipeline(config)

            top_selection = pd.read_csv(outputs["top_selection"])
            top_prices = pd.read_csv(outputs["top_prices"], index_col=0, parse_dates=True)
            metadata = json.loads(outputs["metadata"].read_text(encoding="utf-8"))

            self.assertCountEqual(top_selection["symbol"].tolist(), ["AAA", "BBB", "CCC"])
            self.assertEqual(len(top_prices), 4)
            self.assertEqual(metadata["eligible_count"], 2)
            self.assertCountEqual(metadata["selected_tickers"], ["AAA", "BBB", "CCC"])


if __name__ == "__main__":
    unittest.main()


