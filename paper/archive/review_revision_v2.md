---
title: "A 200-Day Trend Filter for 3× Leveraged U.S. Equity ETFs"
subtitle: "Reviewer-Response Revision: Financing, Exposure-Matched Controls, Risk Inference, and Reproducibility"
author: "Independent quantitative research | Methodological revision v2"
date: "12 November 2026"
lang: en-US
geometry: margin=0.86in
fontsize: 10pt
colorlinks: true
---

# Abstract

This revision reassesses a fixed, long-only rule in which the close of SPY (or QQQ) relative to its 200-session simple moving average (SMA) controls staged next-open investments in the daily-reset 3× product SPXL (or TQQQ). The original observational backtest recorded higher drawdown-adjusted *absolute* losses avoided than unfiltered leveraged buy-and-hold but weaker return and Sharpe performance in the common real-ETF period, 11 February 2010–12 November 2026. We accept the referee's central identification objection: reduced drawdown **by itself** does not demonstrate timing skill because cash exposure is variable. Accordingly, the v2 engine adds unleveraged ETF buy-and-hold, an average-capital-weighted leveraged/cash benchmark, and a lagged-realized-volatility allocator; reconstructs pre-inception leveraged returns with bank-bill funding and consistent adjusted source prices; measures average portfolio weight rather than counting every positive-weight day as a full exposure; and generates regime, rolling-start and trade-ledger diagnostics.

**Evidence boundary.** The present accompanying historical performance figures are *the uncorrected v1 audit*, not results from the corrected financing and dividend model. Its licensed four-instrument daily source archives cannot be fetched inside the current authoring environment. The corrected model and unit tests are provided, but **new v2 benchmark CAGRs, risk-adjusted comparisons, regime tables, and rolling-start distributions are not asserted as validated empirical findings until a complete source refresh and reproduction run succeeds**. A separate, executable paired circular-block bootstrap operates on the available **201 archived month-end observations** and is labeled explicitly as a coarse-frequency sensitivity audit, not a journal-grade daily-risk inference.

# 1. Prior art, research design, and falsifiable hypotheses

The 200-day leverage-switching idea is not novel. Gayed and Bilello (2016), *Leverage for the Long Run*, explicitly connect long-term trend, realized volatility, and the decision to employ leverage or move to Treasury bills. Faber (2007) studies moving-average tactical asset allocation. Avellaneda and Zhang (2010) establish the path dependence of leveraged ETF returns, and Moreira and Muir (2017) provide a competing volatility-management mechanism. The contribution here is therefore best characterized as an **implementation-level replication and adversarial benchmark of an existing hypothesis**, not the discovery of SMA-based leverage rotation.

We prestate three distinct hypotheses, none presumed established: (H1) next-open SMA exit reduces severe realized drawdowns relative to 3× buy-and-hold; (H2) it improves a relevant *risk-adjusted metric* versus equal average leveraged exposure and versus a volatility-managed alternative; (H3) findings transport across an S&P 500-linked and a Nasdaq-100-linked product without asset-specific threshold fitting. H1 is descriptive until inference is performed. H2 is the critical test of market-timing value. SPY and QQQ are correlated U.S. equity exposures; agreement between them is limited transport evidence, not a broad multi-asset replication.

# 2. The unchanged trading rule

For signal ETF closing adjusted price \(P_t\), define

$$
M_t=\frac{1}{200}\sum_{j=0}^{199}P_{t-j}.
$$

After close \(t\), a new entry or one additional staged purchase is scheduled if \(P_t\ge1.04M_t\), until targeted weights 20%, 40%, 60%, 80%, and 100% are reached. The target is based on *total portfolio equity at execution*; no automatic sales rebalance an appreciating partial position. Existing shares are retained if \(0.97M_t\le P_t<1.04M_t\). If invested and \(P_t<0.97M_t\), every leveraged-ETF share is sold. All scheduled orders fill at **open \(t+1\)**. A uniform assumed \(0.10\%\) one-way friction applies per executed notional; taxes and market-impact tails are outside scope. Full stock/ETF purchases permit fractional units.

The 3% filter is a *price-vs-average threshold*, not a fixed 3% stop on ETF equity. A stretched trend can be far above its own SMA; therefore the rule can still suffer large and rapid leveraged drawdowns before exiting.

# 3. Correcting cash, financing, and distributions

## 3.1 Historical T-bill proxy and safe information timing

The revision uses monthly *last available* daily quotations from the Federal Reserve's DTB3 3-month Treasury bill bank-discount series. Only **the previous calendar month's** last available quote is used during month \(m\): the current month's final observation is never used prospectively inside that month. As DTB3 quotes on a bank-discount, 360-day convention, a 91-day investment-equivalent annual rate is approximated by

