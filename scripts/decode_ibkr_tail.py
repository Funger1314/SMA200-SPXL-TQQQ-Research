# LEGACY (v1) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Losslessly decode 2022-2026 IBKR opens/closes to cent precision.

Encoding uses 1 base64url character for day gap from the previous source date
and 3 chars each for open and close in integer USD cents (18 bits each).
High/low/volume were not retained; only open/close are required by the strategy.
The SPXL tail spans 998 daily bars. No data are guessed or interpolated.
"""
from pathlib import Path
from datetime import date, timedelta
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ALPHA='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
SOURCES={'SPY':('2026-07-23',79),'SPXL':('2022-11-18',998),
         'QQQ':('2026-08-28',53),'TQQQ':('2026-08-28',53)}

def unpack(ticker):
    edge, n=SOURCES[ticker]
    encoded=(ROOT/'data/raw'/f'IBKR_{ticker}.packed').read_text(encoding='ascii').strip()
    assert len(encoded)==n*7, (ticker,len(encoded),n*7)
    dt=date.fromisoformat(edge)
    out=[]
    for i in range(n):
        record=encoded[i*7:(i+1)*7]
        dt=dt+timedelta(days=ALPHA.index(record[0]))
        def value(z):
            return ((ALPHA.index(z[0]) << 12) + (ALPHA.index(z[1]) << 6) + ALPHA.index(z[2]))/100
        out.append({'Date':str(dt),'Open':value(record[1:4]),'Close':value(record[4:7])})
    frame=pd.DataFrame(out)
    assert frame.Date.is_unique and frame.Date.is_monotonic_increasing
    assert frame.iloc[-1]['Date']=='2026-11-12', ticker
    return frame

if __name__=='__main__':
    for ticker in SOURCES:
        df=unpack(ticker)
        out=ROOT/'data/derived'/f'ibkr_tail_{ticker}.csv'
        out.parent.mkdir(exist_ok=True)
        df.to_csv(out,index=False,float_format='%.2f')
        print(ticker,len(df),df.iloc[0].to_dict(),df.iloc[-1].to_dict(),out)
