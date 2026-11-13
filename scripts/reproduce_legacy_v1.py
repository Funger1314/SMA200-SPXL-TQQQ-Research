# LEGACY (v1) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Reproduce SMA200 trend-following paper from pinned daily OHLC archives.

Run: python scripts/reproduce.py --fetch
Or:  python scripts/fetch_data.py && python scripts/reproduce.py

This is a RESEARCH backtester, not a brokerage trading program. No live
execution, no account credentials, no future data, no margin beyond ETFs.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from decode_ibkr_tail import SOURCES, unpack

ASOF='2026-11-12'
INCEPTIONS={'SPXL':'2008-11-05','TQQQ':'2010-02-11'}
PAIRS={'SPXL':'SPY','TQQQ':'QQQ'}
BASELINE= {'lookback':200,'entry_buffer':0.04,'exit_buffer':-0.03,
           'transaction_cost':0.001,'cash_yield':0.0}

@dataclass(frozen=True)
class Config:
    lookback: int=200
    entry_buffer: float=0.04
    exit_buffer: float=-0.03
    transaction_cost: float=0.001
    cash_yield: float=0.0


def load_price(ticker: str) -> pd.DataFrame:
    file=ROOT/'data/raw'/f'{ticker}.csv'
    if not file.exists():
        raise FileNotFoundError(f'{file} is missing. Run python scripts/fetch_data.py to retrieve pinned source files.')
    df=pd.read_csv(file)
    cols={str(c).strip().replace(' ','').lower():c for c in df.columns}
    required=['date','open','close']
    if any(c not in cols for c in required):raise ValueError(f'{ticker}: required columns {required} not found')
    df=df.rename(columns={cols[k]:k.title() for k in required})
    df['Date']=pd.to_datetime(df['Date'])
    for col in ['Open','Close']:df[col]=pd.to_numeric(df[col],errors='raise')
    if df['Date'].duplicated().any() or not df['Date'].is_monotonic_increasing:
        raise ValueError(f'{ticker}: dates not uniquely sorted')
    if not ((df.Open>0)&(df.Close>0)).all():raise ValueError(f'{ticker}: nonpositive price')
    df=df[['Date','Open','Close']].set_index('Date')
    # A private exact snapshot can be supplied locally (not distributed).
    # For public GitHub replication, fetch the missing tail independently
    # using Yahoo Finance, then align prices at the archive overlap date.
    last=df.index.max()
    local_tail=ROOT/'data/raw'/f'IBKR_{ticker}.packed'
    if local_tail.exists():
        tail=unpack(ticker).copy()
        tail['Date']=pd.to_datetime(tail['Date'])
        tail=tail.set_index('Date')
        append=tail.loc[tail.index>last]
        print(f'{ticker}: using locally supplied licensed vendor tail (not published)')
    else:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError('Missing yfinance. Run pip install -r requirements.txt') from exc
        # The pre-existing QQQ/TQQQ archives are auto-adjusted, whereas
        # the SPY/SPXL archives use raw OHLC. Preserve that convention.
        auto_adjust=ticker in ('QQQ','TQQQ')
        begin=(last-pd.Timedelta(days=8)).strftime('%Y-%m-%d')
        fetched=yf.download(ticker,start=begin,end='2026-11-13',
                            auto_adjust=auto_adjust,interval='1d',
                            progress=False,threads=False)
        if isinstance(fetched.columns,pd.MultiIndex):
            fetched.columns=fetched.columns.get_level_values(0)
        if fetched.empty or 'Open' not in fetched or 'Close' not in fetched:
            raise RuntimeError(f'{ticker}: vendor tail unavailable from yfinance')
        fetched.index=pd.to_datetime(fetched.index).tz_localize(None)
        fetched=fetched[['Open','Close']].astype(float)
        if last not in fetched.index:
            raise RuntimeError(f'{ticker}: cannot anchor fetched source to {last.date()}')
        factor=df.loc[last,'Close']/fetched.loc[last,'Close']
        append=fetched.loc[fetched.index>last]*factor
        print(f'{ticker}: public Yahoo tail aligned at {last.date()}, factor={factor:.8f}; results may differ from the private IBKR audit')
    if len(append)==0:raise ValueError(f'{ticker}: no new bars after source archive')
    joined=pd.concat([df,append]).sort_index()
    if joined.index.duplicated().any():raise ValueError(f'{ticker}: duplicate dates after stitch')
    if str(joined.index[-1].date())!=ASOF:raise ValueError(f'{ticker}: data end mismatch; expected {ASOF}')
    return joined


