# Invest-a-Bull Senior Market Report

Generated: 2026-04-16 04:57:28 UTC

## Executive summary

This report identifies the **top 5 trending U.S. stocks** using a blended ranking model that combines:

- current Yahoo Finance screener presence
- latest 1-day move
- trailing 5-day, 1-month, and 3-month momentum
- liquidity via average 3-month dollar volume

Data source: `yfinance_screeners`  
Universe size after filtering: **30 stocks**  
Latest market data used in the report: **2026-04-15**

## Top 5 trending stocks

| Rank | Ticker | Company                            | Source Screens                         | Trend Score | 1D Move | 5D Return | 1M Return | 3M Return | Market Cap | Avg 3M Volume |
|------|--------|------------------------------------|----------------------------------------|-------------|---------|-----------|-----------|-----------|------------|---------------|
| 1    | IONQ   | IonQ, Inc.                         | day_gainers, most_actives              | 0.696       | 20.95%  | 49.19%    | 29.92%    | -11.63%   | $15.9B     | 23.3M         |
| 2    | NVDA   | NVIDIA Corporation                 | growth_technology_stocks, most_actives | 0.585       | 1.23%   | 9.22%     | 8.54%     | 7.03%     | $4,833.5B  | 178.4M        |
| 3    | HOOD   | Robinhood Markets, Inc.            | day_gainers, most_actives              | 0.517       | 10.41%  | 21.56%    | 15.95%    | -27.38%   | $78.6B     | 31.1M         |
| 4    | CRDO   | Credo Technology Group Holding Ltd | growth_technology_stocks               | 0.470       | 5.50%   | 52.75%    | 44.04%    | 4.32%     | $31.1B     | 7.4M          |
| 5    | CRWV   | CoreWeave, Inc.                    | most_actives                           | 0.423       | 1.27%   | 33.51%    | 38.24%    | 35.68%    | $62.4B     | 27.8M         |

## Portfolio view

The selected names are combined into an equal-weight portfolio to estimate how the current trend basket behaves as a single product.

| Metric                            | Value   |
|-----------------------------------|---------|
| Portfolio total return (lookback) | -6.53%  |
| Portfolio annualized return       | 4.77%   |
| Portfolio annualized volatility   | 61.55%  |
| Portfolio Sharpe ratio            | 0.01    |
| Portfolio max drawdown            | -44.98% |
| SPY total return (lookback)       | 6.55%   |

## Monte Carlo outlook

A 1-year Monte Carlo simulation is run on the equal-weight basket using recent daily return mean and volatility as inputs.

| Metric       | Value   |
|--------------|---------|
| count        | 250     |
| mean         | 5.52%   |
| std          | 40.36%  |
| min          | -65.62% |
| 25%          | -19.38% |
| 50%          | -0.24%  |
| 75%          | 29.57%  |
| max          | 132.34% |
| 95% CI Lower | -56.95% |
| 95% CI Upper | 99.68%  |

## Visual outputs

- Normalized price chart: `reports\figures\top5_normalized_performance.png`
- Correlation heatmap: `reports\figures\top5_correlation_heatmap.png`

## Methodology notes

1. Pull candidate names from Yahoo predefined screens: `most_actives`, `day_gainers`, and `growth_technology_stocks`.
2. Filter for listed U.S. equities and require minimum price and market-cap thresholds.
3. Download the latest daily adjusted-close history and compute momentum, volatility, and liquidity features.
4. Rank names using a weighted composite trend score and keep the top 5.
5. Produce an equal-weight portfolio view and a Monte Carlo scenario range for decision support.

## Disclaimer

This project is for analytics and educational use only and should not be interpreted as personalized investment advice.
