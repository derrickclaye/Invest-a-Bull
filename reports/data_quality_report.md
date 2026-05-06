# Data Quality Report

Generated: 2026-05-05 03:27:03 UTC

- Latest market data used: **2026-05-04**
- Candidate universe count: **37**
- Eligible securities with sufficient history: **37**
- Selected top-n count: **5**
- Price-history row count: **123**
- Missing values in selected price matrix: **0**
- Selection source: `yfinance_screeners`
- Minimum price-history requirement for preferred selection: **64 rows** (`63` trailing trading days plus the starting observation)
- Candidates excluded for insufficient history before fallback handling: **0**

The pipeline rejects empty universes, removes non-equity results, and keeps only symbols with downloadable price history.

## Selected ticker coverage

| Ticker | Observations | History Start | History End | Missing Cells | Meets Minimum History |
| --- | --- | --- | --- | --- | --- |
| MU | 123 | 2025-11-05 | 2026-05-04 | 0 | Yes |
| NBIS | 123 | 2025-11-05 | 2026-05-04 | 0 | Yes |
| CRCL | 123 | 2025-11-05 | 2026-05-04 | 0 | Yes |
| INTC | 123 | 2025-11-05 | 2026-05-04 | 0 | Yes |
| STX | 123 | 2025-11-05 | 2026-05-04 | 0 | Yes |
