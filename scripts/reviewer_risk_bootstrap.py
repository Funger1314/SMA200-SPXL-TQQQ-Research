# LEGACY (v2) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Reviewer-requested *paired* risk bootstrap from ARCHIVED MONTH-END NAV.

Risk results are MONTHLY approximations and CANNOT replace daily path MDD,
CVaR, Ulcer, CDaR. Monthly sampling hides crisis-time drawdown. The pairing
and dependence are respected by resampling the same month indices together.
A fixed-length circular block bootstrap is NOT stationary bootstrap.
No post-selection p-values and no proof of effective timing.
"""
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def stat(r):
    r=np.asarray(r,dtype=float)
    nav=np.cumprod(np.r_[1,1+r]);dd=nav/np.maximum.accumulate(nav)-1
    st=np.std(r,ddof=1);cagr=np.exp(np.mean(np.log1p(r))*12)-1
    return {'Sharpe0':np.mean(r)*np.sqrt(12)/st if st>0 else np.nan,
            'MaxDrawdownMonthly':dd.min(),'CDaR10Monthly':np.mean(dd[dd<=np.quantile(dd,.1)]),
            'CVaR5Monthly':np.mean(r[r<=np.quantile(r,.05)]),'UlcerMonthly':np.sqrt(np.mean(dd**2)),
            'AnnualLogGrowth':np.mean(np.log1p(r))*12}

def evaluate(n=5000,seed=20261112,block=12):
    x=pd.read_csv(ROOT/'data/results/monthly_equity_2010.csv')
    print('available columns:',list(x.columns))
    rng=np.random.default_rng(seed);output=[]
    for ticker in ['SPXL','TQQQ']:
        a=x[f'{ticker}_strategy'].astype(float).pct_change().dropna().to_numpy()
        b=x[f'{ticker}_buyhold'].astype(float).pct_change().dropna().to_numpy()
        assert len(a)==len(b) and len(a)>50
        original_a=stat(a);original_b=stat(b)
        dist={k:[] for k in original_a}
        for _ in range(n):
            starts=rng.integers(0,len(a),size=(len(a)+block-1)//block)
            ix=np.concatenate([(np.arange(block)+j)%len(a) for j in starts])[:len(a)]
            za=stat(a[ix]);zb=stat(b[ix])
            for key in dist:dist[key].append(za[key]-zb[key])
        for metric,values in dist.items():
            val=np.asarray(values)
            output.append({'Ticker':ticker,'RiskMetric':metric,'DifferenceStrategyMinusBuyHold':original_a[metric]-original_b[metric],
                           'CI2_5':np.quantile(val,.025),'CI97_5':np.quantile(val,.975),
                           'FractionPositive':(val>0).mean(),
                           'DateGranularity':'month-end only','Bootstrap':'paired circular fixed block (12 months)',
                           'N':len(a),'Replicates':n,'Seed':seed})
    r=pd.DataFrame(output)
    out=ROOT/'data/v2_results';out.mkdir(exist_ok=True)
    r.to_csv(out/'paired_monthly_risk_bootstrap_legacy.csv',index=False)
    return r
if __name__=='__main__':
    print(evaluate().to_string(index=False))
