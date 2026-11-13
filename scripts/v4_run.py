"""v4: every analysis requested in the third-round review.

python scripts/v4_run.py                 # full run (~10 min; bootstraps dominate)
python scripts/v4_run.py --quick         # 100 path-bootstrap and 300 SPA replicates
Outputs: data/v4_results/*.csv, figures/v4/*.png, data/v4_results/run_manifest.json
"""
from __future__ import annotations
import argparse
import itertools
import json
import platform
import sys
import time
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine as E
from data_checks import validate_ohlcv, reversal_pairs, nyse_trading_days
from rates import annual_cash_rate

ROOT = E.ROOT
OUT = ROOT / 'data/v4_results'; FIG = ROOT / 'figures/v4'
SEED = 20260806
CAL = ('2010-02-12', '2026-07-31')
REAL, FULL = E.STARTS['real'], E.STARTS['full']
WLAB = {'real': 'REAL ETF 2010-02-11 to 2026-08-06',
        'full': 'HYPOTHETICAL: synthetic 3x before inception, 1999-12-22 to 2026-08-06'}
CRISES = {'Dot-com bear': ('2000-03-24', '2002-10-09'), 'Global financial crisis': ('2007-10-09', '2009-03-09'),
          'COVID crash': ('2020-02-19', '2020-03-23'), '2022 bear': ('2022-01-03', '2022-10-12')}
GRID_L = (150, 175, 200, 225, 250); GRID_EN = (0.02, 0.04, 0.06); GRID_EX = (-0.01, -0.03, -0.05)
PRIOR_W = 0.75     # ex-ante weight used only before one year of SMA-weight history exists
COL = {'SMA rule': '#0f6e7a', '3x hold': '#c0504d', '1x hold': '#4f6fa8', '1x SMA': '#8064a2',
       'Matched weight (ex ante)': '#7f7f7f', 'Vol target 30%': '#d98c1f', 'Matched weight (ex post)': '#bbbbbb'}


def save(df, name):
    df.to_csv(OUT / name, index=False, float_format='%.6f'); return df


# =============================================================== setup / P0
def setup():
    D = E.load_all(True)
    cal, mk = {}, {}
    for lev, und in E.PAIRS.items():
        cal[lev] = E.calibrate_spread(D[und], D[lev], *CAL)
        mk[lev] = E.add_signals(E.build_market(D[und], D[lev], cal[lev]['Spread_s']))
    return D, cal, mk


def p0_data(D):
    rows = []
    for t, d in D.items():
        rows += d.attrs['validation']
    val = pd.DataFrame(rows); save(val, 'data_validation.csv')
    raw = {t: pd.read_csv(ROOT / f'data/raw/{t}.csv', skiprows=[1, 2]).rename(columns={'Price': 'Date'})
           for t in D}
    man = []
    for t, d in D.items():
        r = raw[t]
        man.append({'Ticker': t, 'File': f'data/raw/{t}.csv', 'SHA256': d.attrs['sha256'], 'FirstBar': r.Date.iloc[0],
                    'LastBar': r.Date.iloc[-1], 'Rows': len(r), 'Columns': 'Date,Adj Close,Close,High,Low,Open,Volume',
                    'Vendor': 'Yahoo Finance (market prices, not NAV) via yfinance, auto_adjust=False',
                    'ObtainedFrom': 'github.com/hjyssg/tqqq_simulation',
                    'DownloadTimestamp': 'not recorded upstream; last bar 2026-08-06, so download >= 2026-08-06 '
                                         'close; files received by the author 2026-11-12. '
                                         'scripts/fetch_yahoo.py records the UTC timestamp on any re-download.'})
    save(pd.DataFrame(man), 'data_manifest.csv')
    rp = []
    for lev, und in E.PAIRS.items():
        x = reversal_pairs(D[lev].Close, D[und].Close); x.insert(0, 'Ticker', lev); rp.append(x)
    save(pd.concat(rp), 'tracking_outliers.csv')
    # official cross-checks (official values entered by hand from the cited issuer pages, retrieved 2026-11-12)
    s = pd.read_csv(ROOT / 'data/raw/SPXL.csv', skiprows=[1, 2]).rename(columns={'Price': 'Date'})
    s['Date'] = pd.to_datetime(s.Date); s = s.set_index('Date'); f = s['Adj Close'] / s.Close
    def implied_div(ex):
        i = s.index.get_loc(pd.Timestamp(ex)); return s.Close.iloc[i - 1] * (1 - f.iloc[i - 1] / f.iloc[i])
    tq_first = str(D['TQQQ'].index[0].date())
    off = [
        ('SPXL', 'Inception / first trading day', '2008-11-05 (Direxion)', str(D['SPXL'].index[0].date()), 'match'),
        ('SPXL', 'Market close 2025-02-27', '$163.55 market close; NAV $163.27 (Direxion)',
         f"${s.Close.loc['2025-02-27']:.2f}", 'Yahoo = market close, not NAV'),
        *[('SPXL', f'Distribution ex {ex}', f'${amt:.5f} (Direxion)', f'${implied_div(ex):.5f} implied by Adj Close',
           f'diff ${implied_div(ex) - amt:+.5f}')
          for ex, amt in [('2024-03-19', 0.39478), ('2024-06-25', 0.33671), ('2024-09-24', 0.19251), ('2024-12-23', 0.32070)]],
        ('SPXL', 'Large distribution 2009-11-20', 'not on current issuer page',
         'Close -12.4%, Adj Close -0.84% (SPY -0.36%)', 'price-only data would book a -12% loss'),
        ('TQQQ', 'Fund inception', '2010-02-09 (ProShares)', '-', '-'),
        ('TQQQ', 'First exchange trading day',
         '2010-02-11: Nasdaq release "began trading today" (GlobeNewswire, 11 Feb 2010); BATS circular IC 2010-012: UTP from 12 Feb',
         tq_first, 'match; Yahoo first bar = Nasdaq listing day'),
        ('TQQQ', 'Conflicting issuer statement', 'ProShares release 10 Feb 2025, fn. 5: performance measured "from first day of trading on Feb 10, 2010", based on NAV',
         '-', 'treated as NAV/performance start date, not the exchange listing; primary listing source preferred'),
        ('TQQQ', 'Since-inception total return', '41.02% p.a. NAV, 41.03% market, to 2026-10-31 (ProShares)',
         'sample ends 2026-08-06', 'not comparable; reconciliation pending'),
    ]
    save(pd.DataFrame(off, columns=['ETF', 'Item', 'Official', 'Yahoo / this study', 'Result']), 'official_checks.csv')
    return val


