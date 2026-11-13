---
title: "A 200-Day Trend Filter for 3× Leveraged U.S. Equity ETFs"
subtitle: "No Robust Evidence of Timing Value in the Real-ETF Record: A Replication with Ex-Ante Benchmarks, Walk-Forward Selection and Multiple-Testing Control"
author: "Independent quantitative research · Version 4 (third-round revision)"
date: "12 November 2026 · data through 6 August 2026"
lang: en-US
geometry: margin=0.7in
fontsize: 10pt
colorlinks: true
linkcolor: teal
urlcolor: teal
header-includes:
  - \usepackage{booktabs}
  - \usepackage{float}
  - \floatplacement{figure}{H}
  - \AtBeginEnvironment{longtable}{\footnotesize}
---

# Abstract

We ask whether a 200-day simple-moving-average (SMA) rule adds market-timing value to 3× daily-reset equity ETFs. Signals from SPY drive SPXL and signals from QQQ drive TQQQ. The rule buys in five 20% stages while the signal ETF closes at least 4% above its SMA and sells everything after a close more than 3% below it. Every order fills at the next open and pays 10 bp. The **primary evidence** is the real-ETF period, 11 February 2010 to 6 August 2026. It uses one vendor's validated, total-return market prices for all four ETFs, which we reconcile against the issuers' published prices and distributions. Idle cash earns a lagged T-bill rate. A partly synthetic 1999–2026 history is reported separately and labelled **hypothetical** throughout.

In the real-ETF record, the rule cuts the maximum drawdown of SPXL from −76.9% to −53.4% and of TQQQ from −81.7% to −62.1%. It earns more than unleveraged SPY or QQQ (22.2% versus 14.8% a year, and 30.2% versus 19.7%). Yet it has a **lower** Sharpe ratio and Calmar ratio than simply holding SPY or QQQ, and than a 30% volatility target. **We find no statistically significant evidence of a timing advantage over any non-timing benchmark.**

Several tests reach this conclusion independently:

* A daily path bootstrap re-runs every rule (with identical definitions) on 1,000 resampled histories. Against unleveraged holdings, the ex-ante exposure-matched mix and volatility targeting, no Sharpe or Calmar difference is significant (centred two-sided p ≥ 0.35).
* White's Reality Check and Hansen's SPA test over all 45 parameter configurations give p ≥ 0.77 once returns are scaled to equal volatility.
* A five-year-train, one-year-test walk-forward selection does not beat the fixed baseline for SPXL. For TQQQ it improves on the fixed baseline, but its Sharpe ratio stays below unleveraged QQQ's.

The drawdown reduction relative to 3× buy-and-hold (23 pp for SPXL, 20 pp for TQQQ) occurs in 84–91% of bootstrap paths, but it is not statistically significant (p = 0.09–0.33). The rule's apparent advantage appears only in the hypothetical history that includes 2000–2002 and 2007–2009. In leave-one-crisis-out re-simulations, the SPXL advantage there survives removing any single crisis, but not removing all four crises with their aftermaths. For the Nasdaq-100, a volatility target matches the rule there with a far smaller drawdown.

The defensible reading is narrow. The filter behaves like insurance against prolonged bear markets, and the post-2010 record contains too few such events to show that the insurance is worth its cost.

**Keywords:** leveraged ETFs; trend following; volatility targeting; walk-forward; Reality Check; SPA; drawdown; replication.

# 1. Introduction and related literature

**Trend timing.** Moving-average rules have been studied since Brock, Lakonishok and LeBaron (1992). Faber (2007) popularised a 10-month rule for asset allocation, and Moskowitz, Ooi and Pedersen (2012) and Hurst, Ooi and Pedersen (2017) document time-series momentum across a century of data. Zakamulin (2014) shows that the real-life performance of moving-average timing is much weaker once realistic out-of-sample procedures and costs are imposed.

**Leveraged ETFs.** Daily-reset funds compound three times the daily return, so their long-run return depends on the path of prices and suffers a variance drag of roughly $(L^2-L)\sigma^2/2$ (Cheng and Madhavan 2009; Avellaneda and Zhang 2010). Gayed and Bilello (2016) combine both ideas: they rotate between leveraged equity and T-bills on a 200-day rule. This paper is an implementation-level replication of that idea.

**Volatility management.** Moreira and Muir (2017) and Harvey et al. (2018) show that scaling exposure by recent volatility improves risk-adjusted equity returns. Cederburg et al. (2020) find that the gains are fragile out of sample. Volatility management is the natural rival explanation for any benefit an SMA filter gives a leveraged fund.

