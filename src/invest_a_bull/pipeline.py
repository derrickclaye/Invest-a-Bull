from __future__ import annotations

import sys
from dataclasses import asdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import cast

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


MAX_SELECTION_SEARCH_POOL = 15


def ensure_directories(config: AnalysisConfig) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.reports_dir.mkdir(parents=True, exist_ok=True)
    config.figures_dir.mkdir(parents=True, exist_ok=True)


def _shared_history(candidate_prices: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    return candidate_prices[symbols].dropna(how="any")


def _build_selected_history_row(
    candidate_prices: pd.DataFrame,
    ticker: str,
    preferred_history_rows: int,
) -> dict[str, str | int | bool]:
    price_series = candidate_prices.loc[:, ticker]
    clean_series = price_series.dropna()
    observation_count = int(clean_series.shape[0])
    return {
        "symbol": ticker,
        "observations": observation_count,
        "history_start": clean_series.index.min().date().isoformat(),
        "history_end": clean_series.index.max().date().isoformat(),
        "missing_cells": int(price_series.isna().sum()),
        "meets_minimum_history": bool(observation_count >= preferred_history_rows),
    }


def _selection_score(selection: pd.DataFrame, shared_rows: int) -> tuple[int, float, int]:
    return (
        shared_rows,
        float(selection["trend_score"].sum()),
        -int(selection["rank"].sum()),
    )


def _ranked_selection(ranked_metrics: pd.DataFrame, symbols: tuple[str, ...]) -> pd.DataFrame:
    return ranked_metrics[ranked_metrics["symbol"].isin(symbols)].copy()


def _greedy_shared_history_selection(
    ranked_metrics: pd.DataFrame,
    candidate_prices: pd.DataFrame,
    *,
    top_n: int,
    min_shared_rows: int,
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    symbol_order = cast(list[str], ranked_metrics["symbol"].astype(str).tolist())
    best_symbols: tuple[str, ...] | None = None
    best_shared_history: pd.DataFrame | None = None
    best_score: tuple[int, float, int] | None = None

    for seed in symbol_order:
        chosen = [seed]
        shared_history = _shared_history(candidate_prices, chosen)

        while len(chosen) < top_n:
            best_candidate: str | None = None
            best_candidate_history: pd.DataFrame | None = None
            best_candidate_score: tuple[int, float, int] | None = None

            for candidate in symbol_order:
                if candidate in chosen:
                    continue

                candidate_symbols = tuple(chosen + [candidate])
                candidate_history = _shared_history(candidate_prices, list(candidate_symbols))
                candidate_selection = _ranked_selection(ranked_metrics, candidate_symbols)
                candidate_score = _selection_score(candidate_selection, len(candidate_history))
                if best_candidate_score is None or candidate_score > best_candidate_score:
                    best_candidate = candidate
                    best_candidate_history = candidate_history
                    best_candidate_score = candidate_score

            if best_candidate is None or best_candidate_history is None:
                break

            chosen.append(best_candidate)
            shared_history = best_candidate_history

        if len(chosen) != top_n:
            continue

        if len(shared_history) < min_shared_rows:
            continue

        chosen_symbols = tuple(chosen)
        candidate_selection = _ranked_selection(ranked_metrics, chosen_symbols)
        score = _selection_score(candidate_selection, len(shared_history))
        if best_score is None or score > best_score:
            best_symbols = chosen_symbols
            best_shared_history = shared_history
            best_score = score

    if best_symbols is None or best_shared_history is None:
        return None

    selected = ranked_metrics[ranked_metrics["symbol"].isin(best_symbols)].sort_values("rank").reset_index(drop=True)
    selected = selected.copy()
    selected["rank"] = range(1, len(selected) + 1)
    return selected, best_shared_history


def _select_top_candidates_with_shared_history(
    metrics: pd.DataFrame,
    candidate_prices: pd.DataFrame,
    *,
    top_n: int,
    min_shared_rows: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(metrics) < top_n:
        raise ValueError(f"At least {top_n} ranked candidates are required to build the top selection.")

    ranked_metrics = rank_trending_stocks(metrics, top_n=len(metrics))
    full_pool_size = len(ranked_metrics)
    max_search_pool_size = min(full_pool_size, max(top_n, MAX_SELECTION_SEARCH_POOL))
    search_pool_sizes = sorted(
        {
            min(max_search_pool_size, pool_size)
            for pool_size in (
                top_n,
                min(12, max_search_pool_size),
                max_search_pool_size,
            )
        }
    )

    best_symbols: tuple[str, ...] | None = None
    best_shared_history: pd.DataFrame | None = None
    best_score: tuple[int, float, int] | None = None

    for pool_size in search_pool_sizes:
        pool = ranked_metrics.head(pool_size)
        for symbol_group in combinations(pool["symbol"].tolist(), top_n):
            shared_history = _shared_history(candidate_prices, list(symbol_group))
            shared_rows = len(shared_history)
            if shared_rows < min_shared_rows:
                continue

            candidate_selection = pool[pool["symbol"].isin(symbol_group)].copy()
            score = _selection_score(candidate_selection, shared_rows)
            if best_score is None or score > best_score:
                best_symbols = symbol_group
                best_shared_history = shared_history
                best_score = score

    if best_symbols is None and full_pool_size > max_search_pool_size and top_n > 1:
        anchor_symbols = cast(list[str], ranked_metrics.head(max_search_pool_size)["symbol"].astype(str).tolist())
        lower_ranked_symbols = cast(list[str], ranked_metrics["symbol"].astype(str).tolist()[max_search_pool_size:])
        for symbol_group in combinations(anchor_symbols, top_n - 1):
            for candidate in lower_ranked_symbols:
                expanded_group = tuple((*symbol_group, candidate))
                shared_history = _shared_history(candidate_prices, list(expanded_group))
                shared_rows = len(shared_history)
                if shared_rows < min_shared_rows:
                    continue

                candidate_selection = _ranked_selection(ranked_metrics, expanded_group)
                score = _selection_score(candidate_selection, shared_rows)
                if best_score is None or score > best_score:
                    best_symbols = expanded_group
                    best_shared_history = shared_history
                    best_score = score

    if best_symbols is not None and best_shared_history is not None:
        selected = ranked_metrics[ranked_metrics["symbol"].isin(best_symbols)].sort_values("rank").reset_index(drop=True)
        selected = selected.copy()
        selected["rank"] = range(1, len(selected) + 1)
        return selected, best_shared_history

    greedy_selection = _greedy_shared_history_selection(
        ranked_metrics,
        candidate_prices,
        top_n=top_n,
        min_shared_rows=min_shared_rows,
    )
    if greedy_selection is not None:
        return greedy_selection

    raise ValueError(
        f"Unable to identify {top_n} tickers with at least {min_shared_rows} shared price rows for portfolio analytics."
    )


def run_pipeline(config: AnalysisConfig | None = None) -> dict[str, Path]:
    resolved_config = config or AnalysisConfig()
    ensure_directories(resolved_config)

    generated_at = datetime.now(timezone.utc)
    candidate_rows, selection_source = fetch_screener_candidates(resolved_config)
    candidate_universe = aggregate_candidates(candidate_rows)
    candidate_symbols = tuple(str(symbol) for symbol in candidate_universe["symbol"].astype(str).tolist())

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

    # Probe the actual shared-history rows achievable for the top eligible candidates.
    # Even when every symbol individually meets preferred_history_rows, staggered listing
    # dates can make the group's common overlap shorter. Using the achievable shared window
    # as the floor prevents false "no valid basket" errors in those cases.
    top_eligible_symbols = cast(
        list[str],
        eligible_metrics.sort_values("history_rows", ascending=False)
        .head(resolved_config.top_n)["symbol"]
        .astype(str)
        .tolist(),
    )
    if len(top_eligible_symbols) >= resolved_config.top_n:
        achievable_shared_rows = len(candidate_prices[top_eligible_symbols].dropna(how="any"))
    else:
        achievable_shared_rows = int(eligible_metrics["history_rows"].min())
    effective_min_shared_rows = max(3, min(preferred_history_rows, achievable_shared_rows))

    top_selection, top_prices = _select_top_candidates_with_shared_history(
        eligible_metrics,
        candidate_prices,
        top_n=resolved_config.top_n,
        min_shared_rows=effective_min_shared_rows,
    )
    top_symbols = cast(list[str], top_selection["symbol"].astype(str).tolist())

    selected_history = pd.DataFrame(
        [
            _build_selected_history_row(
                candidate_prices,
                ticker,
                preferred_history_rows,
            )
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

    selection_label = f"top{resolved_config.top_n}"
    normalized_plot = resolved_config.figures_dir / f"{selection_label}_normalized_performance.png"
    correlation_plot = resolved_config.figures_dir / f"{selection_label}_correlation_heatmap.png"
    plot_normalized_prices(top_prices, normalized_plot)
    plot_correlation_heatmap(correlation, correlation_plot)

    top_selection_path = resolved_config.data_dir / f"latest_{selection_label}_selection.csv"
    top_prices_path = resolved_config.data_dir / f"latest_{selection_label}_prices.csv"
    portfolio_path = resolved_config.data_dir / "latest_portfolio_summary.csv"
    simulation_path = resolved_config.data_dir / "latest_monte_carlo_summary.csv"
    metadata_path = resolved_config.data_dir / "latest_run_metadata.json"
    report_path = resolved_config.reports_dir / f"latest_{selection_label}_stock_report.md"
    dq_report_path = resolved_config.reports_dir / "data_quality_report.md"

    top_selection.to_csv(top_selection_path, index=False)
    top_prices.to_csv(top_prices_path)
    portfolio_table.to_csv(portfolio_path, index=False)
    simulation_summary.rename("value").to_csv(simulation_path, header=True)

    config_metadata = {}
    for key, value in asdict(resolved_config).items():
        if key == "project_root":
            config_metadata[key] = "."
        elif isinstance(value, Path):
            config_metadata[key] = str(value)
        else:
            config_metadata[key] = value

    metadata = {
        "generated_at_utc": generated_at.isoformat(),
        "data_as_of": data_as_of,
        "selection_source": selection_source,
        "candidate_count": int(len(candidate_universe)),
        "eligible_count": int(len(metrics.loc[sufficient_history])),
        "excluded_for_history": excluded_for_history,
        "selected_tickers": top_symbols,
        "config": config_metadata,
    }
    write_json(metadata, metadata_path)

    report_markdown = build_report_markdown(
        generated_at=generated_at,
        data_as_of=data_as_of,
        selection_source=selection_source,
        candidate_count=len(candidate_universe),
        min_history_days=resolved_config.min_history_days,
        screener_queries=resolved_config.screener_queries,
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
        preferred_history_rows=preferred_history_rows,
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

