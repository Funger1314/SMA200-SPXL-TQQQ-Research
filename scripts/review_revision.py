# LEGACY (v2) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Independent reviewer-response research engine (v2).

Will not publish new v2 performance numbers without verified local OHLC inputs.
Reads market archives downloaded by scripts/fetch_data.py, enforces
corporate-action adjustments, checks vendor stitch anchor, and computes
interest-bearing cash, three realistic controls, risk metrics and transactions.
No broker credentials or trading access. Does NOT execute orders.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rates import annual_cash_rate

ROOT=Path(__file__).resolve().parents[1]
END='2026-11-12'
PAIRS={'SPXL':'SPY','TQQQ':'QQQ'}
STARTS={'full':'1999-12-22','real':'2010-02-11'}
TAIL_ANCHORS={'SPY':('2026-07-23',738.18),'SPXL':('2022-11-18',69.92),
              'QQQ':('2026-08-28',716.43),'TQQQ':('2026-08-28',71.85)}

@dataclass(frozen=True)
class Parameters:
    sma_days:int=200
    entry:float=.04
    exit:float=-.03
    fee:float=.001
    fin_spread:float=0.0 # extra synthetic annual borrowing spread on TWO funded units
    synth_expense:float=.0095
    # Fixed volatility target: research alternative, not optimized to match realized risk.
    vol_target:float=.30
    vol_window:int=63
    rebalance_days:int=5


def load_adjusted(ticker:str, tail_mode:str='public')->pd.DataFrame:
    path=ROOT/'data/raw'/f'{ticker}.csv'
    if not path.exists():raise FileNotFoundError(f'{path} not found. Use scripts/fetch_data.py or place licensed archives locally.')
    original=pd.read_csv(path)
    cols={str(x).lower().replace(' ','').strip():x for x in original.columns}
    needed=['date','open','close']
    if any(x not in cols for x in needed):raise ValueError(f'{ticker}: missing {needed}')
    d=pd.to_datetime(original[cols['date']],errors='raise')
    c=pd.to_numeric(original[cols['close']],errors='raise').to_numpy(dtype=float)
    o=pd.to_numeric(original[cols['open']],errors='raise').to_numpy(dtype=float)
    # SPY and SPXL archives contain Adj Close; QQQ and TQQQ are already auto-adjusted.
    if ticker in ('SPY','SPXL'):
        if 'adjclose' not in cols:raise ValueError(f'{ticker}: Adj Close required for total-return adjustment')
        adj=pd.to_numeric(original[cols['adjclose']],errors='raise').to_numpy(dtype=float)
        factor=adj/c
        c=adj;o=o*factor
    if (o<=0).any() or (c<=0).any():raise ValueError('nonpositive prices')
    df=pd.DataFrame({'Open':o,'Close':c},index=d).sort_index()
    if df.index.duplicated().any():raise ValueError('duplicate dates')
    edge,anchor=TAIL_ANCHORS[ticker]
    ed=pd.Timestamp(edge)
    if ed not in df.index:raise ValueError(f'{ticker}: expected archive overlap date {edge} missing')
    last=df.index.max()
    if last!=ed:raise ValueError(f'{ticker}: pinned archive end mismatch {last} vs {edge}')
    # The two independent originally accessed sources agree exactly at 1bp level.
    # No arbitrary scale multiplication is allowed in v2.
    if abs(df.loc[ed,'Close']/anchor-1)>1e-4:
        raise ValueError(f'{ticker} vendor stitch FAILED: {df.loc[ed,"Close"]} vs {anchor}, >1bp; do not silently append or rescale')
    private=ROOT/'data/derived'/f'ibkr_tail_{ticker}.csv'
    if tail_mode=='licensed-local' and private.exists():
        tail=pd.read_csv(private,parse_dates=['Date']).set_index('Date')[['Open','Close']]
        provenance='private local IBKR-derived bars'
    elif tail_mode=='public':
        import yfinance as yf
        recent=yf.download(ticker,start=(ed-pd.Timedelta(days=8)).strftime('%Y-%m-%d'),end='2026-11-13',
                          auto_adjust=True,interval='1d',progress=False,threads=False)
        if isinstance(recent.columns,pd.MultiIndex):recent.columns=recent.columns.get_level_values(0)
        if recent.empty or ed not in recent.index:raise ValueError(f'{ticker} public overlapping day missing; stitch aborted')
        recent.index=pd.DatetimeIndex(recent.index).tz_localize(None)
        public_anchor=float(recent.loc[ed,'Close'])
        if abs(df.loc[ed,'Close']/public_anchor-1)>1e-4:
            raise ValueError(f'{ticker}: public tail not aligned within 1bp at {edge}: archive={df.loc[ed,"Close"]:.4f}, tail={public_anchor:.4f}')
        tail=recent[['Open','Close']].loc[recent.index>ed].astype(float)
        provenance='public auto-adjusted Yahoo tail'
    else:
        raise ValueError(f'{ticker}: licensed tail unavailable locally; select --tail-mode public or supply vendor data')
    if tail.empty:raise ValueError(f'{ticker}: empty tail')
    if tail.index.min()<=ed:raise ValueError('tail date not after archive date')
    join=pd.concat([df,tail]).sort_index()
    if join.index.has_duplicates or not join.index.is_monotonic_increasing or join.index[-1]!=pd.Timestamp(END):
        raise ValueError(f'{ticker}: failed date/endpoint join audit')
    join.attrs['provenance']=provenance
    join.attrs['anchor_error_bps']=1e4*(df.loc[ed,'Close']/anchor-1)
    return join


