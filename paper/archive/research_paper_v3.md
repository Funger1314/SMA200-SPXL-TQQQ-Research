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

| Ticker | First bar | Last bar | Rows | SHA-256 (prefix) |
|:--|--:|--:|--:|--:|
| SPY | 1993-01-29 | 2026-08-06 | 8437 | fbe334492366497e… |
| SPXL | 2008-11-05 | 2026-08-06 | 4464 | 3a360f215c5e418b… |
| QQQ | 1999-03-10 | 2026-08-06 | 6895 | 63f612bf338cd636… |
| TQQQ | 2010-02-11 | 2026-08-06 | 4146 | 8097962b66c314fa… |

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

| ETF | Window | Spread s | Residual daily s.d. | Out-of-sample check |
|:--|:--|--:|--:|:--|
| SPXL | full real 2010-2026 | 70 bp | 15.5 bp | — |
| SPXL | train 2010-2017 | 59 bp | 15.4 bp | — |
| SPXL | test 2018-2026 (spread from train) | 59 bp | — | synthetic 25.68% vs real 25.43%; MDD -76.24% vs -76.86%; corr 0.9991; TE 2.45% |
| TQQQ | full real 2010-2026 | 75 bp | 18.6 bp | — |
| TQQQ | train 2010-2017 | 38 bp | 16.9 bp | — |
| TQQQ | test 2018-2026 (spread from train) | 38 bp | — | synthetic 35.96% vs real 35.01%; MDD -81.36% vs -81.66%; corr 0.9991; TE 3.17% |

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

| ETF | Rule | CAGR | Max DD | Calmar | Sharpe (excess) | CDaR 10% | Ulcer | Avg weight | Orders |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| SPXL | SMA rule | 22.22% | -53.41% | 0.416 | 0.700 | -40.01% | 0.215 | 0.80 | 53 |
| SPXL | 3x hold | 31.11% | -76.86% | 0.405 | 0.760 | -51.15% | 0.221 | 1.00 | 1 |
| SPXL | Matched fixed weight | 27.28% | -63.37% | 0.430 | 0.772 | -40.37% | 0.169 | 0.80 | 198 |
| SPXL | Vol target 30% | 20.58% | -48.61% | 0.423 | 0.702 | -34.08% | 0.170 | 0.74 | 707 |
| SPXL | 1x hold | 14.76% | -33.72% | 0.438 | 0.804 | -15.99% | 0.063 | 1.00 | 1 |
| TQQQ | SMA rule | 30.24% | -62.09% | 0.487 | 0.771 | -48.48% | 0.250 | 0.80 | 70 |
| TQQQ | 3x hold | 43.30% | -81.66% | 0.530 | 0.873 | -66.01% | 0.273 | 1.00 | 1 |
| TQQQ | Matched fixed weight | 37.45% | -72.02% | 0.520 | 0.876 | -54.94% | 0.221 | 0.80 | 198 |
| TQQQ | Vol target 30% | 26.27% | -45.05% | 0.583 | 0.835 | -34.87% | 0.161 | 0.61 | 808 |
| TQQQ | 1x hold | 19.65% | -35.12% | 0.560 | 0.899 | -22.79% | 0.087 | 1.00 | 1 |

H1 holds: the rule's maximum drawdown is 23 pp (SPXL) and 20 pp (TQQQ) shallower than holding the fund. H2 does not. The exposure-matched mix, which has the *same* average weight (0.80), earns 5.1 pp (SPXL) and 7.2 pp (TQQQ) more per year and has a higher Calmar and Sharpe ratio. For TQQQ, the SMA rule has the lowest Calmar and Sharpe of all five rules; even unleveraged QQQ beats it on both. Shallower drawdowns are bought with return, at a worse rate than exposure reduction alone would have charged.

![Real-ETF window: growth of \$1 under the five rules.](../figures/v3/equity_real.png){width=100%}

