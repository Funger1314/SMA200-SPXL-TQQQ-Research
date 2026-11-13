---
title: "A 200-Day Trend Filter for 3× Leveraged U.S. Equity ETFs"
subtitle: "A Two-Asset Replication with Trading Frictions, Synthetic Pre-Inception Histories, and Retrospective Robustness Tests (1999–2026)"
author: "Independent Quantitative Research Note"
date: "12 November 2026"
lang: en-US
---

**Research status:** Exploratory, reproducible computational study. This document is *not* a peer-reviewed paper, a prospective trial, an investment recommendation, or proof of a persistent trading edge.

# Abstract

This study evaluates a fixed 200-trading-day simple moving-average (SMA) allocation rule on two U.S. equity exposures: signals from SPY are executed in SPXL, and signals from QQQ are executed in TQQQ. At each daily close, the strategy increases its intended leveraged ETF allocation by 20 percentage points per eligible session whenever the unleveraged signal ETF closes at least 4% above its SMA200, up to 100% invested; it liquidates after a close at least 3% below SMA200. All orders fill at the **following session's open**, with an assumed 10-basis-point cost on each filled notional. Uninvested capital earns zero interest. We compare a common *real-ETF* window (11 February 2010–12 November 2026) with an extended, partly hypothetical history (22 December 1999–12 November 2026). The latter uses a daily-reset 3× proxy before each leveraged ETF existed, and is labeled **synthetic** throughout.

In the common real-ETF window, annualized compound returns are 21.14% for SPXL and 26.93% for TQQQ, with maximum daily equity drawdowns of −52.88% and −62.09%, respectively. Their corresponding buy-and-hold controls have higher CAGRs of 28.94% and 40.91% but worse drawdowns of −76.86% and −81.66%. In the extended partly synthetic window, the rule produces 15.38% and 13.70% CAGR for SPXL and TQQQ, but the TQQQ proxy still suffers a −90.49% drawdown. Across 27 nearby parameter triples per asset in the common period, every CAGR is positive; however, this does **not** establish statistical significance, because the parameters were examined retrospectively and the post-2010 market regime was unusually favorable to leveraged U.S. equities. A paired 12-month block bootstrap does not exclude zero excess log return over the respective buy-and-hold benchmark. These findings support a conditional drawdown-management interpretation, **not** a claim of superior risk-adjusted alpha or cross-market universality.

**Keywords:** leveraged ETFs; trend following; SMA200; TQQQ; SPXL; path dependence; transaction costs; look-ahead bias; data snooping; replication.

# 1. Research question and contribution

The research question is deliberately narrow: **does a pre-specified *mechanical implementation* of a 200-day trend regime rule improve the risk–return profile of 3× leveraged long-only U.S. equity ETF exposure relative to buy-and-hold, and is its observed behavior similar across a broad-market and a Nasdaq-100 exposure?** The word *mechanical* is important: the code specifies every observable signal, intended order, fill timing, and cost assumption. No discretionary exceptions are allowed in the baseline simulation.

We make five contributions. First, we express the strategy as an executable state machine rather than as a loosely described crossing indicator. Second, we test SPXL and TQQQ using the **same** rule and the same 2010–2026 calendar. Third, we separate true ETF prices from hypothetical pre-inception payoffs instead of combining them without disclosure. Fourth, we publish month-end equity snapshots, transaction-cost assumptions, source identifiers, source-verification hashes, downloadable code, parameter grids, and self-tests. Fifth, we explicitly distinguish weaker *retrospective stability* checks from a genuine ex ante experiment.

The economic motivation comes from time-series momentum and the possibility of avoiding lengthy equity bear markets. Trend-following research provides precedent for considering persistent returns, but that literature does **not** imply that a particular 200/4/−3 rule is optimal, that a leveraged ETF will track a threefold long-run index return, or that past parameter performance persists [1–4].

# 2. Investable instruments and source construction

SPY approximates the S&P 500 equity exposure, and QQQ approximates the Nasdaq-100 exposure. SPXL targets **3× the S&P 500's DAILY performance** and began trading on 5 November 2008. TQQQ targets **3× the Nasdaq-100's DAILY performance** and was launched on 9 February 2010; the price sample begins 11 February 2010. Daily resets produce path dependence, financing and trading effects, and leverage decay when volatility and returns interact. It is incorrect to triple an underlying ETF's *cumulative* return [5, 6].

