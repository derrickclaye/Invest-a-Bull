from __future__ import annotations

import numpy as np
import pandas as pd


def trailing_return(series: pd.Series, trading_days: int) -> float:
    clean = series.dropna()
    if len(clean) <= trading_days:
        return float("nan")
    return float(clean.iloc[-1] / clean.iloc[-trading_days - 1] - 1)


def max_drawdown(series: pd.Series) -> float:
    cumulative_max = series.cummax()
    drawdowns = series / cumulative_max - 1
    return float(drawdowns.min())


def _normalize(values: pd.Series) -> pd.Series:
    values = values.astype(float)
    min_value = values.min()
    max_value = values.max()
    if pd.isna(min_value) or pd.isna(max_value) or np.isclose(min_value, max_value):
        return pd.Series(0.5, index=values.index, dtype=float)
    return (values - min_value) / (max_value - min_value)


TREND_SCORE_WEIGHTS: dict[str, float] = {
    "screen_hits": 0.20,
    "day_change_pct": 0.15,
    "return_5d": 0.15,
    "return_21d": 0.20,
    "return_63d": 0.15,
    "dollar_volume": 0.15,
}


def compute_security_metrics(candidates: pd.DataFrame, price_history: pd.DataFrame) -> pd.DataFrame:
    available = [ticker for ticker in candidates["symbol"].tolist() if ticker in price_history.columns]
    if not available:
        raise ValueError("None of the candidate tickers were present in the downloaded price history.")

    aligned_candidates = candidates[candidates["symbol"].isin(available)].copy()
    metrics_rows: list[dict] = []

    for ticker in available:
        prices = price_history[ticker].dropna()
        if len(prices) < 2:
            continue
        daily_returns = prices.pct_change().dropna()
        metrics_rows.append(
            {
                "symbol": ticker,
                "history_rows": int(len(prices)),
                "history_start": prices.index.min().date().isoformat(),
                "history_end": prices.index.max().date().isoformat(),
                "latest_close": float(prices.iloc[-1]),
                "return_5d": trailing_return(prices, 5),
                "return_21d": trailing_return(prices, 21),
                "return_63d": trailing_return(prices, 63),
                "ann_volatility": float(daily_returns.std() * np.sqrt(252)) if not daily_returns.empty else float("nan"),
                "max_drawdown": max_drawdown(prices),
            }
        )

    metrics = pd.DataFrame(metrics_rows)
    if metrics.empty:
        raise ValueError("Downloaded price history did not contain enough observations for any candidate ticker.")

    combined = aligned_candidates.merge(metrics, on="symbol", how="inner")
    combined["dollar_volume"] = combined["latest_close"] * combined["avg_volume_3m"].fillna(0)
    return combined


def rank_trending_stocks(metrics: pd.DataFrame, top_n: int) -> pd.DataFrame:
    ranked = metrics.copy()
    for column in TREND_SCORE_WEIGHTS:
        ranked[f"{column}_norm"] = _normalize(ranked[column].fillna(0))

    ranked["trend_score"] = sum(
        ranked[f"{column}_norm"] * weight for column, weight in TREND_SCORE_WEIGHTS.items()
    )
    ranked = ranked.sort_values(
        ["trend_score", "screen_hits", "dollar_volume"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    ranked.insert(0, "rank", range(1, len(ranked) + 1))
    return ranked.head(top_n).copy()


def equal_weight_portfolio_returns(price_history: pd.DataFrame) -> pd.Series:
    daily_returns = price_history.pct_change().dropna(how="all")
    weights = np.repeat(1 / daily_returns.shape[1], daily_returns.shape[1])
    return pd.Series(daily_returns.to_numpy().dot(weights), index=daily_returns.index, name="portfolio_return")


def portfolio_summary(price_history: pd.DataFrame, benchmark: pd.Series, risk_free_rate: float) -> pd.DataFrame:
    portfolio_returns = equal_weight_portfolio_returns(price_history)
    cumulative = (1 + portfolio_returns).cumprod()
    periods = len(portfolio_returns)
    total_growth = float((1 + portfolio_returns).prod()) if periods else float("nan")
    if periods and total_growth > 0:
        annual_return = float(total_growth ** (252 / periods) - 1)
    else:
        annual_return = float("nan")
    annual_volatility = float(portfolio_returns.std() * np.sqrt(252))
    sharpe = float((annual_return - risk_free_rate) / annual_volatility) if annual_volatility else float("nan")
    total_return = float(cumulative.iloc[-1] - 1)

    benchmark_window = benchmark.reindex(price_history.index).dropna()
    if len(benchmark_window) > 1:
        benchmark_returns = benchmark_window.pct_change().dropna()
        benchmark_total_return = float((1 + benchmark_returns).cumprod().iloc[-1] - 1)
    else:
        benchmark_total_return = float("nan")

    return pd.DataFrame(
        [
            {"metric": "Portfolio total return (lookback)", "value": total_return},
            {"metric": "Portfolio annualized return", "value": annual_return},
            {"metric": "Portfolio annualized volatility", "value": annual_volatility},
            {"metric": "Portfolio Sharpe ratio", "value": sharpe},
            {"metric": "Portfolio max drawdown", "value": max_drawdown(cumulative)},
            {"metric": f"{benchmark.name} total return (lookback)", "value": benchmark_total_return},
        ]
    )


def correlation_matrix(price_history: pd.DataFrame) -> pd.DataFrame:
    return price_history.pct_change().dropna(how="all").corr()
