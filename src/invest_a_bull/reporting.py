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


def _metric_lookup(summary: pd.DataFrame) -> dict[str, float]:
    return dict(zip(summary["metric"], summary["value"], strict=False))


def _posix_path(value: str) -> str:
    return value.replace("\\", "/")


def plot_normalized_prices(price_history: pd.DataFrame, output_path: Path) -> None:
    normalized = price_history / price_history.iloc[0]
    ax = normalized.plot(figsize=(12, 6), linewidth=2)
    ax.set_title(f"Top {price_history.shape[1]} Trending Stocks - Normalized Price Performance")
    ax.set_ylabel("Growth of $1")
    ax.set_xlabel("Date")
    ax.grid(alpha=0.2)
    ax.figure.tight_layout()
    ax.figure.savefig(output_path, dpi=180)
    plt.close(ax.figure)


def plot_correlation_heatmap(correlation: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(correlation, annot=True, cmap="RdYlGn", center=0, fmt=".2f", ax=ax)
    ax.set_title(f"Top {correlation.shape[0]} Trending Stocks - Return Correlation")
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
    screener_queries: tuple[str, ...],
    top_selection: pd.DataFrame,
    portfolio_summary: pd.DataFrame,
    monte_carlo_summary: pd.Series,
    figures: dict[str, str],
) -> str:
    selected_count = len(top_selection)
    portfolio_metrics = _metric_lookup(portfolio_summary)
    portfolio_total_return = portfolio_metrics.get("Portfolio total return (lookback)", float("nan"))
    benchmark_key = next(
        (
            key
            for key in portfolio_metrics
            if key.endswith("total return (lookback)") and key != "Portfolio total return (lookback)"
        ),
        None,
    )
    benchmark_total_return = portfolio_metrics.get(benchmark_key, float("nan")) if benchmark_key else float("nan")
    relative_performance = portfolio_total_return - benchmark_total_return
    expected_mc_return = monte_carlo_summary.get("mean", float("nan")) - 1
    mc_lower = monte_carlo_summary.get("95% CI Lower", float("nan")) - 1
    mc_upper = monte_carlo_summary.get("95% CI Upper", float("nan")) - 1

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
        "history_rows",
    ]].copy()
    report_table["trend_score"] = report_table["trend_score"].map(lambda value: format_number(value, 3))
    report_table["day_change_pct"] = report_table["day_change_pct"].map(format_percent_points)
    report_table["return_5d"] = report_table["return_5d"].map(format_percent)
    report_table["return_21d"] = report_table["return_21d"].map(format_percent)
    report_table["return_63d"] = report_table["return_63d"].map(format_percent)
    report_table["market_cap"] = report_table["market_cap"].map(format_billions)
    report_table["avg_volume_3m"] = report_table["avg_volume_3m"].map(format_millions)
    report_table["history_rows"] = report_table["history_rows"].map(lambda value: format_number(value, 0))
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
        "History Rows",
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

This report identifies the **top {selected_count} trending U.S. stocks** using a blended ranking model that combines:

- current Yahoo Finance screener presence
- latest 1-day move
- trailing 5-day, 1-month, and 3-month momentum
- liquidity via average 3-month dollar volume
- minimum-history preference for more decision-useful names

Data source: `{selection_source}`  
Universe size after filtering: **{candidate_count} stocks**  
Latest market data used in the report: **{data_as_of}**

### Key takeaways

- Selected basket: **{', '.join(top_selection['symbol'].tolist())}**
- Lookback portfolio return: **{format_percent(portfolio_total_return)}**
- Relative performance vs benchmark: **{format_percent(relative_performance)}**
- Monte Carlo expected terminal return: **{format_percent(expected_mc_return)}**
- Monte Carlo 95% range: **{format_percent(mc_lower)} to {format_percent(mc_upper)}**

## Top {selected_count} trending stocks

{dataframe_to_markdown(report_table)}

## Portfolio view

The selected names are combined into an equal-weight portfolio to estimate how the current trend basket behaves as a single product.

{dataframe_to_markdown(portfolio_table)}

## Monte Carlo outlook

A 1-year bootstrap Monte Carlo simulation is run on the equal-weight basket using stabilized empirical portfolio returns.

{dataframe_to_markdown(mc_table)}

## Visual outputs

- Normalized price chart: `{_posix_path(figures['normalized_prices'])}`
- Correlation heatmap: `{_posix_path(figures['correlation_heatmap'])}`

## Methodology notes

1. Pull candidate names from the configured Yahoo predefined screens: `{', '.join(screener_queries)}`.
2. Filter for listed U.S. equities and require minimum price and market-cap thresholds.
3. Download the latest daily adjusted-close history and prefer names with at least a 3-month lookback when available.
4. Rank names using a weighted composite trend score and keep the top {selected_count}.
5. Produce an equal-weight portfolio view and a scenario range for decision support.

## Disclaimer

