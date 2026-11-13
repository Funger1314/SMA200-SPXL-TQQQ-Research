# LEGACY (v1) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Indicative paired monthly block-bootstrap intervals, not post-selection p-values.

Annualized average LOG excess return strategy minus leveraged ETF buy-and-hold.
Monthly block length 12, 5000 replicates, circular stationary-like resampling.
Only a descriptive sensitivity check; does not undo data snooping.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def bootstrap(seed=20261112,replicates=5000,block=12):
    d=pd.read_csv(ROOT/'data/results/monthly_equity_2010.csv',index_col=0)
    rng=np.random.default_rng(seed)
    records=[]
    for ticker in ['SPXL','TQQQ']:
        a=np.diff(np.log(d[f'{ticker}_strategy'].values))
        b=np.diff(np.log(d[f'{ticker}_buyhold'].values))
        dif=a-b;n=len(dif)
        values=[]
        for _ in range(replicates):
            indices=[]
            while len(indices)<n:
                start=int(rng.integers(n))
                indices.extend((start+j)%n for j in range(block))
            values.append(12*dif[np.asarray(indices[:n])].mean())
        lo,hi=np.quantile(values,[.025,.975])
        records.append({
            'Ticker':ticker,'MonthlyObservations':n,'BootstrapReplicates':replicates,
            'BlockMonths':block,'Seed':seed,
            'AvgAnnualLogExcessReturnPct':float(1200*dif.mean()),
            'CI95LowerPct':float(100*lo),'CI95UpperPct':float(100*hi),
            'DescriptiveFractionAboveZero':float(np.mean(np.asarray(values)>0)),
            'Interpretation':'Not corrected for ex-post parameter selection or market nonstationarity'
        })
    result=pd.DataFrame(records)
    result.to_csv(ROOT/'data/results/snapshot_block_bootstrap.csv',index=False)
    return result

if __name__=='__main__':print(bootstrap().to_string(index=False))