def p0_execution_audit(mk):
    """Perturb every price AFTER a cut date; all decisions and weights up to the cut must be unchanged."""
    rows = []
    for lev, m in mk.items():
        cut = pd.Timestamp('2018-06-29'); k = m.index.get_loc(cut)
        m2 = m.copy()
        for c in ('signal_open', 'signal_close', 'asset_open', 'asset_close'):
            m2.loc[m2.index > cut, c] *= np.linspace(1.5, 0.4, (m2.index > cut).sum())
        m2 = E.add_signals(m2.drop(columns=['sma', 'asset_vol']))
        wp1 = exante_wpath(m, REAL); wp2 = exante_wpath(m2, REAL)
        for name, kw in [('SMA rule', dict(mode='trend')), ('Vol target 30%', dict(mode='vol')),
                         ('Matched weight (ex ante)', dict(mode='target', wpath=wp1[0], w=wp1[1])),
                         ('1x SMA', dict(mode='trend', unlevered=True)), ('3x hold', dict(mode='hold'))]:
            kw2 = dict(kw)
            if name.startswith('Matched'):
                kw2.update(wpath=wp2[0], w=wp2[1])
            a, oa = E.run(m, REAL, **kw); b, ob = E.run(m2, REAL, **kw2)
            pre_a = a.loc[:cut]; pre_b = b.loc[:cut]
            same_w = np.allclose(pre_a.Weight, pre_b.Weight, atol=1e-12)
            same_o = oa[oa.Date <= cut].reset_index(drop=True).equals(ob[ob.Date <= cut].reset_index(drop=True))
            # next-open fills: every fill price equals that day's open
            px = m.signal_open if kw.get('unlevered') else m.asset_open
            fills_at_open = bool(np.allclose(oa.FillOpen.values, px.reindex(oa.Date).values)) if len(oa) else True
            rows.append({'ETF': lev, 'Rule': name, 'Decisions_unchanged_before_cut': bool(same_w and same_o),
                         'All_fills_at_that_days_open': fills_at_open, 'Orders': len(oa)})
    rows.append({'ETF': 'all', 'Rule': 'code inspection', 'Decisions_unchanged_before_cut': True,
                 'All_fills_at_that_days_open': True, 'Orders': 0})
    return save(pd.DataFrame(rows), 'execution_audit.csv')


# =============================================================== rules
def trailing_weights(w_hist, w_path, window=1260, minp=252):
    """Ex-ante matched weight: trailing mean (<=`window` days, >=`minp` days, else PRIOR_W)
    of the SMA rule's daily weights, history first. Returns (initial weight known before
    the first path day, array of the trailing weight known at each path close)."""
    w_hist = np.asarray(w_hist, float); W = np.r_[w_hist, np.asarray(w_path, float)]
    t = pd.Series(W).rolling(window, min_periods=minp).mean().to_numpy()
    nh = len(w_hist)
    init = float(t[nh - 1]) if nh and np.isfinite(t[nh - 1]) else PRIOR_W
    tp = t[nh:]
    return init, np.where(np.isfinite(tp), tp, PRIOR_W)


def wpath_from(tp, every=21):
    wp = np.full(len(tp), np.nan); k = np.arange(len(tp)) % every == every - 1; wp[k] = tp[k]; return wp


def sma_history_weights(m, start):
    """Daily weights of the SMA rule run from 1999-12-22 up to the day before `start` (empty if none)."""
    if pd.Timestamp(start) <= pd.Timestamp(FULL):
        return np.array([])
    prev = m.index[m.index.get_loc(pd.Timestamp(start)) - 1]
    return E.run(m, FULL, 'trend', end=str(prev.date()))[0].Weight.to_numpy()


def exante_wpath(m, start, end=E.END, every=21):
    """Same definition as in the path bootstrap: trailing mean of the weights the SMA rule
    actually held (pre-window history from the SMA rule run since 1999-12-22, then the
    in-window SMA run), known at close t and re-set every 21 sessions."""
    d = m.loc[start:end].index
    path = E.run(m, start, 'trend', end=end)[0].Weight.to_numpy()
    init, tp = trailing_weights(sma_history_weights(m, start), path)
    return pd.Series(wpath_from(tp, every), index=d), init


# ---------------------------------------------------------------- path engine
def prep_window(m, start, end=E.END):
    """Arrays describing a window as returns, plus the warm-up prefix, so that any
    re-ordering / deletion of days can be turned back into prices and re-simulated."""
    loc = m.index.get_loc(pd.Timestamp(start)); d = m.loc[:end].iloc[loc - 1:]; pre = m.iloc[max(0, loc - 1300):loc]
    wh = sma_history_weights(m, start)
    return dict(hs=pre.signal_close.values, ha=pre.asset_close.values,
                s0=d.signal_close.values[0], a0=d.asset_close.values[0],
                rs=d.signal_close.values[1:] / d.signal_close.values[:-1], os=d.signal_open.values[1:] / d.signal_close.values[:-1],
                ra=d.asset_close.values[1:] / d.asset_close.values[:-1], oa=d.asset_open.values[1:] / d.asset_close.values[:-1],
                rf=d.rf.values[1:], dates=d.index[1:], w_hist=wh, w_pre=float(wh.mean()) if len(wh) else None)


def path_rules(q, ix, p=E.Params()):
    """Rebuild prices from the selected days' returns (in the given order) and re-run every
    rule with its full state machine. Identical definitions to the main backtest."""
    rs, os_, ra, oa, rf = q['rs'][ix], q['os'][ix], q['ra'][ix], q['oa'][ix], q['rf'][ix]
    sc = q['s0'] * np.cumprod(rs); so = np.r_[q['s0'], sc[:-1]] * os_
    ac = q['a0'] * np.cumprod(ra); ao = np.r_[q['a0'], ac[:-1]] * oa
    nh, na = len(q['hs']), len(q['ha'])
    sma = pd.Series(np.r_[q['hs'], sc]).rolling(200).mean().to_numpy()[nh:]
    vol = pd.Series(np.r_[q['ha'], ac]).pct_change().rolling(63).std().to_numpy()[na:] * np.sqrt(252)
    sim = E.simulate
    runs = {'SMA rule': sim(sc, sma, ao, ac, rf, 'trend', p, 1.0, vol)}
    init, tp = trailing_weights(q['w_hist'], runs['SMA rule']['weight'])
    runs['3x hold'] = sim(sc, sma, ao, ac, rf, 'hold', p, 1.0, vol)
    runs['1x hold'] = sim(sc, sma, so, sc, rf, 'hold', p, 1.0, None)
    runs['1x SMA'] = sim(sc, sma, so, sc, rf, 'trend', p, 1.0, None)
    runs['Matched weight (ex ante)'] = sim(sc, sma, ao, ac, rf, 'target', p, init, vol, wpath=wpath_from(tp))
    runs['Vol target 30%'] = sim(sc, sma, ao, ac, rf, 'vol', p, 1.0, vol)
    if q['w_pre'] is not None:
        runs['Matched (pre-sample constant)'] = sim(sc, sma, ao, ac, rf, 'fixed', p, q['w_pre'], vol)
    return {k: E.stats_from_nav(np.r_[1e4, v['nav']], np.r_[0, rf / 252]) for k, v in runs.items()}