$$
\tilde r_{f,t}=\frac{(365/360)d_{m-1}}{1-(91/360)d_{m-1}},
$$

where \(d_{m-1}\) is the prior-month-end quoted annual discount yield in decimal form. This is a stylized bill reinvestment proxy, not an exact tradeable return series; actual cash accounts may receive less and may have account-specific restrictions. Idle portfolio cash compounds at approximately \(1+\tilde r_{f,t}/252\) per trading day. The machine-readable derivative contains 335 monthly observations spanning December 1998–October 2026; October's latest sourced quote was 26 October. The isolated negative September 2015 quote (−0.01% annual bank discount) is explicitly preserved in the rate decoder rather than silently rounded to zero.

## 3.2 Pre-inception leveraged return, using consistent total-return underlying

Let \(r_t^{TR}\) be the unleveraged ETF daily **adjusted total-return proxy**. The pre-inception synthetic 3× closing series follows

$$
L_t=L_{t-1}\left(1+3r_t^{TR}-2\frac{\tilde r_{f,t}+s}{252}-\frac{f}{252}\right),
$$

where \(s\ge0\) is an explicit additional annual financing spread **per borrowed unit** and \(f=0.0095\) is an illustrative annual operating fee. Two funded units are charged at the short-rate proxy, unlike the prior v1 code, which omitted the borrowing term. The financing and fee are not charged a second time for actual SPXL/TQQQ prices, which already reflect the funds' realized economics. Synthetic openings model 3× the overnight underlying move and an illustrative half-day carry; they remain **not executable historical quotes**. Exact swap costs, futures basis, ETF tracking and historical distribution implementation are not observed and hence cannot be recovered from a price file alone.

SPY and SPXL source files have `Adj Close`; the adjusted Open is reconstructed as `Open × Adj Close / Close` on each date. The already-auto-adjusted QQQ/TQQQ inputs remain adjusted. The recent tail must use matching adjustment conventions. Source stitching **fails rather than rescales** if the archive and the independent overlap close differ by more than one basis point. The IBKR-only snapshot is retained solely as a dated, partly price-return, *legacy comparison*; any new corrected total-return analysis uses vendor-consistent input or stops with an error.

## 3.3 Economic intuition and its limitations

For ideal continuous-time constant daily-reset leverage \(\ell\), arithmetic underlying drift \(\mu\), variance \(\sigma^2\), and a funding rate \(r_f\), the approximate leveraged log growth is

$$
g_{\ell}\simeq\ell\mu-\frac{\ell^2\sigma^2}{2}-(\ell-1)r_f-f.
$$

At \(\ell=3\), the variance penalty is \(4.5\sigma^2\), approximately 55.1% annually for \(\sigma=35\%\), versus 6.48% for \(\sigma=12\%\), holding all else fixed. This illustrates why high-volatility regimes can damage compounded leveraged growth. It is **not evidence that an SMA filter actually predicts future volatility or return**. The v2 `regime_nextday.csv` generator therefore sorts observations by the close-of-day signal regime, then computes the *following* session's underlying mean return, volatility, and illustrative leveraged growth, avoiding same-bar contemporaneous circular reasoning.

# 4. Independent controls that determine timing value

The experiment explicitly compares five investment rules on common timestamps and identical data:

| Method | Target weight in 3× ETF | Cash treatment | Timing information |
|:--|:--|:--|:--|
| SMA200 / +4% / −3% | Original five-stage state machine | Prior-month T-bill yield | Close \(t\), open \(t+1\) |
| Leveraged ETF buy/hold | 100% after first open | None except residual | None |
| Unleveraged SPY or QQQ buy/hold | 100% in 1× ETF | None except residual | None |
| Exposure-matched | Constant leveraged allocation equal to **realized mean SMA weight**, remainder cash; rebalance every 21 trading sessions | Prior-month T-bill yield | Retrospective diagnostic only |
| Volatility-managed | Weight \(\min(1,0.30/\hat\sigma_{63,t})\), 63-day lagged-realized ETF volatility; rebalance every 5 sessions | Prior-month T-bill yield | Trailing through close \(t\) |

The **average weight** is \(\bar w=T^{-1}\sum_t w_t\) where \(w_t=\mathrm{shares}_t\,\mathrm{price}_t/\mathrm{NAV}_t\); a 20%-weight day is therefore only one-fifth of a full-risk day, not 100% exposed. The exposure-matched control calibrates to a **full-sample realized mean SMA weight** and thus is **ex-post only**, not a prospective investment rule; it isolates how much lower average exposure explains. The 30% volatility target is a fixed, plainly stated diagnostic choice, not fit on these two funds. Any claim of superior SMA *timing* demands a relevant advantage versus these alternatives with appropriately calibrated risk and statistical uncertainty, not just superiority to 100%-exposed leveraged ETF drawdown.

