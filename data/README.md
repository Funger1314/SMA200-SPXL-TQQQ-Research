# Data directory

## Current (v4)

| Path | Content |
|---|---|
| `raw/{SPY,SPXL,QQQ,TQQQ}.csv` | Yahoo Finance daily bars via yfinance (`auto_adjust=False`: Open, High, Low, Close, Adj Close, Volume), market prices, through 2026-08-06, obtained from github.com/hjyssg/tqqq_simulation. Supplied in the replication archive only, not committed to GitHub (Yahoo terms). SHA-256 in `v4_results/data_manifest.csv` and `sources.json → v4`. |
| `v4_results/` | every v4 output (see REPRODUCE_V4.md for the file map), including `data_validation.csv`, `official_checks.csv`, `run_manifest.json` |
| `expected_results.json` | 312 reference values checked by `scripts/verify_results.py` |
| `derived/fred_dtb3_month_end_derived.csv` | month-end DTB3 quotes; same values that `scripts/rates.py` decodes |

All prices are converted to total-return bars inside `scripts/engine.py` (Adj Close; open × Adj Close / Close). No splicing across vendors and no IBKR data are used.

## Historical (kept for the audit trail; not used by v4)

| Path | Version | What it was |
|---|---|---|
| `results/` | v1 | month-end snapshots from the mixed GitHub-archive + private IBKR-tail pipeline (price-only SPY/SPXL, adjusted QQQ/TQQQ, 0% cash, end 2026-11-12) |
| `v2_results/` | v2 | monthly-NAV paired bootstrap computed on the v1 snapshots |
| `v3_results/` | v3 | first single-vendor results (ex-post matched benchmark) |
| `sources.json → sources, tail_source` | v1/v2 | upstream archive links and the IBKR tail description |

Do not combine numbers from different versions.
