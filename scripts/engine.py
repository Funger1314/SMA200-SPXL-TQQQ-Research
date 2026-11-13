"""Single-vendor research engine (v3, extended in v4: strict validation,
per-day cost arrays, target-weight paths, tail-risk metrics).

Changes relative to v2 (`review_revision.py`):
  * One vendor for all four instruments (yfinance export of Yahoo Finance daily
    bars, `auto_adjust=False`), so no cross-vendor splice is ever performed.
  * Study end date 2026-08-06 = last common bar in the single-vendor files.
  * Synthetic pre-inception financing spread `s` is CALIBRATED on the real-ETF
    overlap instead of being set to zero.
  * A fast array simulator (`simulate`) with exactly the v2 state-machine
    semantics; tests assert numerical equivalence with v2 `benchmark`.
  * Sharpe uses the standard deviation of EXCESS returns.

Timing convention (unchanged): signals are evaluated after close(t); orders are
filled at open(t+1); uninvested cash accrues the prior-month T-bill proxy.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, replace
from pathlib import Path
import numpy as np
import pandas as pd
from rates import annual_cash_rate
from data_checks import validate_ohlcv

ROOT = Path(__file__).resolve().parents[1]
END = '2026-08-06'
PAIRS = {'SPXL': 'SPY', 'TQQQ': 'QQQ'}
INCEPTION = {'SPXL': '2008-11-05', 'TQQQ': '2010-02-11'}
STARTS = {'real': '2010-02-11', 'full': '1999-12-22'}
UNIVERSE_START = '1999-03-10'   # QQQ first bar; keeps SPY and QQQ warm-ups symmetric


@dataclass(frozen=True)
class Params:
    sma_days: int = 200
    entry: float = 0.04
    exit: float = -0.03
    fee: float = 0.001
    synth_expense: float = 0.0095
    fin_spread: float = 0.007          # replaced per asset by calibration in v3_run
    vol_target: float = 0.30
    vol_window: int = 63
    vol_rebalance: int = 5
    fixed_rebalance: int = 21
    cash: bool = True                  # False reproduces the v1 0% cash convention


# --------------------------------------------------------------------------- data
def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_yahoo(ticker: str, adjusted: bool = True, raw_dir: Path | None = None) -> pd.DataFrame:
    """Read a yfinance multi-header CSV. adjusted=True gives total-return OHLC
    (Open scaled by AdjClose/Close of the same day); False gives split-adjusted
    price-only bars (the v1 convention)."""
    path = (raw_dir or ROOT / 'data/raw') / f'{ticker}.csv'
    if not path.exists():
        raise FileNotFoundError(f'{path} missing; see REPRODUCE_V3.md for the data source')
    head = pd.read_csv(path, nrows=2, header=None)
    skip = [1, 2] if str(head.iloc[1, 0]).strip().lower() == 'ticker' else []
    d = pd.read_csv(path, skiprows=skip)
    d = d.rename(columns={d.columns[0]: 'Date'}) if d.columns[0] in ('Price', 'Date') else d
    d['Date'] = pd.to_datetime(d['Date'], errors='raise')
    d = d.set_index('Date')            # file order kept: validation must see unsorted input
    for c in ('Open', 'Close', 'Adj Close'):
        if c not in d:
            raise ValueError(f'{ticker}: column {c} required')
        d[c] = pd.to_numeric(d[c], errors='raise')
    if 'Volume' in d:
        d['Volume'] = pd.to_numeric(d['Volume'], errors='raise')
    for c in ('High', 'Low'):
        if c in d:
            d[c] = pd.to_numeric(d[c], errors='raise')
    # validate the file exactly as stored (before any sorting or truncation)
    report = validate_ohlcv(d, ticker, leveraged=ticker in INCEPTION, strict=True)
    if adjusted:
        f = d['Adj Close'] / d['Close']
        out = pd.DataFrame({'Open': d['Open'] * f, 'Close': d['Adj Close']})
    else:
        out = d[['Open', 'Close']].copy()
    out = out.loc[:END]
    if out.index[-1] != pd.Timestamp(END):
        raise ValueError(f'{ticker}: data must run through {END}')
    out.attrs['validation'] = report
    out.attrs['sha256'] = sha256(path)
    return out


def load_all(adjusted: bool = True) -> dict[str, pd.DataFrame]:
    data = {t: load_yahoo(t, adjusted) for t in ('SPY', 'SPXL', 'QQQ', 'TQQQ')}
    for lev, und in PAIRS.items():
        a = data[und].loc[data[lev].index[0]:].index
        if not a.equals(data[lev].index):
            raise ValueError(f'{lev}/{und}: trading calendars differ')
    return data


# ----------------------------------------------------------------- calibration
def calibrate_spread(und: pd.DataFrame, lev: pd.DataFrame, start: str, end: str,
                     expense: float = 0.0095) -> dict:
    """Mean of  r_L - 3 r_U + 2 rf/252 + f/252  equals  -2 s/252  under the model."""
    j = pd.concat([lev.Close.pct_change(), und.Close.pct_change()], axis=1,
                  keys=['L', 'U'], sort=True).dropna().loc[start:end]
    rf = annual_cash_rate(j.index)
    resid = j.L - 3 * j.U + 2 * rf / 252 + expense / 252
    s = float(-resid.mean() * 252 / 2)
    return {'Start': str(j.index[0].date()), 'End': str(j.index[-1].date()), 'Days': len(j),
            'MeanRF': float(rf.mean()), 'Spread_s': s,
            'ResidualDailyStd_bp': float(resid.std() * 1e4),
            'ResidualAbsGt2pct_days': int((resid.abs() > 0.02).sum())}


def synthetic_3x(und: pd.DataFrame, s: float, expense: float = 0.0095) -> pd.DataFrame:
    """Forward 3x daily-reset total-return proxy on the underlying's own calendar."""
    rf = annual_cash_rate(und.index).to_numpy()
    c = und.Close.to_numpy(); o = und.Open.to_numpy()
    carry = (2 * (rf + s) + expense) / 252
    close = np.empty(len(c)); opn = np.empty(len(c))
    close[0] = opn[0] = 1.0
    for i in range(1, len(c)):
        fac = 1 + 3 * (c[i] / c[i - 1] - 1) - carry[i]
        if fac <= 0:
            raise ValueError(f'synthetic bankruptcy on {und.index[i].date()}')
        close[i] = close[i - 1] * fac
        opn[i] = close[i - 1] * (1 + 3 * (o[i] / c[i - 1] - 1) - carry[i] / 2)
    return pd.DataFrame({'Open': opn, 'Close': close}, index=und.index)


