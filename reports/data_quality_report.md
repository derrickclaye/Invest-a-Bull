# Data Quality Report

Generated: 2026-05-04 05:56:14 UTC

- Latest market data used: **2026-05-01**
- Candidate universe count: **40**
- Eligible securities with sufficient history: **38**
- Selected top-n count: **5**
- Price-history row count: **124**
- Missing values in selected price matrix: **0**
- Selection source: `yfinance_screeners`
- Minimum price-history requirement for preferred selection: **64 rows** (`63` trailing trading days plus the starting observation)
- Candidates excluded for insufficient history before fallback handling: **2**

The pipeline rejects empty universes, removes non-equity results, and keeps only symbols with downloadable price history.

## Selected ticker coverage

| Ticker | Observations | History Start | History End | Missing Cells | Meets Minimum History |
| --- | --- | --- | --- | --- | --- |
| MU | 124 | 2025-11-03 | 2026-05-01 | 0 | Yes |
| AMD | 124 | 2025-11-03 | 2026-05-01 | 0 | Yes |
| AAOI | 124 | 2025-11-03 | 2026-05-01 | 0 | Yes |
| NVDA | 124 | 2025-11-03 | 2026-05-01 | 0 | Yes |
| INTC | 124 | 2025-11-03 | 2026-05-01 | 0 | Yes |