def synthetic_preinception(under:pd.DataFrame,lev:pd.DataFrame,params:Parameters)->pd.DataFrame:
    """Backward-anchored 3x daily TOTAL-return proxy, 2 funded units + fee.
    For each historical day t, r_f,t uses LAST month-end available before t.
    The open proxy applies half the daily fee/financing over the overnight piece;
    this is explicitly an approximation not a historical executable quote.
    """
    idx=under.index.get_loc(lev.index[0]);assert isinstance(idx,int) and idx>0
    rf=annual_cash_rate(under.index).to_numpy()
    def factor(i):
        carry=(2*(rf[i]+params.fin_spread)+params.synth_expense)/252
        return 1+3*(under.Close.iloc[i]/under.Close.iloc[i-1]-1)-carry
    first=factor(idx)
    if first<=0:raise ValueError('synthetic leverage bankruptcy')
    current=float(lev.Close.iloc[0])/first
    rows=[]
    for i in range(idx-1,0,-1):
        fac=factor(i)
        if fac<=0:raise ValueError(f'unmodelable synthetic fund day {under.index[i]}')
        prior=current/fac
        overnight=(2*(rf[i]+params.fin_spread)+params.synth_expense)/(2*252)
        opening=prior*(1+3*(under.Open.iloc[i]/under.Close.iloc[i-1]-1)-overnight)
        if opening<=0:raise ValueError('synthetic opening price nonpositive')
        rows.append((under.index[i],opening,current))
        current=prior
    return pd.DataFrame(rows,columns=['Date','Open','Close']).set_index('Date').sort_index()


def build_pair(under:pd.DataFrame,leveraged:pd.DataFrame,params:Parameters)->pd.DataFrame:
    # Common 1999 research universe: avoid requiring DTB3 before the archived
    # study's earliest available signal (QQQ launched in March 1999).
    under=under.loc['1999-03-10':].copy()
    syn=synthetic_preinception(under,leveraged,params)
    joined=pd.concat([syn,leveraged]).sort_index()
    if joined.index.has_duplicates:raise ValueError('synthetic-real overlap')
    market=under.rename(columns={'Open':'signal_open','Close':'signal_close'}).join(
         joined.rename(columns={'Open':'asset_open','Close':'asset_close'}),how='inner')
    market['sma']=market.signal_close.rolling(params.sma_days,min_periods=params.sma_days).mean()
    market['rf']=annual_cash_rate(market.index)
    market['synthetic']=market.index<leveraged.index[0]
    market['asset_ret']=market.asset_close.pct_change()
    return market