def path_consistency(mk, curves):
    """The path engine on the unmodified path must reproduce the main backtest exactly."""
    rows = []
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            q = prep_window(m, st); s = path_rules(q, np.arange(len(q['rs'])))
            for k, r in s.items():
                if k not in curves[(lev, per)]: continue
                ref = curves[(lev, per)][k][2]
                rows.append({'Window': per, 'ETF': lev, 'Rule': k, 'CAGR_main': ref['CAGR'], 'CAGR_path': r['CAGR'],
                             'MaxDD_main': ref['MaxDrawdown'], 'MaxDD_path': r['MaxDrawdown'],
                             'MaxAbsDiff': max(abs(ref['CAGR'] - r['CAGR']), abs(ref['MaxDrawdown'] - r['MaxDrawdown']))})
    df = save(pd.DataFrame(rows), 'path_engine_consistency.csv')
    assert df.MaxAbsDiff.max() < 1e-8, df.sort_values('MaxAbsDiff').tail()
    return df


def rules(m, start, end=E.END, p=E.Params(), fee=None, fee1x=None, rf=None, expost=True):
    out = {}
    e, o = E.run(m, start, 'trend', p, end=end, fee_arr=fee, rf=rf); out['SMA rule'] = (e, o)
    out['3x hold'] = E.run(m, start, 'hold', p, end=end, fee_arr=fee, rf=rf)
    out['1x hold'] = E.run(m, start, 'hold', p, end=end, unlevered=True, fee_arr=fee1x, rf=rf)
    out['1x SMA'] = E.run(m, start, 'trend', p, end=end, unlevered=True, fee_arr=fee1x, rf=rf)
    wp, w0 = exante_wpath(m, start, end)
    out['Matched weight (ex ante)'] = E.run(m, start, 'target', p, w=w0, end=end, wpath=wp, fee_arr=fee, rf=rf)
    out['Vol target 30%'] = E.run(m, start, 'vol', p, end=end, fee_arr=fee, rf=rf)
    if expost:
        w = E.metrics(e, o)['AverageWeight']
        out['Matched weight (ex post)'] = E.run(m, start, 'fixed', p, w=w, end=end, fee_arr=fee, rf=rf)
    return {k: (e, o, E.metrics(e, o)) for k, (e, o) in out.items()}


def main_tables(mk):
    rows, curves = [], {}
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            res = rules(m, st); curves[(lev, per)] = res
            for k, (e, o, r) in res.items():
                rows.append({'Window': per, 'SampleType': 'real' if per == 'real' else 'hypothetical',
                             'ETF': lev, 'Rule': k, **r})
    save(pd.DataFrame(rows), 'main_metrics.csv')
    return curves


# =============================================================== P1: walk-forward
def grid_runs(m, start):
    runs = {}
    for L, en, ex in itertools.product(GRID_L, GRID_EN, GRID_EX):
        mm = m.copy(); mm['sma'] = mm.signal_close.rolling(L, min_periods=L).mean()
        e, o = E.run(mm, start, 'trend', replace(E.Params(), sma_days=L, entry=en, exit=ex))
        runs[(L, en, ex)] = (e, o)
    return runs


def _metric(nav, rf, crit):
    s = E.stats_from_nav(np.asarray(nav), np.asarray(rf))
    return s['Calmar'] if crit == 'Calmar' else s['Sharpe']


def walk_forward(mk, runs_by, train_years=5, crits=('Calmar', 'Sharpe')):
    rows, sel_rows, curves = [], [], {}
    vts = np.round(np.arange(0.10, 1.0001, 0.05), 2)
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            runs = runs_by[(lev, per)]
            d = m.loc[st:]; years = sorted(set(d.index.year))
            first_test = years[0] + train_years if d.index[0].month <= 2 else years[0] + train_years + 1
            tests = [y for y in years if y >= first_test]
            rets = {k: e.NAV.pct_change().fillna(e.NAV.iloc[0] / 1e4 - 1) for k, (e, o) in runs.items()}
            wts = {k: e.Weight for k, (e, o) in runs.items()}
            rfd = d.rf / 252
            vol_runs = {vt: E.run(m, st, 'vol', replace(E.Params(), vol_target=vt))[0] for vt in vts}
            for crit in crits:
                chain = []; wf_w = pd.Series(np.nan, index=d.index); wf_vt = pd.Series(np.nan, index=d.index)
                prev = None
                for y in tests:
                    tr = d.index[(d.index.year >= y - train_years) & (d.index.year < y)]
                    te = d.index[d.index.year == y]
                    best = max(runs, key=lambda k: _metric(np.r_[1, (1 + rets[k].loc[tr]).cumprod()],
                                                             np.r_[0, rfd.loc[tr]], crit))
                    r = rets[best].loc[te].copy()
                    if prev is not None and prev != best:   # switching cost at the year's first open
                        r.iloc[0] -= E.Params().fee * abs(wts[best].loc[tr[-1]] - wts[prev].loc[tr[-1]])
                    chain.append(r); prev = best
                    wbar = float(wts[best].loc[tr].mean())
                    vt = min(vts, key=lambda v: abs(vol_runs[v].Weight.loc[tr].mean() - wbar))
                    wf_w.loc[te] = wbar; wf_vt.loc[te] = vt
                    sel_rows.append({'Window': per, 'ETF': lev, 'Criterion': crit, 'TestYear': y,
                                     'SMA': best[0], 'Entry': best[1], 'Exit': best[2], 'TrainAvgWeight': wbar,
                                     'MatchedVolTarget': vt})
                oos = pd.concat(chain); t0 = oos.index[0]; oos_end = oos.index[-1]
                curves_k = {'Walk-forward SMA': 1e4 * (1 + oos).cumprod()}
                base = rets[(200, 0.04, -0.03)].loc[t0:]; curves_k['Fixed 200/+4/-3'] = 1e4 * (1 + base).cumprod()
                # ex-ante benchmarks, continuous simulations over the test span
                reb = pd.Series(np.nan, index=m.index); idx = d.loc[t0:].index
                ystart = idx[np.r_[True, idx.year[1:] != idx.year[:-1]]]
                pos = np.arange(len(idx)); rb = idx[(pos % 21 == 20)]
                for day in rb: reb.loc[day] = wf_w.loc[day]
                for day in ystart[1:]:
                    prior = idx[idx.get_loc(day) - 1]; reb.loc[prior] = wf_w.loc[day]
                e1, _ = E.run(m, str(t0.date()), 'target', w=float(wf_w.loc[t0]), wpath=reb)
                curves_k['WF matched weight'] = e1.NAV
                vpath = pd.Series(np.nan, index=m.index)
                vv = (wf_vt.loc[idx] / m.asset_vol.loc[idx]).clip(upper=1.0)
                vpath.loc[idx[pos % 5 == 0]] = vv.loc[idx[pos % 5 == 0]]
                e2, _ = E.run(m, str(t0.date()), 'target', w=float(min(1, wf_vt.loc[t0] / m.asset_vol.shift(1).loc[t0])),
                              wpath=vpath)
                curves_k['WF vol target'] = e2.NAV
                for nm, mode, kw in [('3x hold', 'hold', {}), ('1x hold', 'hold', {'unlevered': True}),
                                     ('1x SMA', 'trend', {'unlevered': True})]:
                    curves_k[nm] = E.run(m, str(t0.date()), mode, **kw)[0].NAV
                rfo = d.rf.loc[t0:] / 252
                for nm, nav in curves_k.items():
                    s = E.stats_from_nav(np.r_[1e4, nav.loc[t0:].values], np.r_[0, rfo.values])
                    rows.append({'Window': per, 'SampleType': 'real' if per == 'real' else 'hypothetical', 'ETF': lev,
                                 'Criterion': crit, 'OOS_start': str(t0.date()), 'OOS_end': str(oos_end.date()),
                                 'Rule': nm, **s})
                curves[(lev, per, crit)] = curves_k
    save(pd.DataFrame(sel_rows), 'walkforward_selections.csv')
    save(pd.DataFrame(rows), 'walkforward_metrics.csv')
    return curves


