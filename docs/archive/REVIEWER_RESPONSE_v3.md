# Response to the second-round referee report (v3)

The second round raised one blocking issue and seven methodological and writing issues. Each item is listed below with what changed and where. All numbers come from `scripts/v3_run.py`.

| # | Referee point | Response | Where |
|---|---|---|---|
| 1 | The 1 bp stitch gate compared adjusted **levels** across vendors and would always fail | **Resolved by removing every splice.** All four instruments now come from one vendor's adjusted bars (Yahoo via yfinance). Calendars, integrity checks and SHA-256 hashes are audited, and the sample end moves to 2026-08-06. | §2, `data_audit.csv`, `v3_engine.load_yahoo` |
| 2 | v2 contained no new results | **Full v3 results** for both windows, five rules, frontiers, sub-periods, round trips, regimes, rolling starts, a daily bootstrap, the parameter grid and sensitivities. | §6–7, `data/v3_results/` |
| 3 | The vol-target control was not risk-matched | **Frontier comparison.** Fixed weights 0.10–1.00 and vol targets 10–100%; the SMA gap is interpolated at equal MaxDD, CDaR and Ulcer. | §5, §6.2, `frontier_gap.csv`, Fig. 3 |
| 4 | Synthetic spread `s = 0` | **Calibrated** on real ETFs: s = 70 bp (SPXL) and 75 bp (TQQQ). A 2010–2017 fit validated on 2018–2026 gives correlation 0.999, a drawdown error under 0.6 pp and a CAGR error of +0.3 / +1.0 pp. Sensitivity at 0 and 2s. | §4, §7.4 |
| 5 | v1→v2 changes were not decomposed | **One-change-at-a-time waterfall** on identical bars: total-return ETF, total-return signal, T-bill cash. The total effect is +0.1 / +1.2 pp CAGR. | §7.5, `attribution_v1_to_v3.csv` |
| 6 | Rolling starts covered the SMA rule only | **Paired** against 3× hold, a start-specific matched mix, the 30% vol target and 1× hold, for 163 real-ETF and 285 extended starts. Overlap is disclosed. | §7.1 |
| 7a | Sharpe used the s.d. of raw returns | Now uses the s.d. of excess returns. | `v3_engine.stats_from_nav` |
| 7b | Inconsistent sign conventions | Every reported difference is SMA − benchmark of the raw metric (drawdowns are negative, so a positive ΔMaxDD means a shallower drawdown). The bootstrap now re-runs the policy on daily paths, replacing the monthly reshuffle. | §7.2 |
| 7c | SPXL CVaR fraction 0.95 was not mentioned | Superseded by the daily path bootstrap, which reports every share > 0 in the table. | §7.2 |
| 8 | Writing issues (garbled abstract sentence, "licensed archives", "prestated", two separate documents) | Rewritten as **one integrated manuscript**. Hypotheses are labelled "stated after earlier drafts, not preregistered". | Abstract, §1 |

## Additional finding during revision

**v2 engine defect.** After a full exit, floating-point residue left −2.8 × 10⁻¹⁴ shares, so `shares == 0` never held again and the v2 rule could not re-enter. v3 sets shares to exactly zero. A regression test reproduces the v2 failure and verifies that v3 matches v2 to machine precision up to the first re-entry. No v2 results had been published.

## How the conclusions changed

* **H1 (drawdown vs 3× hold):** confirmed. In the bootstrap, 85–88% of draws show a shallower drawdown than holding.
* **H2 (timing value):** rejected for 2010–2026. The rule lies below both non-timing frontiers. It holds only with the synthetic 2000–2009 decade, and for TQQQ not even then against volatility targeting.
* **H3 (transport):** same sign for both ETFs, with a weaker TQQQ result. Two correlated U.S. indices remain weak evidence of generality.