def benchmark(market:pd.DataFrame,start:str,mode:str='trend',params:Parameters=Parameters(),
              fixed_weight:float=1.0,stop:str=END)->tuple[pd.DataFrame,pd.DataFrame]:
    if mode not in ('trend','leveraged_hold','unlevered_hold','fixed_weight','vol_target'):
        raise ValueError('unknown mode')
    d=market.loc[start:stop].copy();assert len(d)>2
    cash=10000.0;shares=0.;stage=0;pending=None;rows=[];orders=[]
    use_under=(mode=='unlevered_hold')
    for i,(date,row) in enumerate(d.iterrows()):
        o=float(row.signal_open if use_under else row.asset_open)
        c=float(row.signal_close if use_under else row.asset_close)
        if i>0:cash*=1+float(row.rf)/252
        action=None;notional=0.;fee=0.
        if i==0 and mode in ('leveraged_hold','unlevered_hold','fixed_weight'):
            pending=('target',1. if mode!='fixed_weight' else float(fixed_weight))
        if pending is not None:
            typ,target=pending
            equity_open=cash+shares*o
            if typ=='exit':target=0
            if typ=='buy_stage':
                stage=int(target);target=min(1,stage*.2)
                # Buy-only: never sell an appreciating partial sleeve.
                desired=max(0.,equity_open*target-shares*o)
                notional=min(desired,cash/(1+params.fee))
                if notional>1e-10:
                    fee=notional*params.fee;cash-=notional+fee;shares+=notional/o;action=f'BUY_{stage}'
            elif typ=='target' or typ=='exit':
                delta=equity_open*float(target)-shares*o
                if delta>1e-10:
                    notional=min(delta,cash/(1+params.fee))
                    fee=notional*params.fee;shares+=notional/o;cash-=notional+fee;action='REBALANCE_BUY'
                elif delta< -1e-10:
                    notional=min(-delta,shares*o)
                    fee=notional*params.fee;shares-=notional/o;cash+=notional-fee;action='SELL' if typ=='exit' else 'REBALANCE_SELL'
                if typ=='exit':stage=0
        nav=cash+shares*c
        if action is not None:orders.append({'Date':date,'Action':action,'FillOpen':o,'Notional':notional,'FeeAndSlippage':fee,'SharesAfter':shares,'NAVClose':nav})
        rows.append({'Date':date,'NAV':nav,'Cash':cash,'Shares':shares,'Weight':shares*c/nav,'RFAnnual':row.rf,
                     'SignalClose':row.signal_close,'SMA':row.sma,'AssetClose':row.asset_close,
                     'Synthetic':bool(row.synthetic)})
        pending=None
        if mode=='trend' and pd.notna(row.sma):
            if shares>0 and row.signal_close<(1+params.exit)*row.sma:pending=('exit',0)
            elif shares==0 and row.signal_close>=(1+params.entry)*row.sma:pending=('buy_stage',1)
            elif shares>0 and stage<5 and row.signal_close>=(1+params.entry)*row.sma:pending=('buy_stage',stage+1)
        elif mode=='fixed_weight' and i%21==20:
            pending=('target',float(fixed_weight))
        elif mode=='vol_target' and i>=params.vol_window and i%params.rebalance_days==0:
            # The t-day return and trailing lookback are known at close(t);
            # target implemented at open(t+1). Prior-to-fill only.
            vol=market.loc[:date,'asset_ret'].iloc[-params.vol_window:].std(ddof=1)*np.sqrt(252)
            if np.isfinite(vol) and vol>0:pending=('target',min(1.0,params.vol_target/vol))
    result=pd.DataFrame(rows).set_index('Date');blotter=pd.DataFrame(orders)
    return result,blotter