def synthetic_prior_returns(under:pd.DataFrame,leverage:pd.DataFrame,
                            annual_drag:float=0.0095) -> pd.DataFrame:
    """3x DAILY returns; leverage 'Close' at inception anchors synthetic sleeve.

    Not a total-return fund simulation: fund financing / spreads / swaps and
    reinvested distributions may differ materially. The open price is a daily
    leveraged overnight proxy, not a tradable historic ETF quote.
    """
    start=leverage.index[0]
    ix=under.index.get_loc(start)
    if not isinstance(ix,int) or ix<1:raise ValueError('missing preceding underlying bar')
    drag=annual_drag/252.0
    anchor_prev=leverage.Close.iloc[0]/(1+3*(under.Close.iloc[ix]/under.Close.iloc[ix-1]-1)-drag)
    current=anchor_prev
    rows=[]
    for i in range(ix-1,0,-1):
        und_now=under.iloc[i]
        und_prev=under.iloc[i-1]
        factor=1+3*(und_now.Close/und_prev.Close-1)-drag
        if factor<=0:raise ValueError('unmodelable >=33.3% underlying close-to-close loss')
        prior=current/factor
        lev_open=prior*(1+3*(und_now.Open/und_prev.Close-1))
        if lev_open<=0:raise ValueError('nonpositive synthetic leveraged open')
        rows.append((under.index[i],lev_open,current))
        current=prior
    out=pd.DataFrame(rows,columns=['Date','Open','Close']).set_index('Date').sort_index()
    return out


def build_market() -> dict[str,pd.DataFrame]:
    inputs={ticker:load_price(ticker) for ticker in ('SPY','SPXL','QQQ','TQQQ')}
    output={}
    for target,signal in PAIRS.items():
        u=inputs[signal];l=inputs[target]
        s=synthetic_prior_returns(u,l)
        sleeve=pd.concat([s,l]).sort_index()
        if sleeve.index.duplicated().any():raise ValueError('synthetic overlap not allowed')
        df=u.rename(columns={'Open':'signal_open','Close':'signal_close'}).join(
            sleeve.rename(columns={'Open':'asset_open','Close':'asset_close'}),how='inner')
        df['sma200']=u.Close.rolling(200,min_periods=200).mean().reindex(df.index)
        df['is_synthetic']=df.index<pd.Timestamp(INCEPTIONS[target])
        df.index.name='Date'
        if df[['signal_open','signal_close','asset_open','asset_close']].isna().any().any():
            raise ValueError(f'OHLC missing for {target}')
        output[target]=df
    return output


def rolling_ma(market:pd.DataFrame,window:int)->pd.Series:
    if window==200 and 'sma200' in market:return market['sma200']
    # market starts near original signal first bar. SPY long history is already
    # included. For alternative SMA250, enough bars exist by 1999-12-22 for QQQ
    # only if its 250th bar is in early 2000. That is an honest warmup constraint.
    return market.signal_close.rolling(window,min_periods=window).mean()


def backtest(market:pd.DataFrame,start:str,stop:str=ASOF,cfg:Config=Config(),
             hold:bool=False)->tuple[pd.DataFrame,pd.DataFrame]:
    """Signals from close(t); execution ONLY at next day's open(t+1)."""
    ma=rolling_ma(market,cfg.lookback)
    d=market.loc[start:stop].copy()
    if d.empty:raise ValueError('no dates in period')
    d['ma']=ma.reindex(d.index)
    cash=10000.0;shares=0.0;stage=0;pending=None
    daily=[]; trades=[]
    for idx,(date,row) in enumerate(d.iterrows()):
        o=float(row.asset_open);c=float(row.asset_close)
        if idx>0 and cfg.cash_yield:
            cash*=1+cfg.cash_yield/252
        if hold and idx==0:pending=('buy',5)
        action=None;notional=0.0;cost=0.0
        if pending is not None:
            side,targetstage=pending
            if side=='sell' and shares>0:
                notional=shares*o;cost=notional*cfg.transaction_cost
                cash+=notional-cost;shares=0.0;stage=0;action='SELL'
            elif side=='buy':
                wealth=cash+shares*o
                target=1.0 if hold else min(1.0,0.2*targetstage)
                need=max(0.0,target*wealth-shares*o)
                notional=min(need,cash/(1+cfg.transaction_cost))
                if notional>1e-9:
                    cost=notional*cfg.transaction_cost
                    shares+=notional/o
                    cash-=notional+cost
                    stage=targetstage
                    action=f'BUY_{targetstage}'
                else:
                    notional=0.0
        nav=cash+shares*c
        if action:
            trades.append({'Date':date,'Action':action,'ExecutionOpen':o,
                           'Notional':notional,'FrictionPaid':cost,
                           'SharesAfter':shares,'CashAfter':cash,'StageAfter':stage,
                           'NAVClose':nav})
        daily.append({'Date':date,'NAV':nav,'Cash':cash,'Shares':shares,
                      'Exposure':shares*c/max(nav,1e-12),
                      'SMA':row.ma,'SignalClose':row.signal_close,
                      'LeveragedClose':row.asset_close,
                      'IsSynthetic':bool(row.is_synthetic)})
        # The bar's close is observed only AFTER all t-day execution is done.
        pending=None
        if not hold and pd.notna(row.ma):
            qualify=row.signal_close >= (1+cfg.entry_buffer)*row.ma
            exit_now=row.signal_close < (1+cfg.exit_buffer)*row.ma
            if shares>0 and exit_now:
                pending=('sell',0)
                stage=0
            elif shares==0 and qualify:
                pending=('buy',1)
            elif shares>0 and stage<5 and qualify:
                pending=('buy',stage+1)
    daily_df=pd.DataFrame(daily).set_index('Date')
    trades_df=pd.DataFrame(trades)
    return daily_df,trades_df