def synthetic_3x_stress(und: pd.DataFrame, s: float, expense: float = 0.0095, leverage: float = 3.0,
                        te_daily: float = 0.0, extra_spread: pd.Series | None = None, seed: int | None = None):
    """Synthetic proxy with stress options: realised leverage != 3, i.i.d. daily tracking
    noise with s.d. `te_daily`, and a time-varying extra financing spread (annual, per
    borrowed unit) e.g. a crisis funding shock."""
    rf = annual_cash_rate(und.index).to_numpy()
    xs = np.zeros(len(und)) if extra_spread is None else extra_spread.reindex(und.index).fillna(0).to_numpy()
    eps = np.zeros(len(und)) if te_daily == 0 else np.random.default_rng(seed).normal(0, te_daily, len(und))
    c = und.Close.to_numpy(); o = und.Open.to_numpy()
    carry = ((leverage - 1) * (rf + s + xs) + expense) / 252
    close = np.empty(len(c)); opn = np.empty(len(c)); close[0] = opn[0] = 1.0
    for i in range(1, len(c)):
        fac = 1 + leverage * (c[i] / c[i - 1] - 1) - carry[i] + eps[i]
        if fac <= 0:
            raise ValueError(f'synthetic bankruptcy on {und.index[i].date()}')
        close[i] = close[i - 1] * fac
        opn[i] = close[i - 1] * (1 + leverage * (o[i] / c[i - 1] - 1) - carry[i] / 2)
    return pd.DataFrame({'Open': opn, 'Close': close}, index=und.index)


def build_market(und: pd.DataFrame, lev: pd.DataFrame, s: float, p: Params = Params(),
                 universe_start: str = UNIVERSE_START, syn: pd.DataFrame | None = None) -> pd.DataFrame:
    """Signal ETF + leveraged sleeve; synthetic before inception, chained so the
    synthetic close on the day before inception continues into the real return."""
    u = und.loc[universe_start:]
    syn = synthetic_3x(u, s, p.synth_expense) if syn is None else syn.loc[universe_start:]
    first = lev.index[0]
    pre = syn.loc[:first].iloc[:-1]
    if len(pre):
        # scale so the synthetic close on the last pre-inception day, compounded by
        # the synthetic first-day factor, equals the first real close
        f_first = syn.Close.loc[first] / pre.Close.iloc[-1]
        scale = lev.Close.iloc[0] / f_first / pre.Close.iloc[-1]
        pre = pre * scale
    sleeve = pd.concat([pre, lev]).sort_index()
    m = u.rename(columns={'Open': 'signal_open', 'Close': 'signal_close'}).join(
        sleeve.rename(columns={'Open': 'asset_open', 'Close': 'asset_close'}), how='inner')
    m['rf'] = annual_cash_rate(m.index)
    m['synthetic'] = m.index < first
    return m


