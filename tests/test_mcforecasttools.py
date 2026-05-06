from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from MCForecastTools import MCSimulation


class MCForecastToolsTests(unittest.TestCase):
    def _portfolio_prices(self) -> pd.DataFrame:
        index = pd.date_range("2026-01-01", periods=5, freq="B")
        columns = pd.MultiIndex.from_tuples(
            [
                ("AAA", "close"),
                ("BBB", "close"),
            ]
        )
        values = [
            [100.0, 50.0],
            [101.0, 50.5],
            [102.0, 51.0],
            [103.0, 51.5],
            [104.0, 52.0],
        ]
        return pd.DataFrame(values, index=index, columns=columns)

    def test_accepts_numpy_array_weights(self) -> None:
        simulation = MCSimulation(self._portfolio_prices(), weights=np.array([0.6, 0.4]), num_simulation=5, num_trading_days=5)
        self.assertTrue(np.allclose(simulation.weights, np.array([0.6, 0.4])))

    def test_raises_for_weight_sum_not_equal_to_one(self) -> None:
        with self.assertRaisesRegex(AttributeError, "Sum of portfolio weights"):
            MCSimulation(self._portfolio_prices(), weights=[0.7, 0.4], num_simulation=5, num_trading_days=5)


if __name__ == "__main__":
    unittest.main()

