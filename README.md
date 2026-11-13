# Market Index Enhancement Strategy

### SMA200 Trend Following & Dynamic Leverage | SPY / QQQ Benchmarks

[Research Paper (PDF)](paper/SMA200_Leveraged_ETF_Research_v4.pdf) · [Reproduction Guide](REPRODUCE_V4.md) · [Methodological Limitations](LIMITATIONS.md) · [中文说明](README_zh.md)

## Overview

This project investigates a **systematic U.S. equity index enhancement strategy** targeting higher long-term returns than passive investments in the **S&P 500 (SPY)** and **Nasdaq-100 (QQQ)**. It combines a 200-day simple moving average (SMA200) trend filter with staged allocations to **SPXL** and **TQQQ**, two 3× daily-reset leveraged ETFs.

Two strategies are evaluated separately:

- **S&P 500 enhancement:** SPY generates trend signals; SPXL implements leveraged exposure.
- **Nasdaq-100 enhancement:** QQQ generates trend signals; TQQQ implements leveraged exposure.

The objective is to examine whether trend-based dynamic leverage improves long-run capital growth, **and whether any improvement represents genuine market-timing value rather than simply taking more risk**.

## Strategy Rules

| Component | Implementation |
|---|---|
| Trend indicator | 200-trading-day simple moving average of the unleveraged signal ETF (SPY or QQQ) |
| Entry condition | Signal ETF closes at or above **104% of its SMA200** |
| Position building | Buy **20% of portfolio capital per eligible trading day**, up to 100% exposure to SPXL or TQQQ |
| Exit condition | Signal ETF closes **below 97% of its SMA200**; exit the leveraged ETF position entirely |
| Execution | Signals observed at the close; orders filled at the **next trading day's open** |
| Transaction costs | **10 basis points per fill** in the backtest |
| Defensive allocation | Uninvested capital earns a **lagged Treasury-bill rate** in the research model |

The entry/exit buffer creates hysteresis intended to avoid excessive turnover around SMA200. **This is not a capital-guaranteed or low-drawdown strategy:** 3× daily leverage can cause severe losses even with a trend filter.

## Backtest: Enhancement vs. Buy-and-Hold

**Primary evaluation window: February 11, 2010 – August 6, 2026 (real ETF data).** The enhancement strategies are compared with passive ownership of their respective **unleveraged** indexes, not just with 3× leveraged buy-and-hold.

| Metric | SPY Buy & Hold | S&P 500 Enhancement (SPXL + SMA200) | QQQ Buy & Hold | Nasdaq-100 Enhancement (TQQQ + SMA200) |
|:--|--:|--:|--:|--:|
| **CAGR** | 14.8% | **22.2%** | 19.7% | **30.2%** |
| **Maximum Drawdown** | **−33.7%** | −53.4% | **−35.1%** | −62.1% |
| **Sharpe Ratio** | **0.804** | 0.700 | **0.899** | 0.771 |
| **Calmar Ratio** | **0.438** | 0.416 | **0.560** | 0.487 |

In this historical sample, the strategy generated approximately **+7.4 percentage points of annualized return over SPY** and **+10.5 percentage points over QQQ**. However, the gains required materially greater downside risk: maximum drawdowns were approximately **19.7 and 27.0 percentage points deeper**, respectively, and both strategies had **lower Sharpe and Calmar ratios** than passive index ownership.

The distinction matters: **higher CAGR does not establish superior risk-adjusted performance**.

![Historical equity curves](figures/v4/equity_real.png)

![Drawdown comparison](figures/v4/drawdown_real.png)

## Research Framework

The study tests whether the trend filter adds value beyond leveraged exposure using multiple benchmarks and robustness checks:

- **3× buy-and-hold:** SPXL and TQQQ held continuously to isolate the effect of the trend filter.
- **1× buy-and-hold:** SPY and QQQ as the investable, unleveraged index baselines.
- **1× trend filter:** The same timing rule applied without leverage.
- **Ex-ante exposure-matched portfolio:** A benchmark using historical, rather than future, information about the strategy's exposure.
- **30% volatility target:** A non-timing alternative that adjusts leverage using trailing realized volatility.
- **Walk-forward validation:** Five-year training windows followed by one-year out-of-sample tests.
- **Stationary bootstrap:** Path-based resampling of strategy outcomes and risk differences.
- **Multiple-testing control:** White's Reality Check and Hansen's SPA test across 45 rule configurations.
- **Stress and mechanism analysis:** Crisis-exclusion path simulations, trading-cost sensitivity, synthetic-history stress tests, and risk attribution.

### Main Finding

**The study does not find statistically significant evidence that SMA200 adds market-timing alpha after accounting for leverage, exposure, volatility, and strategy selection.** Although the filter reduced realized drawdowns relative to continuously holding the 3× ETFs in the real-ETF period, its return enhancement over SPY/QQQ was accompanied by considerably greater risk. Trend filtering is best understood here as a potential defense against *prolonged* bear markets—not as a proven source of superior risk-adjusted returns.

An extended **1999–2026** experiment includes **synthetic leveraged ETF returns before the funds existed**. These results are explicitly **hypothetical** and must not be interpreted as historically executable performance.

## Reproducing the Research

The replication archive includes source-market data snapshots, analytical scripts, tests, tables, and a research manuscript. To reproduce the results from the repository root:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/v4_run.py
python scripts/v4_tables.py
python scripts/verify_results.py
```

The full research-paper build can be run with:

```bash
./run_all.sh
```

**Environment:** Python 3.13 and the dependency versions in `requirements.txt`. PDF generation additionally requires Pandoc and XeLaTeX. See [`REPRODUCE_V4.md`](REPRODUCE_V4.md) for exact data provenance, seeds, hashes, and output descriptions. Note that vendor-adjusted historical prices can be restated, so fresh downloads may not reproduce the archived data hashes exactly.

## Repository Guide

```text
├── README.md                   # Project overview and benchmark comparison
├── README_zh.md                # Chinese project overview
├── paper/                      # Research paper, tables, and build scripts
├── scripts/                    # Strategy engine, statistics, audits, reproduction
├── data/raw/                   # Archived SPY, SPXL, QQQ, TQQQ market data
├── data/v4_results/            # Research outputs and run manifest
├── figures/v4/                # Equity curves, drawdowns, frontiers, robustness charts
├── tests/                     # Automated tests
├── REPRODUCE_V4.md             # Full reproduction procedure
└── LIMITATIONS.md              # Research limitations and interpretation
```

## Limitations & Disclaimer

- Results are **historical backtests**, not live or audited brokerage performance.
- Leveraged ETFs target **3× daily returns**, not 3× compounded long-horizon index returns; volatility drag and tracking effects matter.
- The rules were developed and examined using historical information; the research is **not preregistered** and remains exposed to researcher-selection bias.
- Cash-rate assumptions, transaction costs, fund expenses, market frictions, and data adjustments can affect results.
- **No robust market-timing alpha is established** by the evidence presented here.
- This project is for educational and quantitative research purposes only and does **not** constitute investment advice.

*Research version: v4.1 · Historical data through August 6, 2026.*