**Data mining.** Sullivan, Timmermann and White (1999) show that the apparent success of technical rules shrinks once one corrects for the universe of rules searched. White (2000), Hansen (2005), Bailey and López de Prado (2014) and Harvey, Liu and Zhu (2016) provide the corresponding tests and thresholds.

This version responds to a third-round review. It adds strict data validation and issuer reconciliation, an audit of the information set behind every decision, ex-ante risk matching, walk-forward selection, leave-one-crisis-out analysis, a 45-configuration grid with Reality Check and SPA tests, cost and cash-vehicle scenarios, tail-risk measures, synthetic-sleeve stress tests, a mechanism decomposition, state-conditional tests, and a direct comparison with plain SPY and QQQ.

# 2. Hypotheses and what each benchmark controls

We state three hypotheses. They were written after earlier drafts had been seen and are **not preregistered**.

* **H1 (drawdown).** The rule has a shallower drawdown than holding the same 3× fund.
* **H2 (timing value).** At comparable exposure or risk, the rule earns more than non-timing allocations.
* **H3 (transport).** The answers are the same for the S&P 500 and the Nasdaq-100 versions.

| Benchmark | What it holds fixed | What a win against it would show |
|:--|:--|:--|
| 3× buy-and-hold | same instrument, full exposure | H1 only: lower risk, at a cost in return |
| 1× buy-and-hold (SPY/QQQ) | no leverage, no timing | that leverage plus timing is worth more than the plain index |
| 1× SMA (rule applied to SPY/QQQ) | same timing, no leverage | whether leverage adds value given the timing |
| Matched weight, **ex ante** | 3× weight equal to the trailing (≤5-year) average of the weights the SMA rule actually held, known at each close and re-set every 21 sessions; the same definition in the main backtest, the bootstrap and the crisis re-runs | timing value beyond lower average exposure |
| Vol target 30% | weight $\min(1,0.30/\hat\sigma_t)$ with trailing 63-day volatility; constant fixed in advance | timing value beyond volatility control |
| Matched weight, ex post † and frontiers | full-sample average weight; families over all weights and vol targets | descriptive only: these use the realised sample |

Earlier drafts compared the rule with a mix calibrated to its own full-sample average weight. That benchmark uses information that would not have been available in real time. It is now kept only as a labelled diagnostic (†). All inferential comparisons use the ex-ante version: its weight is the SMA rule's trailing ≤5-year average weight (0.76 on average), and before one year of history exists it is 0.75.

# 3. Data

## 3.1 Provenance

All four series are daily Yahoo Finance **market-price** bars (Open, High, Low, Close, Adj Close, Volume), exported by `yfinance` with `auto_adjust=False` and obtained from the public repository `hjyssg/tqqq_simulation`. The last common bar is 6 August 2026. The upstream repository does not record the download time, and the author received the files on 12 November 2026. `scripts/fetch_yahoo.py` re-downloads the data and records a UTC timestamp, the yfinance version and SHA-256 hashes. Because Yahoo restates dividend adjustments retroactively, a later download can differ; the audited hashes are listed below and in `data/v4_results/data_manifest.csv`. Raw files are shipped in the replication archive for verification but are not committed to the public repository, because of Yahoo's terms.

{{table:data}}

## 3.2 Validation

`load_yahoo()` now runs `validate_ohlcv()` before any computation and stops on any fatal failure. Fatal checks are:

* unsorted or duplicate dates, and weekend bars;
* missing values and non-positive prices;
* OHLC inconsistency (Low ≤ Open, Close ≤ High);
* Adj Close above Close, and a one-day adjustment-factor jump above 50%;
* any session missing from, or added to, an NYSE calendar built from explicit holiday rules and the special closures of 1994–2025.

All four files pass every fatal check and match the NYSE calendar exactly; the calendar is also unit-tested on known closures. The warnings are listed in `data_validation.csv`. They include the March 2020 and April 2025 extreme days, and a 13% adjustment-factor change in SPXL on 20 November 2009. On that day the price-only close fell 12.4% while the total-return series fell 0.84% (SPY fell 0.36%), consistent with a large capital-gain distribution. A price-only backtest would have booked that distribution as a loss.

## 3.3 Reconciliation with issuer data; market price versus NAV

{{table:official}}

