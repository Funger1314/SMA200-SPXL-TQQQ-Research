# Reproduction protocol for the referee-response revision (v2)

## Scope and evidence status

The v2 manuscript and implementation are supplied, **but a fully updated v2 daily result table is NOT bundled**. The data/result files named `snapshot_*` and `monthly_equity_*` are **historical v1** outputs under 0% cash yield and inconsistent SPY/SPXL dividend treatment. The `data/v2_results/paired_monthly_risk_bootstrap_legacy.csv` is newly calculated *from those v1 derived month-end NAVs*, not from the corrected engine. A reader must not merge the two result vintages into a single claim.

## Step-by-step

1. Install Python 3.11+ and execute `pip install -r requirements.txt`.
2. Run `python -m pytest -q` (offline unit tests only; no dependence on personal credentials).
3. Run `python scripts/bootstrap.py` to reproduce the **legacy monthly paired-risk audit**.
4. Run `python scripts/fetch_data.py` to retrieve the four archived daily historical prices from their upstream owners. It validates pinned Git blob SHA-1. Verify third-party market-data licensing.
5. Run `python scripts/reproduce.py --tail-mode public` to request an adjusted public quote tail for the missing archive range. This **must pass** the 1bp close-price overlap assertion. If a vendor restated historical dividends or a split, expect failure; obtain a single appropriately licensed whole-history vendor and rebuild consistent input rather than forcing an arbitrary splice factor.
6. On success, inspect `data/v2_results/benchmark_metrics.csv`, `*_roundtrips.csv`, `*_regime_nextday.csv`, `*_rolling_starts.csv`, `figures/v2/benchmark_equity_real.png` and `data/derived/v2_market_*.csv`.
7. Independently check ETF share-class total-return index / official NAV since inception, reconciling distribution treatment before representing any metrics as publication-quality. Keep the full source file hashes and a data-vintage date in the eventual commit.

## Benchmarks and identification

- The `fixed_weight` benchmark uses the **realized average daily SMA weight** of that full period. It is retrospective calibration by design. For genuine out-of-sample comparison, freeze the weight from a prior training window or use a preregistered ex-ante allocation.
- The `vol_target` control uses **63 previous adjusted daily close returns** and an ex-ante fixed 30% annual vol target. It rebalances every five sessions; the signal is computed after close and filled at next open. It is a preliminary rival rather than an exhaustive model of volatility-management literature.
- `unlevered_hold` uses adjusted SPY/QQQ open and close, not an unadjusted price series.
- Cash earns a lagged monthly 3-month T-bill investment-yield approximation, computed from FRED DTB3 discount quotations. The source includes a small negative yield in 2015; it is not hidden or floored.
- The pre-inception 3× model charges 2 funded units at that rate, plus an explicit optional financing spread and illustrative 0.95% annual expense. The ETF market prices are not doubly charged this theoretical financing cost.
- Monthly-bootstrap inference is frequency-limited and **does not** constitute a daily path-resampling test that reruns the trading policy in each pseudo-world.

## Data-conventions pitfalls

- `scripts/review_revision.py` **requires** `Adj Close` for upstream SPY/SPXL and uses pre-adjusted closes for upstream QQQ/TQQQ.
- Split-adjusted open prices are reconstructed by multiplying historical open by that date's AdjClose/Close ratio. They are *proxies* for fully executable total-return fills.
- Source archives end on different dates. A public tail must overlap, agree within 1bp and run through 2026-11-12. No arbitrary scaling is allowed in v2.
- The first v2 run may legitimately fail the overlap test because Yahoo's present adjusted data differ from a historical GitHub archive's adjustments. That is a **data failure**, not a reason to weaken the test.
- The IBKR cached private tail is NOT redistributed in the GitHub ZIP. A `--tail-mode licensed-local` option is available only for independently owned data; the older IBKR price-return convention should be reconciled against fund dividends before using it as adjusted total return.

## Final publication gates

Corrected day-level results, independent NAV checks, bootstrapped re-execution of the strategy on paired resampled daily **price paths**, a genuine future frozen-model paper trade, and a complete parameter-search history remain outstanding. See [REVIEWER_RESPONSE.md](REVIEWER_RESPONSE.md).
