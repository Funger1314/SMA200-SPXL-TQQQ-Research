# LEGACY (v3) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Run every v3 analysis and write data/v3_results/*.csv and figures/v3/*.png.

python scripts/v3_run.py            # everything (~5-8 min, bootstrap dominates)
python scripts/v3_run.py --quick    # 100 bootstrap replicates
"""
from __future__ import annotations
import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v3_engine as E
from rates import annual_cash_rate

ROOT = E.ROOT
OUT = ROOT / 'data/v3_results'; FIG = ROOT / 'figures/v3'
CAL_WINDOW = ('2010-02-12', '2026-07-31')
SEED = 20260806
COL = {'SMA rule': '#0f6e7a', '3x hold': '#c0504d', 'Matched fixed weight': '#7f7f7f',
       'Vol target 30%': '#d98c1f', '1x hold': '#4f6fa8'}


def save(df: pd.DataFrame, name: str):
    df.to_csv(OUT / name, index=False, float_format='%.6f')


# ------------------------------------------------------------------ setup
def setup():
    D = E.load_all(True)
    cal = {}; mk = {}
    for lev, und in E.PAIRS.items():
        cal[lev] = E.calibrate_spread(D[und], D[lev], *CAL_WINDOW)
        mk[lev] = E.add_signals(E.build_market(D[und], D[lev], cal[lev]['Spread_s']))
    return D, cal, mk


def five_way(m, start, end=E.END, p=E.Params()):
    e, o = E.run(m, start, 'trend', p, end=end); r = E.metrics(e, o); w = r['AverageWeight']
    out = {'SMA rule': (e, o, r)}
    for name, mode, kw in [('3x hold', 'hold', {}), ('Matched fixed weight', 'fixed', {'w': w}),
                           ('Vol target 30%', 'vol', {}), ('1x hold', 'hold', {'unlevered': True})]:
        e2, o2 = E.run(m, start, mode, p, end=end, **kw); out[name] = (e2, o2, E.metrics(e2, o2))
    return out


# ------------------------------------------------------------------ analyses
def data_audit(D):
    rows = []
    for t, d in D.items():
        raw = pd.read_csv(ROOT / f'data/raw/{t}.csv', skiprows=[1, 2])
        rows.append({'Ticker': t, 'FirstDate': str(d.index[0].date()), 'LastDate': str(d.index[-1].date()),
                     'Rows': len(d), 'SHA256': E.sha256(ROOT / f'data/raw/{t}.csv'),
                     'Source': 'Yahoo Finance via yfinance (auto_adjust=False), obtained from github.com/hjyssg/tqqq_simulation'})
    save(pd.DataFrame(rows), 'data_audit.csv')


def calibration(D, cal):
    rows = []
    for lev, und in E.PAIRS.items():
        rows.append({'Ticker': lev, 'Window': 'full real 2010-2026', **cal[lev]})
        a = E.calibrate_spread(D[und], D[lev], '2010-02-12', '2017-12-29')
        rows.append({'Ticker': lev, 'Window': 'train 2010-2017', **a})
        # out-of-sample check: synthetic built with the 2010-2017 spread vs real ETF 2018-2026
        u = D[und].loc['2017-12-29':]; l = D[lev].loc['2017-12-29':]
        syn = E.synthetic_3x(u, a['Spread_s'])
        rs = syn.Close.pct_change().dropna(); rl = l.Close.pct_change().dropna()
        cg = lambda r: (1 + r).prod() ** (252 / len(r)) - 1
        dd = lambda r: ((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min()
        rows.append({'Ticker': lev, 'Window': 'test 2018-2026 (spread from train)',
                     'Start': '2018-01-02', 'End': E.END, 'Days': len(rl), 'Spread_s': a['Spread_s'],
                     'SyntheticCAGR': cg(rs), 'RealCAGR': cg(rl), 'SyntheticMaxDD': dd(rs), 'RealMaxDD': dd(rl),
                     'DailyCorrelation': float(np.corrcoef(rs, rl)[0, 1]),
                     'AnnualTrackingError': float((rs - rl).std() * np.sqrt(252))})
    save(pd.DataFrame(rows), 'calibration_spread.csv')


def main_tables(mk):
    rows = []; curves = {}
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            res = five_way(m, st)
            for name, (e, o, r) in res.items():
                rows.append({'Period': per, 'Ticker': lev, 'Strategy': name, **r})
            curves[(lev, per)] = res
            if per == 'real':
                for name, (e, o, r) in res.items():
                    e.to_csv(OUT / f'equity_{per}_{lev}_{name.replace(" ", "_").replace("%", "pct")}.csv',
                             float_format='%.6f')
            res['SMA rule'][1].to_csv(OUT / f'orders_{per}_{lev}_sma.csv', index=False, float_format='%.6f')
    save(pd.DataFrame(rows), 'main_metrics.csv')
    return curves


def subperiods(mk):
    rows = []
    for lev, m in mk.items():
        for label, a, b in [('2010-2017', '2010-02-11', '2017-12-29'), ('2018-2026', '2018-01-02', E.END),
                            ('2000-2009 (synthetic)', '1999-12-22', '2009-12-31')]:
            for name, (e, o, r) in five_way(m, a, b).items():
                rows.append({'Subperiod': label, 'Ticker': lev, 'Strategy': name, **r})
    save(pd.DataFrame(rows), 'subperiod_metrics.csv')


def frontier(mk):
    rows = []; gaps = []
    ws = np.round(np.arange(0.1, 1.0001, 0.05), 2); vts = np.round(np.arange(0.10, 1.0001, 0.05), 2)
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            e, o = E.run(m, st, 'trend'); s = E.metrics(e, o)
            fam = {}
            for w in ws:
                e2, o2 = E.run(m, st, 'fixed', w=w); r = E.metrics(e2, o2)
                rows.append({'Period': per, 'Ticker': lev, 'Family': 'fixed weight', 'Param': w, **r})
                fam.setdefault('fixed weight', []).append(r)
            for vt in vts:
                e2, o2 = E.run(m, st, 'vol', replace(E.Params(), vol_target=vt)); r = E.metrics(e2, o2)
                rows.append({'Period': per, 'Ticker': lev, 'Family': 'vol target', 'Param': vt, **r})
                fam.setdefault('vol target', []).append(r)
            for f, rs in fam.items():
                for risk in ('MaxDrawdown', 'CDaR10', 'UlcerIndex'):
                    x = np.array([abs(r[risk]) for r in rs]); y = np.array([r['CAGR'] for r in rs])
                    order = np.argsort(x); x, y = x[order], y[order]
                    target = abs(s[risk])
                    inside = x[0] <= target <= x[-1]
                    yi = float(np.interp(target, x, y)) if inside else np.nan
                    gaps.append({'Period': per, 'Ticker': lev, 'Family': f, 'RiskMeasure': risk,
                                 'SMA_risk': target, 'SMA_CAGR': s['CAGR'], 'Frontier_CAGR_at_same_risk': yi,
                                 'SMA_minus_frontier_CAGR': s['CAGR'] - yi if inside else np.nan,
                                 'Note': '' if inside else 'SMA risk outside family range'})
    fr = pd.DataFrame(rows); save(fr, 'frontier_points.csv'); save(pd.DataFrame(gaps), 'frontier_gap.csv')
    return fr


def attribution(D):
    """v1 -> v3 waterfall on the real-ETF window, one change at a time."""
    R = E.load_all(False)
    rows = []
    for lev, und in E.PAIRS.items():
        def market(sig_src, asset_src, cash):
            u = sig_src[und].loc[E.UNIVERSE_START:]; l = asset_src[lev]
            m = u.rename(columns={'Open': 'signal_open', 'Close': 'signal_close'}).join(
                l.rename(columns={'Open': 'asset_open', 'Close': 'asset_close'}), how='inner')
            m['rf'] = annual_cash_rate(m.index); m['synthetic'] = False
            # SMA needs the signal history before the leveraged inception
            sma = u.Close.rolling(200, min_periods=200).mean()
            m['sma'] = sma.reindex(m.index); m['asset_vol'] = np.nan
            return m, replace(E.Params(), cash=cash)
        steps = [('A. v1 conventions: price-only signal & ETF, 0% cash', R, R, False),
                 ('B. + total-return (dividend-adjusted) leveraged ETF', R, D, False),
                 ('C. + total-return signal ETF for SMA', D, D, False),
                 ('D. + prior-month T-bill on idle cash (= v3 baseline)', D, D, True)]
        for label, s_src, a_src, cash in steps:
            m, p = market(s_src, a_src, cash)
            for mode in ('trend', 'hold'):
                e, o = E.run(m, E.STARTS['real'], mode, p); r = E.metrics(e, o)
                rows.append({'Ticker': lev, 'Step': label, 'Strategy': 'SMA rule' if mode == 'trend' else '3x hold',
                             'CAGR': r['CAGR'], 'MaxDrawdown': r['MaxDrawdown'], 'Sharpe': r['Sharpe'],
                             'NumOrders': r['NumOrders']})
    save(pd.DataFrame(rows), 'attribution_v1_to_v3.csv')


def regimes(mk, cal):
    rows = []
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            d = m.loc[st:].copy()
            d['Regime'] = np.where(d.signal_close >= 1.04 * d.sma, 'Above +4%',
                                   np.where(d.signal_close < 0.97 * d.sma, 'Below -3%', 'Middle'))
            d['next'] = d.signal_close.shift(-1) / d.signal_close - 1
            d['nextrf'] = d.rf.shift(-1)
            s = cal[lev]['Spread_s']
            for g, x in d.iloc[:-1].groupby('Regime'):
                mu = x.next.mean() * 252; sg = x.next.std() * np.sqrt(252); rf = x.nextrf.mean()
                rows.append({'Period': per, 'Ticker': lev, 'SignalETF': E.PAIRS[lev], 'RegimeAtClose_t': g,
                             'Days': len(x), 'Share': len(x) / (len(d) - 1),
                             'NextDayMeanAnnual': mu, 'NextDayVolAnnual': sg, 'MeanRF': rf,
                             'Implied3xLogGrowth': 3 * mu - 4.5 * sg ** 2 - 2 * (rf + s) - 0.0095,
                             'Implied1xLogGrowth': mu - 0.5 * sg ** 2})
    save(pd.DataFrame(rows), 'regime_nextday.csv')


def roundtrips(mk):
    rows = []
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            e, o = E.run(m, st, 'trend'); sell = None
            for _, r in o.iterrows():
                if r.Action == 'SELL':
                    sell = r
                elif r.Action == 'BUY_1' and sell is not None:
                    rows.append({'Period': per, 'Ticker': lev, 'ExitFill': str(sell.Date.date()),
                                 'ReentryFill': str(r.Date.date()),
                                 'TradingDaysOut': int(m.index.get_loc(r.Date) - m.index.get_loc(sell.Date)),
                                 'ForegoneLeveredReturn': r.FillOpen / sell.FillOpen - 1,
                                 'Synthetic': bool(m.loc[sell.Date, 'synthetic'])}); sell = None
            if sell is not None:
                rows.append({'Period': per, 'Ticker': lev, 'ExitFill': str(sell.Date.date()), 'ReentryFill': 'open',
                             'TradingDaysOut': int(len(m.loc[sell.Date:]) - 1),
                             'ForegoneLeveredReturn': m.asset_close.iloc[-1] / sell.FillOpen - 1,
                             'Synthetic': bool(m.loc[sell.Date, 'synthetic'])})
    save(pd.DataFrame(rows), 'roundtrips.csv')


def rolling_starts(mk):
    rows = []
    for lev, m in mk.items():
        for per, first in E.STARTS.items():
            idx = m.loc[first:'2023-08-31'].index
            starts = pd.Series(idx, index=idx).groupby(idx.to_period('M')).first()
            for s0 in starts:
                st = str(s0.date())
                res = five_way(m, st)
                base = res['SMA rule'][2]
                rec = {'Window': per, 'Ticker': lev, 'Start': st, 'SMA_CAGR': base['CAGR'],
                       'SMA_MDD': base['MaxDrawdown'], 'SMA_Calmar': base['Calmar']}
                for k in ('3x hold', 'Matched fixed weight', 'Vol target 30%', '1x hold'):
                    r = res[k][2]; tag = {'3x hold': 'Hold3x', 'Matched fixed weight': 'Fixed',
                                          'Vol target 30%': 'Vol30', '1x hold': 'Hold1x'}[k]
                    rec[f'{tag}_CAGR'] = r['CAGR']; rec[f'{tag}_MDD'] = r['MaxDrawdown']; rec[f'{tag}_Calmar'] = r['Calmar']
                rows.append(rec)
    rs = pd.DataFrame(rows); save(rs, 'rolling_starts.csv')
    summ = []
    for (w, t), g in rs.groupby(['Window', 'Ticker']):
        for tag in ('Hold3x', 'Fixed', 'Vol30', 'Hold1x'):
            summ.append({'Window': w, 'Ticker': t, 'Versus': tag, 'Starts': len(g),
                         'Median_dCAGR': (g.SMA_CAGR - g[f'{tag}_CAGR']).median(),
                         'Median_dMDD': (g.SMA_MDD - g[f'{tag}_MDD']).median(),
                         'Median_dCalmar': (g.SMA_Calmar - g[f'{tag}_Calmar']).median(),
                         'Share_SMA_higher_Calmar': (g.SMA_Calmar > g[f'{tag}_Calmar']).mean(),
                         'Share_SMA_shallower_MDD': (g.SMA_MDD > g[f'{tag}_MDD']).mean()})
    save(pd.DataFrame(summ), 'rolling_starts_summary.csv')
    return rs


def param_grid(mk):
    rows = []
    for lev, m in mk.items():
        for per, st in E.STARTS.items():
            for L in (150, 200, 250):
                mm = m.copy(); mm['sma'] = mm.signal_close.rolling(L, min_periods=L).mean()
                for en in (0.02, 0.04, 0.06):
                    for ex in (-0.01, -0.03, -0.05):
                        p = replace(E.Params(), sma_days=L, entry=en, exit=ex)
                        e, o = E.run(mm, st, 'trend', p); r = E.metrics(e, o)
                        e2, o2 = E.run(mm, st, 'fixed', p, w=r['AverageWeight']); f = E.metrics(e2, o2)
                        rows.append({'Period': per, 'Ticker': lev, 'SMA': L, 'Entry': en, 'Exit': ex,
                                     'CAGR': r['CAGR'], 'MaxDrawdown': r['MaxDrawdown'], 'Calmar': r['Calmar'],
                                     'Sharpe': r['Sharpe'], 'AverageWeight': r['AverageWeight'],
                                     'MatchedFixed_Calmar': f['Calmar'], 'MatchedFixed_Sharpe': f['Sharpe'],
                                     'Beats_matched_Calmar': r['Calmar'] > f['Calmar'],
                                     'Beats_matched_Sharpe': r['Sharpe'] > f['Sharpe']})
    save(pd.DataFrame(rows), 'parameter_grid.csv')


def sensitivity(D, cal, mk):
    rows = []
    for lev, m in mk.items():
        for bp in (5, 10, 20, 50):
            p = replace(E.Params(), fee=bp / 1e4)
            for mode in ('trend', 'hold'):
                e, o = E.run(m, E.STARTS['real'], mode, p); r = E.metrics(e, o)
                rows.append({'Test': 'one-way cost', 'Ticker': lev, 'Setting': f'{bp} bp', 'Period': 'real',
                             'Strategy': mode, 'CAGR': r['CAGR'], 'MaxDrawdown': r['MaxDrawdown'], 'Sharpe': r['Sharpe']})
        s0 = cal[lev]['Spread_s']
        for lab, s in [('s = 0', 0.0), (f's = {s0*1e4:.0f} bp (calibrated)', s0), (f's = {2*s0*1e4:.0f} bp', 2 * s0)]:
            mm = E.add_signals(E.build_market(D[E.PAIRS[lev]], D[lev], s))
            for mode in ('trend', 'hold'):
                e, o = E.run(mm, E.STARTS['full'], mode); r = E.metrics(e, o)
                rows.append({'Test': 'synthetic financing spread', 'Ticker': lev, 'Setting': lab, 'Period': 'full',
                             'Strategy': mode, 'CAGR': r['CAGR'], 'MaxDrawdown': r['MaxDrawdown'], 'Sharpe': r['Sharpe']})
    save(pd.DataFrame(rows), 'sensitivity.csv')


# ------------------------------------------------------------- daily bootstrap
def stationary_indices(n, mean_block, rng):
    idx = np.empty(n, dtype=int); p = 1.0 / mean_block
    j = rng.integers(n)
    for t in range(n):
        if t > 0 and rng.random() < p:
            j = rng.integers(n)
        else:
            j = (j + 1) % n if t > 0 else j
        idx[t] = j
    return idx


def bootstrap(mk, reps, blocks=(63, 252)):
    """Stationary bootstrap of the JOINT daily rows (signal close & overnight
    returns, leveraged close & overnight returns, cash rate) for the real window,
    shared indices across both assets; the full trading policy is re-run on every
    pseudo-path. The 200-day pre-sample history is kept so SMA starts warm."""
    st = E.STARTS['real']; rng = np.random.default_rng(SEED)
    prep = {}
    for lev, m in mk.items():
        loc = m.index.get_loc(pd.Timestamp(st)); h = m.iloc[loc - 260:loc]; d = m.iloc[loc - 1:]
        prep[lev] = dict(hist=h, rs=(d.signal_close.values[1:] / d.signal_close.values[:-1]),
                         os=(d.signal_open.values[1:] / d.signal_close.values[:-1]),
                         ra=(d.asset_close.values[1:] / d.asset_close.values[:-1]),
                         oa=(d.asset_open.values[1:] / d.asset_close.values[:-1]),
                         rf=d.rf.values[1:], s0=d.signal_close.values[0], a0=d.asset_close.values[0])
        e, o = E.run(m, st, 'trend'); prep[lev]['w'] = E.metrics(e, o)['AverageWeight']
    n = len(prep['SPXL']['rs']); assert n == len(prep['TQQQ']['rs'])
    rows = []
    p = E.Params()
    for L in blocks:
        for b in range(reps):
            ix = stationary_indices(n, L, rng)
            for lev, q in prep.items():
                sc = q['s0'] * np.cumprod(q['rs'][ix]); so = np.r_[q['s0'], sc[:-1]] * q['os'][ix]
                ac = q['a0'] * np.cumprod(q['ra'][ix]); ao = np.r_[q['a0'], ac[:-1]] * q['oa'][ix]
                rf = q['rf'][ix]
                hs = q['hist'].signal_close.values; ha = q['hist'].asset_close.values
                sig_all = np.r_[hs, sc]   # hs[-1] == s0, so history and path are continuous
                sma = pd.Series(sig_all).rolling(200).mean().values[len(hs):]
                a_all = np.r_[ha, ac]
                vol = pd.Series(a_all).pct_change().rolling(63).std().values[len(ha):] * np.sqrt(252)
                res = {}
                for name, mode, w in [('SMA', 'trend', 1.0), ('Hold3x', 'hold', 1.0),
                                      ('Fixed', 'fixed', q['w']), ('Vol30', 'vol', 1.0)]:
                    out = E.simulate(sc, sma, ao, ac, rf, mode, p, w, vol)
                    res[name] = E.stats_from_nav(np.r_[10000.0, out['nav']], np.r_[0.0, rf / 252], out['weight'])
                rec = {'Block': L, 'Rep': b, 'Ticker': lev}
                for name, r in res.items():
                    for k in ('CAGR', 'MaxDrawdown', 'Calmar', 'Sharpe', 'CDaR10', 'AverageWeight'):
                        rec[f'{name}_{k}'] = r[k]
                rows.append(rec)
    bs = pd.DataFrame(rows); bs.to_csv(OUT / 'bootstrap_daily_paths.csv', index=False, float_format='%.6f')
    summ = []
    for (L, t), g in bs.groupby(['Block', 'Ticker']):
        for vs in ('Hold3x', 'Fixed', 'Vol30'):
            for k in ('CAGR', 'MaxDrawdown', 'Calmar', 'Sharpe', 'CDaR10'):
                dlt = g[f'SMA_{k}'] - g[f'{vs}_{k}']
                summ.append({'MeanBlockDays': L, 'Ticker': t, 'Versus': vs, 'Metric': k, 'Reps': len(g),
                             'Median_SMA_minus_benchmark': dlt.median(), 'CI2_5': dlt.quantile(.025),
                             'CI97_5': dlt.quantile(.975), 'Share_positive': (dlt > 0).mean()})
    save(pd.DataFrame(summ), 'bootstrap_daily_summary.csv')
    return bs


# ------------------------------------------------------------------ figures
def figures(curves, fr, rs, bs, mk):
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
    for per in ('real', 'full'):
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.6), sharey=False)
        for a, lev in zip(ax, ('SPXL', 'TQQQ')):
            for name, (e, o, r) in curves[(lev, per)].items():
                a.plot(e.index, e.NAV / 10000, label=name, color=COL[name], lw=1.8 if name == 'SMA rule' else 1.1)
            if per == 'full':
                inc = pd.Timestamp(E.INCEPTION[lev]); a.axvspan(e.index[0], inc, color='#000', alpha=.06, lw=0)
            a.set_yscale('log'); a.set_title(f'{E.PAIRS[lev]} signal → {lev}'); a.grid(alpha=.2)
        ax[0].set_ylabel('Growth of $1 (log)'); ax[0].legend(fontsize=8, frameon=False)
        ttl = ('Real-ETF window, 2010-02-11 to 2026-08-06' if per == 'real' else
               '1999-12-22 to 2026-08-06; shaded = synthetic pre-inception 3x proxy')
        fig.suptitle(ttl); fig.tight_layout(); fig.savefig(FIG / f'equity_{per}.png', dpi=170); plt.close(fig)
    # underwater real
    fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    for a, lev in zip(ax, ('SPXL', 'TQQQ')):
        for name in ('3x hold', 'Matched fixed weight', 'SMA rule'):
            e = curves[(lev, 'real')][name][0]
            a.plot(e.index, 100 * (e.NAV / np.maximum.accumulate(np.r_[10000, e.NAV.values])[1:] - 1),
                   color=COL[name], lw=1.6 if name == 'SMA rule' else 1, label=name)
        a.set_ylabel(f'{lev} drawdown %'); a.grid(alpha=.2)
    ax[0].legend(fontsize=8, frameon=False, ncol=3); fig.suptitle('Daily drawdowns, real-ETF window')
    fig.tight_layout(); fig.savefig(FIG / 'underwater_real.png', dpi=170); plt.close(fig)
    # frontier
    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    for i, per in enumerate(('real', 'full')):
        for j, lev in enumerate(('SPXL', 'TQQQ')):
            a = ax[i, j]
            for fam, c in (('fixed weight', COL['Matched fixed weight']), ('vol target', COL['Vol target 30%'])):
                g = fr[(fr.Period == per) & (fr.Ticker == lev) & (fr.Family == fam)].sort_values('Param')
                a.plot(-100 * g.MaxDrawdown, 100 * g.CAGR, '-o', ms=2.5, color=c, lw=1.2, label=fam + ' frontier')
            for name in ('SMA rule', '1x hold'):
                r = curves[(lev, per)][name][2]
                a.scatter(-100 * r['MaxDrawdown'], 100 * r['CAGR'], s=60 if name == 'SMA rule' else 35,
                          color=COL[name], zorder=5, label=name, marker='*' if name == 'SMA rule' else 'o')
            a.set_title(f'{lev}, {"2010-2026 real" if per == "real" else "1999-2026 incl. synthetic"}')
            a.set_xlabel('Max daily drawdown, % (lower is better)'); a.set_ylabel('CAGR, %'); a.grid(alpha=.2)
    ax[0, 0].legend(fontsize=8, frameon=False)
    fig.suptitle('Risk-return frontiers of non-timing allocations vs the SMA rule')
    fig.tight_layout(); fig.savefig(FIG / 'frontier.png', dpi=170); plt.close(fig)
    # rolling starts
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for a, lev in zip(ax, ('SPXL', 'TQQQ')):
        for per, c in (('full', '#0f6e7a'), ('real', '#d98c1f')):
            g = rs[(rs.Ticker == lev) & (rs.Window == per)].copy(); g['Start'] = pd.to_datetime(g.Start)
            a.plot(g.Start, g.SMA_Calmar - g.Fixed_Calmar, color=c, lw=1.2,
                   label='start ≥1999-12 (synthetic early)' if per == 'full' else 'start ≥2010-02 (real ETF)')
        a.axhline(0, color='k', lw=.6); a.set_title(f'{lev}: Calmar(SMA) − Calmar(matched fixed weight)')
        a.set_xlabel('Backtest start month (end fixed at 2026-08-06)'); a.grid(alpha=.2)
    ax[0].legend(fontsize=8, frameon=False); fig.tight_layout()
    fig.savefig(FIG / 'rolling_starts.png', dpi=170); plt.close(fig)
    # bootstrap
    if bs is not None:
        fig, ax = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
        for a, lev in zip(ax, ('SPXL', 'TQQQ')):
            for L, c in ((63, '#d98c1f'), (252, '#0f6e7a')):
                g = bs[(bs.Ticker == lev) & (bs.Block == L)]
                a.hist(g.SMA_Calmar - g.Fixed_Calmar, bins=40, alpha=.55, color=c, label=f'mean block {L} days')
            a.axvline(0, color='k', lw=.7); a.set_title(f'{lev}: bootstrap ΔCalmar, SMA − matched fixed weight')
            a.grid(alpha=.2)
        ax[0].legend(fontsize=8, frameon=False); fig.tight_layout()
        fig.savefig(FIG / 'bootstrap_calmar.png', dpi=170); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--quick', action='store_true')
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    D, cal, mk = setup()
    data_audit(D); calibration(D, cal)
    curves = main_tables(mk); subperiods(mk); fr = frontier(mk); attribution(D)
    regimes(mk, cal); roundtrips(mk); rs = rolling_starts(mk); param_grid(mk); sensitivity(D, cal, mk)
    bs = bootstrap(mk, 100 if a.quick else 1000)
    figures(curves, fr, rs, bs, mk)
    json.dump({'end': E.END, 'calibrated_spread': {k: v['Spread_s'] for k, v in cal.items()},
               'bootstrap_reps': 100 if a.quick else 1000, 'seed': SEED},
              open(OUT / 'run_manifest.json', 'w'), indent=2)
    print(pd.read_csv(OUT / 'main_metrics.csv')[['Period', 'Ticker', 'Strategy', 'CAGR', 'MaxDrawdown', 'Calmar', 'Sharpe', 'AverageWeight']].to_string(index=False))


if __name__ == '__main__':
    main()