Yahoo closes are **exchange market prices, not NAVs**: on 27 February 2025, SPXL's Yahoo close equals Direxion's published market close ($163.55), not its NAV ($163.27). The distributions implied by Yahoo's adjustment factor match Direxion's 2024 distributions to within $0.0005. Sources disagree on TQQQ's first trading day. Nasdaq's listing release, dated 11 February 2010, states that the fund "began trading today"; a BATS circular admits it to unlisted trading from 12 February. A 2025 ProShares release dates performance "from first day of trading on Feb 10, 2010, based on the funds' net asset value", which we read as its NAV start rather than its first exchange session. We follow the contemporaneous listing source: the first exchange trading day is **11 February 2010**, which is also Yahoo's first bar, so no session is missing. (Earlier versions said Yahoo omitted 10 February; that was wrong.) ProShares' published since-inception return is as of 31 October 2026, after our sample ends, so a full total-return reconciliation for TQQQ remains open (§11). All returns here are therefore **market-price total returns**, which is what an investor trading at the open would earn, before tax.

# 4. Strategy and execution protocol

Let $P_t$ be the signal ETF's adjusted close and $M_t=\frac1{200}\sum_{j=0}^{199}P_{t-j}$. After the close of day $t$:

1. if invested and $P_t<0.97M_t$, sell all shares at the open of $t+1$;
2. if flat and $P_t\ge1.04M_t$, buy to a 20% weight at the open of $t+1$;
3. if partly invested, below stage 5, and $P_t\ge1.04M_t$, buy up to the next stage (40%, 60%, 80%, 100%);
4. otherwise, hold. Positions are never trimmed to rebalance.

There is **no intraday stop**: no rule reads High or Low prices, and the only exit is the SMA test on the close. No margin or external borrowing is used; leverage exists only inside the ETF. Fills are fractional. Uninvested cash earns the previous month's 3-month T-bill rate, so the rate is known before it is applied.

| Quantity | Information used | Executed |
|:--|:--|:--|
| SMA signal, stage | closes up to and including $t$ | open $t+1$ |
| Vol-target weight | 63 daily returns ending at close $t$ | open $t+1$, every 5 sessions |
| Ex-ante matched weight | SMA-rule weights up to close $t$ (trailing ≤1,260 days) | open $t+1$, every 21 sessions |
| Walk-forward parameters, matched weight, vol target | the five calendar years before the test year | from the test year's first open |
| Cash rate | DTB3 quote from the previous month | daily accrual |
| Costs | constant, or era and trailing-volatility based (§7.4) | at each fill |

Every rule is also audited automatically. All prices after 29 June 2018 are distorted, every rule is re-run, and every decision and weight up to that date must be identical; every fill price must also equal that day's open. All rules pass:

{{table:audit}}

# 5. Hypothetical pre-inception sleeve (secondary evidence only)

Before SPXL (5 November 2008) and TQQQ (11 February 2010) traded, the leveraged sleeve is a daily-reset proxy:

$$L_t=L_{t-1}\left(1+3r_t^{TR}-\frac{2(\tilde r_{f,t}+s)+f}{252}\right).$$

The financing spread $s$ is calibrated on the real funds. It is then validated out of sample: we fit $s$ on 2010–2017 and compare the resulting proxy with the real fund over 2018–2026.

{{table:calib}}

Every result that uses this sleeve is labelled **HYPOTHETICAL**. None of it was investable, and none of it is used for the primary conclusions.

# 6. Primary evidence: the real-ETF record, 2010–2026

## 6.1 Performance and tail risk

{{table:main_real}}

*ES 99% is the mean daily return on the worst 1% of days. Recovery is the number of trading days from the deepest trough back to the previous peak. † Ex post diagnostic.*

![Growth of \$1, real-ETF window.](../figures/v4/equity_real.png){width=100%}

![Daily drawdowns, real-ETF window.](../figures/v4/drawdown_real.png){width=100%}

![Rolling one-year Sharpe ratio, real-ETF window.](../figures/v4/rolling_sharpe_real.png){width=100%}

The rule reduces maximum drawdown, daily ES99 and recovery time relative to the 3× fund. On risk-adjusted measures it ranks low. For TQQQ, its Calmar is below every benchmark except the ex-ante matched mix, and its Sharpe is the lowest of all seven rules.