# =============================================================== P1: LOCO
def crisis_return_removal(curves):
    """Crisis-contribution decomposition: drop crisis days from returns already computed
    on the full path (positions NOT re-simulated). Kept as a secondary, labelled analysis."""
    rows = []
    for (lev, per), res in curves.items():
        cr = {k: v for k, v in CRISES.items() if per == 'full' or pd.Timestamp(v[0]) >= pd.Timestamp(REAL)}
        variants = [('none excluded', [])] + [(k, [k]) for k in cr] + [('all listed excluded', list(cr))]
        for label, keys in variants:
            for ext in (0, 252):
                if not keys and ext: continue
                for rule, (e, o, _) in res.items():
                    if rule == 'Matched weight (ex post)': continue
                    r = e.NAV.pct_change().fillna(e.NAV.iloc[0] / 1e4 - 1); rf = e.RFAnnual / 252
                    keep = pd.Series(True, index=r.index)
                    for k in keys:
                        a, b = pd.Timestamp(cr[k][0]), pd.Timestamp(cr[k][1])
                        if ext:
                            j = r.index.searchsorted(b); b = r.index[min(j + ext, len(r) - 1)]
                        keep &= ~((r.index >= a) & (r.index <= b))
                    s = E.stats_from_nav(np.r_[1, (1 + r[keep]).cumprod().values], np.r_[0, rf[keep].values])
                    rows.append({'Window': per, 'ETF': lev, 'Excluded': label,
                                 'ExclusionSpan': 'decline only' if not ext else 'decline + 252 days after trough',
                                 'DaysKept': int(keep.sum()), 'Rule': rule, 'CAGR': s['CAGR'],
                                 'MaxDrawdown': s['MaxDrawdown'], 'Calmar': s['Calmar'], 'Sharpe': s['Sharpe']})
    return save(pd.DataFrame(rows), 'crisis_contribution_returns_removed.csv')


def loco_rerun(mk):
    """True leave-one-crisis-out: delete the crisis days from the input return series,
    splice the remaining days into a new price path, and re-run every rule from scratch
    (SMA, stages, vol estimates and ex-ante weights are all recomputed on the spliced path)."""
    rows = []
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            q = prep_window(m, st); dates = q['dates']; n = len(dates)
            cr = {k: v for k, v in CRISES.items() if per == 'full' or pd.Timestamp(v[0]) >= pd.Timestamp(REAL)}
            variants = [('none excluded', [])] + [(k, [k]) for k in cr] + [('all listed excluded', list(cr))]
            for label, keys in variants:
                for ext in (0, 252):
                    if not keys and ext: continue
                    keep = np.ones(n, bool)
                    for k in keys:
                        a, b = pd.Timestamp(cr[k][0]), pd.Timestamp(cr[k][1])
                        j = dates.searchsorted(b, side='right') - 1
                        b = dates[min(j + ext, n - 1)]
                        keep &= ~((dates >= a) & (dates <= b))
                    res = path_rules(q, np.flatnonzero(keep))
                    for rule, r in res.items():
                        rows.append({'Window': per, 'SampleType': 'real' if per == 'real' else 'hypothetical', 'ETF': lev,
                                     'Excluded': label, 'ExclusionSpan': '—' if not keys else ('decline only' if not ext else 'decline + 252 days after trough'),
                                     'DaysKept': int(keep.sum()), 'Rule': rule, 'CAGR': r['CAGR'], 'MaxDrawdown': r['MaxDrawdown'],
                                     'Calmar': r['Calmar'], 'Sharpe': r['Sharpe']})
    return save(pd.DataFrame(rows), 'leave_one_crisis_out.csv')


# =============================================================== P1: parameters + SPA
def param_table(mk, runs_by, curves):
    rows = []
    for (lev, per), runs in runs_by.items():
        ref = {k: curves[(lev, per)][k][2] for k in ('Matched weight (ex ante)', 'Vol target 30%', '1x hold', '3x hold')}
        for (L, en, ex), (e, o) in runs.items():
            r = E.metrics(e, o)
            rows.append({'Window': per, 'ETF': lev, 'SMA': L, 'Entry': en, 'Exit': ex, 'Baseline': (L, en, ex) == (200, .04, -.03),
                         'CAGR': r['CAGR'], 'MaxDrawdown': r['MaxDrawdown'], 'Calmar': r['Calmar'], 'Sharpe': r['Sharpe'],
                         'ES99': r['ES99'], 'AverageWeight': r['AverageWeight'], 'Orders': r['NumOrders'],
                         **{f'Beats_{k.split(" (")[0].replace(" ", "")}_Calmar': r['Calmar'] > v['Calmar'] for k, v in ref.items()},
                         **{f'Beats_{k.split(" (")[0].replace(" ", "")}_Sharpe': r['Sharpe'] > v['Sharpe'] for k, v in ref.items()}})
    return save(pd.DataFrame(rows), 'parameter_grid.csv')


def stationary_idx(n, L, rng):
    starts = rng.integers(0, n, n); newblk = rng.random(n) < 1.0 / L; newblk[0] = True
    idx = np.empty(n, dtype=np.int64); j = 0
    for t in range(n):
        j = starts[t] if newblk[t] else (j + 1) % n
        idx[t] = j
    return idx


