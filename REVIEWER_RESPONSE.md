# Response to the third-round review (v4)

Status key: **Done**, **Partly done** (what remains is stated), **Open**. All numbers come from `scripts/v4_run.py`. The manuscript section is given for each item.

## P0 — required

| Item | Status | What was done | Where |
|---|---|---|---|
| Raw OHLCV, Adj Close, source, download time | **Partly done** | The four raw files (Open, High, Low, Close, Adj Close, Volume) ship in the replication archive under `data/raw/`; they are not committed to the public repository because of Yahoo's terms. `data_manifest.csv` records source, vendor, rows, first/last bar and SHA-256. The upstream repository did not record the original download time; this is stated. `scripts/fetch_yahoo.py` re-downloads and writes `DOWNLOAD_MANIFEST.json` with the UTC timestamp, yfinance version and hashes. | §3.1 |
| Validation in `load_yahoo()` | **Done** | `data_checks.validate_ohlcv()` runs on every load. It stops on: unsorted or duplicate dates, weekend bars, missing values, non-positive prices, OHLC inconsistency, Adj Close > Close, factor jumps above 50%, and sessions missing from or added to an NYSE calendar built from rules and special closures. It warns on extreme returns and gaps, zero volume and large distributions. All files pass and match the calendar exactly. 8 new tests. | §3.2, `data_validation.csv` |
| Official ETF data | **Partly done** | SPXL: inception matches Direxion. The Yahoo close on 27 Feb 2025 equals Direxion's market close ($163.55), not its NAV ($163.27), which confirms that Yahoo carries market prices. Distributions implied by Yahoo's adjustment factor match Direxion's four 2024 distributions to within $0.0005. TQQQ: inception 9 Feb 2010; first exchange trading day 11 Feb 2010 (corrected in v4.1; see below). **Open:** a TQQQ total-return check against an official figure dated inside the sample; the published since-inception return is as of 31 Oct 2026, after the sample ends. | §3.3, `official_checks.csv` |
| Execution assumptions | **Done** | Table of the information set behind every decision. No rule uses High or Low; there are no intraday stops. Automated audit: future prices are distorted and all past decisions must be unchanged, and every fill must be at that day's open; all rules pass. 6 parametrised look-ahead tests. | §4, `execution_audit.csv` |
| Real vs synthetic separation | **Done** | Real ETFs are the primary evidence (§6–7). The 1999–2026 history is confined to §8 and labelled HYPOTHETICAL in every table, figure title and CSV (`SampleType`). | §5, §8 |
| Wording of statistical conclusions | **Done** | Every bootstrap and SPA statement reads "no statistically significant evidence of a difference" when an interval includes zero, with a reading guide. Words such as "rejected" and "proves" were removed. H1 is now reported as not statistically significant, although 84–91% of paths favour the rule. | Abstract, §7.1, §10 |

## P1 — strongly recommended

| Item | Status | What was done | Where |
|---|---|---|---|
| Walk-forward | **Done** | 5-year train, 1-year test, 2015–2026 (real) and 2005–2026 (hypothetical). Selection by Calmar or Sharpe among 45 configurations; switching costs charged; benchmarks calibrated on training data only. | §6.3 |
| Ex-ante risk matching | **Done** | Main matched benchmark = trailing ≤5-year SMA-rule weight, re-set monthly. The ex-post version is kept as a labelled diagnostic (†). Bootstrap matched weight fixed from 1999–2009. Vol target fixed at 30% in advance. Walk-forward vol target matched on training data. | §2, §6.1 |
| Synthetic sensitivity | **Done** | 12 scenarios: spread ×0/1/2/4; expense 0.75–1.25%; realised leverage 2.9/3.1; +300 bp funding shock in both crises; tracking noise ×1 and ×2 (50 Monte Carlo paths each); a combined pessimistic case. Dot-com and GFC returns are reported separately. | §8 |
| Leave-one-crisis-out | **Done** | Dot-com, GFC, COVID and 2022 removed one at a time and all together, with the decline alone and with the decline plus 252 days. | §7.3 |
| Parameter robustness and multiple testing | **Done** | 5 SMA lengths × 3 entry × 3 exit thresholds = 45 configurations, all reported (heatmap and CSV). White Reality Check and Hansen SPA_c against four benchmarks, on raw and volatility-matched returns. | §7.2 |
| Stronger bootstrap | **Done** | 63- and 252-day stationary blocks; the policy is re-run on each path; 5 benchmarks; the null hypothesis is stated; median, 95% interval, share > 0 and two-sided p are reported; limitations are discussed. | §7.1 |
| Costs and execution | **Done** | Flat 10/25 bp; era-dependent spread plus volatility-scaled open slippage; ×3 stress; cash at T-bill − 10 bp or 0%. No margin; leverage only inside the ETF. | §4, §7.4 |
| Tail risk | **Done** | VaR 95/99, ES 95/99 (daily), Ulcer, CDaR, peak-to-trough, recovery days, longest underwater spell. | §6.1, §8 |

## P2 — quality

