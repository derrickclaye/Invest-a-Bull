from __future__ import annotations

import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .analytics import compute_security_metrics, correlation_matrix, portfolio_summary, rank_trending_stocks
from .config import AnalysisConfig
from .market_data import aggregate_candidates, download_adjusted_close, download_benchmark_close, fetch_screener_candidates
from .reporting import (
    build_data_quality_markdown,
    build_report_markdown,
    plot_correlation_heatmap,
    plot_normalized_prices,
    write_json,
)
from .simulation import simulate_portfolio_paths, summarize_simulation


def ensure_directories(config: AnalysisConfig) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.reports_dir.mkdir(parents=True, exist_ok=True)
    config.figures_dir.mkdir(parents=True, exist_ok=True)


def run_pipeline(config: AnalysisConfig | None = None) -> dict[str, Path]:
    resolved_config = config or AnalysisConfig()
    ensure_directories(resolved_config)

    generated_at = datetime.now(timezone.utc)
    candidate_rows, selection_source = fetch_screener_candidates(resolved_config)
    candidate_universe = aggregate_candidates(candidate_rows)
    candidate_symbols = candidate_universe["symbol"].tolist()

    if not candidate_symbols:
        raise ValueError("Candidate universe is empty after filtering.")

    candidate_prices = download_adjusted_close(candidate_symbols, period=resolved_config.price_history_period)
    metrics = compute_security_metrics(candidate_universe, candidate_prices)

    preferred_history_rows = resolved_config.min_history_days + 1
    sufficient_history = metrics["history_rows"] >= preferred_history_rows
    eligible_metrics = metrics.loc[sufficient_history].copy()
    excluded_for_history = int((~sufficient_history).sum())

    if len(eligible_metrics) < resolved_config.top_n:
        supplemental = metrics.loc[~sufficient_history].sort_values(
            ["history_rows", "screen_hits", "market_cap"],
            ascending=[False, False, False],
        ).head(resolved_config.top_n - len(eligible_metrics))
        eligible_metrics = pd.concat([eligible_metrics, supplemental], ignore_index=True)

    if eligible_metrics.empty:
        raise ValueError("No eligible securities remained after applying history checks.")

    top_selection = rank_trending_stocks(eligible_metrics, top_n=resolved_config.top_n)
    top_symbols = top_selection["symbol"].tolist()
    top_prices = candidate_prices[top_symbols].dropna(how="any")

    selected_history = pd.DataFrame(
        [
            {
                "symbol": ticker,
                "observations": int(candidate_prices[ticker].dropna().shape[0]),
                "history_start": candidate_prices[ticker].dropna().index.min().date().isoformat(),
                "history_end": candidate_prices[ticker].dropna().index.max().date().isoformat(),
                "missing_cells": int(candidate_prices[ticker].isna().sum()),
                "meets_minimum_history": bool(
                    top_selection.loc[top_selection["symbol"] == ticker, "history_rows"].iloc[0] >= preferred_history_rows
                ),
            }
            for ticker in top_symbols
        ]
    )

    benchmark = download_benchmark_close(resolved_config.benchmark_ticker, period=resolved_config.price_history_period)
    benchmark.name = resolved_config.benchmark_ticker

    portfolio_table = portfolio_summary(top_prices, benchmark, risk_free_rate=resolved_config.risk_free_rate)
    correlation = correlation_matrix(top_prices)
    simulation_paths = simulate_portfolio_paths(
        top_prices,
        num_simulations=resolved_config.monte_carlo_simulations,
        num_trading_days=resolved_config.monte_carlo_days,
        random_seed=resolved_config.random_seed,
    )
    simulation_summary = summarize_simulation(simulation_paths)
    data_as_of = str(top_prices.index.max().date())

    normalized_plot = resolved_config.figures_dir / "top5_normalized_performance.png"
    correlation_plot = resolved_config.figures_dir / "top5_correlation_heatmap.png"
    plot_normalized_prices(top_prices, normalized_plot)
    plot_correlation_heatmap(correlation, correlation_plot)

    top_selection_path = resolved_config.data_dir / "latest_top5_selection.csv"
    top_prices_path = resolved_config.data_dir / "latest_top5_prices.csv"
    portfolio_path = resolved_config.data_dir / "latest_portfolio_summary.csv"
    simulation_path = resolved_config.data_dir / "latest_monte_carlo_summary.csv"
    metadata_path = resolved_config.data_dir / "latest_run_metadata.json"
    report_path = resolved_config.reports_dir / "latest_top5_stock_report.md"
    dq_report_path = resolved_config.reports_dir / "data_quality_report.md"

    top_selection.to_csv(top_selection_path, index=False)
    top_prices.to_csv(top_prices_path)
    portfolio_table.to_csv(portfolio_path, index=False)
    simulation_summary.rename("value").to_csv(simulation_path, header=True)

    metadata = {
        "generated_at_utc": generated_at.isoformat(),
        "data_as_of": data_as_of,
        "selection_source": selection_source,
        "candidate_count": int(len(candidate_universe)),
        "eligible_count": int(len(metrics.loc[sufficient_history])),
        "excluded_for_history": excluded_for_history,
        "selected_tickers": top_symbols,
        "config": {key: str(value) if isinstance(value, Path) else value for key, value in asdict(resolved_config).items()},
    }
    write_json(metadata, metadata_path)

    report_markdown = build_report_markdown(
        generated_at=generated_at,
        data_as_of=data_as_of,
        selection_source=selection_source,
        candidate_count=len(candidate_universe),
        top_selection=top_selection,
        portfolio_summary=portfolio_table,
        monte_carlo_summary=simulation_summary,
        figures={
            "normalized_prices": str(normalized_plot.relative_to(resolved_config.project_root)),
            "correlation_heatmap": str(correlation_plot.relative_to(resolved_config.project_root)),
        },
    )
    report_path.write_text(report_markdown, encoding="utf-8")

    dq_report = build_data_quality_markdown(
        generated_at=generated_at,
        data_as_of=data_as_of,
        candidate_count=len(candidate_universe),
        eligible_count=int(len(metrics.loc[sufficient_history])),
        selected_count=len(top_symbols),
        price_rows=len(top_prices),
        missing_cells=int(top_prices.isna().sum().sum()),
        selection_source=selection_source,
        min_history_days=resolved_config.min_history_days,
        excluded_for_history=excluded_for_history,
        selected_history=selected_history,
    )
    dq_report_path.write_text(dq_report, encoding="utf-8")

    return {
        "top_selection": top_selection_path,
        "top_prices": top_prices_path,
        "portfolio_summary": portfolio_path,
        "monte_carlo_summary": simulation_path,
        "metadata": metadata_path,
        "report": report_path,
        "data_quality_report": dq_report_path,
    }


def main() -> None:
    outputs = run_pipeline()
    print("Invest-a-Bull pipeline completed successfully.")
    for label, path in outputs.items():
        print(f"- {label}: {path}")


if __name__ == "__main__":
    if __package__ in {None, ""}:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    main()