def add_signals(m: pd.DataFrame, p: Params = Params()) -> pd.DataFrame:
    m = m.copy()
    m['sma'] = m.signal_close.rolling(p.sma_days, min_periods=p.sma_days).mean()
    r = m.asset_close.pct_change()
    m['asset_vol'] = r.rolling(p.vol_window, min_periods=p.vol_window).std(ddof=1) * np.sqrt(252)
    return m


# ------------------------------------------------------------------- simulator
def simulate(sig, sma, ao, ac, rf, mode='trend', p: Params = Params(), w=1.0, vol=None,
             capital=10000.0, fee_arr=None, wpath=None):
    """Array simulator with the v2 state machine.

    Returns dict of numpy arrays: nav, weight, shares, cash; and list of orders
    (index, action, fill_price, notional, fee).
    mode: trend | hold | fixed | vol | target   (unlevered hold = 'hold' on signal arrays)
    fee_arr: optional per-day one-way cost rate applied to fills on that day.
    wpath: for mode='target', weight decided at close i (NaN = no order); filled at open i+1.
    """
    n = len(ao)
    cash = capital; sh = 0.0; stage = 0; pend = None
    nav = np.empty(n); wt = np.empty(n); shs = np.empty(n); csh = np.empty(n)
    orders = []
    fee0 = p.fee; entry = 1 + p.entry; ex = 1 + p.exit
    for i in range(n):
        o = ao[i]; c = ac[i]
        fee = fee0 if fee_arr is None else fee_arr[i]
        if i > 0 and p.cash:
            cash *= 1 + rf[i] / 252
        if i == 0:
            if mode == 'hold':
                pend = ('t', 1.0)
            elif mode == 'fixed':
                pend = ('t', w)
            elif mode == 'target' and w is not None and np.isfinite(w):
                pend = ('t', float(w))   # initial weight, decided by the caller before the window
        if pend is not None:
            kind, tgt = pend
            eq = cash + sh * o
            if kind == 'b':
                stage = int(tgt)
                need = max(0.0, eq * min(1.0, 0.2 * stage) - sh * o)
                no = min(need, cash / (1 + fee))
                if no > 1e-10:
                    f = no * fee; cash -= no + f; sh += no / o
                    orders.append((i, f'BUY_{stage}', o, no, f))
            else:
                if kind == 'x':
                    tgt = 0.0
                delta = eq * tgt - sh * o
                if delta > 1e-10:
                    no = min(delta, cash / (1 + fee)); f = no * fee
                    sh += no / o; cash -= no + f
                    orders.append((i, 'REBALANCE_BUY', o, no, f))
                elif delta < -1e-10:
                    no = min(-delta, sh * o); f = no * fee
                    sh -= no / o; cash += no - f
                    if kind == "x" and abs(sh) < 1e-9:
                        sh = 0.0
                    orders.append((i, 'SELL' if kind == 'x' else 'REBALANCE_SELL', o, no, f))
                if kind == 'x':
                    stage = 0
        v = cash + sh * c
        nav[i] = v; wt[i] = sh * c / v; shs[i] = sh; csh[i] = cash
        pend = None
        if mode == 'trend':
            m = sma[i]
            if m == m:  # not NaN
                s = sig[i]
                if sh > 0 and s < ex * m:
                    pend = ('x', 0)
                elif sh == 0 and s >= entry * m:
                    pend = ('b', 1)
                elif sh > 0 and stage < 5 and s >= entry * m:
                    pend = ('b', stage + 1)
        elif mode == 'fixed':
            if i % p.fixed_rebalance == p.fixed_rebalance - 1:
                pend = ('t', w)
        elif mode == 'target':
            if wpath is not None and np.isfinite(wpath[i]):
                pend = ('t', float(wpath[i]))
        elif mode == 'vol':
            if i % p.vol_rebalance == 0 and vol is not None:
                vv = vol[i]
                if vv == vv and vv > 0:
                    pend = ('t', min(1.0, p.vol_target / vv))
    return {'nav': nav, 'weight': wt, 'shares': shs, 'cash': csh, 'orders': orders}


