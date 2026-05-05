# Invest-a-Bull Senior Market Report

Generated: 2026-05-05 03:00:06 UTC

## Executive summary

This report identifies the **top 5 trending U.S. stocks** using a blended ranking model that combines:

- current Yahoo Finance screener presence
- latest 1-day move
- trailing 5-day, 1-month, and 3-month momentum
- liquidity via average 3-month dollar volume
- minimum-history preference for more decision-useful names

Data source: `yfinance_screeners`  
Universe size after filtering: **37 stocks**  
Latest market data used in the report: **2026-05-04**

### Key takeaways

- Selected basket: **MU, NBIS, CRCL, INTC, STX**
- Lookback portfolio return: **110.13%**
- Relative performance vs benchmark: **103.56%**
- Monte Carlo expected terminal return: **433.11%**
- Monte Carlo 95% range: **54.02% to 1342.17%**

## Top 5 trending stocks

| Rank | Ticker | Company | Source Screens | Trend Score | 1D Move | 5D Return | 1M Return | 3M Return | Market Cap | Avg 3M Volume | History Rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | MU | Micron Technology, Inc. | day_gainers, growth_technology_stocks, most_actives | 0.668 | 6.31% | 9.89% | 57.40% | 31.73% | $650.1B | 41.3M | 123 |
| 2 | NBIS | Nebius Group N.V. | day_gainers | 0.554 | 14.20% | 21.70% | 62.12% | 100.11% | $44.8B | 16.4M | 123 |
| 3 | CRCL | Circle Internet Group | day_gainers | 0.538 | 19.89% | 25.24% | 32.43% | 103.08% | $29.5B | 16.4M | 123 |
| 4 | INTC | Intel Corporation | most_actives | 0.499 | -3.85% | 12.70% | 90.12% | 96.23% | $481.4B | 104.8M | 123 |
| 5 | STX | Seagate Technology Holdings plc | growth_technology_stocks | 0.474 | 1.60% | 23.95% | 72.01% | 70.88% | $165.6B | 3.9M | 123 |

## Portfolio view

The selected names are combined into an equal-weight portfolio to estimate how the current trend basket behaves as a single product.

| Metric | Value |
| --- | --- |
| Portfolio total return (lookback) | 110.13% |
| Portfolio annualized return | 363.56% |
| Portfolio annualized volatility | 59.03% |
| Portfolio Sharpe ratio | 6.09 |
| Portfolio max drawdown | -21.99% |
| SPY total return (lookback) | 6.57% |

## Monte Carlo outlook

A 1-year bootstrap Monte Carlo simulation is run on the equal-weight basket using stabilized empirical portfolio returns.

| Metric | Value |
| --- | --- |
| count | 250 |
| mean | 433.11% |
| std | 319.25% |
| min | 0.23% |
| 25% | 210.97% |
| 50% | 347.39% |
| 75% | 591.37% |
| max | 1720.53% |
| 95% CI Lower | 54.02% |
| 95% CI Upper | 1342.17% |

## Visual outputs

- Normalized price chart: `reports/figures/top5_normalized_performance.png`
- Correlation heatmap: `reports/figures/top5_correlation_heatmap.png`

## Methodology notes

1. Pull candidate names from the configured Yahoo predefined screens: `most_actives, day_gainers, growth_technology_stocks`.
2. Filter for listed U.S. equities and require minimum price and market-cap thresholds.
3. Download the latest daily adjusted-close history and prefer names with at least a 3-month lookback when available.
4. Rank names using a weighted composite trend score and keep the top 5.
5. Produce an equal-weight portfolio view and a scenario range for decision support.

## Disclaimer

This project is for analytics and educational use only and should not be interpreted as personalized investment advice.
