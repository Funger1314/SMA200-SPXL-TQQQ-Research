# LEGACY (v1/v2) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Fetch pinned market-data archives from their original GitHub maintainers.

The snapshots were retrieved on 2026-11-12. The script verifies each file's
Git-blob SHA-1 and FAILS if upstream bytes have changed. Data use and
redistribution remain subject to each upstream source's terms.
"""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]

def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()

def fetch():
    cfg=json.loads((ROOT/'data/sources.json').read_text())
    output=ROOT/'data/raw'
    output.mkdir(parents=True,exist_ok=True)
    for ticker, spec in cfg['sources'].items():
        url=f"https://raw.githubusercontent.com/{spec['repo']}/{spec['branch']}/{spec['path']}"
        request=urllib.request.Request(url,headers={'User-Agent':'sma200-research-replication/1.0'})
        with urllib.request.urlopen(request, timeout=45) as response:
            content=response.read()
        actual=git_blob_sha(content)
        expected=spec['git_blob_sha1']
        if actual != expected:
            raise RuntimeError(f'{ticker} changed: expected git blob {expected}, got {actual}. Do not silently mix data revisions.')
        target=output/f'{ticker}.csv'
        target.write_bytes(content)
        print(f'{ticker}: {len(content):,} bytes, SHA verified: {target}')

if __name__=='__main__':fetch()
