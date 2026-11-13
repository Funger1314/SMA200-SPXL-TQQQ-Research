---
title: "A 200-Day Trend Filter for 3× Leveraged U.S. Equity ETFs"
subtitle: "Timing Value or Exposure Reduction? A Single-Vendor Replication with Matched-Risk Benchmarks (1999–2026)"
author: "Independent quantitative research · Version 3 (referee revision)"
date: "12 November 2026 · sample ends 6 August 2026"
lang: en-US
geometry: margin=0.75in
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

We test whether a 200-day simple-moving-average (SMA) rule adds *timing* value to 3× daily-reset equity ETFs, or merely lowers exposure. Signals from SPY are executed in SPXL and signals from QQQ in TQQQ: the rule buys in five 20% stages while the signal ETF closes ≥4% above its SMA200 and exits fully after a close <3% below it, with every order filled at the next open and 10 bp one-way friction. Relative to earlier drafts, this version (i) uses one vendor's split- and dividend-adjusted daily bars for all four instruments, removing every cross-vendor splice; (ii) pays a lagged 3-month T-bill rate on idle cash; (iii) calibrates the financing spread of the pre-inception 3× proxy on the real ETFs (70–75 bp per borrowed unit) and validates it out of sample; and (iv) benchmarks the rule against 1× buy-and-hold, an exposure-matched constant mix, a volatility-targeted allocation, and the full risk–return frontiers of the last two.

In the real-ETF window (11 Feb 2010–6 Aug 2026) the rule cuts maximum drawdown from −76.9% to −53.4% (SPXL) and from −81.7% to −62.1% (TQQQ), but it lies **below** both non-timing frontiers: at equal maximum drawdown a constant mix or a volatility target earned 1.2–4.6 pp more per year, and the gap widens under CDaR and Ulcer measures. A daily stationary bootstrap that re-runs the policy on 1,000 resampled paths places the rule's Calmar ratio below the exposure-matched mix in 72–74% of draws (252-day mean blocks). The picture reverses when the sample includes 2000–2009: on the partly synthetic 1999–2026 history the SPXL rule beats every non-timing frontier by 8–11 pp of CAGR at equal risk, while for TQQQ a simple volatility target matches its return with a far smaller drawdown (−66.9% vs −90.2%). The evidence therefore supports a narrow interpretation: the SMA filter is **insurance against prolonged bear markets**, paid for by repeated whipsaw losses in V-shaped corrections. Its post-2010 record does not show timing value beyond exposure reduction.

**Keywords:** leveraged ETFs; trend following; volatility targeting; drawdown; path dependence; backtest inference; replication.

# 1. Question, prior art and hypotheses

Switching leveraged equity exposure on a long moving average is not new. Gayed and Bilello (2016) document that U.S. equities above their 200-day average exhibit lower subsequent volatility and better leveraged compounding, and propose rotating between leveraged equity and Treasury bills; Faber (2007) popularised the 10-month moving-average timing rule; and the time-series momentum literature supplies a broader rationale (Moskowitz, Ooi and Pedersen 2012; Hurst, Ooi and Pedersen 2017). For daily-reset funds, path dependence makes variance a first-order cost (Cheng and Madhavan 2009; Avellaneda and Zhang 2010), and Moreira and Muir (2017) show that simply scaling exposure by inverse recent variance improves equity risk-adjusted returns. This last result supplies the natural rival explanation: an SMA filter may help leveraged funds only because it lowers average exposure and loosely tracks volatility.

Our contribution is therefore an **implementation-level replication with adversarial benchmarks**, not the discovery of a new rule. We state three hypotheses. They were written after the earlier drafts had been seen and are **not** preregistered.

* **H1 (drawdown).** The rule reduces realised drawdown relative to holding the same 3× ETF.
* **H2 (timing value).** At equal average exposure or equal realised risk, the rule earns more than non-timing allocations (a constant mix and a volatility target).
* **H3 (transport).** The answers to H1–H2 are the same for an S&P 500 and a Nasdaq-100 implementation without asset-specific tuning.

