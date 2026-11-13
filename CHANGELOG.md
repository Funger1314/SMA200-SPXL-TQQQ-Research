# Changelog

## v4.1.0 — 2026-11-12 (fourth-round review)
- One definition of the ex-ante matched weight everywhere: trailing mean of the weights the SMA rule actually held
  (pre-window history + in-window run). The main backtest, path bootstrap and crisis re-runs share `path_rules()`;
  a consistency check and a unit test show that the path engine reproduces the main backtest exactly.
- Bootstrap: centred two-sided test of H0: Delta = 0 (Hall & Wilson 1991). Percentile intervals and Delta*>0 shares
  are relabelled as descriptive. The pre-sample constant weight is kept as a labelled extra benchmark.
- Leave-one-crisis-out is now a true counterfactual re-simulation on spliced paths. The old return-deletion is
  relabelled "crisis-contribution decomposition".
- `load_yahoo()` validates the file in stored order before any sorting; an unsorted-file test was added.
- TQQQ first exchange trading day corrected to 2010-02-11 (Nasdaq listing release; BATS circular). The
  ProShares "Feb 10" footnote is documented as a conflicting, NAV-based statement.
- Historical v1/v2/v3 data and scripts are clearly labelled (`data/README.md`, `scripts/README.md`, LEGACY
  banners, `sources.json` status fields, DATA_LICENSE_NOTICE).
- 46 tests; `verify_results.py` checks 682 values.

## v4.0.0 — 2026-11-12 (data through 2026-08-06)
- Strict data validation in `load_yahoo()` (`scripts/data_checks.py`, rule-based NYSE calendar); issuer reconciliation (Direxion/ProShares).
- Execution-timing audit (automated perturbation test for every rule); information-set table.
- Real-ETF record is primary; 1999-2026 history confined to a labelled HYPOTHETICAL section.
- Ex-ante matched-weight benchmark (trailing <=5y SMA weight); ex-post version kept as labelled diagnostic.
- New: 1x buy-and-hold and 1x SMA benchmarks; walk-forward (5y/1y) selection over 45 configurations;
  Reality Check / SPA_c; leave-one-crisis-out; cost and cash-vehicle scenarios; tail metrics
  (VaR/ES 95/99, recovery, underwater); 12-scenario synthetic stress; mechanism decomposition; state tests.
- Engine moved to `scripts/engine.py` (per-day cost arrays, target-weight paths); `v3_engine.py` is an alias.
- Reproducibility: pinned requirements, `run_all.sh`, `verify_results.py` + `data/expected_results.json`,
  `fetch_yahoo.py` with download manifest. 44 tests.
- Wording: bootstrap/SPA conclusions stated as "no statistically significant evidence".

## v3.0.0 — 2026-11-12 (sample ends 2026-08-06)
- Single-vendor data (Yahoo/yfinance adjusted bars for SPY, SPXL, QQQ, TQQQ); all splices removed; SHA-256 audit.
- New engine `scripts/v3_engine.py` (fast array simulator, same state machine); fixes v2 exit-dust defect that blocked re-entry.
- Synthetic financing spread calibrated on real ETFs (70/75 bp) with 2018–2026 out-of-sample validation.
- Full results: five rules, fixed-weight and vol-target frontiers, sub-periods, round trips, next-day regime table,
  paired rolling starts, daily stationary bootstrap re-running the policy (1,000 reps, 63/252-day blocks),
  per-cell matched parameter grid, cost and spread sensitivity, v1→v3 attribution waterfall.
- Sharpe on excess-return s.d.; integrated manuscript `paper/SMA200_Leveraged_ETF_Research_v3.pdf/.docx`.
- v1/v2 manuscripts and docs moved to `paper/archive/` and `docs/archive/`.

## v2 referee-response revision — 2026-11-12
- Changed inference: the v1 TQQQ SMA rule loses to 3× hold on CAGR, Sharpe and Calmar; independent timing skill unproven.
- New standalone v2 engine and FRED-derived lagged monthly rates; unified adjusted archive and hard 1bp stitch gate.
- Added unleveraged/weight-matched/vol-managed controls, daily risk diagnostics, trade-episode attribution, rolling monthly starts, regime analysis.
- Added offline 201-month paired fixed-block risk bootstrap, explicitly *not* corrected daily inference.
- Recompiled v1 and v2 manuscripts with mathematical typesetting using XeLaTeX/OMML.
- New v2 fully refreshed numeric performance is **not** reported without a verified four-asset source-data rerun.

## v1.0.0 — 2026-11-12 (initial research snapshot)

- Frozen user rule: SMA200, +4% entry threshold, +20% incremental capital targets, -3% exit buffer, next-session open, 10 bps per fill.
- Calculated matched warm-up-complete 1999-12-22–2026-11-12 extended/synthetic sample and matched 2010-02-11–2026-11-12 real-ETF sample.
- Added 27-cell neighborhood for each leveraged ETF, three-part time-regime split, cost friction sensitivity, illustrative monthly block-bootstrap comparison, and eight self-contained tests.
- Published manuscript, five embedded figures, six standalone PNGs, CSV audit summaries, source checksum manifest, and local downloader.
- Raw third-party price feeds excluded due data redistribution considerations.

Revisions must document *every* change in source data, corporate-action convention, cost modeling, or strategy parameter. Do not silently rewrite the original study's numerical history.
