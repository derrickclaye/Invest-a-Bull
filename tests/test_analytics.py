from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from invest_a_bull.analytics import rank_trending_stocks, trailing_return
from invest_a_bull.simulation import simulate_portfolio_paths, summarize_simulation


class AnalyticsTests(unittest.TestCase):
    def test_trailing_return_uses_requested_window(self) -> None:
        series = pd.Series([100, 110, 121, 133.1])
        self.assertAlmostEqual(trailing_return(series, 2), 0.21)

    def test_rank_trending_stocks_returns_sorted_top_n(self) -> None:
        frame = pd.DataFrame(
            {
                "symbol": ["AAA", "BBB", "CCC"],
                "name": ["A", "B", "C"],
                "screens": ["s1", "s1, s2", "s2"],
                "screen_hits": [1, 2, 1],
                "day_change_pct": [0.01, 0.04, 0.02],
                "return_5d": [0.03, 0.06, 0.01],
                "return_21d": [0.05, 0.10, 0.02],
                "return_63d": [0.08, 0.12, 0.03],
                "avg_volume_3m": [1_000_000, 2_000_000, 900_000],
                "latest_close": [10.0, 20.0, 8.0],
                "market_cap": [10_000_000_000, 20_000_000_000, 9_000_000_000],
                "dollar_volume": [10_000_000, 40_000_000, 7_200_000],
            }
        )
        ranked = rank_trending_stocks(frame, top_n=2)
        self.assertEqual(ranked["symbol"].tolist(), ["BBB", "AAA"])
        self.assertEqual(ranked["rank"].tolist(), [1, 2])

    def test_simulation_outputs_expected_shape_and_summary(self) -> None:
        prices = pd.DataFrame(
            {
                "AAA": np.linspace(100, 120, 40),
                "BBB": np.linspace(50, 62, 40),
                "CCC": np.linspace(30, 45, 40),
            },
            index=pd.date_range("2025-01-01", periods=40, freq="B"),
        )
        paths = simulate_portfolio_paths(prices, num_simulations=25, num_trading_days=10, random_seed=42)
        self.assertEqual(paths.shape, (11, 25))
        summary = summarize_simulation(paths)
        self.assertIn("95% CI Lower", summary.index)
        self.assertIn("95% CI Upper", summary.index)


if __name__ == "__main__":
    unittest.main()