H1 is easy to satisfy; H2 is the economically important test.

# 2. Data

All four series are Yahoo Finance daily bars exported by `yfinance` with `auto_adjust=False` (columns Open, High, Low, Close, Adj Close), obtained from the public repository `hjyssg/tqqq_simulation`. Using one vendor for every instrument removes the splice and convention mismatches of the earlier drafts (price-only SPY/SPXL versus adjusted QQQ/TQQQ, and a separately sourced 2022–2026 tail). The raw files are not redistributed; their SHA-256 hashes are recorded below and in `data/v3_results/data_audit.csv`.

{{table:audit}}

*Total-return bars.* `Adj Close` incorporates splits and cash distributions. Because Yahoo's `Close` is split-adjusted only, the dividend-adjusted open is reconstructed as Open × AdjClose / Close on each date. Both the SMA signal and all fills use these total-return bars.

*Integrity checks.* The files are sorted and unique, with no missing or non-positive prices and no High/Low inconsistencies, and SPY/SPXL and QQQ/TQQQ share identical trading calendars after each fund's inception. Regressing daily leveraged returns on three times the underlying leaves a residual standard deviation of 15–19 bp. The few residuals above 2% occur in sign-reversing pairs (SPXL in November 2008, July 2009 and 9–10 April 2025; TQQQ on 21–24 May 2010 and 17 March 2020). These are consistent with closing-price deviations from NAV. Because investors trade at market prices, they are retained.

*Sample end.* The common last bar is **6 August 2026**. Earlier drafts reported through 12 November 2026 using a private tail, so their last three months are not comparable.

*Cash.* Idle cash accrues the prior month's last DTB3 3-month T-bill quote converted to an investment yield, so no rate is used before it is observable. The 3× products' own prices already embed their financing and are not charged again.

# 3. The trading rule (unchanged)

Let $P_t$ be the signal ETF's adjusted close and $M_t=\frac{1}{200}\sum_{j=0}^{199}P_{t-j}$. After the close of day $t$:

1. if invested and $P_t<0.97M_t$, sell all leveraged shares at the open of $t+1$;
2. otherwise, if flat and $P_t\ge1.04M_t$, buy to a 20% portfolio weight at the open of $t+1$;
3. otherwise, if partly invested, below stage 5, and $P_t\ge1.04M_t$, buy up to the next stage (40%, 60%, 80%, 100%);
4. between the bands, do nothing. Positions are never sold to rebalance.

Each fill pays 10 bp of notional. The SMA buffer is not a stop on fund equity: the rule can lose heavily before the signal ETF falls 3% below a rising average, and gaps between close and next open are borne in full.

# 4. Pre-inception 3× proxy: calibrated, then validated

Before each fund existed (SPXL before 5 Nov 2008, TQQQ before 11 Feb 2010) the leveraged sleeve is a daily-reset proxy

$$
L_t=L_{t-1}\left(1+3r^{TR}_t-\tfrac{2(\tilde r_{f,t}+s)+f}{252}\right),
$$

where $r^{TR}_t$ is the signal ETF's total return, $\tilde r_{f,t}$ the lagged T-bill rate, $f=0.95\%$ an expense ratio, and $s$ an extra financing spread per borrowed unit. The proxy's opening price applies three times the underlying's overnight move with half a day's carry. The proxy is chained so that its last value flows continuously into the first real close.

Earlier drafts fixed $s=0$. Under the model, the mean of $r^L_t-3r_t+[2\tilde r_{f,t}+f]/252$ on real-ETF days equals $-2s/252$, which identifies $s$. To check that the model carries over to a period it was not fitted on, we fit $s$ on 2010–2017 only and compare the resulting proxy with the real fund over 2018–2026:

{{table:calibration}}

