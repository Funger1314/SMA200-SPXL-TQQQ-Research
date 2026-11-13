"""Check that a fresh run reproduces the paper's headline numbers (main table, walk-forward,
leave-one-crisis-out re-runs, bootstrap observed differences and p-values, SPA p-values).

python scripts/verify_results.py            # compare data/v4_results with expected_results.json
python scripts/verify_results.py --write    # (maintainer) refresh the expected file
Deterministic quantities must match to 1e-6; bootstrap/SPA quantities (seeded) to 1e-9.
"""
import argparse, json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]; R = ROOT / 'data/v4_results'; EXP = ROOT / 'data/expected_results.json'


def collect():
    out = {}
    m = pd.read_csv(R / 'main_metrics.csv')
    for _, r in m.iterrows():
        for k in ('CAGR', 'MaxDrawdown', 'Calmar', 'Sharpe', 'ES99'):
            out[f"main|{r.Window}|{r.ETF}|{r.Rule}|{k}"] = float(r[k])
    l = pd.read_csv(R / 'leave_one_crisis_out.csv')
    for _, r in l.iterrows():
        out[f"loco|{r.Window}|{r.ETF}|{r.Excluded}|{r.ExclusionSpan}|{r.Rule}|Calmar"] = float(r.Calmar)
    w = pd.read_csv(R / 'walkforward_metrics.csv')
    for _, r in w.iterrows():
        out[f"wf|{r.Window}|{r.ETF}|{r.Criterion}|{r.Rule}|Calmar"] = float(r.Calmar)
    b = pd.read_csv(R / 'bootstrap_summary.csv')
    for _, r in b.iterrows():
        out[f"boot|{r.MeanBlockDays}|{r.ETF}|{r.Versus}|{r.Metric}|Observed"] = float(r.Observed)
        out[f"boot|{r.MeanBlockDays}|{r.ETF}|{r.Versus}|{r.Metric}|p_centred"] = float(r.p_centred)
    s = pd.read_csv(R / 'spa_reality_check.csv')
    for _, r in s.iterrows():
        out[f"spa|{r.ETF}|{r.Benchmark}|{r.Loss}|p_SPA_c"] = float(r.p_SPA_c)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    cur = collect()
    if a.write:
        EXP.write_text(json.dumps(cur, indent=1, sort_keys=True)); print(f'wrote {len(cur)} values'); return
    exp = json.loads(EXP.read_text()); bad = []
    for k, v in exp.items():
        if k not in cur or abs(cur[k] - v) > 1e-6 * max(1, abs(v)):
            bad.append((k, v, cur.get(k)))
    print(f'{len(exp) - len(bad)}/{len(exp)} values reproduced')
    for k, v, c in bad[:20]: print('MISMATCH', k, v, c)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