def metrics(eq:pd.DataFrame,trades:pd.DataFrame|None=None)->dict:
    v=eq.NAV.astype(float);ret=v.pct_change().iloc[1:]
    rf=eq.RFAnnual.iloc[1:]/252
    excess=ret-rf
    dd=v/v.cummax()-1
    downside=ret.quantile(.05)
    underwater=dd<0
    groups=(underwater!=underwater.shift(1)).cumsum()
    durations=underwater.groupby(groups).sum()
    cagr=(v.iloc[-1]/10000)**(252/(len(v)-1))-1
    mdd=float(dd.min())
    r={'Start':v.index[0].strftime('%Y-%m-%d'),'End':v.index[-1].strftime('%Y-%m-%d'),
       'NAVEnd':float(v.iloc[-1]),'CAGR':float(cagr),'MaxDrawdown':mdd,
       'Calmar':float(cagr/abs(mdd)) if mdd<0 else np.nan,
       'SharpeRF':float(excess.mean()/ret.std(ddof=1)*np.sqrt(252)),
       'AnnualVol':float(ret.std(ddof=1)*np.sqrt(252)),
       'CVaR5Daily':float(ret[ret<=downside].mean()),
       'CDaR10Daily':float(dd[dd<=dd.quantile(.1)].mean()),
       'UlcerIndex':float(np.sqrt(np.mean(np.square(dd)))),
       'MeanDrawdown':float(dd.mean()),
       'TimeUnderwater':float(underwater.mean()),
       'LongestUnderwaterTradingDays':int(durations.max()),
       'AverageWeight':float(eq.Weight.mean()),
       'ExposedDaysFraction':float((eq.Shares>0).mean()),
       'FrictionPaid':float(trades.FeeAndSlippage.sum()) if trades is not None and len(trades) else 0.,
       'NumOrders':int(len(trades)) if trades is not None else 0}
    return r


def regime_table(market:pd.DataFrame,start:str)->pd.DataFrame:
    """At close t observe signal/SMA; compute return/volatility over *next* day t+1."""
    d=market.loc[start:].copy();d['Regime']=np.where(d.signal_close>=1.04*d.sma,'Above +4%',
                   np.where(d.signal_close<.97*d.sma,'Below -3%','Middle'))
    d['FutureReturn']=d.signal_close.shift(-1)/d.signal_close-1
    d['FutureRF']=d.rf.shift(-1)
    out=[]
    for name,g in d.iloc[:-1].groupby('Regime'):
        r=g.FutureReturn.dropna();mu=float(r.mean()*252);sigma=float(r.std(ddof=1)*np.sqrt(252));rf=float(g.FutureRF.mean());
        out.append({'RegimeAtT':name,'Observations':len(r),'UnderlyingMuAnnual':mu,
                    'UnderlyingVolAnnual':sigma,'RFAnnual':rf,
                    'IllustrativeLeveredLogGrowth':3*mu-4.5*sigma**2-2*rf-.0095})
    return pd.DataFrame(out)


def rolling_entry_analysis(market:pd.DataFrame,mode:str,params:Parameters,first='2010-02-11',last='2023-12-31')->pd.DataFrame:
    dates=pd.Series(market.loc[first:last].index,index=market.loc[first:last].index)
    starts=dates.groupby(dates.index.to_period('M')).first().values
    items=[]
    for s in starts:
        eq,tr=benchmark(market,pd.Timestamp(s).strftime('%Y-%m-%d'),mode=mode,params=params)
        if len(eq)<252:continue
        mm=metrics(eq,tr);items.append({'Start':mm['Start'],'CAGR':mm['CAGR'],
                                        'MaxDrawdown':mm['MaxDrawdown'],'EndingNAV':mm['NAVEnd']})
    return pd.DataFrame(items)