The proxy is accurate out of sample. Daily correlation is 0.999, drawdowns match within 0.6 pp, and the annual return error is +0.3 pp (SPXL) and +1.0 pp (TQQQ). The error is on the optimistic side, because spreads were lower in the near-zero-rate training years. The full-sample estimates (70 and 75 bp) are used throughout, and §7.4 shows that the conclusions are insensitive to doubling them. The proxy still omits swap-counterparty, basis and tracking frictions that may have been larger in 2000–2009, so all pre-inception results remain **hypothetical**.

# 5. Benchmarks and measurement

All rules start with \$10,000 cash on the same date, use the same bars, fill at the next open, and pay the same 10 bp friction.

| Rule | Leveraged weight | Information | Purpose |
|:--|:--|:--|:--|
| **SMA rule** | five-stage state machine above | signal close $t$ | strategy under test |
| 3× hold | 100% | none | H1 control |
| 1× hold | 100% in SPY or QQQ | none | unleveraged control |
| Matched fixed weight | constant $\bar w$ = the SMA rule's realised average weight, rebalanced every 21 sessions | **ex post** | isolates exposure reduction |
| Vol target 30% | $\min(1, 0.30/\hat\sigma_t)$, $\hat\sigma_t$ = 63-day realised vol of the 3× ETF, rebalanced every 5 sessions | trailing to close $t$ | Moreira–Muir rival |
| Frontiers | the fixed-weight family $w\in[0.10,1.00]$ and the vol-target family $\sigma^*\in[10\%,100\%]$, step 0.05 | — | equal-risk comparison |

*Average weight* is the time mean of the daily market-value weight, so a day at 20% counts as one fifth of a fully invested day. We report CAGR, maximum daily drawdown, Calmar (CAGR/|MaxDD|), Sharpe on excess returns over the T-bill proxy, CDaR (mean of the worst 10% of daily drawdowns), and the Ulcer index (root-mean-square drawdown).

The **frontier gap** is the SMA rule's CAGR minus the CAGR a non-timing family attains at the *same* risk level, linearly interpolated along that family. A negative gap means the same risk could have been bought more cheaply without timing. Because each family has one parameter and the gap is evaluated at the SMA rule's own risk level, the comparison involves no selection of the best benchmark.

# 6. Results

## 6.1 Real-ETF window, 11 February 2010 – 6 August 2026

{{table:main_real}}

H1 holds: the rule's maximum drawdown is 23 pp (SPXL) and 20 pp (TQQQ) shallower than holding the fund. H2 does not. The exposure-matched mix, which has the *same* average weight (0.80), earns 5.1 pp (SPXL) and 7.2 pp (TQQQ) more per year and has a higher Calmar and Sharpe ratio. For TQQQ, the SMA rule has the lowest Calmar and Sharpe of all five rules; even unleveraged QQQ beats it on both. Shallower drawdowns are bought with return, at a worse rate than exposure reduction alone would have charged.

![Real-ETF window: growth of \$1 under the five rules.](../figures/v3/equity_real.png){width=100%}

