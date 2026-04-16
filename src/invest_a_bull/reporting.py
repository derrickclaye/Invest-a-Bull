from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def format_percent(value: float) -> str:
    return "n/a" if pd.isna(value) else f"{value:.2%}"


def format_percent_points(value: float) -> str:
    return "n/a" if pd.isna(value) else f"{value / 100:.2%}"


def format_ratio(value: float) -> str:
    return "n/a" if pd.isna(value) else f"{value:,.2f}"


def format_number(value: float, digits: int = 2) -> str:
    return "n/a" if pd.isna(value) else f"{value:,.{digits}f}"


def format_billions(value: float) -> str:
    return "n/a" if pd.isna(value) else f"${value / 1_000_000_000:,.1f}B"


def format_millions(value: float) -> str:
    return "n/a" if pd.isna(value) else f"{value / 1_000_000:,.1f}M"


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def plot_normalized_prices(price_history: pd.DataFrame, output_path: Path) -> None:
    normalized = price_history / price_history.iloc[0]
    ax = normalized.plot(figsize=(12, 6), linewidth=2)
    ax.set_title("Top 5 Trending Stocks - Normalized Price Performance")
    ax.set_ylabel("Growth of $1")
    ax.set_xlabel("Date")
    ax.grid(alpha=0.2)
    ax.figure.tight_layout()
    ax.figure.savefig(output_path, dpi=180)
    plt.close(ax.figure)


def plot_correlation_heatmap(correlation: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(correlation, annot=True, cmap="RdYlGn", center=0, fmt=".2f", ax=ax)
    ax.set_title("Top 5 Trending Stocks - Return Correlation")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def write_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def build_report_markdown(
    *,
    generated_at: datetime,
    data_as_of: str,
    selection_source: str,
    candidate_count: int,
    top_selection: pd.DataFrame,
    portfolio_summary: pd.DataFrame,
    monte_carlo_summary: pd.Series,
    figures: dict[str, str],
) -> str:
    report_table = top_selection[[
        "rank",
        "symbol",
        "name",
        "screens",
        "trend_score",
        "day_change_pct",
        "return_5d",
        "return_21d",
        "return_63d",
        "market_cap",
        "avg_volume_3m",
    ]].copy()
    report_table["trend_score"] = report_table["trend_score"].map(lambda value: format_number(value, 3))
    report_table["day_change_pct"] = report_table["day_change_pct"].map(format_percent_points)
    report_table["return_5d"] = report_table["return_5d"].map(format_percent)
    report_table["return_21d"] = report_table["return_21d"].map(format_percent)
    report_table["return_63d"] = report_table["return_63d"].map(format_percent)
    report_table["market_cap"] = report_table["market_cap"].map(format_billions)
    report_table["avg_volume_3m"] = report_table["avg_volume_3m"].map(format_millions)
    report_table.columns = [
        "Rank",
        "Ticker",
        "Company",
        "Source Screens",
        "Trend Score",
        "1D Move",
        "5D Return",
        "1M Return",
        "3M Return",
        "Market Cap",
        "Avg 3M Volume",
    ]

    portfolio_table = portfolio_summary.copy()
    portfolio_table["value"] = portfolio_table.apply(
        lambda row: format_ratio(row["value"]) if "Sharpe" in row["metric"] else format_percent(row["value"]),
        axis=1,
    )
    portfolio_table.columns = ["Metric", "Value"]

    mc_table = monte_carlo_summary.reset_index()
    mc_table.columns = ["Metric", "Value"]
    def _format_mc_value(row: pd.Series) -> str:
        metric = row["Metric"]
        value = row["Value"]
        if metric == "count":
            return format_number(value, 0)
        if metric == "std":
            return format_percent(value)
        if metric in {"mean", "min", "25%", "50%", "75%", "max", "95% CI Lower", "95% CI Upper"}:
            return format_percent(value - 1)
        return format_number(value, 4)

    mc_table["Value"] = mc_table.apply(_format_mc_value, axis=1)

    return f"""# Invest-a-Bull Senior Market Report

Generated: {generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Executive summary

This report identifies the **top 5 trending U.S. stocks** using a blended ranking model that combines:

- current Yahoo Finance screener presence
- latest 1-day move
- trailing 5-day, 1-month, and 3-month momentum
- liquidity via average 3-month dollar volume

Data source: `{selection_source}`  
Universe size after filtering: **{candidate_count} stocks**  
Latest market data used in the report: **{data_as_of}**

## Top 5 trending stocks

{dataframe_to_markdown(report_table)}

## Portfolio view

The selected names are combined into an equal-weight portfolio to estimate how the current trend basket behaves as a single product.

{dataframe_to_markdown(portfolio_table)}

## Monte Carlo outlook

A 1-year Monte Carlo simulation is run on the equal-weight basket using recent daily return mean and volatility as inputs.

{dataframe_to_markdown(mc_table)}

## Visual outputs

- Normalized price chart: `{figures['normalized_prices']}`
- Correlation heatmap: `{figures['correlation_heatmap']}`

## Methodology notes

1. Pull candidate names from Yahoo predefined screens: `most_actives`, `day_gainers`, and `growth_technology_stocks`.
2. Filter for listed U.S. equities and require minimum price and market-cap thresholds.
3. Download the latest daily adjusted-close history and compute momentum, volatility, and liquidity features.
4. Rank names using a weighted composite trend score and keep the top 5.
5. Produce an equal-weight portfolio view and a Monte Carlo scenario range for decision support.

## Disclaimer

This project is for analytics and educational use only and should not be interpreted as personalized investment advice.
"""


def build_data_quality_markdown(
    *,
    generated_at: datetime,
    candidate_count: int,
    selected_count: int,
    price_rows: int,
    missing_cells: int,
    selection_source: str,
) -> str:
    return f"""# Data Quality Report

Generated: {generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

- Candidate universe count: **{candidate_count}**
- Selected top-n count: **{selected_count}**
- Price-history row count: **{price_rows}**
- Missing values in selected price matrix: **{missing_cells}**
- Selection source: `{selection_source}`

The pipeline rejects empty universes, removes non-equity results, and keeps only symbols with downloadable price history.
"""


