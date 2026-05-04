from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from invest_a_bull.analytics import compute_security_metrics, portfolio_summary, rank_trending_stocks, trailing_return
from invest_a_bull.config import AnalysisConfig
from invest_a_bull.market_data import fetch_screener_candidates
from invest_a_bull.pipeline import _select_top_candidates_with_shared_history
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

    def test_compute_security_metrics_tracks_history_depth(self) -> None:
        candidates = pd.DataFrame(
            {
                "symbol": ["AAA", "BBB"],
                "name": ["A", "B"],
                "screen_hits": [1, 1],
                "screens": ["s1", "s2"],
                "price": [10.0, 20.0],
                "day_change_pct": [0.01, 0.02],
                "market_cap": [10_000_000_000, 20_000_000_000],
                "avg_volume_3m": [1_000_000, 2_000_000],
            }
        )
        price_history = pd.DataFrame(
            {
                "AAA": [10, 10.5, 11, 11.5, 12],
                "BBB": [20, 20.2, 20.4, 20.6, 20.8],
            },
            index=pd.date_range("2025-01-01", periods=5, freq="B"),
        )

        metrics = compute_security_metrics(candidates, price_history)
        self.assertIn("history_rows", metrics.columns)
        self.assertTrue((metrics["history_rows"] == 5).all())
        self.assertIn("history_start", metrics.columns)
        self.assertIn("history_end", metrics.columns)

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
        self.assertTrue((paths.iloc[0] == 1).all())
        summary = summarize_simulation(paths)
        self.assertIn("95% CI Lower", summary.index)
        self.assertIn("95% CI Upper", summary.index)

    def test_portfolio_summary_aligns_benchmark_to_portfolio_window(self) -> None:
        price_history = pd.DataFrame(
            {
                "AAA": [100.0, 110.0, 121.0],
                "BBB": [50.0, 55.0, 60.5],
            },
            index=pd.date_range("2025-01-03", periods=3, freq="B"),
        )
        benchmark = pd.Series(
            [90.0, 100.0, 120.0, 132.0],
            index=pd.date_range("2025-01-02", periods=4, freq="B"),
            name="SPY",
        )

        summary = portfolio_summary(price_history, benchmark, risk_free_rate=0.0)
        benchmark_return = float(summary.loc[summary["metric"] == "SPY total return (lookback)", "value"].iloc[0])
        self.assertAlmostEqual(benchmark_return, 0.32)

    def test_portfolio_summary_annualizes_realized_compounded_return(self) -> None:
        price_history = pd.DataFrame(
            {
                "AAA": [100.0, 110.0, 121.0],
                "BBB": [50.0, 55.0, 60.5],
            },
            index=pd.date_range("2025-01-01", periods=3, freq="B"),
        )
        benchmark = pd.Series(
            [100.0, 101.0, 102.0],
            index=price_history.index,
            name="SPY",
        )

        summary = portfolio_summary(price_history, benchmark, risk_free_rate=0.0)
        annualized_return = float(summary.loc[summary["metric"] == "Portfolio annualized return", "value"].iloc[0])
        expected = float((1.21 ** (252 / 2)) - 1)
        self.assertAlmostEqual(annualized_return, expected, delta=1e-3)

    def test_fetch_screener_candidates_reports_partial_failures(self) -> None:
        config = AnalysisConfig(
            screener_queries=("most_actives", "day_gainers"),
            screener_count=1,
            min_price=1.0,
            min_market_cap=1,
        )
        success_payload = {
            "quotes": [
                {
                    "symbol": "AAA",
                    "longName": "Alpha Inc.",
                    "quoteType": "EQUITY",
                    "exchange": "NMS",
                    "regularMarketPrice": 10.0,
                    "regularMarketChangePercent": 1.5,
                    "marketCap": 10_000_000,
                    "averageDailyVolume3Month": 1_000_000,
                }
            ]
        }

        with patch("invest_a_bull.market_data.yf.screen", side_effect=[success_payload, RuntimeError("screen unavailable")]):
            frame, selection_source = fetch_screener_candidates(config)

        self.assertEqual(frame["symbol"].tolist(), ["AAA"])
        self.assertIn("yfinance_screeners_partial", selection_source)
        self.assertIn("day_gainers", selection_source)

    def test_select_top_candidates_with_shared_history_avoids_empty_overlap(self) -> None:
        metrics = pd.DataFrame(
            {
                "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE"],
                "name": ["A", "B", "C", "D", "E"],
                "screens": ["s1", "s1", "s1", "s2", "s2"],
                "screen_hits": [2, 2, 2, 1, 1],
                "day_change_pct": [0.03, 0.025, 0.02, 0.15, 0.14],
                "return_5d": [0.04, 0.035, 0.03, 0.25, 0.24],
                "return_21d": [0.08, 0.075, 0.07, 0.40, 0.39],
                "return_63d": [0.12, 0.11, 0.10, 0.60, 0.59],
                "avg_volume_3m": [5_000_000, 4_500_000, 4_000_000, 3_000_000, 2_500_000],
                "latest_close": [100.0, 95.0, 90.0, 15.0, 14.0],
                "market_cap": [500_000_000_000, 400_000_000_000, 300_000_000_000, 20_000_000_000, 18_000_000_000],
                "dollar_volume": [500_000_000, 427_500_000, 360_000_000, 45_000_000, 35_000_000],
                "history_rows": [10, 10, 10, 2, 2],
            }
        )
        candidate_prices = pd.DataFrame(
            {
                "AAA": [100, 101, 102, 103, 104, 105],
                "BBB": [90, 91, 92, 93, 94, 95],
                "CCC": [80, 81, 82, 83, 84, 85],
                "DDD": [np.nan, np.nan, np.nan, np.nan, 15, 16],
                "EEE": [np.nan, np.nan, np.nan, np.nan, 14, 15],
            },
            index=pd.date_range("2025-01-01", periods=6, freq="B"),
        )

        top_selection, top_prices = _select_top_candidates_with_shared_history(
            metrics,
            candidate_prices,
            top_n=3,
            min_shared_rows=2,
        )

        self.assertEqual(top_selection["symbol"].tolist(), ["AAA", "BBB", "CCC"])
        self.assertGreaterEqual(len(top_prices), 2)


if __name__ == "__main__":
    unittest.main()