Two changes from v3 matter here. First, the ex-ante matched mix (average weight 0.76) has a lower Calmar than the SMA rule for both funds, while the ex-post version used in v3 had a higher one. Part of v3's "the rule is beaten at equal exposure" result therefore came from look-ahead in the benchmark. Second, the matched mix still has the higher Sharpe ratio (0.739 versus 0.700, and 0.829 versus 0.771).

## 6.2 Does the strategy beat simply holding SPY or QQQ?

{{table:onex}}

The leveraged rule earns 7–11 pp a year more than the plain index, with roughly 20–27 pp deeper drawdowns. On every risk-adjusted measure in the real-ETF record, plain SPY or QQQ is at least as good. The SPA test finds the higher *raw* return of the SMA configurations over QQQ significant (p = 0.010) and borderline over SPY (p = 0.058). That reflects leverage, not timing: once returns are scaled to equal volatility, p = 1.000. A plain 1× SMA rule has the highest real-window Calmar of all for SPY (0.49). Over 1999–2026, the hypothetical history, the 3× rule beats unleveraged holdings on both measures (§8).

## 6.3 Walk-forward selection

In each test year from 2015, the configuration with the best Calmar (or Sharpe) over the previous five years is chosen from 45 candidates: SMA lengths 150/175/200/225/250, entry +2/+4/+6% and exit −1/−3/−5%. Only the test-year returns are kept. Switching configurations is charged its trading cost. The benchmarks are matched using training-window information only: a constant mix at the selected configuration's training-window average weight, and a volatility target chosen so that its training-window average weight equals the same value.

{{table:wf_real}}

{{table:wf_sel}}

![Walk-forward out-of-sample growth, 2015–2026, real ETFs.](../figures/v4/walkforward_real.png){width=100%}

Re-estimating the parameters every year does not help SPXL: the walk-forward rule's Calmar (0.247) is below the fixed baseline (0.341) and below every benchmark. For TQQQ, Calmar-based selection is slightly better than the fixed rule (0.506 versus 0.472), and Sharpe-based selection gives the highest Calmar of all rules (0.688). Its Sharpe ratio (0.801) is still below plain QQQ (0.807). The selected parameters drift across years (SMA 150–250, exit −1% to −5%), which is what one expects when differences between configurations are mostly noise. The hypothetical 2005–2026 walk-forward is in `walkforward_metrics.csv`.

## 6.4 Equal-risk frontiers (ex post, descriptive)

{{table:frontier}}

*Gap = rule CAGR minus the CAGR of the fixed-weight or vol-target family at the rule's own risk level, in pp per year. These families use the realised sample and are descriptive only.*

![Frontiers of non-timing allocations versus the SMA rule, SPY/QQQ and the 1× SMA rule.](../figures/v4/frontier.png){width=100%}

# 7. Inference and robustness (real-ETF record)

## 7.1 Daily path bootstrap with the policy re-run

We resample the joint daily vector (signal and leveraged close-to-close and overnight returns, and the cash rate) with the stationary bootstrap (Politis and Romano 1994), using mean blocks of 63 and 252 days. Both ETF pairs share the same resampled indices. On each of 1,000 paths, the prices are rebuilt and **every rule is re-run with exactly the definitions of the main backtest**, starting from the real pre-sample history. This includes the ex-ante matched mix: its weight is the trailing average of the weights the SMA rule actually holds on that path, with the SMA rule's pre-2010 weights as history. Re-running the engine on the unaltered path reproduces the main-table numbers to machine precision (`path_engine_consistency.csv`, and a unit test). As a separately labelled extra benchmark (‡), we also report a constant mix at the SMA rule's 1999–2009 average weight (0.57 for SPXL, 0.52 for TQQQ).

**Test.** For each comparison, $\Delta$ is the metric of the SMA rule minus that of the benchmark, and $H_0:\Delta=0$. Following Hall and Wilson (1991), we approximate the null distribution by centring the bootstrap distribution at the observed value, $\Delta^*-\hat\Delta$, and report the two-sided p-value $P^*(|\Delta^*-\hat\Delta|\ge|\hat\Delta|)$. The 2.5–97.5% percentile interval and the share of $\Delta^*>0$ are reported as **descriptive** statistics only. Results for 252-day blocks are shown; the 63-day results are in `bootstrap_summary.csv` and lead to the same conclusions.

{{table:boot}}

![Observed differences, bootstrap percentile intervals and centred p-values for Calmar and Sharpe.](../figures/v4/bootstrap_intervals.png){width=100%}

*‡ constant weight from 1999–2009. \* p < 0.05; n.s. otherwise.*

