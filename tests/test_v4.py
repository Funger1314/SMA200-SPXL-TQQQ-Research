"""v4 tests: data validation, NYSE calendar, look-ahead safety of every rule, tail metrics."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import engine as E
from data_checks import validate_ohlcv, nyse_trading_days, DataValidationError


def clean_frame(n=300, start='2015-01-02'):
    idx = nyse_trading_days(start, '2030-12-31')[:n]
    c = 100 * np.exp(np.cumsum(np.random.default_rng(0).normal(0, .01, n)))
    o = c * 1.001
    return pd.DataFrame({'Open': o, 'High': np.maximum(o, c) * 1.002, 'Low': np.minimum(o, c) * 0.998,
                         'Close': c, 'Adj Close': c * 0.99, 'Volume': 1e6}, index=idx)


def test_clean_frame_passes():
    recs = validate_ohlcv(clean_frame(), 'X')
    assert not [r for r in recs if r['Status'] == 'FATAL']


@pytest.mark.parametrize('breaker,check', [
    (lambda d: d.assign(High=d.Low * 0.99), 'OHLC'),
    (lambda d: pd.concat([d, d.iloc[[5]]]).sort_index(), 'duplicate'),
    (lambda d: d.drop(d.index[50]), 'missing NYSE'),
    (lambda d: d.assign(Close=d.Close.where(d.index != d.index[10], np.nan)), 'missing values'),
    (lambda d: d.assign(Open=d.Open.where(d.index != d.index[10], -1.0)), 'non-positive'),
    (lambda d: d.assign(**{'Adj Close': d.Close * 1.01}), 'Adj Close <= Close'),
])
def test_fatal_defects_raise(breaker, check):
    with pytest.raises(DataValidationError, match=check):
        validate_ohlcv(breaker(clean_frame()), 'X')


def test_nyse_calendar_known_dates():
    days = nyse_trading_days('2001-09-01', '2026-12-31')
    for closed in ['2001-09-11', '2001-09-14', '2012-10-29', '2018-12-05', '2025-01-09', '2026-04-03',
                   '2022-06-20', '2026-01-19', '2021-12-24']:
        assert pd.Timestamp(closed) not in days, closed
    for open_ in ['2001-09-17', '2021-12-31', '2026-08-06', '2022-12-30']:
        assert pd.Timestamp(open_) in days, open_


@pytest.mark.skipif(not (ROOT / 'data/raw/SPY.csv').exists(), reason='vendor files not present')
def test_vendor_files_pass_strict_validation_and_full_calendar():
    D = E.load_all(True)
    for t, d in D.items():
        assert not [r for r in d.attrs['validation'] if r['Status'] == 'FATAL']
        cal = nyse_trading_days(d.index[0], d.index[-1])
        assert cal.equals(d.index)


def toy_market(n=900, seed=5):
    rng = np.random.default_rng(seed); idx = pd.bdate_range('2005-01-03', periods=n)
    s = 100 * np.exp(np.cumsum(rng.normal(2e-4, .012, n))); a = 10 * np.exp(np.cumsum(rng.normal(6e-4, .036, n)))
    m = pd.DataFrame({'signal_open': s * 1.001, 'signal_close': s, 'asset_open': a * 1.002, 'asset_close': a,
                      'rf': .02, 'synthetic': False}, index=idx)
    return E.add_signals(m)


@pytest.mark.parametrize('mode,kw', [('trend', {}), ('vol', {}), ('fixed', {'w': .6}), ('hold', {}),
                                     ('trend', {'unlevered': True})])
def test_no_lookahead_any_rule(mode, kw):
    m = toy_market(); cut = m.index[600]
    m2 = m.copy()
    for c in ('signal_open', 'signal_close', 'asset_open', 'asset_close'):
        m2.loc[m2.index > cut, c] *= 0.5
    m2 = E.add_signals(m2.drop(columns=['sma', 'asset_vol']))
    a, oa = E.run(m, str(m.index[250].date()), mode, end=str(m.index[-1].date()), **kw)
    b, ob = E.run(m2, str(m.index[250].date()), mode, end=str(m.index[-1].date()), **kw)
    assert np.allclose(a.loc[:cut].Weight, b.loc[:cut].Weight)
    assert oa[oa.Date <= cut].reset_index(drop=True).equals(ob[ob.Date <= cut].reset_index(drop=True))


def test_target_path_fills_next_open_only():
    m = toy_market(); wp = pd.Series(np.nan, index=m.index); d = m.index[300]; wp.loc[d] = 0.5
    e, o = E.run(m, str(m.index[250].date()), 'target', w=0.0, wpath=wp, end=str(m.index[400].date()))
    assert o.Date.iloc[0] == m.index[301] and o.FillOpen.iloc[0] == m.asset_open.loc[m.index[301]]


def test_fee_array_is_applied_per_day():
    m = toy_market(); fee = pd.Series(0.0, index=m.index); fee.loc[m.index[251]] = 0.01
    e, o = E.run(m, str(m.index[250].date()), 'hold', fee_arr=fee, end=str(m.index[300].date()))
    assert o.Date.iloc[0] == m.index[250] and o.Fee.iloc[0] == 0.0     # cost of day 250 is zero
    e2, o2 = E.run(m, str(m.index[250].date()), 'hold', fee_arr=fee * 0 + 0.01, end=str(m.index[300].date()))
    assert o2.Fee.iloc[0] == pytest.approx(0.01 * o2.Notional.iloc[0])


def test_tail_metrics():
    nav = np.array([100, 110, 99, 88, 95, 111, 120.])
    s = E.stats_from_nav(nav)
    assert s['MaxDrawdown'] == pytest.approx(88 / 110 - 1)
    assert s['PeakToTroughDays'] == 2 and s['RecoveryDays'] == 2
    r = nav[1:] / nav[:-1] - 1
    assert s['VaR99'] == pytest.approx(np.quantile(r, .01)) and s['ES95'] <= s['VaR95']


def test_unsorted_file_is_rejected_before_sorting(tmp_path):
    src = ROOT / 'data/raw/SPY.csv'
    if not src.exists():
        pytest.skip('vendor files not present')
    d = pd.read_csv(src, skiprows=[1, 2])
    d.iloc[np.r_[1, 0, 2:len(d)]].to_csv(tmp_path / 'SPY.csv', index=False)   # swap first two rows
    with pytest.raises(DataValidationError, match='sorted ascending'):
        E.load_yahoo('SPY', raw_dir=tmp_path)


@pytest.mark.skipif(not (ROOT / 'data/raw/SPY.csv').exists(), reason='vendor files not present')
def test_path_engine_reproduces_main_backtest_and_ex_ante_definition():
    import v4_run as V
    D = E.load_all(True)
    m = E.add_signals(E.build_market(D['QQQ'], D['TQQQ'], 0.0075))
    q = V.prep_window(m, E.STARTS['real']); s = V.path_rules(q, np.arange(len(q['rs'])))
    for rule, kw in [('SMA rule', dict(mode='trend')), ('1x SMA', dict(mode='trend', unlevered=True))]:
        e, o = E.run(m, E.STARTS['real'], **kw)
        assert s[rule]['CAGR'] == pytest.approx(E.metrics(e, o)['CAGR'], abs=1e-10)
    wp, w0 = V.exante_wpath(m, E.STARTS['real'])
    e, o = E.run(m, E.STARTS['real'], 'target', w=w0, wpath=wp)
    assert s['Matched weight (ex ante)']['CAGR'] == pytest.approx(E.metrics(e, o)['CAGR'], abs=1e-10)