| Item | Status | Where |
|---|---|---|
| Mechanism (bear avoidance, volatility drag, exposure) | **Done**: exposure and timing split, mean and variance-drag split, contributions by SMA state and by crisis | §9 |
| State-conditional tests | **Done**: by trend, volatility bucket and drawdown duration, with Newey–West t-statistics | §9 |
| Benchmark logic | **Done**: a table of what each benchmark controls | §2 |
| Limitations | **Done**: 8 points (selection, survivorship, synthetic history, regimes, inference, data, execution and tax, generalisation) | §11 |
| Figures | **Done**: cumulative NAV, drawdown, rolling Sharpe, frontier, parameter heatmap, bootstrap interval plot, walk-forward; every title labels the window and sample type | `figures/v4/` |
| Reproducibility package | **Done**: pinned `requirements.txt`, the run manifest with versions, the `run_all.sh` entry point, fixed seeds, data manifest, `verify_results.py` (682 values in v4.1), README. A second independent run reproduced all values. | Reproducibility |
| Abstract, conclusion, literature | **Done**: centred on "no statistically significant evidence of timing alpha"; adds trend-timing, volatility-management, leveraged-ETF and data-mining references | Abstract, §1, §12 |
| **Plain SPY/QQQ buy-and-hold** (author's request) | **Done**: a dedicated section plus the 1× SMA rule; included in the bootstrap, SPA, walk-forward, LOCO and frontier | §6.2 |

## Changes to conclusions relative to v3

1. Part of v3's "beaten at equal exposure" result came from the ex-post benchmark. Against the ex-ante matched mix, the rule has the **higher** Calmar but the lower Sharpe.
2. H1 (drawdown versus 3× hold) is now stated as **not statistically significant**, although it holds in 84–91% of bootstrap paths.
3. Plain SPY and QQQ have higher Sharpe and Calmar ratios than the rule in the real-ETF record. The rule earns more raw return, which reflects leverage, not timing (SPA: vol-matched p = 1.00).
4. Walk-forward re-selection of parameters does not help SPXL. The baseline ranks 17th and 23rd of 45, so the original choice was not in-sample optimised.

---

# Fourth-round items (v4.1)

| Priority | Item | Response | Where |
|---|---|---|---|
| P0 | Bootstrap matched benchmark differs from the main backtest | **Unified.** One definition everywhere: the trailing (≤1,260-day) mean of the weights the SMA rule actually held, using pre-window history from the SMA rule run since 1999-12-22, known at each close and re-set every 21 sessions. The main backtest, the bootstrap and the crisis re-runs all call `path_rules()`. `path_engine_consistency.csv` shows a maximum deviation of 0.0 on the unaltered path, and a unit test checks it. The former pre-sample constant (0.57/0.52) is kept as a separately labelled benchmark (‡). | §2, §7.1 |
| P0 | TQQQ first trading day | **Corrected to 11 Feb 2010.** Nasdaq's listing release (GlobeNewswire, 11 Feb 2010) says "began trading today"; the BATS circular IC 2010-012 admits unlisted trading from 12 Feb. ProShares' 2025 footnote ("first day of trading on Feb 10, 2010, based on … NAV") is documented as a conflicting NAV-based statement. Yahoo's first bar (11 Feb) is therefore complete; the earlier claim that Yahoo omits a session is withdrawn. | §3.3, `official_checks.csv` |
| P1 | Unsorted CSV passed validation | **Fixed.** `load_yahoo()` now validates the frame in stored order before sorting or truncation; the "sorted ascending" check is fatal. A test swaps two rows and expects rejection. | `engine.load_yahoo`, `tests/test_v4.py` |
| P1 | Bootstrap p-value definition | **Formal test.** H0: Δ = 0. The bootstrap distribution is centred at the observed Δ (Hall and Wilson 1991) and the two-sided p = P*(\|Δ*−Δ̂\| ≥ \|Δ̂\|). Percentile intervals and Δ*>0 shares are labelled descriptive. We explain why they can disagree for drawdowns (resampling shifts the drawdown distribution). | §7.1, `bootstrap_summary.csv` |
| P1 | Leave-one-crisis-out is not a counterfactual | **Re-simulated.** Crisis days are deleted from the input returns, the remaining days are spliced into a new price path, and every rule is re-run from scratch (SMA, stages, volatility, ex-ante weights). The old method is kept, relabelled as a crisis-contribution decomposition. | §7.3 |
| P2 | Stale data documentation | **Fixed.** `data/README.md` rewritten with current and historical sections; `README_HISTORICAL.md` added in `results/`, `v2_results/` and `v3_results/`; `scripts/README.md` added and LEGACY banners placed on 12 historical scripts; `sources.json` marks the v1/v2 blocks historical; DATA_LICENSE_NOTICE rewritten. | data/, scripts/ |

## Effect on conclusions

* H1 is now quantified by a test: drawdown gain over 3× hold of 23 pp (SPXL) and 20 pp (TQQQ), p = 0.09 and 0.16 (252-day blocks), 0.20 and 0.33 (63-day blocks). Not significant.
* H2 is unchanged: all Calmar and Sharpe differences against 1× hold, the matched mixes and the volatility target have p ≥ 0.35.
* Some drawdown differences whose percentile interval excluded zero in v4.0 (SPXL vs SPY; TQQQ vs the volatility target) are not significant under the centred test; TQQQ vs QQQ is significant only with 252-day blocks.
* The re-simulated LOCO slightly strengthens the hypothetical SPXL result (best even with all four declines removed) but not with their aftermaths; the real-record conclusions are unchanged (best in 3 of 12 cases).