*How to read this.* A p-value above 0.05 means the data provide **no statistically significant evidence** of a difference. It does not show that the rule is ineffective or that the strategies are equal.

* **H1.** The drawdown is shallower than holding the 3× fund in 91% (SPXL) and 84% (TQQQ) of paths, but the difference is not significant (p = 0.09 and 0.16; 0.20 and 0.33 with 63-day blocks).
* **H2.** No Calmar or Sharpe difference against 1× hold, either matched mix or the volatility target is significant (all p ≥ 0.35).
* **Significant differences.** Against the 1× SMA rule, the 3× rule's drawdown is significantly deeper for both funds, and its Sharpe ratio is significantly lower for SPXL (p < 0.001): this is the cost of leverage. Against plain QQQ, the TQQQ rule's drawdown is significantly deeper with 252-day blocks (p = 0.019), but not with 63-day blocks (p = 0.074).
* **Why the two summaries can disagree.** For drawdowns, several percentile intervals exclude zero although the centred test is not significant, for example SPXL versus SPY and TQQQ versus the volatility target. Resampling breaks the post-2010 tendency of declines to reverse quickly, so the bootstrap distribution of drawdown differences is shifted away from the observed value (compare the observed Δ with the interval). The centred test corrects for this shift. The percentile interval does not, which is why we treat it as descriptive.

*Limitations of the resampling.* Blocks with a mean length of 63 or 252 days shorten the multi-year trends a 200-day filter relies on, which biases the bootstrap against trend rules. The real-ETF window also contains few long bear markets to resample. The intervals are therefore conditional on the post-2010 dependence structure and are not corrected for the earlier parameter choice. The SPA test in §7.2 handles that correction.

## 7.2 Parameter grid and multiple testing

{{table:grid}}

*Entries are the number of the 45 configurations that beat the benchmark, Calmar / Sharpe.*

![Calmar ratios of all 45 configurations, real-ETF window. * = baseline.](../figures/v4/parameter_heatmap_real.png){width=100%}

The baseline ranks 17th (SPXL) and 23rd (TQQQ) of 45 in the real window, so it was not the best in-sample choice. Real-window Calmar ratios range from 0.25 to 0.54 (SPXL) and from 0.37 to 0.62 (TQQQ). Configurations around SMA 150–175 with +4% entry look best, but the walk-forward test (§6.3) shows that picking them in advance did not pay off.

To correct for the 45 configurations searched, we apply White's (2000) Reality Check and Hansen's (2005) SPA_c test. Both use the stationary bootstrap with a mean block of 63 days and 2,000 replicates, and test the hypothesis that **no** configuration beats the benchmark.

{{table:spa}}

Against 1× hold, the best configuration's raw-return advantage is significant for QQQ and borderline for SPY. After scaling every configuration to the benchmark's volatility, no test comes close to rejecting (p ≥ 0.77 across all benchmarks). Against the ex-ante matched mix and the 30% volatility target, p ≥ 0.07 for raw returns. Even the best of 45 configurations shows no significant risk-adjusted superiority.

## 7.3 Leave-one-crisis-out

Crises are dated from index peak to trough: dot-com (2000-03-24 to 2002-10-09), global financial crisis (2007-10-09 to 2009-03-09), COVID (2020-02-19 to 2020-03-23) and 2022 (2022-01-03 to 2022-10-12).

**Counterfactual re-run (primary).** The crisis days are deleted from the input return series, either the decline alone or the decline plus the following 252 trading days, which captures the re-entry period. The remaining days are spliced into a new price path, and **every rule is re-simulated from scratch** on it with the path engine of §7.1. SMA levels, stages, volatility estimates and ex-ante weights are all recomputed, so each rule trades the history as if the crisis had not happened.

{{table:loco}}

In the real record, the rule has the best Calmar of the five rules in only 3 of 12 exclusion cases: SPXL without 2022 (both spans), and TQQQ without the COVID decline. For TQQQ, removing 2022 raises the rule's Calmar only from 0.487 to 0.620, while every benchmark rises to 0.78–0.87. In the hypothetical history, the SPXL rule keeps the best Calmar in every single-crisis exclusion, and even when the four declines alone are removed (1.147 versus 1.117 for SPY). It loses the lead only when the declines and their aftermaths are all removed (0.666 versus 0.825 for SPY). The TQQQ rule is best only when the dot-com crash is removed; in every other case volatility targeting is better. **The rule's favourable results depend on the large bear markets; none survives removing all of them with their recoveries, and in the real record they rest mainly on 2022.**