# 5. Results audit and Calmar correction

The following **v1** figures are preserved to show what was criticized. They are *not* asserted as corrected total-return, financing-inclusive v2 results. The common actual-ETF dates were 11 February 2010–12 November 2026, with 10 bp execution cost and **zero** yield on uninvested cash.

| Original 2010–2026 audit | SMA CAGR | 3× hold CAGR | SMA max DD | Hold max DD | SMA Calmar | Hold Calmar |
|:--|--:|--:|--:|--:|--:|--:|
| SPXL | 21.14% | 28.94% | −52.88% | −76.86% | 0.400 | 0.377 |
| TQQQ | 26.93% | 40.91% | −62.09% | −81.66% | 0.434 | **0.501** |

The TQQQ SMA rule underperformed unfiltered leveraged buy/hold on CAGR, Sharpe, **and Calmar**, and only offered a smaller *absolute* observed maximum drawdown. Even SPXL's Calmar advantage is narrow. Thus the original draft's blanket risk-management framing was too strong. Since lower exposure plausibly accounts for some downside improvement, **the independent value of the SMA filter remains unproven** until the v2 control runs finish.

![Figure 1. Legacy real-ETF 2010–2026 audited equity curves, *before* funding, dividend and benchmark revisions. Do not read as v2 performance.](../figures/equity_2010.png){width=93%}

# 6. Paired risk uncertainty: newly computed, frequency-limited evidence

A paired fixed-length **circular block bootstrap** reuses the archived *201 monthly close-to-close observations* of both strategies and their leveraged buy/hold controls (5,000 draws, 12-month blocks, seed 20261112). Each bootstrap draw uses the **same sampled month indices** for the strategy and its control, preserving contemporaneous co-movement. These are percentile intervals from an explicitly *retrospective* sample; the method is not the Politis–Romano stationary bootstrap, does not use Ledoit–Wolf's complete studentized Sharpe procedure, and does not correct for earlier parameter search.

| Asset | Risk difference (strategy minus 3× hold) | Observed | Paired 95% percentile interval |
|:--|:--|--:|--:|
| SPXL | Monthly-return Sharpe (rf = 0) | −0.047 | [−0.276, +0.184] |
| TQQQ | Monthly-return Sharpe (rf = 0) | −0.121 | [−0.375, +0.182] |
| SPXL | Max drawdown, sampled monthly NAV | +0.213 | [−0.066, +0.338] |
| TQQQ | Max drawdown, sampled monthly NAV | +0.289 | [−0.215, +0.351] |
| SPXL | Worst 5% monthly CVaR | +0.052 | [−0.009, +0.109] |
| TQQQ | Worst 5% monthly CVaR | +0.025 | [−0.029, +0.075] |

![Figure 2. Legacy monthly paired bootstrap intervals. Every shown interval intersects zero; these do not estimate daily policy-resampling uncertainty.](../figures/v2/paired_monthly_risk_intervals.png){width=93%}

The sign of drawdown/CVaR differences is written so a positive value indicates a **smaller absolute loss** under SMA. All six exploratory intervals cross zero. This does not demonstrate risk-indicator superiority. Month-end sampling misses adverse daily peaks and therefore these figures cannot be substituted for daily-sampled drawdown inferential results. A valid future analysis should bootstrap the **joint daily asset-return and cash-rate process**, **re-run the trading policy within every resampled path**, and respect estimation and parameter-selection uncertainty; merely shuffling precomputed strategy returns does not retrain the policy on counterfactual prices.

# 7. Stress and sensitivity diagnostics, disclosure of multiple testing

The baseline remains SMA200/+4%/−3%, selected before this revision. The previously inspected 27-cell grid per ETF uses SMA lengths 150, 200, 250; entry buffers +2%, +4%, +6%; and exit buffers −1%, −3%, −5%. All 54 variants produced positive historical CAGR in the original 2010 sample, **but not one exceeded its fund's corresponding 3× buy-and-hold CAGR** (SPXL grid maximum 22.54% versus leveraged hold 28.94%; TQQQ grid maximum 31.12% versus leveraged hold 40.91%). This comparison matters more than the visual positivity of the heatmap. The grid does not establish a broad optimal plateau; repeated inspection creates data snooping. White (2000) and Hansen (2005) motivate formal correction, but the set of previously tried unpublished rules is unknown, so a defensible comprehensive multiple-testing adjustment cannot be claimed.