![Daily drawdowns, real-ETF window. The SMA rule's long flat stretches below zero, for example 2022–2023, are periods spent in cash after an exit, waiting to re-enter.](../figures/v3/underwater_real.png){width=100%}

## 6.2 Equal-risk comparison with non-timing frontiers

{{table:frontier}}

![CAGR versus maximum drawdown for the fixed-weight and vol-target families, with the SMA rule (star) and 1× hold (dot).](../figures/v3/frontier.png){width=100%}

In 2010–2026 the SMA rule lies below both frontiers under every risk measure. The gap is smallest for maximum drawdown (−1.2 to −4.6 pp) and largest for Ulcer (−3.8 to −10.7 pp), because after an exit the rule sits flat at its drawdown for months before re-entering. Over 1999–2026 the result flips for SPXL: the rule beats both frontiers by 8–11 pp. For TQQQ it beats the fixed-weight frontier (+6.9 pp) but not the vol-target frontier (−2.0 pp at equal MaxDD).

## 6.3 Extended window including the synthetic 2000–2009 sleeve

{{table:main_full}}

![1999–2026; shaded years use the calibrated synthetic 3× proxy.](../figures/v3/equity_full.png){width=100%}

All of the extended window's advantage comes from 2000–2009. Over that decade the SMA–SPXL path earns +10.5% a year with a −38.0% maximum drawdown, while every non-timing rule loses money. For TQQQ, even the SMA rule suffers a −90.2% drawdown, because the 2000 crash began with QQQ so far above its average that the −3% band was reached only after the 3× sleeve had collapsed. The 30% volatility target, which held a much smaller position throughout the high-volatility years 2000–2002, ends with the same CAGR and a −66.9% drawdown.

{{table:subperiod}}

## 6.4 Every exit, one by one

The table lists each full exit and the leveraged fund's open-to-open return until the first re-entry stage. A positive value is the price paid for being out; a negative value is a loss avoided.

{{table:roundtrips}}

In the real-ETF period, SPXL made 8 round trips and TQQQ 11. **Only the 2022 exit avoided a loss** (−13.8% and −52.9%). Every other exit was followed by a rebound that the rule bought back higher, for example 2015–16, 2018–19, March 2020 and April 2025. The pre-2010 history contains the episodes that justify the rule: the 2000–2003 and 2007–2009 exits avoided losses of 75–97%. Over 26 years the rule's value therefore rests on a handful of exits: two or three per fund before 2010, plus 2022.

## 6.5 Mechanism: what follows each regime

{{table:regime}}

Regimes are assigned at close $t$ and measured on day $t+1$, so the table is predictive rather than contemporaneous. The implied 3× growth is $3\mu-4.5\sigma^2-2(\tilde r_f+s)-f$. The volatility channel is visible in both samples: next-day volatility below the −3% band is two to three times that above +4%. What differs is the mean. Over 1999–2026 the below-band regime implies 3× log growth of −25% (SPY) and −65% (QQQ) a year, which is what the rule avoids. Over 2010–2026 the same regime was followed by strong rebounds (+43% annualised next-day mean). This estimate is imprecise: with about 410 days its standard error is roughly ±27 pp. Even so, it explains why exiting cost money in the recent era. Whether the filter helps depends on whether below-trend markets keep falling (2000–02, 2008, 2022) or recover quickly (2011, 2015–16, 2018, 2020, 2025).

# 7. Robustness and inference

## 7.1 Start-date sensitivity

{{table:rolling}}

![Calmar difference against the exposure-matched mix for every monthly start date (end date fixed). Windows overlap heavily, so neighbouring points are not independent.](../figures/v3/rolling_starts.png){width=100%}

Start-date variation softens the conclusion of §6.1, and we report it as such. Starting in any month from 2010 to 2023, the SMA rule had a higher Calmar than the matched mix in 66% (SPXL) and 85% (TQQQ) of start dates. Against 1× hold, the shares are 14% and 40%. The ranking is unstable for starts close to a crash: the TQQQ line swings from +0.5 to −0.28 between 2020 and 2023 starts, depending on whether the window opens just before or just after the 2022 exit. Because every window shares the same ending, these shares describe sensitivity to the start date and are not independent replications.

## 7.2 Daily path bootstrap with the policy re-run

To measure sampling uncertainty while respecting the strategy's path dependence, we resample the joint daily vector (signal close-to-close and overnight returns, leveraged close-to-close and overnight returns, cash rate) for 2010–2026 using the stationary bootstrap (Politis and Romano 1994). The same indices are used for both pairs. Each pseudo-history is attached to the real 260-day pre-sample, so the SMA starts warm, and on every path we **re-run** the SMA rule, 3× hold, the matched mix (weight fixed at the observed 0.80) and the 30% vol target. We use 1,000 replicates with seed 20260806 and mean block lengths of 63 and 252 days. The table reports 252-day blocks; the 63-day results are in the CSV and agree in sign.

{{table:bootstrap}}

The bootstrap confirms H1 against 3× hold in most draws (the rule has the shallower drawdown in 85–88% of them) but finds no support for H2. Against the matched mix, the drawdown benefit disappears (median +3.5 pp and +0.7 pp), and the rule's Calmar ratio is lower in about three quarters of draws and its Sharpe ratio in about four fifths. Against the volatility target, the TQQQ drawdown difference is −18.8 pp, with a 95% interval that excludes zero.

One caveat applies. Block resampling with mean lengths of 63 or 252 days shortens the multi-year trends that a 200-day filter needs, so the bootstrap is biased against trend rules. The intervals therefore show what the post-2010 dependence structure supports. They do not reproduce the long 2000–2002 bear market, which lies outside this window.

![Bootstrap distribution of Calmar(SMA) − Calmar(matched mix), real-ETF window.](../figures/v3/bootstrap_calmar.png){width=100%}

## 7.3 Parameter neighbourhood (27 cells per ETF and window)

{{table:grid}}

Each grid cell is compared with a constant mix matched to *that cell's* average weight. In the real-ETF window, no cell beats its matched mix on Sharpe, and 3 (SPXL) and 6 (TQQQ) of 27 beat it on Calmar. In the extended window all 54 cells beat their matched mix on both measures. The conclusion therefore depends on whether 2000–2009 is in the sample, not on the parameter choice. This is a robustness check, not a search; the 200/+4/−3 baseline is unchanged.

## 7.4 Costs and synthetic financing

{{table:sensitivity}}

Raising friction fivefold, to 50 bp per fill, costs the rule 0.5–0.7 pp a year. Varying the synthetic spread between 0 and twice the calibrated value moves the extended-window results by at most ±0.3 pp. Neither changes any ranking.

## 7.5 From the v1 draft to v3: one change at a time

{{table:attribution}}

On identical bars, moving from the v1 conventions to v3 changes the rule's CAGR by +0.1 pp (SPXL) and +1.2 pp (TQQQ), and its maximum drawdown by at most 0.6 pp. Remaining differences from the numbers published in v1 (21.14% and 26.93%) therefore come from the data vendor and the end date, not from methodology.

# 8. Discussion

**What the rule is.** The SMA filter behaves like a long-dated put on a prolonged bear market, financed by many small whipsaw losses. When below-trend markets keep falling, as in 2000–2002, 2007–2009 and 2022, it is extremely valuable for a 3× fund, whose variance drag turns a 50% index decline into near-total loss. When they rebound within weeks, as in most of 2010–2026, each exit sells low and re-buys higher. Sixteen years of real ETF data contain one bear market of the first kind; twenty-six years of mostly synthetic data contain three. Its value cannot be established or ruled out from post-2010 data.

**Exposure versus timing.** In the period that can be traded with real funds, the rule's drawdown reduction is fully explained by exposure: a constant mix with the same average weight and a volatility target both achieve the same reduction at lower cost. The volatility target also handles the case where the SMA rule is weakest, a crash from far above trend (2000 for QQQ, February–March 2020), because realised volatility can rise before price breaks a rising 200-day average. This supports Moreira–Muir as a serious competing explanation for the benefits of filtering leveraged ETFs.

**Transport (H3).** Results agree in sign across SPXL and TQQQ, but the margin differs. TQQQ's SMA rule is weaker on every relative measure, and its extended-window drawdown (−90%) shows that the −3% band does not protect a Nasdaq 3× position from a bubble-top crash. SPY and QQQ are highly correlated, so their agreement is weak evidence of generality.

**Implications for any extension.** Combining the trend signal with volatility scaling, or replacing cash with 1× exposure in the band, is the natural next hypothesis. Because such rules would be designed after seeing 2000 and 2020, they must be specified in advance and tested on data not used here, for example non-U.S. indices and their synthetic 3× counterparts, or a forward paper-trading period.

# 9. Limitations

1. *Ex post design.* The 200/+4/−3 rule and all hypotheses were formed after the history was observed; no result here is out of sample. The matched mix uses the rule's realised average weight and is an ex post diagnostic.
2. *Synthetic decade.* Most of the evidence for the rule comes from 2000–2009, when no 3× ETF existed. The calibrated proxy tracks real funds closely after 2018, but it cannot reproduce swap availability, counterparty risk or fund closures in 2000–2009.
3. *Few independent events.* Four large avoided losses carry the extended result. Monthly-start and bootstrap analyses quantify sensitivity but cannot add independent bear markets.
4. *Bootstrap design.* Block resampling weakens long trends, as noted in §7.2. A model-based simulation of regime persistence would be the natural complement.
5. *Execution.* Fills are fractional and at the open with constant friction; taxes are ignored. Frequent full liquidations would be costly for a U.S. taxable investor and are not modelled.
6. *Data.* A single public vendor improves consistency but has not been reconciled to official fund NAV total returns. That reconciliation remains outstanding before any publication-grade claim.

# 10. Conclusion

With consistent total-return data, interest on cash, calibrated synthetic financing and matched-risk controls, the 200-day filter clearly reduces drawdowns of 3× equity ETFs relative to holding them. In 2010–2026, the only period with real funds, a constant mix or a volatility target achieved the same reduction more cheaply. The rule's advantage appears only in histories that include the 2000–2002 and 2007–2009 bear markets, which must be reconstructed synthetically. Even there, a plain volatility target matches it for the Nasdaq-100. The defensible claim is therefore conditional: the SMA rule is a bet that future bear markets will be prolonged rather than V-shaped. Investors who care mainly about drawdown should compare it with volatility targeting before relying on it.

# Reproducibility and changes in v3

`python scripts/v3_run.py` regenerates every table and figure from the four vendor files, in about five minutes, most of it the bootstrap. `python scripts/v3_tables.py` renders the tables, and `python -m pytest -q` runs 27 offline tests. The v3 engine reproduces the v2 engine to machine precision for the buy-and-hold and fixed-weight rules.

While writing those tests we found a defect in the v2 engine. After a full exit, floating-point residue left a share balance of −2.8×10⁻¹⁴, so the `shares == 0` test never fired again and the v2 code could not re-enter after its first exit. v3 sets the balance to exactly zero, and a regression test (`test_matches_v2_trend_until_first_reentry_and_fixes_v2_dust_bug`) covers the fix. No v2 performance numbers had been published, so no reported result is affected.

# References

1. Avellaneda, M., and S. Zhang (2010). Path-dependence of leveraged ETF returns. *SIAM Journal on Financial Mathematics* 1, 586–603.
2. Cheng, M., and A. Madhavan (2009). The dynamics of leveraged and inverse exchange-traded funds. *Journal of Investment Management* 7(4), 43–62.
3. Faber, M. T. (2007). A quantitative approach to tactical asset allocation. *Journal of Wealth Management* 9(4), 69–79.
4. Gayed, M. A., and C. V. Bilello (2016). Leverage for the long run: a systematic approach to managing risk and magnifying returns in stocks. Charles H. Dow Award paper, CMT Association.
5. Hansen, P. R. (2005). A test for superior predictive ability. *Journal of Business & Economic Statistics* 23(4), 365–380.
6. Hurst, B., Y. H. Ooi, and L. H. Pedersen (2017). A century of evidence on trend-following investing. *Journal of Portfolio Management* 44(1), 15–29.
7. Ledoit, O., and M. Wolf (2008). Robust performance hypothesis testing with the Sharpe ratio. *Journal of Empirical Finance* 15(5), 850–859.
8. Moreira, A., and T. Muir (2017). Volatility-managed portfolios. *Journal of Finance* 72(4), 1611–1644.
9. Moskowitz, T. J., Y. H. Ooi, and L. H. Pedersen (2012). Time series momentum. *Journal of Financial Economics* 104(2), 228–250.
10. Politis, D. N., and J. P. Romano (1994). The stationary bootstrap. *Journal of the American Statistical Association* 89(428), 1303–1313.
11. White, H. (2000). A reality check for data snooping. *Econometrica* 68(5), 1097–1126.
12. Board of Governors of the Federal Reserve System. 3-Month Treasury Bill Secondary Market Rate, Discount Basis (DTB3). FRED, Federal Reserve Bank of St. Louis.
