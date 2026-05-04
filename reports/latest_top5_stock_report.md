# Invest-a-Bull Senior Market Report

Generated: 2026-05-04 05:01:23 UTC

## Executive summary

This report identifies the **top 5 trending U.S. stocks** using a blended ranking model that combines:

- current Yahoo Finance screener presence
- latest 1-day move
- trailing 5-day, 1-month, and 3-month momentum
- liquidity via average 3-month dollar volume
- minimum-history preference for more decision-useful names

Data source: `yfinance_screeners`  
Universe size after filtering: **40 stocks**  
Latest market data used in the report: **2026-05-01**

### Key takeaways

- Selected basket: **MU, AMD, AAOI, NVDA, INTC**
- Lookback portfolio return: **135.19%**
- Relative performance vs benchmark: **129.13%**
- Monte Carlo expected terminal return: **478.54%**
- Monte Carlo 95% range: **61.95% to 1277.09%**

## Top 5 trending stocks

| Rank | Ticker | Company                       | Source Screens                         | Trend Score | 1D Move | 5D Return | 1M Return | 3M Return | Market Cap | Avg 3M Volume | History Rows |
|------|--------|-------------------------------|----------------------------------------|-------------|---------|-----------|-----------|-----------|------------|---------------|--------------|
| 1    | MU     | Micron Technology, Inc.       | growth_technology_stocks, most_actives | 0.590       | 4.84%   | 9.16%     | 47.40%    | 30.75%    | $611.5B    | 41.1M         | 124          |
| 2    | AMD    | Advanced Micro Devices, Inc.  | growth_technology_stocks, most_actives | 0.569       | 1.71%   | 3.66%     | 71.51%    | 52.30%    | $587.8B    | 37.5M         | 124          |
| 3    | AAOI   | Applied Optoelectronics, Inc. | day_gainers                            | 0.556       | 11.56%  | 13.16%    | 112.52%   | 320.80%   | $14.7B     | 10.9M         | 124          |
| 4    | NVDA   | NVIDIA Corporation            | growth_technology_stocks, most_actives | 0.519       | -0.56%  | -4.72%    | 12.92%    | 3.84%     | $4,823.3B  | 174.2M        | 124          |
| 5    | INTC   | Intel Corporation             | most_actives                           | 0.502       | 5.42%   | 20.69%    | 107.41%   | 114.37%   | $500.6B    | 104.7M        | 124          |

## Portfolio view

The selected names are combined into an equal-weight portfolio to estimate how the current trend basket behaves as a single product.

| Metric                            | Value   |
|-----------------------------------|---------|
| Portfolio total return (lookback) | 135.19% |
| Portfolio annualized return       | 193.84% |
| Portfolio annualized volatility   | 60.42%  |
| Portfolio Sharpe ratio            | 3.14    |
| Portfolio max drawdown            | -18.91% |
| SPY total return (lookback)       | 6.06%   |

## Monte Carlo outlook

A 1-year bootstrap Monte Carlo simulation is run on the equal-weight basket using stabilized empirical portfolio returns.

| Metric       | Value    |
|--------------|----------|
| count        | 250      |
| mean         | 478.54%  |
| std          | 373.41%  |
| min          | 33.11%   |
| 25%          | 246.75%  |
| 50%          | 405.57%  |
| 75%          | 602.95%  |
| max          | 2857.73% |
| 95% CI Lower | 61.95%   |
| 95% CI Upper | 1277.09% |

## Visual outputs

- Normalized price chart: `reports/figures/top5_normalized_performance.png`
- Correlation heatmap: `reports/figures/top5_correlation_heatmap.png`

## Methodology notes

1. Pull candidate names from Yahoo predefined screens: `most_actives`, `day_gainers`, and `growth_technology_stocks`.
2. Filter for listed U.S. equities and require minimum price and market-cap thresholds.
3. Download the latest daily adjusted-close history and prefer names with at least a 3-month lookback when available.
4. Rank names using a weighted composite trend score and keep the top 5.
5. Produce an equal-weight portfolio view and a scenario range for decision support.

## Disclaimer

This project is for analytics and educational use only and should not be interpreted as personalized investment advice.
