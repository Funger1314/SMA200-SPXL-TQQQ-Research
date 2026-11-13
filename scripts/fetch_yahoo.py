"""Re-download the four vendor files with yfinance and record provenance.

python scripts/fetch_yahoo.py [--end 2026-08-07]
Writes data/raw/{SPY,SPXL,QQQ,TQQQ}.csv (auto_adjust=False: Open, High, Low, Close,
Adj Close, Volume) and data/raw/DOWNLOAD_MANIFEST.json with the UTC download time,
yfinance version and SHA-256 of every file. Yahoo revises dividend adjustments
retroactively, so a fresh download can differ from the audited files; compare the
hashes with data/sources.json -> v3/v4 before reproducing the paper's numbers.
"""
import argparse, datetime as dt, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = {'SPY': '1993-01-29', 'QQQ': '1999-03-10', 'SPXL': '2008-11-05', 'TQQQ': '2010-02-09'}


def main():
    import yfinance as yf
    ap = argparse.ArgumentParser(); ap.add_argument('--end', default='2026-08-07'); a = ap.parse_args()
    out = ROOT / 'data/raw'; out.mkdir(parents=True, exist_ok=True)
    man = {'downloaded_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
           'yfinance': yf.__version__, 'auto_adjust': False, 'end_exclusive': a.end, 'files': {}}
    for t, s in START.items():
        df = yf.download(t, start=s, end=a.end, auto_adjust=False, actions=False, progress=False, threads=False)
        df.to_csv(out / f'{t}.csv')
        man['files'][t] = {'rows': len(df), 'first': str(df.index[0].date()), 'last': str(df.index[-1].date()),
                           'sha256': hashlib.sha256((out / f'{t}.csv').read_bytes()).hexdigest()}
    (out / 'DOWNLOAD_MANIFEST.json').write_text(json.dumps(man, indent=2))
    print(json.dumps(man, indent=2))


if __name__ == '__main__':
    main()
