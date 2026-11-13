"""Self-contained guardrails; no third-party data or internet required."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from reproduce import Config, backtest, performance
from decode_snapshot import decode_monthly


def market_frame(closes,opens=None,under=None):
    n=len(closes)
    idx=pd.bdate_range('2020-01-01',periods=n)
    if opens is None:opens=closes
    if under is None:under=[100]*n
    return pd.DataFrame({'signal_open':under,'signal_close':under,
          'asset_open':opens,'asset_close':closes,
          'sma200':[100.0]*n,'is_synthetic':[False]*n},index=idx)


def test_no_same_day_open_trade_after_close_signal():
    m=market_frame([10]*5,under=[100,105,105,105,105])
    equity,trades=backtest(m,str(m.index[0].date()),cfg=Config())
    assert str(trades.iloc[0]['Date'].date())==str(m.index[2].date())
    assert equity.Shares.iloc[1]==0
    assert equity.Shares.iloc[2]>0


def test_five_tranches_and_hold_without_intra_buffer_rebalancing():
    m=market_frame([10]*12,under=[105]*7+[101]*5)
    equity,trades=backtest(m,str(m.index[0].date()),cfg=Config())
    assert list(trades.Action)==['BUY_1','BUY_2','BUY_3','BUY_4','BUY_5']
    assert 0.99<equity.Exposure.iloc[5]<=1
    assert abs(equity.Shares.iloc[-1]-equity.Shares.iloc[7])<1e-10


def test_exit_at_following_open_not_at_stop_signal_close():
    m=market_frame([10]*8,under=[105,105,105,105,105,95,95,95])
    equity,trades=backtest(m,str(m.index[0].date()),cfg=Config())
    exit_day=m.index[6]
    assert trades.Action.iloc[-1]=='SELL'
    assert trades.Date.iloc[-1]==exit_day
    assert equity.Shares.loc[m.index[5]]>0
    assert equity.Shares.loc[exit_day]==0


def test_higher_friction_weakly_reduces_wealth_when_fills_exist():
    m=market_frame([10]*12,under=[105]*12)
    a,_=backtest(m,str(m.index[0].date()),cfg=Config(transaction_cost=.0005))
    b,_=backtest(m,str(m.index[0].date()),cfg=Config(transaction_cost=.005))
    assert b.NAV.iloc[-1] < a.NAV.iloc[-1]


def test_snapshot_decode_has_expected_endpoint():
    r=decode_monthly('2010-02',202,'monthly_2010.packed')
    assert len(r)==202
    assert abs(r.iloc[-1].TQQQ_strategy-539595.9)<35
    assert abs(r.iloc[-1].SPXL_strategy-247070.35)<35


def test_cagr_and_maxdrawdown_formula():
    m=market_frame([10]*3)
    eq=pd.DataFrame({'NAV':[10000,12000,6000], 'Shares':[1,1,1]},index=m.index[:3])
    report=performance(eq)
    assert abs(report['MaxDrawdown']+.5)<1e-8
    assert report['CAGR']<0


def test_no_signals_before_buffer():
    m=market_frame([10]*12,under=[101]*12)
    e,t=backtest(m,str(m.index[0].date()))
    assert t.empty
    assert (e.NAV==10000).all()


def test_market_reference_sma_is_from_underlying():
    m=market_frame([10,100,100,100,100],under=[100]*5)
    _,trades=backtest(m,str(m.index[0].date()))
    assert trades.empty
