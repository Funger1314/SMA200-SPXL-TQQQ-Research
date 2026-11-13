# Reviewer-response revision v2 — Research replication (not fully refreshed)

**Start here.** The referee's methodological criticisms were accepted. The new [v2 revision manuscript](paper/SMA200_Review_Revision_v2.pdf), [reviewer response checklist](REVIEWER_RESPONSE.md), [v2 reproduction protocol](REPRODUCE_V2.md), new engine `scripts/review_revision.py`, historical monthly Treasury-rate proxy `scripts/rates.py`, and paired monthly-risk bootstrap `scripts/reviewer_risk_bootstrap.py` are included. The original v1 empirical snapshot below is retained only as a **legacy audit**, not the result of the new financing/adjustment model. Complete new v2 historical performance metrics are *pending source-data validation and a rerun*.

**Run:**
```bash
pip install -r requirements.txt
python -m pytest -q
python scripts/reviewer_risk_bootstrap.py
python scripts/fetch_data.py
python scripts/reproduce.py --tail-mode public
```

The final command intentionally **fails** if adjusted archive and the newly downloaded tail differ by >1bp on their overlap day. Do not disable the control merely to force a successful run. Consistent licensed data need to be acquired if vendor adjustments change.

---

## Legacy v1 README and audit values (superseded as evidence)

# SMA200 Regime Filter on SPXL and TQQQ (1999–2026)

[简体中文说明](README_zh.md) · [Research paper PDF](paper/SMA200_Leveraged_ETF_Research.pdf) · [Data provenance](data/sources.json) · [Limitations](LIMITATIONS.md)

**Status:** A transparent *exploratory research* backtest—not a validated trading signal, pre-registered experiment, or offer of investment advice. Market data were analyzed through **2026-11-12**.

![Common 2010–2026 real-ETF equity curves](figures/equity_2010.png)

## Exact strategy

Signal pair | Underlying ETF close | Leveraged ETF actually traded
---|---|---
Broad U.S. equity | SPY | SPXL (daily 3× S&P 500)
Growth/large-cap | QQQ | TQQQ (daily 3× Nasdaq-100)

1. Compute the **200-session simple moving average on the signal ETF's daily closes**, after a full warm-up.
2. If today's **closing** signal ETF price is **at least 104% of SMA200**, queue a purchase at **next trading day's open**. Target 20% / 40% / 60% / 80% / 100% portfolio equity, one stage per eligible session, with all existing positions retained. If between thresholds, pause purchases and hold the existing position.
3. If today's closing signal ETF price is **below 97% of SMA200**, queue **full liquidation at next session's open**. Then re-enter only after the +4% condition is met again.
4. No external leverage beyond the leveraged ETF, **10 bps cost per filled buy/sell notional** (5 bps assumed fee + 5 bps modeled slippage), **0% cash return**, no tax or SGOV yield. Fractional shares permitted.

These are **level** conditions, *not* a strict requirement to newly cross the boundary on that particular day. There is no intraday hard stop; a SMA-based exit cannot cap gap losses.

## Results: identical real-ETF common period (2010-02-11–2026-11-12)

| Instrument | Strategy | CAGR | Max daily drawdown | Sharpe (rf=0) | $10k grows to |
|---|---|---:|---:|---:|---:|
| SPXL | SMA200 | **21.14%** | **-52.88%** | 0.720 | $247,070 |
| SPXL | Buy & hold | 28.94% | -76.86% | 0.754 | $701,252 |
| TQQQ | SMA200 | **26.93%** | **-62.09%** | 0.746 | $539,596 |
| TQQQ | Buy & hold | 40.91% | -81.66% | 0.864 | $3,093,421 |

The SMA rule reduces observed drawdown by approximately **24 pp for SPXL** and **20 pp for TQQQ**, but it does **not** outperform either leveraged ETF on historical CAGR or Sharpe in the common real-instrument sample.

## Extended hypothetical history (1999-12-22–2026-11-12)