**Crisis-contribution decomposition (secondary).** For comparison, the earlier method simply deletes the crisis days from returns already computed on the full path, without re-simulating positions. That is a decomposition of where the return came from, not a counterfactual backtest, and we report it only as such (`crisis_contribution_returns_removed.csv`):

{{table:loco_decomp}}

The two methods differ wherever a crisis changed the rule's later state. For example, after re-simulation the real-window SPXL rule is best without the 2022 decline, but in the decomposition it is not.

## 7.4 Costs, execution and cash

{{table:costs}}

*Entries are CAGR / Calmar.*

The model-based cost scenario charges an era-dependent half-spread (5 bp in 2010–14, 2 bp in 2015–19, 1 bp from 2020) plus open-auction slippage of 5 bp + 0.1 bp per percentage point of the leveraged ETF's trailing 20-day volatility. This gives about 12–13 bp per SMA fill, rising to 35–40 bp in the ×3 stress. Commissions are included in the flat cases. Cash is either the T-bill rate less 10 bp, standing in for a T-bill ETF's expense ratio and settlement drag, or zero.

No scenario changes any ranking. The SMA rule trades rarely, 53–70 orders in 16 years. The volatility target trades often (707–808 orders), but its rebalances are small. All results are pre-tax: for a U.S. taxable investor, the SMA rule's full liquidations realise short-term gains, a cost not modelled here. Results assume fractional shares, open-auction liquidity sufficient for the order size, and no market impact.

# 8. Secondary evidence: the hypothetical 1999–2026 history

{{table:main_full}}

![1999–2026; shaded = synthetic pre-inception sleeve (HYPOTHETICAL).](../figures/v4/equity_full.png){width=100%}

Including 2000–2009 reverses the ranking for SPXL. The rule has the best Calmar and Sharpe among the leveraged rules and beats SPY on both (0.323 versus 0.152, and 0.577 versus 0.412), because it was in cash for most of both long bear markets. For TQQQ, the volatility target has a higher Calmar (0.210 versus 0.158) and Sharpe (0.511 versus 0.480), with a −66.9% instead of a −90.2% drawdown. The 1× SMA rule has the best Calmar of all for SPY (0.427), and is level with the volatility target for QQQ (0.209 versus 0.210).

**Synthetic-sleeve stress.** The scenarios cover the financing spread at 0 to 4 times its calibrated value, expense ratios of 0.75–1.25%, realised leverage of 2.9 or 3.1, a +300 bp funding shock during both crises, i.i.d. tracking noise at one and two times the observed residual (50 Monte Carlo paths each), and a pessimistic combination of these.

{{table:stress}}

Across all twelve scenarios, the SPXL rule's Calmar stays between 0.30 and 0.33 and the volatility target's between 0.13 and 0.15. For TQQQ, the volatility target stays ahead in every scenario. The 3× fund still loses 92–94% in the dot-com bear and 95–96% in the global financial crisis. The hypothetical conclusions do not depend on the synthetic-cost assumptions, but they rest entirely on two episodes that could not have been traded with these instruments.

# 9. Mechanism and state dependence

**Decomposition.** We split the gap in log growth between the rule and the 3× fund into two parts. The *exposure effect* is the ex-post matched mix minus the 3× fund. The *timing effect* is the rule minus the matched mix. Each gap is further split into a mean-return part and a variance-drag part, using $g\approx\mu-\sigma^2/2$.

{{table:mech}}

In the real record, the timing effect costs 4.1 pp (SPXL) and 5.4 pp (TQQQ) a year. Lower variance drag returns only 1.4 and 0.4 pp of that; the rest is the lower mean return from being out of the market during rebounds. In the hypothetical history, the timing effect adds 7.7 and 7.9 pp a year, mostly through the mean, by avoiding the 2000–2002 and 2007–2009 declines. In the real record, leverage itself (3× SMA versus 1× SMA) raises log growth by 10–14 pp a year, after 6–10 pp of extra variance drag.

**Where the timing effect comes from.**

{{table:mech_state}}

The pattern is the same in both histories. Inside the dated crises the rule gains: about 5–9 pp a year from the dot-com and 2008 bears, and 1–4 pp from 2022. Outside them it loses 6–10 pp a year. This is the profile of insurance: a small, recurring premium paid in normal markets and occasional large payouts in prolonged declines.