![Daily drawdowns, real-ETF window. The SMA rule's long flat stretches below zero, for example 2022–2023, are periods spent in cash after an exit, waiting to re-enter.](../figures/v3/underwater_real.png){width=100%}

## 6.2 Equal-risk comparison with non-timing frontiers

| Window | ETF | Non-timing family | Risk held equal | SMA CAGR | Frontier CAGR | SMA − frontier (pp) |
|:--|:--|:--|:--|--:|--:|--:|
| real | SPXL | fixed weight | Max DD | 22.22% | 23.64% | -1.4 |
| real | SPXL | fixed weight | CDaR 10% | 22.22% | 27.11% | -4.9 |
| real | SPXL | fixed weight | Ulcer | 22.22% | 30.82% | -8.6 |
| real | SPXL | vol target | Max DD | 22.22% | 23.85% | -1.6 |
| real | SPXL | vol target | CDaR 10% | 22.22% | 24.32% | -2.1 |
| real | SPXL | vol target | Ulcer | 22.22% | 25.97% | -3.8 |
| full | SPXL | fixed weight | Max DD | 17.26% | 6.29% | +11.0 |
| full | SPXL | fixed weight | CDaR 10% | 17.26% | 6.37% | +10.9 |
| full | SPXL | fixed weight | Ulcer | 17.26% | 7.00% | +10.3 |
| full | SPXL | vol target | Max DD | 17.26% | 8.72% | +8.5 |
| full | SPXL | vol target | CDaR 10% | 17.26% | 8.21% | +9.1 |
| full | SPXL | vol target | Ulcer | 17.26% | 8.84% | +8.4 |
| real | TQQQ | fixed weight | Max DD | 30.24% | 31.46% | -1.2 |
| real | TQQQ | fixed weight | CDaR 10% | 30.24% | 33.52% | -3.3 |
| real | TQQQ | fixed weight | Ulcer | 30.24% | 40.99% | -10.7 |
| real | TQQQ | vol target | Max DD | 30.24% | 34.85% | -4.6 |
| real | TQQQ | vol target | CDaR 10% | 30.24% | 34.63% | -4.4 |
| real | TQQQ | vol target | Ulcer | 30.24% | 37.59% | -7.4 |
| full | TQQQ | fixed weight | Max DD | 14.28% | 7.40% | +6.9 |
| full | TQQQ | fixed weight | CDaR 10% | 14.28% | 7.43% | +6.8 |
| full | TQQQ | fixed weight | Ulcer | 14.28% | 7.43% | +6.8 |
| full | TQQQ | vol target | Max DD | 14.28% | 16.24% | -2.0 |
| full | TQQQ | vol target | CDaR 10% | 14.28% | 15.59% | -1.3 |
| full | TQQQ | vol target | Ulcer | 14.28% | 14.38% | -0.1 |

![CAGR versus maximum drawdown for the fixed-weight and vol-target families, with the SMA rule (star) and 1× hold (dot).](../figures/v3/frontier.png){width=100%}

In 2010–2026 the SMA rule lies below both frontiers under every risk measure. The gap is smallest for maximum drawdown (−1.2 to −4.6 pp) and largest for Ulcer (−3.8 to −10.7 pp), because after an exit the rule sits flat at its drawdown for months before re-entering. Over 1999–2026 the result flips for SPXL: the rule beats both frontiers by 8–11 pp. For TQQQ it beats the fixed-weight frontier (+6.9 pp) but not the vol-target frontier (−2.0 pp at equal MaxDD).

## 6.3 Extended window including the synthetic 2000–2009 sleeve

| ETF | Rule | CAGR | Max DD | Calmar | Sharpe (excess) | CDaR 10% | Ulcer | Avg weight | Orders |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| SPXL | SMA rule | 17.26% | -53.41% | 0.323 | 0.577 | -37.97% | 0.215 | 0.71 | 71 |
| SPXL | 3x hold | 7.07% | -98.25% | 0.072 | 0.374 | -93.72% | 0.641 | 1.00 | 1 |
| SPXL | Matched fixed weight | 8.54% | -91.58% | 0.093 | 0.356 | -79.84% | 0.464 | 0.71 | 319 |
| SPXL | Vol target 30% | 10.01% | -68.91% | 0.145 | 0.399 | -58.22% | 0.297 | 0.70 | 1159 |
| SPXL | 1x hold | 8.40% | -55.19% | 0.152 | 0.412 | -37.57% | 0.161 | 1.00 | 1 |
| TQQQ | SMA rule | 14.28% | -90.23% | 0.158 | 0.480 | -87.97% | 0.594 | 0.69 | 118 |
| TQQQ | 3x hold | -2.28% | -99.98% | -0.023 | 0.347 | -99.93% | 0.955 | 1.00 | 1 |
| TQQQ | Matched fixed weight | 5.63% | -99.12% | 0.057 | 0.332 | -98.16% | 0.788 | 0.69 | 319 |
| TQQQ | Vol target 30% | 14.05% | -66.90% | 0.210 | 0.511 | -56.59% | 0.298 | 0.54 | 1316 |
| TQQQ | 1x hold | 8.84% | -82.96% | 0.107 | 0.376 | -74.81% | 0.440 | 1.00 | 1 |

![1999–2026; shaded years use the calibrated synthetic 3× proxy.](../figures/v3/equity_full.png){width=100%}

All of the extended window's advantage comes from 2000–2009. Over that decade the SMA–SPXL path earns +10.5% a year with a −38.0% maximum drawdown, while every non-timing rule loses money. For TQQQ, even the SMA rule suffers a −90.2% drawdown, because the 2000 crash began with QQQ so far above its average that the −3% band was reached only after the 3× sleeve had collapsed. The 30% volatility target, which held a much smaller position throughout the high-volatility years 2000–2002, ends with the same CAGR and a −66.9% drawdown.

| Subperiod | ETF | Rule | CAGR | Max DD | Calmar |
|:--|:--|:--|--:|--:|--:|
| 2010-2017 | SPXL | SMA rule | 25.95% | -41.31% | 0.628 |
| 2010-2017 | SPXL | 3x hold | 37.58% | -53.81% | 0.698 |
| 2010-2017 | SPXL | Matched fixed weight | 31.10% | -45.23% | 0.687 |
| 2010-2017 | SPXL | Vol target 30% | 26.25% | -34.82% | 0.754 |
| 2018-2026 | SPXL | SMA rule | 18.12% | -53.41% | 0.339 |
| 2018-2026 | SPXL | 3x hold | 25.29% | -76.86% | 0.329 |
| 2018-2026 | SPXL | Matched fixed weight | 23.39% | -63.24% | 0.370 |
| 2018-2026 | SPXL | Vol target 30% | 15.33% | -51.07% | 0.300 |
| 2000-2009 (synthetic) | SPXL | SMA rule | 10.45% | -37.96% | 0.275 |
| 2000-2009 (synthetic) | SPXL | 3x hold | -22.17% | -98.25% | -0.226 |
| 2000-2009 (synthetic) | SPXL | Matched fixed weight | -8.43% | -83.52% | -0.101 |
| 2000-2009 (synthetic) | SPXL | Vol target 30% | -4.32% | -68.91% | -0.063 |
| 2010-2017 | TQQQ | SMA rule | 25.87% | -53.84% | 0.480 |
| 2010-2017 | TQQQ | 3x hold | 52.90% | -44.54% | 1.188 |
| 2010-2017 | TQQQ | Matched fixed weight | 42.41% | -36.71% | 1.155 |
| 2010-2017 | TQQQ | Vol target 30% | 33.01% | -32.19% | 1.026 |
| 2018-2026 | TQQQ | SMA rule | 32.86% | -62.09% | 0.529 |
| 2018-2026 | TQQQ | 3x hold | 34.75% | -81.66% | 0.426 |
| 2018-2026 | TQQQ | Matched fixed weight | 32.66% | -71.99% | 0.454 |
| 2018-2026 | TQQQ | Vol target 30% | 19.18% | -44.26% | 0.433 |
| 2000-2009 (synthetic) | TQQQ | SMA rule | -6.58% | -90.23% | -0.073 |
| 2000-2009 (synthetic) | TQQQ | 3x hold | -46.79% | -99.98% | -0.468 |
| 2000-2009 (synthetic) | TQQQ | Matched fixed weight | -17.18% | -95.37% | -0.180 |
| 2000-2009 (synthetic) | TQQQ | Vol target 30% | -1.96% | -66.90% | -0.029 |

## 6.4 Every exit, one by one

The table lists each full exit and the leveraged fund's open-to-open return until the first re-entry stage. A positive value is the price paid for being out; a negative value is a loss avoided.

| ETF | Exit fill | First re-entry fill | Days out | Leveraged return while out | Synthetic |
|:--|:--|:--|--:|--:|:--|
| SPXL | 2000-10-10 | 2003-04-23 | 633 | -83.71% | yes |
| SPXL | 2004-08-09 | 2004-11-05 | 63 | 29.42% | yes |
| SPXL | 2007-11-23 | 2009-06-10 | 388 | -84.29% | yes |
| SPXL | 2010-06-07 | 2010-10-06 | 85 | 24.99% | no |
| SPXL | 2011-08-05 | 2012-01-19 | 114 | 10.96% | no |
| SPXL | 2015-08-24 | 2016-04-14 | 161 | 32.88% | no |
| SPXL | 2018-10-25 | 2019-03-22 | 100 | 14.12% | no |
| SPXL | 2020-03-10 | 2020-06-04 | 60 | 2.24% | no |
| SPXL | 2022-02-24 | 2023-02-02 | 236 | -13.78% | no |
| SPXL | 2025-03-14 | 2025-06-09 | 59 | 15.16% | no |
| SPXL | 2026-03-30 | 2026-04-15 | 11 | 27.04% | no |
| TQQQ | 2000-05-24 | 2000-06-02 | 6 | 77.88% | yes |
| TQQQ | 2000-07-31 | 2000-08-18 | 14 | 27.83% | yes |
| TQQQ | 2000-09-18 | 2001-12-06 | 304 | -97.42% | yes |
| TQQQ | 2001-12-21 | 2003-03-18 | 309 | -83.55% | yes |
| TQQQ | 2004-07-19 | 2004-11-04 | 77 | 17.08% | yes |
| TQQQ | 2005-04-18 | 2005-06-02 | 32 | 32.37% | yes |
| TQQQ | 2006-05-18 | 2006-10-11 | 101 | 6.14% | yes |
| TQQQ | 2008-01-09 | 2008-05-19 | 90 | 9.76% | yes |
| TQQQ | 2008-06-27 | 2009-05-27 | 229 | -74.59% | yes |
| TQQQ | 2010-06-30 | 2010-09-16 | 54 | 30.59% | no |
| TQQQ | 2011-08-05 | 2011-10-25 | 56 | 11.01% | no |
| TQQQ | 2011-11-22 | 2012-01-13 | 35 | 21.90% | no |
| TQQQ | 2012-11-14 | 2013-02-11 | 59 | 24.26% | no |
| TQQQ | 2015-08-24 | 2015-10-26 | 44 | 56.87% | no |
| TQQQ | 2016-01-08 | 2016-07-15 | 130 | 14.21% | no |
| TQQQ | 2018-10-25 | 2019-03-20 | 98 | 10.48% | no |
| TQQQ | 2020-03-13 | 2020-04-15 | 22 | 16.60% | no |
| TQQQ | 2022-01-24 | 2023-02-03 | 259 | -52.94% | no |
| TQQQ | 2025-03-11 | 2025-05-14 | 45 | 17.53% | no |
| TQQQ | 2026-03-27 | 2026-04-15 | 12 | 32.08% | no |

In the real-ETF period, SPXL made 8 round trips and TQQQ 11. **Only the 2022 exit avoided a loss** (−13.8% and −52.9%). Every other exit was followed by a rebound that the rule bought back higher, for example 2015–16, 2018–19, March 2020 and April 2025. The pre-2010 history contains the episodes that justify the rule: the 2000–2003 and 2007–2009 exits avoided losses of 75–97%. Over 26 years the rule's value therefore rests on a handful of exits: two or three per fund before 2010, plus 2022.

## 6.5 Mechanism: what follows each regime

| Window | Signal | Regime at close t | Days | Next-day mean (ann.) | Next-day vol (ann.) | Implied 3x log growth |
|:--|:--|:--|--:|--:|--:|--:|
| real | SPY | Above +4% | 2840 | 10.94% | 12.02% | 20.88% |
| real | SPY | Below -3% | 403 | 43.07% | 34.81% | 69.66% |
| real | SPY | Middle | 902 | 16.03% | 18.62% | 27.32% |
| full | SPY | Above +4% | 3843 | 7.93% | 12.37% | 10.82% |
| full | SPY | Below -3% | 1216 | 10.75% | 33.68% | -25.08% |
| full | SPY | Middle | 1635 | 13.97% | 17.88% | 20.72% |
| real | QQQ | Above +4% | 3038 | 13.03% | 16.47% | 21.34% |
| real | QQQ | Below -3% | 421 | 43.63% | 37.69% | 60.76% |
| real | QQQ | Middle | 686 | 36.43% | 22.64% | 81.72% |
| full | QQQ | Above +4% | 4122 | 9.82% | 19.27% | 6.50% |
| full | QQQ | Below -3% | 1362 | 9.22% | 43.62% | -65.25% |
| full | QQQ | Middle | 1210 | 22.90% | 23.79% | 37.31% |

Regimes are assigned at close $t$ and measured on day $t+1$, so the table is predictive rather than contemporaneous. The implied 3× growth is $3\mu-4.5\sigma^2-2(\tilde r_f+s)-f$. The volatility channel is visible in both samples: next-day volatility below the −3% band is two to three times that above +4%. What differs is the mean. Over 1999–2026 the below-band regime implies 3× log growth of −25% (SPY) and −65% (QQQ) a year, which is what the rule avoids. Over 2010–2026 the same regime was followed by strong rebounds (+43% annualised next-day mean). This estimate is imprecise: with about 410 days its standard error is roughly ±27 pp. Even so, it explains why exiting cost money in the recent era. Whether the filter helps depends on whether below-trend markets keep falling (2000–02, 2008, 2022) or recover quickly (2011, 2015–16, 2018, 2020, 2025).

# 7. Robustness and inference

## 7.1 Start-date sensitivity

| Start months | ETF | Versus | Starts | Median ΔCAGR (pp) | Median ΔMax DD (pp) | Median ΔCalmar | SMA higher Calmar |
|:--|:--|:--|--:|--:|--:|--:|--:|
| 1999-12…2023-08 | SPXL | 3x hold | 285 | -6.0 | +23.4 | +0.056 | 92% |
| 1999-12…2023-08 | SPXL | Matched fixed weight | 285 | -2.8 | +12.6 | +0.041 | 80% |
| 1999-12…2023-08 | SPXL | Vol target 30% | 285 | +4.3 | +2.3 | +0.100 | 87% |
| 1999-12…2023-08 | SPXL | 1x hold | 285 | +8.9 | -19.7 | -0.005 | 47% |
| 1999-12…2023-08 | TQQQ | 3x hold | 285 | -2.0 | +19.6 | +0.118 | 84% |
| 1999-12…2023-08 | TQQQ | Matched fixed weight | 285 | +0.9 | +11.1 | +0.104 | 87% |
| 1999-12…2023-08 | TQQQ | Vol target 30% | 285 | +6.9 | -15.9 | +0.041 | 69% |
| 1999-12…2023-08 | TQQQ | 1x hold | 285 | +11.8 | -16.2 | +0.036 | 60% |
| 2010-02…2023-08 | SPXL | 3x hold | 163 | -7.2 | +23.4 | +0.034 | 87% |
| 2010-02…2023-08 | SPXL | Matched fixed weight | 163 | -3.7 | +11.0 | +0.016 | 66% |
| 2010-02…2023-08 | SPXL | Vol target 30% | 163 | +3.3 | -2.3 | +0.046 | 78% |
| 2010-02…2023-08 | SPXL | 1x hold | 163 | +7.5 | -19.7 | -0.047 | 14% |
| 2010-02…2023-08 | TQQQ | 3x hold | 163 | -6.6 | +19.6 | +0.059 | 81% |
| 2010-02…2023-08 | TQQQ | Matched fixed weight | 163 | -1.6 | +10.3 | +0.061 | 85% |
| 2010-02…2023-08 | TQQQ | Vol target 30% | 163 | +9.2 | -16.8 | +0.056 | 62% |
| 2010-02…2023-08 | TQQQ | 1x hold | 163 | +14.1 | -27.0 | -0.016 | 40% |

![Calmar difference against the exposure-matched mix for every monthly start date (end date fixed). Windows overlap heavily, so neighbouring points are not independent.](../figures/v3/rolling_starts.png){width=100%}

Start-date variation softens the conclusion of §6.1, and we report it as such. Starting in any month from 2010 to 2023, the SMA rule had a higher Calmar than the matched mix in 66% (SPXL) and 85% (TQQQ) of start dates. Against 1× hold, the shares are 14% and 40%. The ranking is unstable for starts close to a crash: the TQQQ line swings from +0.5 to −0.28 between 2020 and 2023 starts, depending on whether the window opens just before or just after the 2022 exit. Because every window shares the same ending, these shares describe sensitivity to the start date and are not independent replications.

## 7.2 Daily path bootstrap with the policy re-run

To measure sampling uncertainty while respecting the strategy's path dependence, we resample the joint daily vector (signal close-to-close and overnight returns, leveraged close-to-close and overnight returns, cash rate) for 2010–2026 using the stationary bootstrap (Politis and Romano 1994). The same indices are used for both pairs. Each pseudo-history is attached to the real 260-day pre-sample, so the SMA starts warm, and on every path we **re-run** the SMA rule, 3× hold, the matched mix (weight fixed at the observed 0.80) and the 30% vol target. We use 1,000 replicates with seed 20260806 and mean block lengths of 63 and 252 days. The table reports 252-day blocks; the 63-day results are in the CSV and agree in sign.

| ETF | Versus | Metric (SMA − benchmark) | Median | 95% interval | Share > 0 |
|:--|:--|:--|--:|--:|--:|
| SPXL | 3x hold | CAGR (pp) | -10.5 | [-21.8, +0.9] | 4% |
| SPXL | 3x hold | Max DD (pp) | +15.1 | [-10.8, +30.1] | 88% |
| SPXL | 3x hold | Calmar | -0.068 | [-0.411, +0.198] | 28% |
| SPXL | 3x hold | Sharpe | -0.115 | [-0.362, +0.128] | 17% |
| SPXL | Matched fixed | CAGR (pp) | -6.5 | [-16.3, +4.6] | 12% |
| SPXL | Matched fixed | Max DD (pp) | +3.5 | [-21.3, +19.0] | 63% |
| SPXL | Matched fixed | Calmar | -0.088 | [-0.401, +0.196] | 26% |
| SPXL | Matched fixed | Sharpe | -0.119 | [-0.362, +0.126] | 17% |
| SPXL | Vol target 30% | CAGR (pp) | -0.3 | [-9.5, +10.1] | 48% |
| SPXL | Vol target 30% | Max DD (pp) | -7.8 | [-28.1, +8.5] | 18% |
| SPXL | Vol target 30% | Calmar | -0.059 | [-0.363, +0.210] | 30% |
| SPXL | Vol target 30% | Sharpe | -0.049 | [-0.269, +0.152] | 32% |
| TQQQ | 3x hold | CAGR (pp) | -14.8 | [-29.7, +6.3] | 9% |
| TQQQ | 3x hold | Max DD (pp) | +10.8 | [-15.0, +32.1] | 85% |
| TQQQ | 3x hold | Calmar | -0.124 | [-0.519, +0.286] | 27% |
| TQQQ | 3x hold | Sharpe | -0.142 | [-0.392, +0.154] | 18% |
| TQQQ | Matched fixed | CAGR (pp) | -8.3 | [-22.4, +9.1] | 18% |
| TQQQ | Matched fixed | Max DD (pp) | +0.7 | [-24.8, +23.0] | 52% |
| TQQQ | Matched fixed | Calmar | -0.126 | [-0.511, +0.301] | 28% |
| TQQQ | Matched fixed | Sharpe | -0.141 | [-0.390, +0.161] | 18% |
| TQQQ | Vol target 30% | CAGR (pp) | +3.3 | [-10.9, +20.2] | 66% |
| TQQQ | Vol target 30% | Max DD (pp) | -18.8 | [-39.3, -3.0] | 1% |
| TQQQ | Vol target 30% | Calmar | -0.112 | [-0.457, +0.220] | 24% |
| TQQQ | Vol target 30% | Sharpe | -0.076 | [-0.310, +0.147] | 26% |

The bootstrap confirms H1 against 3× hold in most draws (the rule has the shallower drawdown in 85–88% of them) but finds no support for H2. Against the matched mix, the drawdown benefit disappears (median +3.5 pp and +0.7 pp), and the rule's Calmar ratio is lower in about three quarters of draws and its Sharpe ratio in about four fifths. Against the volatility target, the TQQQ drawdown difference is −18.8 pp, with a 95% interval that excludes zero.

One caveat applies. Block resampling with mean lengths of 63 or 252 days shortens the multi-year trends that a 200-day filter needs, so the bootstrap is biased against trend rules. The intervals therefore show what the post-2010 dependence structure supports. They do not reproduce the long 2000–2002 bear market, which lies outside this window.

![Bootstrap distribution of Calmar(SMA) − Calmar(matched mix), real-ETF window.](../figures/v3/bootstrap_calmar.png){width=100%}

## 7.3 Parameter neighbourhood (27 cells per ETF and window)

| Window | ETF | Cells | CAGR min / median / max | Beat matched-weight Calmar | Beat matched-weight Sharpe |
|:--|:--|--:|--:|--:|--:|
| full | SPXL | 27 | 9.18% / 15.62% / 18.05% | 27 / 27 | 27 / 27 |
| full | TQQQ | 27 | 8.36% / 12.71% / 16.11% | 27 / 27 | 27 / 27 |
| real | SPXL | 27 | 11.66% / 20.22% / 23.29% | 3 / 27 | 0 / 27 |
| real | TQQQ | 27 | 22.80% / 29.29% / 33.49% | 6 / 27 | 0 / 27 |

Each grid cell is compared with a constant mix matched to *that cell's* average weight. In the real-ETF window, no cell beats its matched mix on Sharpe, and 3 (SPXL) and 6 (TQQQ) of 27 beat it on Calmar. In the extended window all 54 cells beat their matched mix on both measures. The conclusion therefore depends on whether 2000–2009 is in the sample, not on the parameter choice. This is a robustness check, not a search; the 200/+4/−3 baseline is unchanged.

## 7.4 Costs and synthetic financing

| Test | ETF | Setting | Rule | CAGR | Max DD |
|:--|:--|:--|:--|--:|--:|
| one-way cost | SPXL | 5 bp | SMA rule | 22.28% | -53.37% |
| one-way cost | SPXL | 5 bp | 3x hold | 31.12% | -76.86% |
| one-way cost | SPXL | 10 bp | SMA rule | 22.22% | -53.41% |
| one-way cost | SPXL | 10 bp | 3x hold | 31.11% | -76.86% |
| one-way cost | SPXL | 20 bp | SMA rule | 22.09% | -53.51% |
| one-way cost | SPXL | 20 bp | 3x hold | 31.10% | -76.86% |
| one-way cost | SPXL | 50 bp | SMA rule | 21.71% | -53.78% |
| one-way cost | SPXL | 50 bp | 3x hold | 31.08% | -76.86% |
| synthetic financing spread | SPXL | s = 0 | SMA rule | 17.57% | -53.41% |
| synthetic financing spread | SPXL | s = 0 | 3x hold | 7.57% | -98.02% |
| synthetic financing spread | SPXL | s = 70 bp (calibrated) | SMA rule | 17.26% | -53.41% |
| synthetic financing spread | SPXL | s = 70 bp (calibrated) | 3x hold | 7.07% | -98.25% |
| synthetic financing spread | SPXL | s = 140 bp | SMA rule | 16.94% | -53.41% |
| synthetic financing spread | SPXL | s = 140 bp | 3x hold | 6.57% | -98.44% |
| one-way cost | TQQQ | 5 bp | SMA rule | 30.33% | -62.09% |
| one-way cost | TQQQ | 5 bp | 3x hold | 43.31% | -81.66% |
| one-way cost | TQQQ | 10 bp | SMA rule | 30.24% | -62.09% |
| one-way cost | TQQQ | 10 bp | 3x hold | 43.30% | -81.66% |
| one-way cost | TQQQ | 20 bp | SMA rule | 30.06% | -62.09% |
| one-way cost | TQQQ | 20 bp | 3x hold | 43.29% | -81.66% |
| one-way cost | TQQQ | 50 bp | SMA rule | 29.53% | -62.09% |
| one-way cost | TQQQ | 50 bp | 3x hold | 43.27% | -81.66% |
| synthetic financing spread | TQQQ | s = 0 | SMA rule | 14.62% | -90.16% |
| synthetic financing spread | TQQQ | s = 0 | 3x hold | -1.72% | -99.98% |
| synthetic financing spread | TQQQ | s = 75 bp (calibrated) | SMA rule | 14.28% | -90.23% |
| synthetic financing spread | TQQQ | s = 75 bp (calibrated) | 3x hold | -2.28% | -99.98% |
| synthetic financing spread | TQQQ | s = 150 bp | SMA rule | 13.94% | -90.29% |
| synthetic financing spread | TQQQ | s = 150 bp | 3x hold | -2.84% | -99.98% |

Raising friction fivefold, to 50 bp per fill, costs the rule 0.5–0.7 pp a year. Varying the synthetic spread between 0 and twice the calibrated value moves the extended-window results by at most ±0.3 pp. Neither changes any ranking.

## 7.5 From the v1 draft to v3: one change at a time

| ETF | Step | SMA CAGR | SMA Max DD | SMA orders | 3x hold CAGR | 3x hold Max DD |
|:--|:--|--:|--:|--:|--:|--:|
| SPXL | A. v1 conventions: price-only signal & ETF, 0% cash | 22.13% | -52.88% | 53 | 30.12% | -76.86% |
| SPXL | B. + total-return (dividend-adjusted) leveraged ETF | 22.93% | -52.85% | 53 | 31.11% | -76.86% |
| SPXL | C. + total-return signal ETF for SMA | 21.86% | -53.46% | 53 | 31.11% | -76.86% |
| SPXL | D. + prior-month T-bill on idle cash (= v3 baseline) | 22.22% | -53.41% | 53 | 31.11% | -76.86% |
| TQQQ | A. v1 conventions: price-only signal & ETF, 0% cash | 29.09% | -62.09% | 69 | 42.86% | -81.75% |
| TQQQ | B. + total-return (dividend-adjusted) leveraged ETF | 29.41% | -62.09% | 69 | 43.30% | -81.66% |
| TQQQ | C. + total-return signal ETF for SMA | 29.88% | -62.09% | 70 | 43.30% | -81.66% |
| TQQQ | D. + prior-month T-bill on idle cash (= v3 baseline) | 30.24% | -62.09% | 70 | 43.30% | -81.66% |

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
