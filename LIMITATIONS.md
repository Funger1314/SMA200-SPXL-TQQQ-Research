# Limitations (v4)

See manuscript §11 for the full list. In short:

1. Ex-post design: rule and hypotheses were chosen after the data were seen. Walk-forward and SPA tests reduce but do not remove this bias. Only two related U.S. indices were studied.
2. Survivorship: SPXL and TQQQ are surviving flagship funds.
3. The 1999–2009 results are hypothetical. No 3× daily-reset ETF existed then, and swap availability and counterparty risk cannot be reproduced.
4. Regimes: the post-2010 record contains one prolonged bear market (2022). Rates and market structure differ across the sample.
5. Inference: block bootstraps weaken long trends; p-values are conditional on the stated nulls and the 45-configuration universe.
6. Data: Yahoo market prices, not NAV. TQQQ's first trading day is missing. The TQQQ total-return reconciliation with ProShares is still open.
7. Execution: fractional fills at the open, modelled costs, no market impact, pre-tax.
8. No claim of generalisation to other markets or future regimes.

---

# Limitations (v3)

1. **Ex post design.** The rule, hypotheses and benchmarks were chosen after the history had been seen. The matched fixed weight uses the rule's realised average weight.
2. **The evidence for timing value is synthetic.** The rule beats non-timing frontiers only when 2000–2009 is included, and no 3× ETF existed then. The calibrated proxy tracks real funds closely in 2018–2026 (correlation 0.999), but it cannot reproduce 2000-era swap availability, counterparty risk or fund closures.
3. **Few independent events.** Two or three large avoided losses per fund before 2010, plus 2022, carry the result.
4. **Bootstrap.** Block resampling (mean 63/252 days) shortens multi-year trends and is therefore conservative for trend rules.
5. **Execution.** Fractional fills at the open with constant friction; no taxes; no capacity modelling.
6. **Data.** A single public vendor gives consistent data, but it has not yet been reconciled to official fund NAV total returns. Yahoo revises its adjustments, so check the file hashes. Raw files are not redistributed.

---

## Earlier (v1/v2) limitations, retained for the record


1. **Ex-post design.** The parameters 200 / +4% / -3% were discussed after observing historical markets. No preregistration or unobserved prospective holdout exists. A 2018 date split is only a retrospective pseudo-out-of-sample check. Reporting 27 neighboring parameter configurations helps reveal a performance plateau but does not de-bias the selected rule.
2. **Limited generality.** SPY and QQQ are highly correlated U.S. large-cap equity exposures. SPXL and TQQQ both target daily 3× returns. Two related instruments cannot prove broad asset-class transport. Do not claim universality.
3. **Different corporate-action conventions.** Archived SPY/SPXL OHLC are unadjusted Yahoo-style series; QQQ/TQQQ archive uses auto-adjusted OHLC. The later IBKR snapshot comes from another provider and has price-only conventions. This particularly limits the interpretation of fine cross-ETF return comparisons. Using a fully licensed, unified adjusted total-return history is required for stronger claims.
4. **Pre-inception synthetic history.** 3× SPY/QQQ daily reset minus illustrative fee does not reconstruct historical 3× financing, swaps, tracking errors, portfolio management, distributions, halts, or investable prices. All results before the leveraged ETF's first real quote are hypothetical. Common long-run start 1999-12-22 follows a valid 200-day QQQ SMA warm-up.
5. **No hard risk cap.** A close below -3% of SMA200 produces a sale at NEXT open, not a stop-loss at that underlying threshold. Drawdowns of -53% (SPXL) and -62% (TQQQ) in the real 2010+ period are possible despite filtering.
6. **Execution assumptions.** Every buy/sell costs a fixed 10bps of notional, fractional shares are allowed, open fills are always available, no taxes, no borrow or credit constraints, and idle cash earns 0%. In severe gaps, true execution quality may be much worse; a fixed-bps model is not sufficient to certify capacity.
7. **Comparisons.** Both live-period strategies underperformed their own 3× buy-and-hold on CAGR and zero-cash Sharpe, albeit with less peak-to-trough loss. A matched-volatility portfolio and Treasury-cash control are necessary to isolate timing value from lower risky-asset exposure.
8. **Statistical inference.** The bootstrap on monthly log excess returns is descriptive, assumes time-series resampling is meaningful, and does not correct for multiple hypothesis testing or nonstationarity. Do not describe its percentile interval as proof of no edge or of a significant edge. DSR/PBO are not computed because the full historical strategy-search universe and trial count are unknown.
9. **Hindsight in source selection.** Both leveraged ETFs survived. Failure, delisting, changes to strategy mandates, and vintage data revision risk are absent from this small asset universe.
10. **Market-data publication rights.** Public Yahoo Finance and IBKR bars may not be freely redistributed even when obtained from public GitHub repositories or a subscribed API. GitHub ZIP contains derived research outputs and source links, not vendor source feeds. Check licenses separately.

## Research roadmap

- Collect single-vendor, split-and-dividend-adjusted data; reconcile every corporate action and independent data sample.
- Add cash benchmarks based on historical T-bill yields and explicitly separate price-only and total-return figures.
- Compare fixed SMA strategy against matched-volatility SPXL/TQQQ plus cash, not only fully exposed buy-and-hold.
- Commit the current rule in an immutable tag; run truly forward paper trading without changing parameters.
- Track all future attempts/parameters (successful AND unsuccessful). If searching many variants, use proper PBO/CSCV/DSR and robust multiple-testing corrections.
- Repeat on independent geographies, rates, commodities, and unleveraged/futures exposures, without tuning the rule per asset.
- Implement venue-specific exchange and broker order fill simulation around open auctions, spreads, and jumps.
