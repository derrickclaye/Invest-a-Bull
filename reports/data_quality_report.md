# Data Quality Report

Generated: 2026-04-16 04:57:28 UTC

- Candidate universe count: **30**
- Selected top-n count: **5**
- Price-history row count: **124**
- Missing values in the selected price matrix: **0**
- Selection source: `yfinance_screeners`

The pipeline rejects empty universes, removes non-equity results, and keeps only symbols with downloadable price history.
