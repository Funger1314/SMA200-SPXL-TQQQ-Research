# Response to 15 referee comments — v2 (2026-11-12)

**IMPORTANT**: The v2 code is implemented and offline tests pass, but the full daily sourced v2 return comparison has NOT been regenerated in this environment. The old snapshot must not be presented as corrected evidence.

| Referee point | Response/status | Where |
|---|---|---|
| 1. Calmar, not just DD | **Corrected interpretation.** TQQQ original rule Calmar 0.434 < hold 0.501. Timing skill not established. | `paper/review_revision_v2.md`, §5 |
| 2. 1×, matched-weight, vol target | **Implemented, results pending source refresh.** Match uses ex-post mean time-weighted equity weight; volatility allocator uses trailing 63 sessions, 30% annual target, five-session rebalance. | `scripts/review_revision.py`, `benchmark`, `run_all` |
| 3. ExposedDays biased | **Implemented correction.** `AverageWeight` is mean daily equity weight; `ExposedDaysFraction` is explicitly a distinct diagnostic. | `scripts/review_revision.py`, `metrics` |
| 4. Regime-conditioned mechanism | **Implemented, results pending.** Condition at t close, next t+1 returns, volatility, approximated 3× log growth. | `scripts/review_revision.py`, `regime_table` |
| 5. Wide stop buffer in bubbles | **Discussed; no silent strategy change.** Proposed alternative exits are separate preregisterable hypotheses. | revision paper §7 |
| 6. Financing/adjusted synthetic | **Implemented, results pending.** Adjusted total-return ETF proxy, 2× lagged short funding + expense + spread parameter. | `scripts/review_revision.py`, `synthetic_preinception` |
| 7. Cash at 0% | **Implemented.** Prior-month DTB3 investment-yield proxy applied to uninvested cash. | `scripts/rates.py`, `benchmark` |
| 8. Bad vendor join | **Fail-fast 1bp archive-independent anchor audit.** No arbitrary rescale. Public append requires overlapping date and same adjusted convention; official NAV independent validation still pending. | `scripts/review_revision.py`, `load_adjusted` |
| 9. Wrong bootstrap null/terminology | **Partial corrected.** Paired circular fixed-length block bootstrap for Sharpe, MDD, CDaR, CVaR, Ulcer **on archived monthly paths only**. Robust daily policy-re-estimation bootstrap still pending. | `scripts/reviewer_risk_bootstrap.py` |
| 10. Event/roundtrip and underwater | **Implemented, results pending.** Average DD, CDaR, Ulcer, longest underwater and exit→reentry foregone ETF return. | `metrics`, `pair_trades` |
| 11. Parameter data mining | **Disclosed.** All 54 inspected variants underperformed their own 3× hold CAGR in original audit. | revision paper §7 |
| 12. Start-date sensitivity | **Implemented, results pending.** First trading date of each month through Dec 2023, fresh $10k start with full SMA warmup. | `rolling_entry_analysis` |
| 13. Literature | **Added.** Gayed/Bilello, Faber, Avellaneda/Zhang, Cheng/Madhavan, Moreira/Muir, Ledoit/Wolf, Politis/Romano, White and Hansen. | revision paper References |
| 14. Malformed formula rendering | **Fixed.** Pandoc with `+tex_math_single_backslash+tex_math_dollars`; XeLaTeX PDF and Word OMML maths. | `paper/*.pdf`, `paper/*.docx` |
| 15. Overuse of disclaimers | **Consolidated.** One prominent evidence boundary, later transparent remaining gates. | revision paper §§Abstract, 8 |

## Publication gate

To publish revised empirical claims, run `python scripts/fetch_data.py` then `python scripts/review_revision.py --tail-mode public`. If strict dividend-overlap audit fails, use a single properly licensed consistent vendor to rebuild the entire source history rather than automatically rescaling mismatched streams. Publish `data/v2_results/benchmark_metrics.csv`, the trade ledger and regime tables, and record the audit hashes. The current v2 ZIP ships code plus the *legacy snapshot* and a new **monthly** paired-risk bootstrap; it does not ship fictitious updated return numbers.
