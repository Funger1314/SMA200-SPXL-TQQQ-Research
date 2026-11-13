# Reproducing v4

## Environment

* Python 3.13; package versions pinned in `requirements.txt` (numpy 2.5.3, pandas 3.0.5, matplotlib 3.11.2, scipy 1.18.1, pytest 9.1.1).
* The manuscript build needs pandoc ≥ 3.1 and xelatex.
* `data/v4_results/run_manifest.json` records the versions, seeds and data hashes of the audited run.

## Data

* `data/raw/{SPY,SPXL,QQQ,TQQQ}.csv` are yfinance exports with `auto_adjust=False` (columns Price/Date, Adj Close, Close, High, Low, Open, Volume).
* The audited files are shipped in the replication archive. Verify them against the SHA-256 values in `data/v4_results/data_manifest.csv` or `data/sources.json`.
* To re-download, run `python scripts/fetch_yahoo.py`. It writes `data/raw/DOWNLOAD_MANIFEST.json` with the UTC time, yfinance version and hashes. Yahoo restates adjustments retroactively, so new hashes mean that numbers may differ slightly.
* `load_yahoo()` refuses any file that fails the fatal checks in `scripts/data_checks.py`.

## Run

```bash
./run_all.sh
# = python -m pytest -q             (46 tests, offline except the vendor-file tests)
#   python scripts/v4_run.py         (~3 min; seeds 20260806 path bootstrap, 20260807 SPA)
#   python scripts/v4_tables.py
#   python paper/build_v4.py
#   python scripts/verify_results.py (682 reference values; exit code 1 on any mismatch)
```

`python scripts/v4_run.py --quick` uses 100 path-bootstrap and 300 SPA replicates for a fast check. With `--quick`, `verify_results.py` will report mismatches in the bootstrap and SPA values; this is expected.

## Output map (`data/v4_results/`)

| File | Content | Paper |
|---|---|---|
| data_manifest, data_validation, tracking_outliers, official_checks | provenance, validation, issuer reconciliation | §3 |
| execution_audit | look-ahead audit of every rule | §4 |
| calibration_spread, calibration_validation | synthetic financing spread and out-of-sample check | §5 |
| main_metrics | 7 rules × 2 windows × 2 ETFs, including tail metrics | §6.1, §8 |
| walkforward_metrics, walkforward_selections | walk-forward selection | §6.3 |
| frontier_points, frontier_gap | ex-post frontiers (descriptive) | §6.4 |
| bootstrap_paths, bootstrap_summary | daily path bootstrap (Observed Δ, percentile interval, centred p) | §7.1 |
| parameter_grid, spa_reality_check | 45 configurations; Reality Check and SPA | §7.2 |
| leave_one_crisis_out | crisis exclusions, re-simulated (counterfactual) | §7.3 |
| crisis_contribution_returns_removed | crisis-contribution decomposition (returns deleted, positions not re-simulated) | §7.3 |
| path_engine_consistency | path engine on the unaltered path = main backtest | §7.1 |
| cost_scenarios | costs and cash vehicle | §7.4 |
| synthetic_stress | synthetic-sleeve stress | §8 |
| mechanism_decomposition, mechanism_by_state, state_conditional | mechanism and states | §9 |