def spa_tests(runs_by, curves, reps, L=63):
    """White (2000) Reality Check and Hansen (2005) SPA_c on all 45 SMA configurations
    against each benchmark, real-ETF window. Two loss functions: raw daily return
    differential, and differential after scaling each configuration to the benchmark's volatility."""
    rng = np.random.default_rng(SEED + 1); rows = []
    for lev in ('SPXL', 'TQQQ'):
        runs = runs_by[(lev, 'real')]
        R = np.column_stack([e.NAV.pct_change().fillna(e.NAV.iloc[0] / 1e4 - 1).values for e, o in runs.values()])
        n = R.shape[0]; idxs = [stationary_idx(n, L, rng) for _ in range(reps)]
        for bname in ('1x hold', 'Vol target 30%', 'Matched weight (ex ante)', '3x hold'):
            b = curves[(lev, 'real')][bname][0].NAV; b = b.pct_change().fillna(b.iloc[0] / 1e4 - 1).values
            for kind in ('raw return', 'volatility-matched'):
                X = R * (b.std() / R.std(axis=0)) if kind == 'volatility-matched' else R
                Dm = X - b[:, None]; dbar = Dm.mean(axis=0)
                boot = np.array([Dm[ix].mean(axis=0) for ix in idxs])            # reps x K
                omega = boot.std(axis=0) * np.sqrt(n)
                V = np.sqrt(n) * dbar.max(); Vb = np.sqrt(n) * (boot - dbar).max(axis=1)
                p_rc = float((Vb >= V).mean())
                T = max(0.0, (np.sqrt(n) * dbar / omega).max())
                thr = -np.sqrt(omega ** 2 / n * 2 * np.log(np.log(n)))
                mu_c = np.where(dbar >= thr, dbar, 0.0)
                Tb = np.maximum(0, (np.sqrt(n) * (boot - mu_c) / omega).max(axis=1))
                p_spa = float((Tb >= T).mean())
                k = int(np.argmax(dbar)); best = list(runs)[k]
                rows.append({'ETF': lev, 'Benchmark': bname, 'Loss': kind, 'Configs': R.shape[1], 'Reps': reps,
                             'MeanBlock': L, 'BestConfig': f'{best[0]}/{best[1]:+.0%}/{best[2]:+.0%}',
                             'BestAnnualDiff': 252 * dbar[k], 'BaselineAnnualDiff': 252 * dbar[list(runs).index((200, .04, -.03))],
                             'p_RealityCheck': p_rc, 'p_SPA_c': p_spa})
    return save(pd.DataFrame(rows), 'spa_reality_check.csv')


# =============================================================== P1: path bootstrap
def path_bootstrap(mk, reps, blocks=(63, 252)):
    """Stationary bootstrap of the joint daily return vector (both ETF pairs share the
    indices); every rule, including the ex-ante matched weight (same definition as the
    main backtest), is re-run on every pseudo path with path_rules().

    Test of H0: Delta = 0 for Delta = metric(SMA) - metric(benchmark). Following Hall and
    Wilson (1991) the bootstrap distribution is centred at the observed Delta to mimic
    the null: p = P*(|Delta* - Delta_obs| >= |Delta_obs|). Percentile intervals and the
    share of Delta* > 0 are reported as descriptive statistics only."""
    rng = np.random.default_rng(SEED)
    Q = {lev: prep_window(m, REAL) for lev, m in mk.items()}
    n = len(Q['SPXL']['rs']); assert n == len(Q['TQQQ']['rs'])
    obs = {lev: path_rules(q, np.arange(n)) for lev, q in Q.items()}
    rows = []
    for L in blocks:
        for b in range(reps):
            ix = stationary_idx(n, L, rng)
            for lev, q in Q.items():
                rec = {'Block': L, 'Rep': b, 'ETF': lev}
                for rule, s in path_rules(q, ix).items():
                    for k in ('CAGR', 'MaxDrawdown', 'Calmar', 'Sharpe', 'ES99', 'CDaR10'):
                        rec[f'{rule}|{k}'] = s[k]
                rows.append(rec)
    bs = pd.DataFrame(rows); bs.to_csv(OUT / 'bootstrap_paths.csv', index=False, float_format='%.6f')
    summ = []
    vs_list = ['3x hold', '1x hold', '1x SMA', 'Matched weight (ex ante)', 'Vol target 30%', 'Matched (pre-sample constant)']
    for (L, lev), g in bs.groupby(['Block', 'ETF']):
        for vs in vs_list:
            for k in ('CAGR', 'MaxDrawdown', 'Calmar', 'Sharpe', 'ES99'):
                dl = (g[f'SMA rule|{k}'] - g[f'{vs}|{k}']).to_numpy()
                d0 = obs[lev]['SMA rule'][k] - obs[lev][vs][k]
                p_c = float(np.mean(np.abs(dl - d0) >= abs(d0)))
                lo, hi = np.quantile(dl, [.025, .975])
                summ.append({'MeanBlockDays': L, 'ETF': lev, 'Versus': vs, 'Metric': k, 'Reps': len(g),
                             'Observed': d0, 'BootMedian': float(np.median(dl)), 'CI2_5': lo, 'CI97_5': hi,
                             'SharePositive': float((dl > 0).mean()), 'p_centred': p_c,
                             'Reading': 'significant at 5%' if p_c < 0.05 else 'not significant at 5%'})
    return bs, save(pd.DataFrame(summ), 'bootstrap_summary.csv')


# =============================================================== P1: costs
def cost_arrays(m, scen):
    """Per-day one-way cost for the 3x ETF and for the 1x signal ETF."""
    idx = m.index
    sig_vol = (m.signal_close.pct_change().rolling(20).std() * np.sqrt(252)).bfill()
    lev_vol = (m.asset_close.pct_change().rolling(20).std() * np.sqrt(252)).bfill()
    if scen['kind'] == 'flat':
        return pd.Series(scen['bp'] / 1e4, index=idx), pd.Series(scen['bp'] / 1e4, index=idx)
    hs = pd.Series(0.0005, index=idx); hs[idx >= '2015-01-01'] = 0.0002; hs[idx >= '2020-01-01'] = 0.0001
    lev = hs + 0.0005 + 0.001 * lev_vol            # half-spread by era + open-auction slippage rising with vol
    one = 0.0001 + 0.0002 + 0.001 * sig_vol
    k = scen.get('mult', 1.0)
    return lev * k, one * k


def costs(mk):
    scen = [('Flat 10 bp (baseline)', dict(kind='flat', bp=10), 0.0, True),
            ('Flat 25 bp', dict(kind='flat', bp=25), 0.0, True),
            ('Era spread + vol-scaled slippage', dict(kind='model'), 0.0, True),
            ('Same, x3 stress', dict(kind='model', mult=3.0), 0.0, True),
            ('Model costs, cash = T-bill - 10 bp', dict(kind='model'), 0.001, True),
            ('Model costs, cash = 0%', dict(kind='model'), None, False)]
    rows = []
    for lev, m in mk.items():
        for label, sc, hair, cash in scen:
            fee, fee1 = cost_arrays(m, sc)
            rf = None if hair is None else (m.rf - hair).clip(lower=-0.01)
            p = replace(E.Params(), cash=cash)
            res = rules(m, REAL, p=p, fee=fee, fee1x=fee1, rf=rf, expost=False)
            for k, (e, o, r) in res.items():
                rows.append({'ETF': lev, 'Scenario': label, 'Rule': k, 'CAGR': r['CAGR'], 'MaxDrawdown': r['MaxDrawdown'],
                             'Calmar': r['Calmar'], 'Sharpe': r['Sharpe'], 'Orders': r['NumOrders'],
                             'FrictionPaid': r['FrictionPaid'],
                             'MeanCostPerFill_bp': 1e4 * (o.Fee.sum() / o.Notional.sum()) if len(o) else np.nan})
    return save(pd.DataFrame(rows), 'cost_scenarios.csv')


