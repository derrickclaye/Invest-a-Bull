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

    portfolio_returns = daily_returns.mean(axis=1)
    lower_bound = float(portfolio_returns.quantile(0.05))
    upper_bound = float(portfolio_returns.quantile(0.95))
    stabilized_returns = portfolio_returns.clip(lower=lower_bound, upper=upper_bound).to_numpy()
    if stabilized_returns.size == 0:
        raise ValueError("Price history must contain enough rows to simulate portfolio paths.")

    rng = np.random.default_rng(random_seed)
    simulated_portfolio_returns = rng.choice(
        stabilized_returns,
        size=(num_trading_days, num_simulations),
        replace=True,
    )
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