The program additionally writes full-sample *daily* risk summaries (mean/conditional mean drawdown, CDaR10, CVaR5, Ulcer Index, underwater fraction, longest underwater spell), a trade ledger mapping each full exit to the subsequent first-stage reentry, and a monthly-start distribution of strategy CAGR and maximum drawdown. The ledger records the leveraged ETF return **forgone between exit and reentry**. A positive foregone return is a reentry opportunity cost; a negative one reflects avoiding part of a decline. It is not counterfactual causal identification, and the trade count is small. These features are implemented but do not have populated corrected-run tables in this release because the four raw price streams are unavailable locally.

**Mechanical weakness to test next:** as price rises far above a trailing average, the absolute exit distance expands; during violent crashes a next-open execution can suffer a material gap. Alternative volatility-scaled buffers or trade-level drawdown stops can be prospectively preregistered as **new** experiments, not silently substituted into this baseline.

# 8. Code validation, data requirements, and pending publication gates

The revised code includes offline unit tests verifying next-open timing, staged orders, proper liquidation, average capital weight, interest accrual on uninvested cash, last-month-only Treasury quotations, failure on an unaligned vendor splice, and that higher financing costs worsen the synthetic invested return. A separate paired monthly-risk file is generated directly from shipped derived NAV snapshots and runs entirely offline. The entire corrected cross-asset backtest requires four *locally retrieved* adjusted OHLC archives plus a tail that passes the 1 bp overlap audit.

The following **must** be satisfied before the paper can honestly be treated as a revised empirical replication rather than an executable research protocol:

1. Acquire licensed, consistent total-return OHLC for all four instruments, with dividend/split reconciliation and independent checks of official fund NAV total returns.
2. Rerun `scripts/review_revision.py`; publish the **new** v2 results rather than reusing v1 metrics; record the source file hashes and merge-status report.
3. Evaluate 1×, cash-weight-matched, and volatility-managed benchmarks on identical windows, with both matched-weight and volatility-target opportunity costs explicitly discussed.
4. Run a daily dependent risk bootstrap that recalculates strategy decisions on resampled price *paths*, and a truly future frozen-parameter paper-trading sample.
5. Release any additional parameter trials together with their outcomes. Do not describe the 2018–2026 split as an untouched holdout given the historical experimentation.

The record remains *exploratory* until these conditions are met. This is a deliberately stronger and more falsifiable characterization than “risk management validated.”

# References

1. Gayed, M. A. and Bilello, C. V. (2016). *Leverage for the Long Run: A Systematic Approach to Managing Risk and Magnifying Returns in Stocks*. Charles H. Dow Award. https://cmtassociation.org/wp-content/uploads/2025/08/2016-gayed-bilello.pdf.
2. Faber, M. T. (2007). *A Quantitative Approach to Tactical Asset Allocation*. Journal of Wealth Management. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461.
3. Avellaneda, M. and Zhang, S. (2010). *Path-Dependence of Leveraged ETF Returns*. SIAM Journal on Financial Mathematics, 1, 586–603. https://math.nyu.edu/inmemoriam/avellaneda/SIAMLETFS.pdf.pdf.
4. Cheng, M. and Madhavan, A. (2009). *The Dynamics of Leveraged and Inverse Exchange-Traded Funds*. Journal of Investment Management, 7(4).
5. Moreira, A. and Muir, T. (2017). *Volatility-Managed Portfolios*. Journal of Finance, 72, 1611–1644. https://doi.org/10.1111/jofi.12513.
6. Ledoit, O. and Wolf, M. (2008). *Robust Performance Hypothesis Testing with the Sharpe Ratio*. Journal of Empirical Finance, 15, 850–859. https://doi.org/10.1016/j.jempfin.2008.03.002.
7. Politis, D. N. and Romano, J. P. (1994). *The Stationary Bootstrap*. JASA, 89(428), 1303–1313. https://doi.org/10.1080/01621459.1994.10476870.
8. White, H. (2000). *A Reality Check for Data Snooping*. Econometrica, 68(5), 1097–1126. https://doi.org/10.1111/1468-0262.00152.
9. Hansen, P. R. (2005). *A Test for Superior Predictive Ability*. Journal of Business & Economic Statistics, 23(4), 365–380. https://doi.org/10.1198/073500105000000063.
10. Board of Governors of the Federal Reserve System (U.S.). DTB3, 3-Month Treasury Bill Secondary Market Rate, Bank-Discount Basis. Federal Reserve Bank of St. Louis (FRED). https://fred.stlouisfed.org/series/DTB3.
11. Direxion. *SPXL fund profile and daily target*. https://www.direxion.com/product/daily-sp-500-bull-bear-3x-etfs.
12. ProShares. *TQQQ fund profile and daily target*. https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq.
