from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_portfolio_paths(
    price_history: pd.DataFrame,
    num_simulations: int,
    num_trading_days: int,
    random_seed: int,
) -> pd.DataFrame:
    daily_returns = price_history.pct_change().dropna(how="all")
    if daily_returns.empty:
        raise ValueError("Price history must contain enough rows to calculate returns.")

    weights = np.repeat(1 / daily_returns.shape[1], daily_returns.shape[1])
    mean_returns = daily_returns.mean().to_numpy()
    std_returns = daily_returns.std().replace(0, 1e-9).to_numpy()

    rng = np.random.default_rng(random_seed)
    simulated_asset_returns = rng.normal(
        loc=mean_returns[:, None, None],
        scale=std_returns[:, None, None],
        size=(len(mean_returns), num_trading_days, num_simulations),
    )
    simulated_portfolio_returns = np.tensordot(weights, simulated_asset_returns, axes=(0, 0))
    cumulative_paths = np.vstack(
        [
            np.ones((1, num_simulations)),
            np.cumprod(1 + simulated_portfolio_returns, axis=0),
        ]
    )

    return pd.DataFrame(cumulative_paths, columns=[f"sim_{i+1}" for i in range(num_simulations)])


def summarize_simulation(paths: pd.DataFrame) -> pd.Series:
    terminal = paths.iloc[-1]
    summary = terminal.describe()
    ci = terminal.quantile([0.025, 0.975]).copy()
    ci.index = ["95% CI Lower", "95% CI Upper"]
    combined = pd.concat([summary, ci], axis=0)
    return pd.Series(combined, dtype=float)


