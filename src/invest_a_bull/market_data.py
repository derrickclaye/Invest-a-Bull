from __future__ import annotations

from typing import Iterable

import pandas as pd
import yfinance as yf

from .config import AnalysisConfig


def _as_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=[
                "screen",
                "symbol",
                "name",
                "quote_type",
                "exchange",
                "price",
                "day_change_pct",
                "market_cap",
                "avg_volume_3m",
            ]
        )
    return pd.DataFrame.from_records(records)


def fetch_screener_candidates(config: AnalysisConfig) -> tuple[pd.DataFrame, str]:
    records: list[dict] = []
    failures: dict[str, str] = {}

    for screen_name in config.screener_queries:
        try:
            response = yf.screen(screen_name, count=config.screener_count)
            quotes = response.get("quotes", [])
            for quote in quotes:
                records.append(
                    {
                        "screen": screen_name,
                        "symbol": quote.get("symbol"),
                        "name": quote.get("longName") or quote.get("shortName") or quote.get("symbol"),
                        "quote_type": quote.get("quoteType"),
                        "exchange": quote.get("exchange"),
                        "price": quote.get("regularMarketPrice"),
                        "day_change_pct": quote.get("regularMarketChangePercent"),
                        "market_cap": quote.get("marketCap"),
                        "avg_volume_3m": quote.get("averageDailyVolume3Month"),
                    }
                )
        except Exception as exc:  # pragma: no cover - network-dependent path
            failures[screen_name] = str(exc)

    frame = _as_dataframe(records)
    if not frame.empty:
        frame = frame.dropna(subset=["symbol"]).copy()
        frame = frame[
            (frame["quote_type"] == "EQUITY")
            & (frame["exchange"].isin(config.allowed_exchanges))
        ].copy()
        frame = frame[
            (frame["price"].fillna(0) >= config.min_price)
            & (frame["market_cap"].fillna(0) >= config.min_market_cap)
        ].copy()

    if frame.empty:
        fallback = pd.DataFrame(
            {
                "screen": "fallback_momentum_universe",
                "symbol": list(config.fallback_universe),
                "name": list(config.fallback_universe),
                "quote_type": "EQUITY",
                "exchange": "NMS",
                "price": pd.NA,
                "day_change_pct": pd.NA,
                "market_cap": pd.NA,
                "avg_volume_3m": pd.NA,
            }
        )
        reason = "fallback_momentum_universe"
        if failures:
            reason = f"fallback_momentum_universe ({'; '.join(f'{k}: {v}' for k, v in failures.items())})"
        return fallback, reason

    return frame, "yfinance_screeners"


def aggregate_candidates(candidate_rows: pd.DataFrame) -> pd.DataFrame:
    if candidate_rows.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "name",
                "screen_hits",
                "screens",
                "screen_presence_score",
                "price",
                "day_change_pct",
                "market_cap",
                "avg_volume_3m",
            ]
        )

    grouped = candidate_rows.groupby("symbol", as_index=False).agg(
        name=("name", "first"),
        screen_hits=("screen", "count"),
        screens=("screen", lambda values: ", ".join(sorted(set(values)))),
        price=("price", "max"),
        day_change_pct=("day_change_pct", "max"),
        market_cap=("market_cap", "max"),
        avg_volume_3m=("avg_volume_3m", "max"),
    )
    max_hits = max(grouped["screen_hits"].max(), 1)
    grouped["screen_presence_score"] = grouped["screen_hits"] / max_hits
    return grouped.sort_values(["screen_hits", "market_cap"], ascending=[False, False]).reset_index(drop=True)


def download_adjusted_close(tickers: Iterable[str], period: str) -> pd.DataFrame:
    ticker_list = list(dict.fromkeys(tickers))
    if not ticker_list:
        raise ValueError("At least one ticker is required.")

    data = yf.download(ticker_list, period=period, interval="1d", auto_adjust=False, progress=False, threads=True)
    if data.empty:
        raise ValueError("No price data returned from Yahoo Finance.")

    if isinstance(data.columns, pd.MultiIndex):
        price_level = data.columns.get_level_values(0)
        target_col = "Adj Close" if "Adj Close" in price_level else "Close"
        prices = data[target_col].copy()
    else:
        target_col = "Adj Close" if "Adj Close" in data.columns else "Close"
        ticker = ticker_list[0]
        prices = data[[target_col]].copy()
        prices.columns = [ticker]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=ticker_list[0])

    return prices.dropna(axis=0, how="all").sort_index()


def download_benchmark_close(ticker: str, period: str) -> pd.Series:
    return download_adjusted_close([ticker], period=period).iloc[:, 0].dropna()