This project is for analytics and educational use only and should not be interpreted as personalized investment advice.
"""


def build_data_quality_markdown(
    *,
    generated_at: datetime,
    data_as_of: str,
    candidate_count: int,
    eligible_count: int,
    selected_count: int,
    price_rows: int,
    missing_cells: int,
    selection_source: str,
    min_history_days: int,
    preferred_history_rows: int,
    excluded_for_history: int,
    selected_history: pd.DataFrame,
) -> str:
    history_table = selected_history.copy()
    if not history_table.empty:
        history_table.columns = [
            "Ticker",
            "Observations",
            "History Start",
            "History End",
            "Missing Cells",
            "Meets Minimum History",
        ]
        history_table["Observations"] = history_table["Observations"].map(lambda value: format_number(value, 0))
        history_table["Meets Minimum History"] = history_table["Meets Minimum History"].map(
            lambda flag: "Yes" if flag else "Fallback"
        )

    return f"""# Data Quality Report

Generated: {generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

- Latest market data used: **{data_as_of}**
- Candidate universe count: **{candidate_count}**
- Eligible securities with sufficient history: **{eligible_count}**
- Selected top-n count: **{selected_count}**
- Price-history row count: **{price_rows}**
- Missing values in selected price matrix: **{missing_cells}**
- Selection source: `{selection_source}`
- Minimum price-history requirement for preferred selection: **{preferred_history_rows} rows** (`{min_history_days}` trailing trading days plus the starting observation)
- Candidates excluded for insufficient history before fallback handling: **{excluded_for_history}**

The pipeline rejects empty universes, removes non-equity results, and keeps only symbols with downloadable price history.

## Selected ticker coverage

{dataframe_to_markdown(history_table) if not history_table.empty else 'No selected ticker history was available.'}
"""


README_AUTO_SECTION_START = "<!-- AUTO-GENERATED:START -->"
README_AUTO_SECTION_END = "<!-- AUTO-GENERATED:END -->"


def build_readme_latest_results_section(
    *,
    generated_at: datetime,
    data_as_of: str,
    selection_source: str,
    top_selection: pd.DataFrame,
    portfolio_summary: pd.DataFrame,
    monte_carlo_summary: pd.Series,
) -> str:
    selected_count = len(top_selection)
    selection_label = f"top{selected_count}"
    portfolio_metrics = _metric_lookup(portfolio_summary)
    lookback_return = portfolio_metrics.get("Portfolio total return (lookback)", float("nan"))
    sharpe_ratio = portfolio_metrics.get("Portfolio Sharpe ratio", float("nan"))
    drawdown = portfolio_metrics.get("Portfolio max drawdown", float("nan"))
    mc_expected = monte_carlo_summary.get("mean", float("nan")) - 1
    mc_lower = monte_carlo_summary.get("95% CI Lower", float("nan")) - 1
    mc_upper = monte_carlo_summary.get("95% CI Upper", float("nan")) - 1

    readme_table = top_selection[["rank", "symbol", "name", "trend_score", "return_21d", "return_63d"]].copy()
    readme_table.columns = ["Rank", "Ticker", "Company", "Trend Score", "1M Return", "3M Return"]
    readme_table["Trend Score"] = readme_table["Trend Score"].map(lambda value: format_number(value, 3))
    readme_table["1M Return"] = readme_table["1M Return"].map(format_percent)
    readme_table["3M Return"] = readme_table["3M Return"].map(format_percent)

    return f"""{README_AUTO_SECTION_START}
## Latest generated result

Most recent successful automated run:

- **Generated:** {generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Latest market data used:** {data_as_of}
- **Selection source:** `{selection_source}`
- **Top {selected_count} trending stocks:** `{', '.join(top_selection['symbol'].tolist())}`
- **Lookback portfolio return:** {format_percent(lookback_return)}
- **Portfolio Sharpe ratio:** {format_ratio(sharpe_ratio)}
- **Portfolio max drawdown:** {format_percent(drawdown)}
- **Monte Carlo expected terminal return:** {format_percent(mc_expected)}
- **Monte Carlo 95% range:** {format_percent(mc_lower)} to {format_percent(mc_upper)}

### Current top-{selected_count} snapshot

{dataframe_to_markdown(readme_table)}

See the generated deliverables:

- `reports/latest_{selection_label}_stock_report.md`
- `reports/data_quality_report.md`
- `data/processed/latest_{selection_label}_selection.csv`
- `data/processed/latest_portfolio_summary.csv`
- `reports/figures/{selection_label}_normalized_performance.png`
- `reports/figures/{selection_label}_correlation_heatmap.png`
{README_AUTO_SECTION_END}"""


def update_readme_with_latest_results(readme_path: Path, summary_section: str) -> None:
    current = readme_path.read_text(encoding="utf-8")
    if README_AUTO_SECTION_START not in current or README_AUTO_SECTION_END not in current:
        raise ValueError("README.md is missing the auto-generated section markers.")

    start_index = current.index(README_AUTO_SECTION_START)
    end_index = current.index(README_AUTO_SECTION_END) + len(README_AUTO_SECTION_END)
    refreshed = current[:start_index] + summary_section + current[end_index:]
    readme_path.write_text(refreshed, encoding="utf-8")

