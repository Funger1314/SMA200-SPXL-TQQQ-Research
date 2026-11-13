"""Offline tests for the v3 single-vendor engine."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import v3_engine as E
import review_revision as v2


def market(n=1500, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range('2005-01-03', periods=n)
    sig = 100 * np.exp(np.cumsum(rng.normal(3e-4, 0.012, n)))
    a = 10 * np.exp(np.cumsum(rng.normal(9e-4, 0.036, n)))
    m = pd.DataFrame({'signal_open': sig, 'signal_close': sig,
                      'asset_open': a * np.exp(rng.normal(0, .005, n)), 'asset_close': a}, index=idx)
    m['sma'] = m.signal_close.rolling(200).mean(); m['rf'] = 0.02; m['synthetic'] = False
    m['asset_ret'] = m.asset_close.pct_change(); m['asset_vol'] = np.nan
    return m


@pytest.mark.parametrize('mode,v2mode', [('hold', 'leveraged_hold'), ('fixed', 'fixed_weight')])
def test_matches_v2_for_non_timing_rules(mode, v2mode):
    m = market(); end = str(m.index[-1].date())
    a, _ = v2.benchmark(m, str(m.index[0].date()), v2mode, fixed_weight=.6, stop=end)
    b, _ = E.run(m, str(m.index[0].date()), mode, w=.6, end=end)
    assert np.allclose(a.NAV.values, b.NAV.values, rtol=1e-12)


def test_matches_v2_trend_until_first_reentry_and_fixes_v2_dust_bug():
    m = market(); end = str(m.index[-1].date())
    a, oa = v2.benchmark(m, str(m.index[0].date()), 'trend', stop=end)
    b, ob = E.run(m, str(m.index[0].date()), 'trend', end=end)
    first_sell = ob[ob.Action == 'SELL'].Date.iloc[0]
    reentry = ob[(ob.Action == 'BUY_1') & (ob.Date > first_sell)].Date.iloc[0]
    k = m.index.get_loc(reentry)
    assert np.allclose(a.NAV.values[:k], b.NAV.values[:k], rtol=1e-12)
    # v2 leaves -2.8e-14 shares after a full exit and can never re-enter; v3 can.
    assert (oa.Action == 'BUY_1').sum() == 1 and (ob.Action == 'BUY_1').sum() > 1
    assert (b.Shares >= 0).all()


def test_full_exit_leaves_exactly_zero_shares():
    m = market(); e, o = E.run(m, str(m.index[0].date()), 'trend', end=str(m.index[-1].date()))
    after = [m.index.get_loc(d) for d in o[o.Action == 'SELL'].Date]
    assert after and all(e.Shares.iloc[i] == 0.0 for i in after)


def test_signal_at_close_fills_next_open():
    n = 260; idx = pd.bdate_range('2020-01-01', periods=n)
    sig = np.r_[np.full(n - 5, 100.), np.full(5, 110.)]
    m = pd.DataFrame({'signal_open': sig, 'signal_close': sig, 'asset_open': 10., 'asset_close': 10.,
                      'sma': 100., 'rf': 0., 'synthetic': False, 'asset_vol': np.nan}, index=idx)
    e, o = E.run(m, '2020-01-01', 'trend', end=str(idx[-1].date()))
    assert o.Date.iloc[0] == idx[n - 4] and o.Action.iloc[0] == 'BUY_1'


def test_vol_target_uses_only_trailing_information():
    m = market()
    m['asset_vol'] = m.asset_close.pct_change().rolling(63).std() * np.sqrt(252)
    end = str(m.index[-1].date())
    a, _ = E.run(m, '2005-06-01', 'vol', end=end)
    m2 = m.copy(); m2.loc[m2.index[-10]:, ['asset_close', 'asset_open']] *= 3   # perturb the future only
    m2['asset_vol'] = m2.asset_close.pct_change().rolling(63).std() * np.sqrt(252)
    b, _ = E.run(m2, '2005-06-01', 'vol', end=end)
    k = len(a) - 10
    assert np.allclose(a.Weight.values[:k], b.Weight.values[:k])


def test_synthetic_3x_matches_formula_and_financing_lowers_return():
    idx = pd.bdate_range('2001-01-02', periods=30)
    c = np.geomspace(100, 103, 30); u = pd.DataFrame({'Open': c, 'Close': c}, index=idx)
    lo, hi = E.synthetic_3x(u, 0.0), E.synthetic_3x(u, 0.02)
    assert hi.Close.iloc[-1] < lo.Close.iloc[-1]
    from rates import annual_cash_rate
    rf = annual_cash_rate(idx).iloc[1]
    assert lo.Close.iloc[1] == pytest.approx(1 + 3 * (c[1] / c[0] - 1) - (2 * rf + .0095) / 252)


def test_calibration_recovers_known_spread():
    idx = pd.bdate_range('2012-01-02', periods=600)
    rng = np.random.default_rng(3); r = rng.normal(4e-4, .01, 600); c = 100 * np.cumprod(1 + r)
    u = pd.DataFrame({'Open': c, 'Close': c}, index=idx)
    lev = E.synthetic_3x(u, 0.0123)
    est = E.calibrate_spread(u, lev, str(idx[1].date()), str(idx[-1].date()))
    assert est['Spread_s'] == pytest.approx(0.0123, abs=1e-9)


@pytest.mark.skipif(not (ROOT / 'data/raw/SPY.csv').exists(), reason='vendor files not present')
def test_vendor_files_align_and_chain():
    D = E.load_all(True)
    for lev, und in E.PAIRS.items():
        m = E.build_market(D[und], D[lev], 0.007)
        real = m.loc[E.INCEPTION[lev]:]
        assert np.allclose(real.asset_close, D[lev].loc[E.INCEPTION[lev]:].Close)
        assert m.synthetic.loc[:E.INCEPTION[lev]].iloc[:-1].all()
        assert m.index[-1] == pd.Timestamp(E.END)
