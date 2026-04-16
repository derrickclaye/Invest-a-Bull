# Invest-a-Bull

Invest-a-Bull has been upgraded from a classroom-style notebook into a **reproducible market-analysis pipeline** that identifies and analyzes the **latest top 5 trending U.S. stocks** using live Yahoo Finance data.

The project now blends:

- market screening
- momentum and liquidity scoring
- equal-weight portfolio analysis
- Monte Carlo scenario modeling
- report generation with current outputs and figures

![priceplots](short.gif)

## Latest generated result

Most recent successful live run:

- **Generated:** 2026-04-16 UTC
- **Latest market data used:** 2026-04-15
- **Top 5 trending stocks:** `IONQ`, `NVDA`, `HOOD`, `CRDO`, `CRWV`

See the generated deliverables:

- `reports/latest_top5_stock_report.md`
- `reports/data_quality_report.md`
- `data/processed/latest_top5_selection.csv`
- `data/processed/latest_portfolio_summary.csv`
- `reports/figures/top5_normalized_performance.png`
- `reports/figures/top5_correlation_heatmap.png`

## What changed

This repository now includes a senior-style workflow built around package code instead of only notebook cells.

### New capabilities

- pulls candidate stocks from Yahoo Finance predefined screens
- filters to liquid U.S. equities with minimum market-cap and price thresholds
- ranks stocks with a blended **trend score** using:
  - screener presence
  - 1-day move
  - 5-day return
  - 1-month return
  - 3-month return
  - 3-month dollar volume
- builds an equal-weight portfolio of the selected names
- runs a 1-year Monte Carlo scenario analysis
- exports refreshed CSV, JSON, Markdown, and PNG artifacts

## Project structure

- `run_latest_top5_analysis.py` - one-command entry point for the live analysis pipeline
- `src/invest_a_bull/config.py` - runtime configuration
- `src/invest_a_bull/market_data.py` - screener and price-download layer
- `src/invest_a_bull/analytics.py` - ranking and portfolio analytics
- `src/invest_a_bull/simulation.py` - Monte Carlo simulation utilities
- `src/invest_a_bull/reporting.py` - report and chart generation
- `src/invest_a_bull/pipeline.py` - end-to-end orchestration
- `tests/test_analytics.py` - automated unit tests
- `MasterAnalysisFinal.ipynb` - notebook workflow retained for exploratory use
- `masterAnalysis.ipynb` - legacy notebook version
- `MCForecastTools.py` - compatibility helper for the notebook-based Monte Carlo workflow

## Setup

Install the project dependencies with either `requirements.txt` or the package metadata.

```powershell
python -m pip install -r requirements.txt
```

Optional editable install:

```powershell
python -m pip install -e .
```

## Run the latest analysis

To regenerate the top-5 trending stock report with fresh market data:

```powershell
python .\run_latest_top5_analysis.py
```

If the package is installed in editable mode, you can also run:

```powershell
invest-a-bull-latest
```

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## Methodology

1. Pull candidate equities from Yahoo Finance screens:
   - `most_actives`
   - `day_gainers`
   - `growth_technology_stocks`
2. Keep only U.S.-listed equities that pass minimum price and market-cap filters.
3. Download recent adjusted-close history.
4. Compute security-level momentum, volatility, drawdown, and liquidity features.
5. Rank the candidate universe by a weighted trend score.
6. Analyze the selected top 5 as an equal-weight portfolio.
7. Produce a 1-year Monte Carlo scenario range and save the outputs.

## Notes

- The live selection is dynamic and will change as the market changes.
- If Yahoo screeners are unavailable, the pipeline falls back to a large-cap momentum universe.
- The notebook workflow still works, but the package pipeline is now the recommended entry point.
- This project is for analytics and educational use only, not personalized investment advice.