Daily open/close history originates from four upstream public GitHub archives (listed with Git-blob SHA-1 checksums in `data/sources.json`) and was augmented for the original November 2026 audit with historical daily bars retrieved from IBKR. The public repository **does not redistribute** third-party raw quote feeds. Instead it ships source links, validation hashes, reproducible downloads, derived monthly equity curves, and an optional public Yahoo-finance tail loader. Data-provider revisions can prevent a future public refresh from matching the original audited IBKR tail to the cent. Our private audit snapshot was evaluated through **12 November 2026**.

**Important data-convention limitation.** The archived SPY/SPXL OHLC inputs are source-provided price-series closes; the archived QQQ/TQQQ files are yfinance auto-adjusted OHLC. Cash distributions are therefore **not handled on a perfectly uniform total-return basis** across the two markets. Within-ETF strategy-versus-buy-and-hold comparisons use the same price stream and remain more interpretable than precision-level cross-ETF performance differences. The ideal publication-quality next stage is a single licensed, split- and dividend-adjusted vendor for all four instruments, with an independent reconciliation of corporate actions. No claim of exact cross-asset alpha is made here.

The early source calendar begins with QQQ on 10 March 1999. To avoid giving the SPY signal an artificial nine-month head start merely because SPY has older history, the common **extended** evaluation starts on 22 December 1999, after a complete QQQ SMA200 warm-up. The common **real-ETF** evaluation begins on 11 February 2010. Results are reinitialized with $10,000 cash at each evaluation start. Monthly charts depict sampled daily simulations; *maximum drawdown figures always use the underlying daily NAV path*, not sampled month-end extrema.

# 3. Fully specified trading protocol

Let \(P_t\) denote the unleveraged signal ETF's daily closing price. Its look-back moving average is

\[
M_t = \frac{1}{200}\sum_{j=0}^{199}P_{t-j}.
\]

An **entry-eligible close** is \(P_t \ge 1.04M_t\). A **full-exit close** is \(P_t < 0.97M_t\). These are *level conditions*, not a requirement that today's ratio newly cross a boundary from yesterday. The distinction matters in choppy markets and when a fresh evaluation begins while the underlying is already above its entry zone.

The trading state is \(k_t\in\{0,1,2,3,4,5\}\), recording the latest intended allocation stage. At close \(t\):

1. If invested and \(P_t <0.97M_t\), schedule sale of **all** leveraged-ETF shares for the next open; reset the intended stage to zero.
2. Otherwise, if flat and \(P_t \ge1.04M_t\), schedule a stage-one purchase targeting **20% of total portfolio value** at the next open.
3. Otherwise, if at a partial stage below five and the entry-eligible close persists, schedule the next stage targeting 40%, 60%, 80%, then 100% of portfolio equity.
4. If the underlying lies between the two thresholds, do nothing; keep the existing shares and cash. After the portfolio reaches stage five, no daily rebalancing is performed unless a full-exit condition is observed.

At the *next* market open, the buyer acquires only enough new shares to attain the target weight; a purchase never forcibly sells an already appreciated position to rebalance downward. Because costs are debited from cash, the residual cash at the nominal 100% stage may be slightly positive. Open-gap returns between signal and fill accrue only to positions actually held. Execution is modeled as fractional-share fills, without intraday liquidity constraints or partial-fill mechanics. No intraday limit or hard stop is assumed. Consequently, a −3% **SMA buffer is not a maximum-loss cap**; the portfolio may incur a large overnight gap before the queued sale executes.

# 4. Costs, leverage, and synthetic pre-inception sleeve

The baseline charges 0.10% of each buy or sell notional: 0.05% nominal commission plus 0.05% modeled slippage. These are **scenario assumptions**, not a representation of any user's actual IBKR fee schedule. On a $2,000 tranche purchase, modeled friction is $2; on a $10,000 liquidation, $10. The strategies use no external margin loan beyond the leverage embedded in the product. Cash earns **0%**, tax and borrowing constraints are omitted, and residual cash is not invested in Treasury bills. Real SPXL/TQQQ traded prices already embed their internal daily resetting, fund expenses, and financing effects; these are **not** charged a second time.