# =============================================================== P1: synthetic stress
def synthetic_stress(D, cal, mc=50):
    rows = []
    shock = pd.Series(0.0, index=D['SPY'].index)
    for a, b in (CRISES['Dot-com bear'], CRISES['Global financial crisis']):
        shock.loc[a:b] = 0.03
    for lev, und in E.PAIRS.items():
        s0 = cal[lev]['Spread_s']; te0 = cal[lev]['ResidualDailyStd_bp'] / 1e4
        scen = [('Base (calibrated)', dict(s=s0), 1), ('s = 0', dict(s=0.0), 1), ('s = 2x', dict(s=2 * s0), 1),
                ('s = 4x', dict(s=4 * s0), 1), ('expense 0.75%', dict(s=s0, expense=0.0075), 1),
                ('expense 1.25%', dict(s=s0, expense=0.0125), 1), ('realised leverage 2.9', dict(s=s0, leverage=2.9), 1),
                ('realised leverage 3.1', dict(s=s0, leverage=3.1), 1),
                ('+300 bp funding shock in 2000-02 and 2007-09', dict(s=s0, extra_spread=shock), 1),
                ('tracking noise = observed', dict(s=s0, te_daily=te0), mc),
                ('tracking noise = 2x observed', dict(s=s0, te_daily=2 * te0), mc),
                ('Pessimistic: 2x s, 1.25% fee, shock, 2x noise',
                 dict(s=2 * s0, expense=0.0125, extra_spread=shock, te_daily=2 * te0), mc)]
        for label, kw, n in scen:
            res = []
            for j in range(n):
                syn = E.synthetic_3x_stress(D[und].loc[E.UNIVERSE_START:], seed=SEED + j, **kw)
                m = E.add_signals(E.build_market(D[und], D[lev], s0, syn=syn))
                rr = {}
                for nm, mode, kw2 in [('SMA rule', 'trend', {}), ('3x hold', 'hold', {}), ('Vol target 30%', 'vol', {})]:
                    e, o = E.run(m, FULL, mode, **kw2); r = E.metrics(e, o)
                    nav = e.NAV
                    sub = {c: float(nav.loc[:CRISES[c][1]].iloc[-1] / nav.loc[:CRISES[c][0]].iloc[-1] - 1)
                           for c in ('Dot-com bear', 'Global financial crisis')}
                    rr[nm] = (r['CAGR'], r['MaxDrawdown'], r['Calmar'], sub['Dot-com bear'], sub['Global financial crisis'])
                res.append(rr)
            for nm in ('SMA rule', '3x hold', 'Vol target 30%'):
                arr = np.array([x[nm] for x in res])
                rows.append({'ETF': lev, 'Scenario': label, 'Paths': n, 'Rule': nm,
                             'CAGR': np.median(arr[:, 0]), 'CAGR_p5': np.quantile(arr[:, 0], .05), 'CAGR_p95': np.quantile(arr[:, 0], .95),
                             'MaxDrawdown': np.median(arr[:, 1]), 'Calmar': np.median(arr[:, 2]),
                             'Return_DotCom': np.median(arr[:, 3]), 'Return_GFC': np.median(arr[:, 4])})
    return save(pd.DataFrame(rows), 'synthetic_stress.csv')


# =============================================================== P2: mechanism + states
def mechanism(curves):
    rows, by = [], []
    for (lev, per), res in curves.items():
        r = {k: res[k][0].NAV.pct_change().fillna(res[k][0].NAV.iloc[0] / 1e4 - 1) for k in res}
        lg = {k: np.log1p(v) for k, v in r.items()}
        g = {k: 252 * lg[k].mean() for k in r}; mu = {k: 252 * r[k].mean() for k in r}; v = {k: 252 * r[k].var() for k in r}
        def split(a, b):
            return {'LogGrowthDiff': g[a] - g[b], 'MeanReturnPart': mu[a] - mu[b], 'VarianceDragPart': -0.5 * (v[a] - v[b]),
                    'HigherOrderResidual': (g[a] - g[b]) - (mu[a] - mu[b]) + 0.5 * (v[a] - v[b])}
        for lab, a, b in [('Total: SMA vs 3x hold', 'SMA rule', '3x hold'),
                          ('Exposure effect: matched (ex post) vs 3x hold', 'Matched weight (ex post)', '3x hold'),
                          ('Timing effect: SMA vs matched (ex post)', 'SMA rule', 'Matched weight (ex post)'),
                          ('SMA vs vol target 30%', 'SMA rule', 'Vol target 30%'),
                          ('SMA (3x) vs 1x hold', 'SMA rule', '1x hold'),
                          ('Leverage given SMA: SMA 3x vs SMA 1x', 'SMA rule', '1x SMA')]:
            rows.append({'Window': per, 'ETF': lev, 'Comparison': lab, **split(a, b)})
        # timing effect by SMA state at previous close and by crisis periods
        w = res['SMA rule'][0].Weight.shift(1).fillna(0)
        dlt = lg['SMA rule'] - lg['Matched weight (ex post)']
        state = pd.Series(np.where(w < 1e-9, 'out (cash)', np.where(w < 0.95, 'partial', 'fully invested')), index=w.index)
        crisis = pd.Series('no crisis', index=w.index)
        for k, (a, b) in CRISES.items():
            crisis[(crisis.index >= a) & (crisis.index <= b)] = k
        years = len(dlt) / 252
        for lab, grp in (('SMA state at t-1', state), ('Crisis window', crisis)):
            for k, x in dlt.groupby(grp):
                by.append({'Window': per, 'ETF': lev, 'Grouping': lab, 'Group': k, 'Days': len(x),
                           'Contribution_pp_per_year': 100 * x.sum() / years})
    save(pd.DataFrame(by), 'mechanism_by_state.csv')
    return save(pd.DataFrame(rows), 'mechanism_decomposition.csv')


def nw_t(x, lags=10):
    """Newey-West t-statistic of the mean of x."""
    x = np.asarray(x, float); n = len(x)
    if n < 30: return np.nan
    mu = x.mean(); z = x - mu; s = z @ z / n
    for l in range(1, lags + 1):
        s += 2 * (1 - l / (lags + 1)) * (z[l:] @ z[:-l] / n)
    return mu / np.sqrt(s / n) if s > 0 else np.nan


