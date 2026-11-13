# Reproducing v3

1. `pip install -r requirements.txt` (Python ≥ 3.11). PDF and DOCX builds additionally need `pandoc` ≥ 3 and `xelatex`.
2. **Data.** Put four yfinance CSV exports named `SPY.csv`, `SPXL.csv`, `QQQ.csv` and `TQQQ.csv` in `data/raw/`. They must be produced with `auto_adjust=False`, so that they contain both `Close` and `Adj Close`, and must run through 2026-08-06. The audited files came from `github.com/hjyssg/tqqq_simulation`; their SHA-256 hashes are listed in `data/sources.json → v3` and `data/v3_results/data_audit.csv`. The loader accepts both the multi-row yfinance header and a plain `Date,...` header. Equivalent bars downloaded later from Yahoo can differ slightly, because Yahoo revises dividend adjustments retroactively; compare against the hashes first.
3. `python -m pytest -q`: 27 offline tests. They cover next-open timing, staged entries, exact-zero shares after an exit (the v2 defect), equivalence with the v2 engine, the synthetic formula, spread calibration, and vendor-calendar alignment.
4. `python scripts/v3_run.py` writes `data/v3_results/*.csv` and `figures/v3/*.png`. Use `--quick` for a 100-replicate bootstrap. The bootstrap seed is 20260806.
5. `python scripts/v3_tables.py` then `python paper/build_v3.py` rebuild the manuscript. Every number in the paper's tables comes from step 4.

## Key files

| File | Content |
|---|---|
| `main_metrics.csv` | five rules × two windows × two ETFs |
| `frontier_points.csv`, `frontier_gap.csv` | fixed-weight and vol-target frontiers; SMA gap at equal risk |
| `calibration_spread.csv` | financing-spread estimate and 2018–2026 out-of-sample proxy check |
| `attribution_v1_to_v3.csv` | v1 → v3 changes applied one at a time |
| `regime_nextday.csv` | next-day return and volatility by SMA regime |
| `roundtrips.csv` | every exit and re-entry |
| `rolling_starts*.csv` | all monthly start dates, paired against each benchmark |
| `bootstrap_daily_*.csv` | stationary bootstrap that re-runs the policy on each path (1,000 replicates, mean blocks of 63 and 252 days) |
| `parameter_grid.csv` | 27 cells × 2 windows × 2 ETFs, each compared with its own matched mix |
| `sensitivity.csv` | trading costs; synthetic financing spread |

## Remaining publication gates

* Reconcile the buy-and-hold total returns with ProShares/Direxion official NAV returns.
* Run a frozen-parameter forward paper-trading test.
* Test transport on non-U.S. indices with the same synthetic 3× construction, without tuning.