Before each ETF's inception, its daily *closing* total-return proxy is built from the corresponding unleveraged ETF daily return \(r_t\):

\[
L_t=L_{t-1}\left(1+3r_t-\frac{0.0095}{252}\right).
\]

The synthetic opening price uses a corresponding 3× underlying overnight price move from the prior underlying close. The entire pre-inception series is chained backward from the first observed leveraged ETF price, avoiding an arbitrary late-period scale break. The model subtracts an illustrative 0.95% annual fee drag but **does not** exactly reconstruct historical swap spreads, funding rates, index-futures basis, dividends, dynamic hedge costs, tracking error, or actual pre-inception ETF availability. A hypothetical instrument can also be impossible to trade at the reconstructed open; this is a *stress-test proxy*, not a live trading record. Simulated profits or losses before an ETF existed are not attainable histories.

Portfolio \(V_t\) is valued at the daily close, and daily returns are \(R_t=V_t/V_{t-1}-1\). We report \(\mathrm{CAGR}=(V_T/V_0)^{252/(N-1)}-1\), maximum peak-to-trough drawdown \(\min_t(V_t/\max_{s\le t}V_s-1)\), and the zero-risk-free-rate Sharpe statistic \(\sqrt{252}\,\overline R/s(R)\). Calendar-time CAGR would be slightly different; 252 trading days is used consistently with the original audit. All results are *nominal*, before tax.

# 5. Primary empirical results: common real-ETF period

**Table 1. February 2010–November 2026; $10,000 starting capital; 10 bp per filled side; zero return on cash.**

| Leveraged ETF | Rule | Final wealth ($) | CAGR | Max daily drawdown | Sharpe (rf=0) |
|:--|:--|--:|--:|--:|--:|
| SPXL | 200-SMA rule | 247,070 | 21.14% | −52.88% | 0.720 |
| SPXL | Buy & hold | 701,252 | 28.94% | −76.86% | 0.754 |
| TQQQ | 200-SMA rule | 539,596 | 26.93% | −62.09% | 0.746 |
| TQQQ | Buy & hold | 3,093,421 | 40.91% | −81.66% | 0.864 |

The rule reduces observed worst drawdown by **23.98 percentage points for SPXL** and **19.57 points for TQQQ** compared with buying and holding that same instrument. This is a meaningful *descriptive* reduction. It is **not** a reduction to tolerable or capital-protection levels: an investor could still lose over half their portfolio peak value. Crucially, both strategies have **lower** historical CAGR and **lower** zero-rate Sharpe than their own buy-and-hold controls in this period. Therefore the study does **not** demonstrate positive benchmark-relative alpha or superiority under all utility preferences. An investor willing to bear an 80% drawdown could historically have earned more by staying fully invested.

![Figure 1. Monthly sampled, log-scale wealth curves for the two rules and their buy-and-hold controls. The 2010–2026 common window uses actual leveraged-ETF price observations.](../figures/equity_2010.png){width=94%}

![Figure 2. Month-end sampled drawdown paths for the two rules, 2010–2026. Daily maximum drawdowns in Table 1 may be worse than the sampled lines.](../figures/underwater_monthly_2010.png){width=94%}

Part of the reduction in drawdown is explained by **lower market exposure**, not solely superior timing: the SPXL rule was invested on about 79.72% of trading days; the TQQQ rule on 80.55%. The public audit includes a 0% cash benchmark, making idle-capital opportunity costs visible. A matched-volatility benchmark, risk-parity sizing, or interest-bearing cash would be needed to distinguish timing skill from simply lowering exposure. The latter tests are proposed rather than presented as completed.

# 6. Extended 1999–2026 retrospective stress test

**Table 2. Extended common warm-up-complete period, December 1999–November 2026. Pre-inception leveraged returns are synthetic.**

| Leveraged ETF | Rule | Final wealth ($) | CAGR | Max daily drawdown | Sharpe (rf=0) |
|:--|:--|--:|--:|--:|--:|
| SPXL | 200-SMA rule | 464,788 | 15.38% | −52.88% | 0.591 |
| SPXL | Synthetic/real buy & hold | 55,781 | 6.61% | −97.81% | 0.400 |
| TQQQ | 200-SMA rule | 313,784 | 13.70% | −90.49% | 0.510 |
| TQQQ | Synthetic/real buy & hold | 9,213 | −0.31% | −99.96% | 0.397 |