def state_groups(mk, curves):
    rows = []
    for (lev, per), res in curves.items():
        m = mk[lev].loc[res['SMA rule'][0].index]
        sig = mk[lev].signal_close
        trend = np.where(sig >= mk[lev].sma, 'above SMA200', 'below SMA200')
        vol = sig.pct_change().rolling(20).std() * np.sqrt(252)
        volb = pd.cut(vol, [-1, 0.15, 0.25, 9], labels=['vol < 15%', 'vol 15-25%', 'vol > 25%']).astype(str)
        hi = sig.rolling(252, min_periods=20).max()
        last = sig.eq(hi)
        since = last.groupby(last.cumsum()).cumcount()
        ddb = pd.cut(since, [-1, 20, 120, 10 ** 6], labels=['<=20 d since 1y high', '21-120 d', '>120 d']).astype(str)
        cond = pd.DataFrame({'Trend': pd.Series(trend, index=sig.index), 'Volatility': volb, 'Drawdown duration': ddb}).shift(1)
        cond = cond.reindex(m.index)
        r = {k: res[k][0].NAV.pct_change().fillna(0) for k in res}
        for bench in ('Matched weight (ex ante)', 'Vol target 30%', '1x hold', '3x hold'):
            dlt = r['SMA rule'] - r[bench]
            for dim in cond.columns:
                for k, x in dlt.groupby(cond[dim]):
                    if k == 'nan': continue
                    rows.append({'Window': per, 'ETF': lev, 'Versus': bench, 'Dimension': dim, 'State': k, 'Days': len(x),
                                 'AnnualisedMeanDiff': 252 * x.mean(), 'NeweyWest_t': nw_t(x.values)})
    return save(pd.DataFrame(rows), 'state_conditional.csv')


# =============================================================== frontier (ex post, descriptive)
def frontier(mk, curves):
    rows, gaps = [], []
    ws = np.round(np.arange(0.1, 1.0001, 0.05), 2); vts = np.round(np.arange(0.10, 1.0001, 0.05), 2)
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            fam = {'fixed weight': [], 'vol target': []}
            for w in ws:
                e, o = E.run(m, st, 'fixed', w=w); r = E.metrics(e, o); fam['fixed weight'].append(r)
                rows.append({'Window': per, 'ETF': lev, 'Family': 'fixed weight', 'Param': w, **r})
            for vt in vts:
                e, o = E.run(m, st, 'vol', replace(E.Params(), vol_target=vt)); r = E.metrics(e, o); fam['vol target'].append(r)
                rows.append({'Window': per, 'ETF': lev, 'Family': 'vol target', 'Param': vt, **r})
            for rule in ('SMA rule', '1x hold', '1x SMA'):
                s = curves[(lev, per)][rule][2]
                for f, rs in fam.items():
                    for risk in ('MaxDrawdown', 'CDaR10', 'UlcerIndex', 'ES99'):
                        x = np.array([abs(r[risk]) for r in rs]); y = np.array([r['CAGR'] for r in rs]); o_ = np.argsort(x)
                        x, y = x[o_], y[o_]; t = abs(s[risk]); inside = x[0] <= t <= x[-1]
                        gaps.append({'Window': per, 'ETF': lev, 'Rule': rule, 'Family': f, 'RiskMeasure': risk,
                                     'Rule_risk': t, 'Rule_CAGR': s['CAGR'],
                                     'Frontier_CAGR': float(np.interp(t, x, y)) if inside else np.nan,
                                     'Gap_pp': 100 * (s['CAGR'] - np.interp(t, x, y)) if inside else np.nan})
    return save(pd.DataFrame(rows), 'frontier_points.csv'), save(pd.DataFrame(gaps), 'frontier_gap.csv')


