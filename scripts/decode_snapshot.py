# LEGACY (v1) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Decode audited monthly NAV snapshots carried in the repository.

Snapshot values are log-quantized at 1e-4; this preserves monthly chart
resolution but is NOT the original daily OHLC market data.
"""
from pathlib import Path
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
COLUMN_NAMES = ['SPXL_strategy', 'TQQQ_strategy', 'SPXL_buyhold', 'TQQQ_buyhold']


def decode_monthly(start: str, length: int, filename: str) -> pd.DataFrame:
    s = (ROOT / 'data' / 'results' / filename).read_text(encoding='ascii').strip()
    assert len(s) == length * 4 * 3, (filename, len(s), length)
    index = pd.period_range(start, periods=length, freq='M').to_timestamp('M')
    rows = []
    for i in range(length):
        encoded = s[i * 12:(i + 1) * 12]
        values = []
        for j in range(4):
            code = encoded[j * 3:(j + 1) * 3]
            q = (ALPHA.index(code[0]) << 12) + (ALPHA.index(code[1]) << 6) + ALPHA.index(code[2])
            values.append(10000 * math.exp(q / 10000.0 - 14.0))
        rows.append(values)
    return pd.DataFrame(rows, index=index, columns=COLUMN_NAMES).rename_axis('Month')


def main():
    out = ROOT / 'data' / 'results'
    for key, n, start in [('1999',324,'1999-12'),('2010',202,'2010-02')]:
        df = decode_monthly(start,n,f'monthly_{key}.packed')
        target=out / f'monthly_equity_{key}.csv'
        df.round(5).to_csv(target, date_format='%Y-%m-%d')
        print(f'{target}: {len(df)} rows; tail {df.iloc[-1].round().to_dict()}')

if __name__ == '__main__': main()