def performance(equity:pd.DataFrame,trades:pd.DataFrame|None=None)->dict:
    val=equity.NAV.astype(float)
    if len(val)<2:raise ValueError('need at least 2 NAV points')
    ret=val.pct_change().dropna();annual=252
    cagr=(val.iloc[-1]/10000)**(annual/(len(val)-1))-1
    dd=val/val.cummax()-1
    return {
        'Start':str(val.index[0].date()),'End':str(val.index[-1].date()),
        'Days':len(val),'FinalWealth':round(val.iloc[-1],2),
        'CumulativeReturn':round(val.iloc[-1]/10000-1,5),
        'CAGR':round(cagr,5),'MaxDrawdown':round(dd.min(),5),
        'Sharpe0':round(float(np.sqrt(annual)*ret.mean()/ret.std(ddof=1)),4),
        'AnnualizedVolatility':round(float(ret.std(ddof=1)*np.sqrt(annual)),5),
        'ExposedDays':int((equity.Shares>0).sum()),
        'CostUSD':round(float(trades.FrictionPaid.sum()),2) if trades is not None and not trades.empty else 0,
        'BuyOrders':int(trades.Action.str.startswith('BUY').sum()) if trades is not None and not trades.empty else 0,
        'SellOrders':int((trades.Action=='SELL').sum()) if trades is not None and not trades.empty else 0
    }


def chart_equity(dfs: dict[str,pd.DataFrame],name:str,out:Path):
    plt.figure(figsize=(11.8,6.3))
    for label,x in dfs.items():
        plt.plot(x.index,x.NAV/10000,label=label,linewidth=1.6)
    plt.yscale('log')
    plt.title(name+' | Growth of $1 (log scale)')
    plt.ylabel('Wealth multiple, log scale')
    plt.xlabel('Calendar date')
    plt.grid(alpha=.25);plt.legend(fontsize=9,ncol=2);plt.tight_layout()
    plt.savefig(out,dpi=190);plt.close()


def chart_drawdown(dfs: dict[str,pd.DataFrame],name:str,out:Path):
    plt.figure(figsize=(11.8,5.7))
    for label,x in dfs.items():
        nav=x.NAV
        dd=100*(nav/nav.cummax()-1)
        plt.plot(x.index,dd,label=label,linewidth=1.35)
    plt.title(name+' | Underwater drawdown')
    plt.ylabel('Drawdown (%)');plt.ylim(-100,5)
    plt.grid(alpha=.25);plt.legend(fontsize=9,ncol=2);plt.tight_layout()
    plt.savefig(out,dpi=190);plt.close()


