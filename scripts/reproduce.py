# LEGACY (v1/v2) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Primary v2 reproducibility entrypoint.

Usage:
  python scripts/reproduce.py --fetch
  python scripts/reproduce.py --tail-mode public
  python scripts/reproduce.py --tail-mode licensed-local

Compatibility exports Config/backtest/performance preserve old offline unit tests;
use scripts/reproduce_legacy_v1.py only to reconstruct the ORIGINAL v1 audit,
not to claim corrected research. The actual v2 engine is review_revision.py.
"""
from reproduce_legacy_v1 import Config,backtest,performance

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--fetch',action='store_true',help='fetch pinned public archives then recompute')
    p.add_argument('--tail-mode',default='public',choices=['public','licensed-local'])
    p.add_argument('--no-figures',action='store_true')
    args=p.parse_args()
    if args.fetch:
        from fetch_data import fetch
        fetch()
    from review_revision import run_all
    result=run_all(tail_mode=args.tail_mode,figures=not args.no_figures)
    print(result[['Period','Ticker','Benchmark','CAGR','MaxDrawdown','SharpeRF','AverageWeight']].to_string(index=False))

if __name__=='__main__':main()