**State-conditional differences.** For each benchmark, we group days by the state at the previous close: trend (above or below SMA200), the signal ETF's trailing 20-day volatility (fixed thresholds of 15% and 25%), and the number of days since its one-year high. We then report the annualised mean daily return difference and its Newey–West t-statistic (10 lags).

{{table:states}}

In the real record, the rule out-earns its benchmarks in calm uptrends, because it is fully invested in 3× while the matched mix holds about 0.76: about +7 to +10 pp a year against the matched mix, t ≈ 2.0–2.4. It loses when the signal is below trend, because it sits in cash during rebounds: −54 to −70 pp a year, t ≈ −1.7 to −1.8. The losses in the below-trend and high-volatility states are large but not statistically significant, because those states cover only about 600 days.

# 10. Discussion

**No sufficient evidence of timing alpha.** In the period that can be traded with real funds, no test finds a statistically significant risk-adjusted advantage for the SMA rule. This holds against unleveraged SPY/QQQ, ex-ante exposure-matched mixes and volatility targeting, and across fixed parameters, the full grid and walk-forward selection. Its drawdown reduction relative to the 3× fund is large in the point estimates (20–23 pp), but it is not statistically significant (p = 0.09–0.33). This is not evidence that the rule fails. It means 16 years containing one prolonged bear market (2022) cannot distinguish the rule from simpler alternatives.

**Why the hypothetical history differs.** The rule's value depends on whether below-trend markets keep falling, as in 2000–02, 2007–09 and 2022, or recover within weeks, as in 2010, 2011, 2015–16, 2018, 2020 and 2025. Volatility targeting responds to rising volatility rather than to price relative to trend, so it handles crash-from-the-top episodes such as QQQ in 2000 better. That explains why it dominates the Nasdaq-100 version even in the hypothetical history.

**Implications.** An investor who wants an unleveraged index's risk-adjusted profile can hold the index. An investor who wants leverage and tail protection should compare the SMA rule with volatility targeting and should not expect a timing premium. Any modified rule, such as SMA combined with volatility scaling, was conceived after seeing this history and must be tested on data not used here, such as non-U.S. indices or a forward paper-trading period.

# 11. Limitations

1. **Selection and design.** The rule, thresholds, benchmarks and hypotheses were chosen after the history was observed. Walk-forward and SPA tests reduce, but cannot remove, this bias. Only two closely related U.S. indices were studied (sample-selection bias).
2. **Survivorship.** SPXL and TQQQ are the surviving, largest funds in their category. Closed or restructured leveraged funds are not represented.
3. **Synthetic history.** 2000–2009 results use a calibrated proxy that tracks real funds well after 2018. It cannot reproduce 2000-era swap availability, counterparty and termination risk, or fund closures. Daily-reset leveraged ETFs did not exist then.
4. **Regime differences.** Market structure, ETF liquidity, interest rates (zero-rate years 2009–15 and 2020–21) and monetary-policy regimes differ across the sample. The post-2010 record contains only one prolonged bear market.
5. **Inference.** Bootstrap resampling weakens long trends. All p-values are conditional on the stated null hypotheses and on the 45-configuration universe. Earlier unrecorded exploration cannot be corrected for.
6. **Data.** Yahoo market prices are not NAVs. Sources conflict on TQQQ's first trading day; we use the Nasdaq listing date, 11 February 2010. The TQQQ total-return reconciliation with ProShares awaits an official figure dated inside the sample.
7. **Execution and taxes.** Fills are fractional, at the open, with modelled rather than observed costs, and without market impact. Results are pre-tax.
8. **Generalisation.** Nothing here establishes that the conclusions transfer to other markets, leverage ratios or future regimes.

# 12. Conclusion

With validated single-vendor data, a verified execution protocol and ex-ante benchmarks, the 200-day filter reduces the drawdowns of 3× equity ETFs in the point estimates. In the real-ETF record we find no statistically significant evidence that it adds timing value: not against unleveraged SPY/QQQ, not against exposure-matched mixes, not against volatility targeting, and not after correcting for the 45 configurations searched. Its advantages appear only in a hypothetical history whose decisive episodes predate the instruments. The appropriate description is a transparent tail-risk rule whose value depends on the shape of future bear markets, not a demonstrated source of alpha.

# Reproducibility

