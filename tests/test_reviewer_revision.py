"""Offline reviewer-requested state-machine and data validation tests."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from rates import rates_table,annual_cash_rate
from review_revision import benchmark,metrics,Parameters,synthetic_preinception,regime_table,load_adjusted
import review_revision as v2


def frame(signal=None,asset=None,n=270):
    d=pd.bdate_range('2020-01-01',periods=n)
    if signal is None: signal=np.full(n,100.)
    if asset is None:asset=np.full(n,10.)
    return pd.DataFrame({'signal_open':signal,'signal_close':signal,
         'asset_open':asset,'asset_close':asset,
         'sma':100.,'rf':0.02,'synthetic':False,
         'asset_ret':pd.Series(asset).pct_change().to_numpy()},index=d)


def test_rates_are_prior_month_only():
    x=rates_table()
    d=pd.to_datetime(['2026-11-02','2026-11-12'])
    r=annual_cash_rate(d)
    assert r.iloc[0]==pytest.approx(x.loc['2026-10','InvestmentYield'])
    assert r.iloc[1]==pytest.approx(r.iloc[0])
    assert len(x)==335 and x.index[-1]=='2026-10'


def test_buy_after_close_signal_only():
    sig=np.r_[100.,105.,np.full(268,105.)]
    e,tr=benchmark(frame(sig),'2020-01-01','trend')
    assert pd.Timestamp(tr.iloc[0].Date)==e.index[2]
    assert e.loc[e.index[1],'Shares']==0
    assert tr.iloc[0].Action=='BUY_1'


def test_exit_after_stop_next_open():
    sig=np.r_[np.full(8,105.),np.full(262,90.)]
    e,tr=benchmark(frame(sig),'2020-01-01','trend')
    stop_idx=8
    assert e.Shares.iloc[stop_idx]>0
    assert tr[tr.Action=='SELL'].iloc[0].Date==e.index[stop_idx+1]


def test_exposed_days_different_from_avg_weight():
    sig=np.r_[105.,np.full(269,100.)]
    e,tr=benchmark(frame(sig),'2020-01-01','trend')
    result=metrics(e,tr)
    assert result['ExposedDaysFraction']>0.95
    assert 0.15<result['AverageWeight']<0.25


def test_zero_market_cash_earns_interest_and_no_trades():
    e,tr=benchmark(frame(),'2020-01-01','trend')
    assert len(tr)==0
    assert e.NAV.iloc[-1]>10000
    assert e.NAV.iloc[-1]==pytest.approx(10000*(1+.02/252)**(len(e)-1),rel=1e-10)


def test_constant_weight_strategy_follows_no_future_information():
    e,tr=benchmark(frame(),'2020-01-01','fixed_weight',fixed_weight=.35)
    assert len(tr)>0
    assert 0.34<e.Weight.mean()<0.36


def test_adjusted_archive_rejects_nonoverlapping_or_bad_prices(tmp_path,monkeypatch):
    (tmp_path/'data/raw').mkdir(parents=True)
    pd.DataFrame({'Date':['2026-07-23'],'Open':[739.],'Close':[900.],
                  'Adj Close':[900.]}).to_csv(tmp_path/'data/raw/SPY.csv',index=False)
    monkeypatch.setattr(v2,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='vendor stitch FAILED'):
        load_adjusted('SPY',tail_mode='public')


def test_funding_reduces_synthetic_forward_return():
    idx=pd.bdate_range('2000-01-03',periods=20)
    close=np.geomspace(100,110,len(idx));under=pd.DataFrame({'Open':close,'Close':close},index=idx)
    lev=pd.DataFrame({'Open':[10.],'Close':[10.]},index=pd.DatetimeIndex([idx[-1]]))
    a=synthetic_preinception(under,lev,Parameters(fin_spread=0.0))
    b=synthetic_preinception(under,lev,Parameters(fin_spread=.05))
    # Backward anchored: more financing drag requires a higher INITIAL price
    # to reach the same inception quote. Therefore synthetic total return falls.
    assert b.Close.iloc[0]>a.Close.iloc[0]


def test_new_regime_table_labels_predictive_t_plus_one_not_same_bar():
    f=frame(np.linspace(90,110,270),np.full(270,10.))
    r=regime_table(f,'2020-01-01')
    assert int(r.Observations.sum())==len(f)-1
    assert set(r.RegimeAtT).issubset({'Above +4%','Middle','Below -3%'})


def test_build_pair_trims_spy_pre_1999_before_rate_lookup():
    idx=pd.bdate_range('1993-01-01','2001-12-31')
    prices=np.geomspace(20,40,len(idx))
    u=pd.DataFrame({'Open':prices,'Close':prices},index=idx)
    lev_idx=pd.bdate_range('2001-01-02','2001-12-31')
    lv=np.geomspace(5,10,len(lev_idx))
    l=pd.DataFrame({'Open':lv,'Close':lv},index=lev_idx)
    m=v2.build_pair(u,l,Parameters())
    assert m.index.min().year==1999
    assert m.rf.notna().all()
    assert m.sma.loc['1999-12-22':].notna().any()