def chart_grid(grid:pd.DataFrame,out:Path):
    fig,axes=plt.subplots(1,2,figsize=(12,5.1),sharey=True)
    for ax,ticker in zip(axes,['SPXL','TQQQ']):
        subset=grid[(grid.Ticker==ticker)&(grid.ExitBuffer==-0.03)]
        mat=subset.pivot(index='EntryBuffer',columns='Lookback',values='CAGR').sort_index()
        image=ax.imshow(100*mat.to_numpy(),origin='lower',aspect='auto',cmap='viridis')
        ax.set_xticks(range(len(mat.columns)),mat.columns)
        ax.set_yticks(range(len(mat.index)),[f'{100*v:.0f}%' for v in mat.index])
        ax.set_title(ticker+' CAGR (%) | exit -3%')
        ax.set_xlabel('SMA lookback (days)')
        if ticker=='SPXL':ax.set_ylabel('Entry threshold')
        for i in range(len(mat)):
            for j in range(len(mat.columns)):
                ax.text(j,i,f'{100*mat.iloc[i,j]:.1f}',ha='center',va='center',fontsize=10,color='white')
        fig.colorbar(image,ax=ax,shrink=.85)
    plt.tight_layout();plt.savefig(out,dpi=190);plt.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fetch',action='store_true',help='download exact pinned raw archives first')
    parser.add_argument('--no-figures',action='store_true')
    args=parser.parse_args()
    if args.fetch:
        from fetch_data import fetch
        fetch()
    markets=build_market()
    (ROOT/'data/derived').mkdir(parents=True,exist_ok=True)
    (ROOT/'data/results').mkdir(parents=True,exist_ok=True)
    (ROOT/'figures').mkdir(parents=True,exist_ok=True)
    for ticker,market in markets.items():
        market.to_csv(ROOT/'data/derived'/f'market_{ticker}.csv',float_format='%.8f')
    metrics=[];grid=[];costs=[];regimes=[]
    for label,start in [('full','1999-12-22'),('real','2010-02-11')]:
        curves={}
        for ticker in PAIRS:
            data=markets[ticker]
            for kind in ('trend','buyhold'):
                equity,trade=backtest(data,start,hold=(kind=='buyhold'))
                key=f'{ticker}_{kind}';curves[key]=equity
                report=performance(equity,trade)
                metrics.append({'Period':label,'Ticker':ticker,'Strategy':kind,**report})
                equity.to_csv(ROOT/'data/results'/f'equity_daily_{label}_{key}.csv',float_format='%.8f')
                trade.to_csv(ROOT/'data/results'/f'trades_{label}_{key}.csv',index=False,float_format='%.8f')
        if not args.no_figures:
            chart_equity(curves,'Full synthetic+real, 1999-12 to 2026-11' if label=='full' else 'Real ETF common window, 2010-02 to 2026-11',ROOT/'figures'/f'equity_{label}.png')
            chart_drawdown(curves,'Full 1999-2026' if label=='full' else 'Real ETFs 2010-2026',ROOT/'figures'/f'drawdown_{label}.png')
    for ticker in PAIRS:
        for window in [150,200,250]:
            for entry in [0.02,0.04,0.06]:
                for exit_threshold in [-0.01,-0.03,-0.05]:
                    cfg=Config(window,entry,exit_threshold)
                    eq,tr=backtest(markets[ticker],'2010-02-11',cfg=cfg)
                    perf=performance(eq,tr)
                    grid.append({'Ticker':ticker,'Lookback':window,'EntryBuffer':entry,
                                 'ExitBuffer':exit_threshold,'CAGR':perf['CAGR'],
                                 'MaxDrawdown':perf['MaxDrawdown'],'Sharpe0':perf['Sharpe0']})
        for cost in [0.0005,0.001,0.002,0.005]:
            eq,tr=backtest(markets[ticker],'2010-02-11',cfg=Config(transaction_cost=cost))
            perf=performance(eq,tr)
            costs.append({'Ticker':ticker,'OneWayCost':cost,**perf})
        for epoch,begin,end in [('early_2010_2017','2010-02-11','2017-12-29'),
                                ('late_2018_2026','2018-01-02',ASOF),
                                ('synthetic_1999_2008','1999-12-22','2008-11-04')]:
            eq,tr=backtest(markets[ticker],begin,end)
            regimes.append({'Ticker':ticker,'Epoch':epoch,**performance(eq,tr)})
    pd.DataFrame(metrics).to_csv(ROOT/'data/results'/'summary_metrics.csv',index=False)
    grid_df=pd.DataFrame(grid)
    grid_df.to_csv(ROOT/'data/results'/'parameter_grid_2010.csv',index=False)
    pd.DataFrame(costs).to_csv(ROOT/'data/results'/'cost_sensitivity.csv',index=False)
    pd.DataFrame(regimes).to_csv(ROOT/'data/results'/'epoch_analysis.csv',index=False)
    if not args.no_figures:chart_grid(grid_df,ROOT/'figures'/'parameter_plateau.png')
    print(pd.DataFrame(metrics)[['Period','Ticker','Strategy','CAGR','MaxDrawdown','Sharpe0','FinalWealth']].to_string(index=False))

if __name__=='__main__':main()