The entry point `./run_all.sh` runs the 46 unit tests, all analyses (`scripts/v4_run.py`, about 3 minutes), the tables, the manuscript build and `scripts/verify_results.py`. The last step checks 682 reference values (main table, walk-forward, crisis re-runs, bootstrap differences and p-values, SPA) against `data/expected_results.json`, and a second independent run reproduced all of them. Seeds are fixed: 20260806 for the path bootstrap and 20260807 for SPA. Pinned versions are in `requirements.txt` and the run manifest (Python 3.13, numpy 2.5.3, pandas 3.0.5, matplotlib 3.11.2). Data provenance, hashes and validation reports are in `data/v4_results/`.

# References

1. Avellaneda, M., and S. Zhang (2010). Path-dependence of leveraged ETF returns. *SIAM Journal on Financial Mathematics* 1, 586–603.
2. Bailey, D. H., and M. López de Prado (2014). The deflated Sharpe ratio. *Journal of Portfolio Management* 40(5), 94–107.
3. BATS Exchange (2010). Information Circular IC 2010-012: ProShares UltraPro QQQ and UltraPro Short QQQ, commencement of trading 12 February 2010. 11 February 2010.
4. Board of Governors of the Federal Reserve System. 3-Month Treasury Bill Secondary Market Rate, Discount Basis (DTB3), via FRED.
5. Brock, W., J. Lakonishok, and B. LeBaron (1992). Simple technical trading rules and the stochastic properties of stock returns. *Journal of Finance* 47(5), 1731–1764.
6. Cederburg, S., M. S. O'Doherty, F. Wang, and X. Yan (2020). On the performance of volatility-managed portfolios. *Journal of Financial Economics* 138(1), 95–117.
7. Cheng, M., and A. Madhavan (2009). The dynamics of leveraged and inverse exchange-traded funds. *Journal of Investment Management* 7(4), 43–62.
8. Direxion (2026). Direxion Daily S&P 500 Bull 3X Shares (SPXL): fund page, distributions and daily NAV/market close. Retrieved 12 November 2026.
9. Faber, M. T. (2007). A quantitative approach to tactical asset allocation. *Journal of Wealth Management* 9(4), 69–79.
10. Gayed, M. A., and C. V. Bilello (2016). Leverage for the long run. Charles H. Dow Award paper, CMT Association.
11. Hall, P., and S. R. Wilson (1991). Two guidelines for bootstrap hypothesis testing. *Biometrics* 47(2), 757–762.
12. Hansen, P. R. (2005). A test for superior predictive ability. *Journal of Business & Economic Statistics* 23(4), 365–380.
13. Harvey, C. R., E. Hoyle, R. Korgaonkar, S. Rattray, M. Sargaison, and O. Van Hemert (2018). The impact of volatility targeting. *Journal of Portfolio Management* 45(1), 14–33.
14. Harvey, C. R., Y. Liu, and H. Zhu (2016). … and the cross-section of expected returns. *Review of Financial Studies* 29(1), 5–68.
15. Hurst, B., Y. H. Ooi, and L. H. Pedersen (2017). A century of evidence on trend-following investing. *Journal of Portfolio Management* 44(1), 15–29.
16. Ledoit, O., and M. Wolf (2008). Robust performance hypothesis testing with the Sharpe ratio. *Journal of Empirical Finance* 15(5), 850–859.
17. Moreira, A., and T. Muir (2017). Volatility-managed portfolios. *Journal of Finance* 72(4), 1611–1644.
18. Moskowitz, T. J., Y. H. Ooi, and L. H. Pedersen (2012). Time series momentum. *Journal of Financial Economics* 104(2), 228–250.
19. NASDAQ OMX (2010). ProShares Launches Two New Exchange Traded Funds Based on the NASDAQ-100 Index. GlobeNewswire, New York, 11 February 2010 ("began trading today").
20. Politis, D. N., and J. P. Romano (1994). The stationary bootstrap. *Journal of the American Statistical Association* 89(428), 1303–1313.
21. ProShares (2025, 2026). UltraPro QQQ (TQQQ): fund page and performance; press release "ProShares Celebrates 15 Year Anniversary of TQQQ" (10 February 2025). Retrieved 12 November 2026.
22. Sullivan, R., A. Timmermann, and H. White (1999). Data-snooping, technical trading rule performance, and the bootstrap. *Journal of Finance* 54(5), 1647–1691.
23. White, H. (2000). A reality check for data snooping. *Econometrica* 68(5), 1097–1126.
24. Zakamulin, V. (2014). The real-life performance of market timing with moving average and time-series momentum rules. *Journal of Asset Management* 15(4), 261–278.