def pair_trades(trades:pd.DataFrame, market:pd.DataFrame)->pd.DataFrame:
    if trades.empty:return pd.DataFrame()
    records=[];prior_sell=None
    for _,row in trades.iterrows():
        if row.Action=='SELL':
            prior_sell={'SellDate':row.Date,'SellPrice':float(row.FillOpen),'ProceedsAfterFees':row.Notional-row.FeeAndSlippage}
        elif row.Action=='BUY_1' and prior_sell is not None:
            # Counterfactual SPXL/TQQQ return if held between the exit open and
            # the next staged reentry open; *not* net skill or causally avoided losses.
            s=prior_sell.copy();s['ReentryDate']=row.Date;s['ReentryPrice']=float(row.FillOpen)
            s['ForegoneLeveredReturn']=float(row.FillOpen/prior_sell['SellPrice']-1)
            s['ReentryNotional']=float(row.Notional)
            records.append(s);prior_sell=None
    if prior_sell is not None:
        last=market.iloc[-1];s=prior_sell.copy();s.update({'ReentryDate':pd.NaT,
          'ReentryPrice':np.nan,'ForegoneLeveredReturn':last.asset_close/prior_sell['SellPrice']-1,
          'ReentryNotional':np.nan});records.append(s)
    return pd.DataFrame(records)


def run_all(tail_mode='public',figures=True):
    inputs={s:load_adjusted(s,tail_mode=tail_mode) for s in ('SPY','SPXL','QQQ','TQQQ')}
    folder=ROOT/'data/v2_results';folder.mkdir(exist_ok=True)
    fig=ROOT/'figures/v2';fig.mkdir(exist_ok=True)
    p=Parameters()
    reports=[];curves={}
    for target,under in PAIRS.items():
        market=build_pair(inputs[under],inputs[target],p)
        market.to_csv(ROOT/'data/derived'/f'v2_market_{target}.csv')
        for period,start in STARTS.items():
            base,tr=benchmark(market,start,'trend',p)
            average=metrics(base,tr)['AverageWeight']
            alternatives=[('trend',None),('leveraged_hold',None),('unlevered_hold',None),
                          ('fixed_weight',average),('vol_target',None)]
            for mode,w in alternatives:
                eq,orders=benchmark(market,start,mode,p,fixed_weight=1 if w is None else w)
                eq.to_csv(folder/f'{period}_{target}_{mode}_equity.csv',float_format='%.10f')
                orders.to_csv(folder/f'{period}_{target}_{mode}_orders.csv',index=False)
                reports.append({'Period':period,'Ticker':target,'Benchmark':mode,**metrics(eq,orders)})
                if mode=='trend':
                    pair_trades(orders,market).to_csv(folder/f'{period}_{target}_roundtrips.csv',index=False)
                if period=='real':curves[f'{target}_{mode}']=eq
        regime_table(market,'2010-02-11').to_csv(folder/f'{target}_regime_nextday.csv',index=False)
        rolling_entry_analysis(market,'trend',p).to_csv(folder/f'{target}_rolling_starts.csv',index=False)
    out=pd.DataFrame(reports)
    out.to_csv(folder/'benchmark_metrics.csv',index=False)
    if figures:
        fig1,ax=plt.subplots(figsize=(11,6))
        for name,eq in curves.items():ax.plot(eq.index,eq.NAV/10000,label=name,lw=1.4)
        ax.set_yscale('log');ax.legend(ncol=2,fontsize=8);ax.grid(alpha=.2)
        ax.set_title('2010–2026: strategy vs 1x, fixed exposure and vol-managed benchmarks')
        ax.set_ylabel('Growth of $1 (log scale)');fig1.tight_layout();fig1.savefig(fig/'benchmark_equity_real.png',dpi=175);plt.close(fig1)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--tail-mode',default='public',choices=['public','licensed-local']);ap.add_argument('--no-figures',action='store_true')
    a=ap.parse_args()
    results=run_all(tail_mode=a.tail_mode,figures=not a.no_figures)
    print(results[['Period','Ticker','Benchmark','CAGR','MaxDrawdown','SharpeRF','AverageWeight']].to_string(index=False))