# =============================================================== figures
def figures(curves, fr, bsum, wfc, grid, mk):
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
    show = ['SMA rule', '3x hold', '1x hold', '1x SMA', 'Matched weight (ex ante)', 'Vol target 30%']
    for per in ('real', 'full'):
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
        for a, lev in zip(ax, ('SPXL', 'TQQQ')):
            for k in show:
                e = curves[(lev, per)][k][0]
                a.plot(e.index, e.NAV / 1e4, color=COL[k], lw=1.9 if k == 'SMA rule' else 1.0, label=k)
            if per == 'full':
                a.axvspan(e.index[0], pd.Timestamp(E.INCEPTION[lev]), color='k', alpha=.07, lw=0)
            a.set_yscale('log'); a.grid(alpha=.2); a.set_title(f'{E.PAIRS[lev]} signal -> {lev}')
        ax[0].legend(fontsize=7.5, frameon=False); ax[0].set_ylabel('Growth of $1 (log)')
        fig.suptitle(WLAB[per] + (' (shaded = synthetic)' if per == 'full' else '')); fig.tight_layout()
        fig.savefig(FIG / f'equity_{per}.png', dpi=170); plt.close(fig)
    fig, ax = plt.subplots(2, 1, figsize=(12, 6.2), sharex=True)
    for a, lev in zip(ax, ('SPXL', 'TQQQ')):
        for k in ('3x hold', 'Vol target 30%', '1x hold', 'SMA rule'):
            e = curves[(lev, 'real')][k][0]; nav = np.r_[1e4, e.NAV.values]
            a.plot(e.index, 100 * (nav / np.maximum.accumulate(nav) - 1)[1:], color=COL[k], lw=1.5 if k == 'SMA rule' else .9, label=k)
        a.set_ylabel(f'{lev} drawdown, %'); a.grid(alpha=.2)
    ax[0].legend(fontsize=8, frameon=False, ncol=4); fig.suptitle('Daily drawdowns - ' + WLAB['real'])
    fig.tight_layout(); fig.savefig(FIG / 'drawdown_real.png', dpi=170); plt.close(fig)
    fig, ax = plt.subplots(2, 1, figsize=(12, 6.2), sharex=True)
    for a, lev in zip(ax, ('SPXL', 'TQQQ')):
        for k in ('SMA rule', '3x hold', '1x hold', 'Vol target 30%'):
            e = curves[(lev, 'real')][k][0]; r = e.NAV.pct_change() - e.RFAnnual / 252
            rs = r.rolling(252).mean() / r.rolling(252).std() * np.sqrt(252)
            a.plot(e.index, rs, color=COL[k], lw=1.5 if k == 'SMA rule' else .9, label=k)
        a.axhline(0, color='k', lw=.6); a.set_ylabel(f'{lev} rolling 1y Sharpe'); a.grid(alpha=.2)
    ax[0].legend(fontsize=8, frameon=False, ncol=4); fig.suptitle('Rolling 252-day Sharpe ratio - ' + WLAB['real'])
    fig.tight_layout(); fig.savefig(FIG / 'rolling_sharpe_real.png', dpi=170); plt.close(fig)
    fig, ax = plt.subplots(2, 2, figsize=(11, 8.2))
    for i, per in enumerate(('real', 'full')):
        for j, lev in enumerate(('SPXL', 'TQQQ')):
            a = ax[i, j]
            for f, c in (('fixed weight', '#7f7f7f'), ('vol target', '#d98c1f')):
                g = fr[(fr.Window == per) & (fr.ETF == lev) & (fr.Family == f)].sort_values('Param')
                a.plot(-100 * g.MaxDrawdown, 100 * g.CAGR, '-o', ms=2.3, color=c, lw=1.1, label=f + ' frontier (ex post)')
            for k, mkr in (('SMA rule', '*'), ('1x hold', 'o'), ('1x SMA', 's'), ('Matched weight (ex ante)', 'D')):
                r = curves[(lev, per)][k][2]
                a.scatter(-100 * r['MaxDrawdown'], 100 * r['CAGR'], color=COL[k], marker=mkr, s=70 if mkr == '*' else 30, zorder=5, label=k)
            a.set_title(f"{lev} - {'REAL ETF 2010-2026' if per == 'real' else 'HYPOTHETICAL 1999-2026'}")
            a.set_xlabel('Max daily drawdown, %'); a.set_ylabel('CAGR, %'); a.grid(alpha=.2)
    ax[0, 0].legend(fontsize=7, frameon=False); fig.tight_layout(); fig.savefig(FIG / 'frontier.png', dpi=170); plt.close(fig)
    fig, ax = plt.subplots(2, 3, figsize=(12, 6.4))
    for i, lev in enumerate(('SPXL', 'TQQQ')):
        for j, ex in enumerate(GRID_EX):
            g = grid[(grid.Window == 'real') & (grid.ETF == lev) & (grid.Exit == ex)]
            mat = g.pivot(index='Entry', columns='SMA', values='Calmar').sort_index()
            a = ax[i, j]; im = a.imshow(mat.values, origin='lower', cmap='viridis', aspect='auto', vmin=0.2, vmax=0.6)
            a.set_xticks(range(len(mat.columns)), mat.columns); a.set_yticks(range(len(mat.index)), [f'+{100*x:.0f}%' for x in mat.index])
            for (r_, c_), v in np.ndenumerate(mat.values):
                base = (mat.columns[c_] == 200 and mat.index[r_] == .04 and ex == -.03)
                a.text(c_, r_, f'{v:.2f}' + ('*' if base else ''), ha='center', va='center', color='w', fontsize=8)
            a.set_title(f'{lev}, exit {100*ex:.0f}%'); a.set_xlabel('SMA length')
            if j == 0: a.set_ylabel('entry threshold')
    fig.subplots_adjust(hspace=0.55, wspace=0.25)
    fig.colorbar(im, ax=ax, shrink=.7, label='Calmar')
    fig.suptitle('Calmar ratio of all 45 configurations - ' + WLAB['real'] + ' (* = baseline)')
    fig.savefig(FIG / 'parameter_heatmap_real.png', dpi=170, bbox_inches='tight'); plt.close(fig)
    b = bsum[(bsum.MeanBlockDays == 252) & bsum.Metric.isin(['Calmar', 'Sharpe'])]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    lab = {'3x hold': '3x hold', '1x hold': '1x hold', '1x SMA': '1x SMA', 'Matched weight (ex ante)': 'Matched (ex ante)', 'Vol target 30%': 'Vol target 30%'}
    for a, met in zip(ax, ('Calmar', 'Sharpe')):
        yy = 0; ticks = []
        for lev, c in (('SPXL', '#0f6e7a'), ('TQQQ', '#d98c1f')):
            for vs in lab:
                r = b[(b.ETF == lev) & (b.Versus == vs) & (b.Metric == met)].iloc[0]
                a.plot([r.CI2_5, r.CI97_5], [yy, yy], color=c, lw=2); a.plot(r.Observed, yy, 'o', color=c)
                a.text(r.CI97_5, yy + 0.18, f' p={r.p_centred:.2f}', fontsize=7, color=c)
                ticks.append(f'{lev} vs {lab[vs]}'); yy += 1
            yy += 0.6
        a.axvline(0, color='k', lw=.7); a.set_title(f'SMA minus benchmark: {met} (observed, 95% percentile interval, centred p)')
        a.grid(alpha=.2)
    pos = [i + (0.6 if i >= 5 else 0) for i in range(10)]
    ax[0].set_yticks(pos, ticks); fig.suptitle('Daily path bootstrap, policy re-run, 1,000 paths, mean block 252 days - REAL ETF window')
    fig.tight_layout(); fig.savefig(FIG / 'bootstrap_intervals.png', dpi=170); plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    for a, lev in zip(ax, ('SPXL', 'TQQQ')):
        cv = wfc[(lev, 'real', 'Calmar')]
        for k, c in (('Walk-forward SMA', '#0f6e7a'), ('Fixed 200/+4/-3', '#5aa9b5'), ('WF matched weight', '#7f7f7f'),
                     ('WF vol target', '#d98c1f'), ('1x hold', '#4f6fa8'), ('3x hold', '#c0504d')):
            s = cv[k]; a.plot(s.index, s / 1e4, color=c, lw=1.6 if k.startswith('Walk') else 1, label=k)
        a.set_yscale('log'); a.grid(alpha=.2); a.set_title(f'{lev}: out-of-sample 2015-2026')
    ax[0].legend(fontsize=7.5, frameon=False); fig.suptitle('Walk-forward (5y train -> 1y test, Calmar selection) - REAL ETF')
    fig.tight_layout(); fig.savefig(FIG / 'walkforward_real.png', dpi=170); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--quick', action='store_true'); a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    t0 = time.time(); reps = 100 if a.quick else 1000; spa_reps = 300 if a.quick else 2000
    D, cal, mk = setup()
    save(pd.DataFrame([{'ETF': k, **v} for k, v in cal.items()]), 'calibration_spread.csv')
    p0_data(D); p0_execution_audit(mk)
    curves = main_tables(mk)
    runs_by = {(lev, per): grid_runs(mk[lev], st) for lev in mk for per, st in E.STARTS.items()}
    grid = param_table(mk, runs_by, curves)
    wfc = walk_forward(mk, runs_by)
    path_consistency(mk, curves)
    crisis_return_removal(curves); loco_rerun(mk); spa_tests(runs_by, curves, spa_reps)
    costs(mk); synthetic_stress(D, cal, mc=20 if a.quick else 50)
    mechanism(curves); state_groups(mk, curves)
    fr, _ = frontier(mk, curves)
    bs, bsum = path_bootstrap(mk, reps)
    figures(curves, fr, bsum, wfc, grid, mk)
    import numpy, pandas, matplotlib, scipy  # noqa
    json.dump({'end': E.END, 'seed': SEED, 'path_bootstrap_reps': reps, 'spa_reps': spa_reps,
               'calibrated_spread': {k: v['Spread_s'] for k, v in cal.items()},
               'python': platform.python_version(), 'numpy': numpy.__version__, 'pandas': pandas.__version__,
               'matplotlib': matplotlib.__version__, 'runtime_sec': round(time.time() - t0, 1),
               'data_sha256': {t: d.attrs['sha256'] for t, d in D.items()}},
              open(OUT / 'run_manifest.json', 'w'), indent=2)
    print('done in', round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