| Instrument | Strategy CAGR | Worst daily drawdown | Model status |
|---|---:|---:|---|
| SPXL | 15.38% | -52.88% | **synthetic** 1999–2008; real afterwards |
| TQQQ | 13.70% | -90.49% | **synthetic** 1999–2010; real afterwards |

![1999–2026 extended monthly equity curves](figures/equity_1999.png)

The synthetic period is a daily-reset 3× model with illustrative 0.95% annual drag, **not a tradable ETF**. QQQ's 200-day look-back begins only after its 1999 launch, so the matched evaluation begins in **December 1999**, not March 1999. **Do not present this as a real live history.**

## Robustness is not proof of an edge

The 2010–2026 tests include a fixed 27-cell grid on each ETF: SMA 150/200/250, entry buffer +2/+4/+6%, and exit buffer -1/-3/-5%. Every variant earns positive *absolute* historical CAGR, but both assets experienced long equity bull markets, many strategy variants were inspected, and related SPY/QQQ exposures are **not independent** assets. A retrospective 2018–2026 subperiod is *pseudo-out-of-sample*, not truly blinded. A paired 12-month block bootstrap does not establish positive excess log return over buy-and-hold.

See [paper](paper/SMA200_Leveraged_ETF_Research.pdf) for full methodology, raw-vs-adjusted data conventions, cross-instrument limitations, cost stress tests, transaction diagnostics, and proposed prospective falsification tests.

## Quick start (reproduce with your own permitted local data downloads)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m pytest -q
python scripts/reproduce.py --fetch
python scripts/bootstrap.py
```

`--fetch` retrieves the **upstream historical archives** into your *local* `data/raw/` and verifies their **Git blob SHA-1**, then downloads a public Yahoo Finance tail up to the frozen audit date. The original audit tail came from IBKR and **is not published** due market-data redistribution restrictions, so small discrepancies versus the published audit snapshot can occur. The code fails on missing source or unexpected dates instead of inventing or forward-filling prices.

**If a pinned upstream SHA changes**, fetch aborts. Check the source changes and update `data/sources.json` only after independently validating the new input. To reproduce the exact original IBKR-tail audit, one must separately hold appropriately licensed market data with the matching vintage.

The shipped `data/results/monthly_equity_*.csv` are **derived sampled strategy NAVs**, *not* the four raw OHLC archives. To build complete local `data/derived/market_SPXL.csv`, `market_TQQQ.csv`, daily equity, trade blotters, and new figures, run the reproduction command above.

### Repository map

```text
paper/                              Academic manuscript (PDF, DOCX, Markdown)
figures/                            Equity curves, sampled drawdowns, annual returns, grid
scripts/reproduce.py                Strategy engine + daily NAV/trades + full analyses
scripts/fetch_data.py               Validated source-downloader
scripts/build_snapshot_artifacts.py Frozen snapshot chart/table builder
scripts/bootstrap.py                Descriptive 12-month paired block-bootstrap check
scripts/decode_snapshot.py          Decode compact historical NAV audit snapshots
tests/test_engine.py                Eight no-internet logic tests
data/sources.json                   Source URLs, blob hashes, conventions, dates
data/results/                       Audited month-end NAVs, metrics, sensitivity results
LIMITATIONS.md                      Assumptions, inference and data rights
```

## Data rights and publication note

The original Yahoo Finance/IBKR **full price feeds are not bundled or licensed for redistribution by this research repository**. This repo ships only derived result series and links to the original providers. See [DATA_LICENSE_NOTICE.md](DATA_LICENSE_NOTICE.md). Third-party sites may change, remove, or restrict downloads. The source archives' GitHub publication does not itself authorize downstream republication.

## Citation and contribution

For citation use: *A 200-Day Trend Filter for 3× Leveraged U.S. Equity ETFs: A Two-Asset Replication, 1999–2026*, independent quantitative research note, 12 November 2026. To contribute, submit code tests, verified corporate-action corrections, risk-matched benchmarks, or a preregistered forward test; **do not** overwrite historical published results without a versioned changelog.

**Code license:** MIT (`LICENSE`) applies to authored code and documentation only; **no rights in third-party market data are granted**.