![Figure 3. Extended 1999–2026 wealth curves. Portions before SPXL (2008) and TQQQ (2010) existed are entirely hypothetical. The common evaluation begins after QQQ's SMA200 warm-up.](../figures/equity_1999.png){width=94%}

The extended window suggests that a slow regime gate can keep leveraged exposure out of substantial portions of long bear markets. However, this interpretation should not be overstated. First, a reconstructed *daily-reset* Nasdaq-100 3× portfolio experiences catastrophic early-2000s losses even with trend screening; a **−90.49%** rule drawdown is not evidence of effective capital preservation. Second, the two synthetic intervals end on different ETF inception dates and use different underlying dividend conventions. Third, historical financing conditions and the availability of a true 3× ETF during 2000–2002 are unknowable from modern adjusted price data. Thus the 1999 results are valuable for **hypothesis stress testing**, but the 2010 common real-ETF period receives greater evidential weight.

# 7. Temporal transport and cross-asset replication

A fixed-parameter historical split gives a **pseudo-forward evaluation**, not truly unused out-of-sample data. We restart each strategy with $10,000 and the same precomputed underlying SMA200 at the beginning of two non-overlapping intervals; we do **not** optimize the thresholds separately in the second interval.

**Table 3. Retrospective chronological partitions; values are fresh-start CAGRs and maximum daily drawdowns.**

| Rule | 2010–2017 CAGR | 2010–2017 MaxDD | 2018–2026 CAGR | 2018–2026 MaxDD |
|:--|--:|--:|--:|--:|
| SPY → SPXL | 25.06% | −42.3% | 17.03% | −52.9% |
| QQQ → TQQQ | 25.85% | −53.8% | 26.51% | −62.1% |

Both rules compound positively in both subperiods, but SPXL's CAGR declines in the later window; TQQQ maintains a high CAGR while sustaining deep drawdowns. This is *regime-dependent transport*, not evidence that equity exposure timing generalizes to other markets or higher turnover. SPY and QQQ are highly correlated U.S. equities, and their 3× funds share leverage mechanics. Two related instruments are **not independent confirmations** of a universal rule. Truly external asset classes, different monetary-policy regimes, and a future paper-trading holdout would materially strengthen or refute the generality claim.

![Figure 4. Retrospective year-over-year strategy returns in the common actual-ETF sample. Differences reflect varying broad-market and growth-equity exposure.](../figures/annual_returns_2010.png){width=94%}

# 8. Parameter neighborhood: a stability check, not optimized evidence

To examine local fragility without changing the baseline, we evaluate a **3×3×3 grid**: SMA look-backs of 150, 200, or 250 trading days; entry buffers of +2%, +4%, or +6%; and exit buffers of −1%, −3%, or −5%. The originally discussed baseline remains 200/+4%/−3% and is not replaced by the best-performing cell. Every grid run includes next-open execution and the same 10 bp per-side friction. Source: `data/results/snapshot_parameter_grid_2010.csv`.

All 27 SPXL grid configurations have positive post-2010 CAGR (range **8.77%–22.54%**, median **17.14%**); all 27 TQQQ configurations also have positive CAGR (**19.76%–31.12%**, median **26.07%**). Positive performance across a neighborhood suggests the baseline is not a single isolated profitable pixel. It does **not** demonstrate a stable *edge*: an upward-trending buy-and-hold leveraged ETF can make many partially invested variants look profitable, even when none beats the benchmark. Also, repeated inspection of this grid is itself multiple testing. Reporting the maximum as an expected return would be data mining.

![Figure 5. Local parameter-sensitivity heatmap, with exit fixed at −3%; values are historical CAGRs for each entry buffer and SMA length. The complete 27-cell grids are in CSV.](../figures/parameter_grid_2010.png){width=94%}

# 9. Transaction-cost and statistical uncertainty audits

**Table 4. Common actual-ETF period: CAGR under assumed one-way execution friction.**

| One-way friction per fill | SPXL SMA200 CAGR | TQQQ SMA200 CAGR |
|:--|--:|--:|
| 5 basis points | 21.20% | 27.02% |
| 10 basis points (baseline) | 21.14% | 26.93% |
| 20 basis points | 21.02% | 26.76% |
| 50 basis points | 20.65% | 26.22% |

Performance does not collapse merely by doubling modeled costs because the system trades less frequently than daily-rebalanced, short-signal strategies. This is **not** a liquidity guarantee: extreme crisis-time open gaps, market impact, spread widening, and order execution failures are not simulated by a constant bps charge. A meaningful future test should add volatility-dependent slippage, a position-size stress test, and broker-specific fee tiers.

We also compute a deliberately limited uncertainty check from the archived **201 monthly close-to-close return pairs** in the 2010 sample. For each asset, we form the strategy's monthly *log return minus its buy-and-hold log return*; draw 5,000 paired circular block-bootstrap resamples using 12-month blocks and a fixed random seed (20261112); then annualize the mean log difference by multiplying by 12. The estimated annualized differences are **−5.82 percentage points** for SPXL (indicative 95% interval **[−13.73, +3.13]**) and **−9.84 points** for TQQQ (**[−21.66, +5.12]**). Both ranges span zero. These intervals illustrate noisy monthly relative returns; they do *not* correct for historical parameter choice, changing volatility regimes, overlapping blocks, or nonstationarity. The analysis provides **no basis for rejecting a zero-alpha null**. There is no valid claim here of a statistically significant improvement over buy-and-hold.

# 10. Look-ahead, selection, and survivorship safeguards

The backtest contains eight automated unit tests independent of internet access. These assert that a close(t) signal cannot fill at open(t), that staged purchases are incremental and capped at five, that a stop fills at the *next* open, that a price within the buffer causes no trade, that fees reduce final wealth when trades occur, that baseline calculations are internally consistent, and that the serialized monthly snapshot decodes to the audited endpoint. They can be run with `python -m pytest -q`.

**What the safeguards solve.** The source code uses daily closes to calculate SMA200 only after the close. The pending order is executed at the next daily open. Historical moving averages require a full 200 observations; the two markets use a common evaluation start after warm-up. Every attempted fill debits a positive transaction charge; data dates are sorted, unique, positive, and checked for overlapping source feeds. Strategy and buy-and-hold use the same instrument price stream within their respective comparisons. Source blobs are Git-blob-hash verified at download time and the audit date is frozen. The published figure source is the *actual month-end sampling* of the computed daily NAV, not a decorative or interpolated illustration.

**What they do NOT solve.** This research is not ex-ante registered. The user-chosen +4% and −3% buffers may have been influenced by prior exploration, and SMA200 is a common historical market heuristic. An apparent post-2018 “holdout” cannot be untouched if the researcher already knows 2018–2026 outcomes. Backtest overfitting probability (PBO/CSCV), White's Reality Check, and a Deflated Sharpe Ratio would require an exhaustively logged strategy-search universe and a valid multiple-trial correction; no such trial log exists, so **no invented p-value or Deflated Sharpe Ratio is reported** [7, 8]. Asset-selection survivorship is also possible: both ETFs remain alive, while failed or closed leverage funds are absent from the universe. Publishing *every* future parameter trial, retaining a precommitted setup, and collecting genuinely prospective paper/live (small-size) executions are necessary if the strategy is to graduate beyond an exploratory claim.

# 11. Economic interpretation and falsifiable predictions

A coherent but **unverified** mechanism is that long-horizon equity momentum allows a trend filter to avoid some bear-market persistence while buffers reduce repeated churn close to a moving average. The 20%-per-day ramp limits the immediate entry exposure; nevertheless, five favorable sessions can rapidly restore full 3× risk. The full-exit rule, not a short hedge, is the source of much downside avoidance. This produces a testable tradeoff: reduced prolonged-bear exposure, lower effective equity participation, and potentially substantial whipsaw in sideways and V-shaped markets.

Three forward-looking claims are falsifiable. **(i)** Over a preregistered five-year future window, the rule should reduce each ETF's observed maximum drawdown relative to its own buy-and-hold; otherwise its central risk-management hypothesis weakens. **(ii)** With parameters frozen, turnover-adjusted Sharpe should remain competitive with a matched-exposure cash/ETF blend, not merely a full-leverage portfolio; otherwise any appearance of skill may be exposure reduction alone. **(iii)** A fixed identical rule tested on unrelated equity geographies, rate futures, commodities, and real-market 2× ETFs should not require extensive per-market tuning to avoid large whipsaw losses; otherwise its scope should be described as U.S. equity-specific. These are research hypotheses, **not claims of tests already completed**.

# 12. Conclusion

Under a reproducible interpretation of the user-defined 200/+4%/−3% allocation rule, the SPY→SPXL and QQQ→TQQQ versions both deliver positive post-2010 compounded returns while suffering materially smaller maximum drawdowns than buying and holding the corresponding leveraged ETF. However, the absolute drawdowns remain severe (−52.88% and −62.09%), and the two rules **underperform** buy-and-hold on CAGR and Sharpe during the common *real* period. The partly simulated 1999 history is useful as a bear-market stress test, not as an investable return record or proof that SPXL is inherently superior to TQQQ. A retrospective neighborhood of profitable parameters and similar results on two correlated equity markets do not establish causality, statistical significance, or broad generality.

**Appropriate final characterization:** a transparent, repeatable, long-only leveraged-equity *risk-management hypothesis* with promising descriptive drawdown behavior, demanding further matched-risk benchmarking, unified total-return data, prospective validation, and explicit reporting of all subsequent trials.

# Data/code availability and reproducibility

The project includes `README.md`, `scripts/reproduce.py`, `scripts/fetch_data.py`, `scripts/build_snapshot_artifacts.py`, `scripts/bootstrap.py`, `tests/test_engine.py`, source hashes in `data/sources.json`, derived month-end equity CSVs, risk/parameter/cost summaries, and the PNG figures. Full daily licensed market-data archives and IBKR historical bars are **not** republished. A reader with internet access can retrieve upstream archives and a public historical tail, then run the same logic; minor numeric divergence from the frozen IBKR-tail audit is possible because public vendors change corporate-action adjustments and because the price inputs are not fully homogeneous. Raw vendor permissions must be checked separately. The GitHub repository is a reproducibility companion and disclosure record, not a live signal service.

# References

[1] Moskowitz, T. J., Y. H. Ooi, and L. H. Pedersen (2012). “Time Series Momentum.” *Journal of Financial Economics* 104(2): 228–250. https://doi.org/10.1016/j.jfineco.2011.11.003.

[2] Hurst, B., Y. H. Ooi, and L. H. Pedersen (2017). “A Century of Evidence on Trend-Following Investing.” *Journal of Portfolio Management* 44(1): 15–29. https://doi.org/10.3905/jpm.2017.44.1.015.

[3] Harvey, C. R., and Y. Liu (2015). “Backtesting.” *Journal of Portfolio Management* 42(1): 13–28. https://doi.org/10.3905/jpm.2015.42.1.013.

[4] Fung, W., and D. A. Hsieh (2001). “The Risk in Hedge Fund Strategies: Theory and Evidence from Trend Followers.” *Review of Financial Studies* 14(2): 313–341. https://doi.org/10.1093/rfs/14.2.313.

[5] Direxion. “Daily S&P 500 Bull 3X Shares (SPXL): Fund Profile and Daily Investment Objective.” https://www.direxion.com/product/daily-sp-500-bull-bear-3x-etfs (accessed 12 November 2026).

[6] ProShares. “UltraPro QQQ (TQQQ): Fund Overview and Daily Investment Objective.” https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq (accessed 12 November 2026).

[7] Bailey, D. H., and M. López de Prado (2014). “The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality.” *Journal of Portfolio Management* 40(5): 94–107. https://doi.org/10.3905/jpm.2014.40.5.094.

[8] Bailey, D. H., J. M. Borwein, M. López de Prado, and Q. J. Zhu (2017). “The Probability of Backtest Overfitting.” *Journal of Computational Finance*. https://doi.org/10.21314/JCF.2016.322.

[9] Public historical source repositories, with exact blob hashes in `data/sources.json`: https://github.com/Setooooo/etf-insight ; https://github.com/xjcarter/data ; https://github.com/kienta1999/qqq-overnight-drift .

[10] Interactive Brokers. “Market Data and Analytics Subscriber Agreement” and API market-data documentation. https://www.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?file=IBISAgreement.html ; https://www.interactivebrokers.com/docs/tws-api/doc/md/introduction .