def run(m: pd.DataFrame, start: str, mode: str = 'trend', p: Params = Params(), w: float = 1.0,
        end: str = END, unlevered: bool = False, fee_arr=None, wpath=None, rf=None):
    """fee_arr / wpath / rf: optional pd.Series aligned on m.index (sliced here)."""
    d = m.loc[start:end]
    sl = lambda x: None if x is None else pd.Series(x).reindex(d.index).to_numpy(dtype=float)
    if unlevered:
        ao, ac = d.signal_open.to_numpy(), d.signal_close.to_numpy()
    else:
        ao, ac = d.asset_open.to_numpy(), d.asset_close.to_numpy()
    rfa = d.rf.to_numpy() if rf is None else sl(rf)
    res = simulate(d.signal_close.to_numpy(), d.sma.to_numpy(), ao, ac, rfa,
                   mode, p, w, d.asset_vol.to_numpy() if 'asset_vol' in d else None,
                   fee_arr=sl(fee_arr), wpath=sl(wpath))
    eq = pd.DataFrame({'NAV': res['nav'], 'Weight': res['weight'], 'Shares': res['shares'],
                       'Cash': res['cash'], 'RFAnnual': rfa if p.cash else 0.0,
                       'Synthetic': d.synthetic.to_numpy()}, index=d.index)
    od = pd.DataFrame(res['orders'], columns=['i', 'Action', 'FillOpen', 'Notional', 'Fee'])
    od.insert(0, 'Date', d.index[od.i.to_numpy()] if len(od) else pd.DatetimeIndex([]))
    return eq, od.drop(columns='i')


# --------------------------------------------------------------------- metrics
def stats_from_nav(nav: np.ndarray, rf_daily: np.ndarray | None = None, weight=None) -> dict:
    nav = np.asarray(nav, float)
    ret = nav[1:] / nav[:-1] - 1
    ex = ret - (rf_daily[1:] if rf_daily is not None else 0.0)
    peak = np.maximum.accumulate(nav); dd = nav / peak - 1
    cagr = (nav[-1] / nav[0]) ** (252 / (len(nav) - 1)) - 1
    mdd = dd.min()
    q5 = np.quantile(ret, .05); q10 = np.quantile(dd, .10)
    uw = dd < 0
    longest = 0; run_ = 0
    for x in uw:
        run_ = run_ + 1 if x else 0; longest = max(longest, run_)
    sd = ex.std(ddof=1)
    # tail risk (daily, historical; reported as returns, i.e. negative numbers)
    q1 = np.quantile(ret, .01)
    t_trough = int(np.argmin(dd)); t_peak = int(np.argmax(nav[:t_trough + 1])) if t_trough > 0 else 0
    rec = np.nonzero(nav[t_trough:] >= peak[t_trough])[0]
    recovery = int(rec[0]) if len(rec) and rec[0] > 0 else (0 if mdd == 0 else np.nan)
    out = {'CAGR': cagr, 'MaxDrawdown': mdd,
           'VaR95': q5, 'VaR99': q1, 'ES95': ret[ret <= q5].mean(), 'ES99': ret[ret <= q1].mean(),
           'PeakToTroughDays': t_trough - t_peak, 'RecoveryDays': recovery, 'Calmar': cagr / abs(mdd) if mdd < 0 else np.nan,
           'Sharpe': ex.mean() / sd * np.sqrt(252) if sd > 0 else np.nan,
           'AnnualVol': ret.std(ddof=1) * np.sqrt(252),
           'CVaR5Daily': ret[ret <= q5].mean(), 'CDaR10': dd[dd <= q10].mean(),
           'UlcerIndex': float(np.sqrt(np.mean(dd ** 2))), 'MeanDrawdown': dd.mean(),
           'TimeUnderwater': uw.mean(), 'LongestUnderwaterDays': longest}
    if weight is not None:
        out['AverageWeight'] = float(np.mean(weight))
    return out


def metrics(eq: pd.DataFrame, orders: pd.DataFrame | None = None, capital=10000.0) -> dict:
    nav = np.r_[capital, eq.NAV.to_numpy()]   # CAGR/drawdown measured from initial cash
    rf = np.r_[0.0, eq.RFAnnual.to_numpy() / 252]
    r = stats_from_nav(nav, rf)
    r.update({'Start': str(eq.index[0].date()), 'End': str(eq.index[-1].date()),
              'NAVEnd': float(eq.NAV.iloc[-1]), 'AverageWeight': float(eq.Weight.mean()),
              'ExposedDaysFraction': float((eq.Shares > 0).mean()),
              'NumOrders': int(len(orders)) if orders is not None else 0,
              'FrictionPaid': float(orders.Fee.sum()) if orders is not None and len(orders) else 0.0})
    return r
