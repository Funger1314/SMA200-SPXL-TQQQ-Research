"""Render the v4 manuscript tables (markdown) from data/v4_results."""
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; R = ROOT / 'data/v4_results'; T = ROOT / 'paper/tables_v4'
pc = lambda x: '—' if pd.isna(x) else f'{100*x:.1f}%'
pc2 = lambda x: '—' if pd.isna(x) else f'{100*x:.2f}%'
f3 = lambda x: '—' if pd.isna(x) else f'{x:.3f}'
pp = lambda x: '—' if pd.isna(x) else f'{100*x:+.1f}'
ii = lambda x: 'n.r.' if pd.isna(x) else f'{int(x)}'
def md(rows, cols, align=None):
    a = align or ['l'] + ['r'] * (len(cols) - 1)
    s = '| ' + ' | '.join(cols) + ' |\n|' + '|'.join(':--' if x == 'l' else '--:' for x in a) + '|\n'
    return s + ''.join('| ' + ' | '.join(str(v) for v in r) + ' |\n' for r in rows)
out = {}
ORDER = ['SMA rule', '3x hold', '1x hold', '1x SMA', 'Matched weight (ex ante)', 'Vol target 30%', 'Matched weight (ex post)']
SHORT = {'Matched weight (ex ante)': 'Matched weight, ex ante', 'Matched weight (ex post)': 'Matched weight, ex post †'}
# --- data
man = pd.read_csv(R / 'data_manifest.csv'); val = pd.read_csv(R / 'data_validation.csv')
rows = []
for _, r in man.iterrows():
    v = val[val.Ticker == r.Ticker]
    rows.append([r.Ticker, r.FirstBar, r.LastBar, r.Rows, r.SHA256[:12] + '…',
                 int((v.Status == 'FATAL').sum()), int((v.Status == 'WARN').sum())])
out['data'] = md(rows, ['File', 'First bar', 'Last bar', 'Rows', 'SHA-256', 'Fatal checks failed', 'Warnings'])
out['official'] = md(pd.read_csv(R / 'official_checks.csv').values.tolist(), ['ETF', 'Item', 'Issuer value', 'Yahoo / this study', 'Result'], ['l'] * 5)
ea = pd.read_csv(R / 'execution_audit.csv'); ea = ea[ea.ETF != 'all']
out['audit'] = md([[r.ETF, r.Rule, 'yes' if r.Decisions_unchanged_before_cut else 'NO', 'yes' if r.All_fills_at_that_days_open else 'NO', r.Orders] for _, r in ea.iterrows()],
                  ['ETF', 'Rule', 'Decisions before cut unchanged', 'All fills at that day\'s open', 'Orders'], ['l', 'l', 'r', 'r', 'r'])
# --- main
m = pd.read_csv(R / 'main_metrics.csv')
for per in ('real', 'full'):
    rows = []
    for lev in ('SPXL', 'TQQQ'):
        for k in ORDER:
            r = m[(m.Window == per) & (m.ETF == lev) & (m.Rule == k)].iloc[0]
            rows.append([lev, SHORT.get(k, k), pc(r.CAGR), pc(r.MaxDrawdown), f3(r.Calmar), f3(r.Sharpe), pc2(r.ES99),
                         f3(r.UlcerIndex), ii(r.RecoveryDays), ii(r.LongestUnderwaterDays), f'{r.AverageWeight:.2f}', int(r.NumOrders)])
    out[f'main_{per}'] = md(rows, ['ETF', 'Rule', 'CAGR', 'Max DD', 'Calmar', 'Sharpe', 'ES 99% (daily)', 'Ulcer',
                                   'Recovery (days)', 'Longest underwater (days)', 'Avg weight', 'Orders'], ['l', 'l'] + ['r'] * 10)
# --- 1x question
b = pd.read_csv(R / 'bootstrap_summary.csv'); w = pd.read_csv(R / 'walkforward_metrics.csv'); s = pd.read_csv(R / 'spa_reality_check.csv')
rows = []
for lev, und in (('SPXL', 'SPY'), ('TQQQ', 'QQQ')):
    a = m[(m.Window == 'real') & (m.ETF == lev)].set_index('Rule')
    f = m[(m.Window == 'full') & (m.ETF == lev)].set_index('Rule')
    bb = b[(b.MeanBlockDays == 252) & (b.ETF == lev) & (b.Versus == '1x hold')].set_index('Metric')
    wf = w[(w.Window == 'real') & (w.ETF == lev) & (w.Criterion == 'Calmar')].set_index('Rule')
    sp = s[(s.ETF == lev) & (s.Benchmark == '1x hold')].set_index('Loss')
    rows += [[lev, und, 'CAGR, real 2010-26', pc(a.loc['SMA rule', 'CAGR']), pc(a.loc['1x hold', 'CAGR']), 'SMA higher'],
             [lev, und, 'Max DD, real', pc(a.loc['SMA rule', 'MaxDrawdown']), pc(a.loc['1x hold', 'MaxDrawdown']), '1x shallower'],
             [lev, und, 'Calmar / Sharpe, real', f"{f3(a.loc['SMA rule','Calmar'])} / {f3(a.loc['SMA rule','Sharpe'])}",
              f"{f3(a.loc['1x hold','Calmar'])} / {f3(a.loc['1x hold','Sharpe'])}", '1x higher on both'],
             [lev, und, 'Calmar / Sharpe, hypothetical 1999-26', f"{f3(f.loc['SMA rule','Calmar'])} / {f3(f.loc['SMA rule','Sharpe'])}",
              f"{f3(f.loc['1x hold','Calmar'])} / {f3(f.loc['1x hold','Sharpe'])}", 'SMA higher on both'],
             [lev, und, 'Walk-forward OOS 2015-26, Calmar', f3(wf.loc['Walk-forward SMA', 'Calmar']) + ' (WF) / ' + f3(wf.loc['Fixed 200/+4/-3', 'Calmar']) + ' (fixed)',
              f3(wf.loc['1x hold', 'Calmar']), '1x higher'],
             [lev, und, 'Bootstrap ΔSharpe, observed [95%], p', f"{bb.loc['Sharpe','Observed']:+.3f} [{bb.loc['Sharpe','CI2_5']:+.3f}, {bb.loc['Sharpe','CI97_5']:+.3f}], p = {bb.loc['Sharpe','p_centred']:.2f}", '—', 'not significant at 5%' if bb.loc['Sharpe','p_centred'] >= .05 else 'significant at 5%'],
             [lev, und, 'SPA p, raw / vol-matched return', f"{sp.loc['raw return','p_SPA_c']:.3f} / {sp.loc['volatility-matched','p_SPA_c']:.3f}", '—',
              'more return; no risk-adjusted superiority']]
out['onex'] = md(rows, ['ETF', '1x', 'Measure', 'SMA rule (3x)', '1x hold', 'Reading'], ['l', 'l', 'l', 'r', 'r', 'l'])
# --- walk-forward
rows = []
for _, r in w[w.Window == 'real'].iterrows():
    rows.append([r.ETF, r.Criterion, r.Rule, pc(r.CAGR), pc(r.MaxDrawdown), f3(r.Calmar), f3(r.Sharpe)])
out['wf_real'] = md(rows, ['ETF', 'Selection', 'Rule (OOS 2015-01-02 to 2026-08-06)', 'CAGR', 'Max DD', 'Calmar', 'Sharpe'], ['l', 'l', 'l', 'r', 'r', 'r', 'r'])
rows = []
for _, r in w[(w.Window == 'full') & (w.Criterion == 'Calmar')].iterrows():
    rows.append([r.ETF, r.Rule, pc(r.CAGR), pc(r.MaxDrawdown), f3(r.Calmar), f3(r.Sharpe)])
out['wf_full'] = md(rows, ['ETF', 'Rule (OOS 2005-01-03 to 2026-08-06, hypothetical before inception)', 'CAGR', 'Max DD', 'Calmar', 'Sharpe'], ['l', 'l', 'r', 'r', 'r', 'r'])
sel = pd.read_csv(R / 'walkforward_selections.csv'); sel = sel[(sel.Window == 'real') & (sel.Criterion == 'Calmar')]
rows = []
for lev, g in sel.groupby('ETF'):
    rows.append([lev, ', '.join(f"{int(r.TestYear)}: {int(r.SMA)}/{100*r.Entry:+.0f}/{100*r.Exit:.0f}" for _, r in g.iterrows())])
out['wf_sel'] = md(rows, ['ETF', 'Selected SMA/entry%/exit% by test year (Calmar criterion)'], ['l', 'l'])
# --- LOCO
l = pd.read_csv(R / 'leave_one_crisis_out.csv'); rows = []
cols = ['SMA rule', '3x hold', '1x hold', 'Matched weight (ex ante)', 'Vol target 30%']
for (per, lev, ex, span), g in l.groupby(['Window', 'ETF', 'Excluded', 'ExclusionSpan'], sort=False):
    if span != 'decline only' and ex != 'none excluded' and ex != 'all listed excluded':
        pass
    gg = g.set_index('Rule')
    best = gg.loc[cols, 'Calmar'].drop('SMA rule').max()
    rows.append([per, lev, ex, '—' if ex == 'none excluded' else span] + [f3(gg.loc[c, 'Calmar']) for c in cols] + ['yes' if gg.loc['SMA rule', 'Calmar'] > best else 'no'])
out['loco'] = md(rows, ['Window', 'ETF', 'Excluded', 'Span'] + ['SMA', '3x hold', '1x hold', 'Matched (ex ante)', 'Vol 30%'] + ['SMA best?'], ['l'] * 4 + ['r'] * 6)
dc = pd.read_csv(R / 'crisis_contribution_returns_removed.csv'); rows = []
for (per, lev, ex, span), g in dc.groupby(['Window', 'ETF', 'Excluded', 'ExclusionSpan'], sort=False):
    if span != 'decline only': continue
    gg = g.set_index('Rule')
    rows.append([per, lev, ex] + [f3(gg.loc[c, 'Calmar']) for c in cols])
out['loco_decomp'] = md(rows, ['Window', 'ETF', 'Days removed'] + ['SMA', '3x hold', '1x hold', 'Matched (ex ante)', 'Vol 30%'], ['l'] * 3 + ['r'] * 5)
# --- grid
g = pd.read_csv(R / 'parameter_grid.csv'); rows = []
for (per, lev), x in g.groupby(['Window', 'ETF']):
    rk = int(x.Calmar.rank(ascending=False)[x.Baseline].iloc[0])
    rows.append([per, lev, len(x), f"{f3(x.Calmar.min())} / {f3(x.Calmar.median())} / {f3(x.Calmar.max())}", f'{rk} / 45',
                 *[f"{int(x[c].sum())} / {int(x[c.replace('Calmar','Sharpe')].sum())}" for c in
                   ('Beats_Matchedweight_Calmar', 'Beats_Voltarget30%_Calmar', 'Beats_1xhold_Calmar', 'Beats_3xhold_Calmar')]])
out['grid'] = md(rows, ['Window', 'ETF', 'Configs', 'Calmar min / median / max', 'Baseline rank', 'Beat matched (ex ante)', 'Beat vol 30%', 'Beat 1x hold', 'Beat 3x hold'],
                 ['l', 'l', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
out['spa'] = md([[r.ETF, r.Benchmark, r.Loss, r.BestConfig, pp(r.BestAnnualDiff), pp(r.BaselineAnnualDiff), f'{r.p_RealityCheck:.3f}', f'{r.p_SPA_c:.3f}']
                 for _, r in s.iterrows()], ['ETF', 'Benchmark', 'Loss', 'Best of 45', 'Best Δ (pp/yr)', 'Baseline Δ (pp/yr)', 'p (Reality Check)', 'p (SPA_c)'],
                ['l', 'l', 'l', 'l', 'r', 'r', 'r', 'r'])
# --- bootstrap
lab = {'3x hold': '3x hold', '1x hold': '1x hold', '1x SMA': '1x SMA', 'Matched weight (ex ante)': 'Matched (ex ante)',
       'Vol target 30%': 'Vol target 30%', 'Matched (pre-sample constant)': 'Matched (pre-sample const.) ‡'}
rows = []
for _, r in b[(b.MeanBlockDays == 252) & b.Metric.isin(['CAGR', 'MaxDrawdown', 'Calmar', 'Sharpe'])].iterrows():
    fm = (lambda x: f'{100*x:+.1f}') if r.Metric in ('CAGR', 'MaxDrawdown') else (lambda x: f'{x:+.3f}')
    rows.append([r.ETF, lab[r.Versus], {'CAGR': 'CAGR (pp)', 'MaxDrawdown': 'Max DD (pp)'}.get(r.Metric, r.Metric), fm(r.Observed),
                 f'[{fm(r.CI2_5)}, {fm(r.CI97_5)}]', f'{100*r.SharePositive:.0f}%', f'{r.p_centred:.3f}', 'n.s.' if r.p_centred >= .05 else '*'])
out['boot'] = md(rows, ['ETF', 'Versus', 'Δ = SMA − benchmark', 'Observed Δ', '95% percentile interval', 'Share Δ*>0', 'p (centred, 2-sided)', ''],
                 ['l', 'l', 'l', 'r', 'r', 'r', 'r', 'l'])
b63 = b[(b.MeanBlockDays == 63) & b.Metric.isin(['Calmar', 'Sharpe'])]
out['boot63'] = md([[r.ETF, lab[r.Versus], r.Metric, f'{r.Observed:+.3f}', f'{r.p_centred:.3f}'] for _, r in b63.iterrows()],
                   ['ETF', 'Versus', 'Metric', 'Observed Δ', 'p (63-day blocks)'], ['l', 'l', 'l', 'r', 'r'])
# --- costs
c = pd.read_csv(R / 'cost_scenarios.csv'); rows = []
for (lev, sc), x in c.groupby(['ETF', 'Scenario'], sort=False):
    xx = x.set_index('Rule')
    rows.append([lev, sc] + [f"{pc(xx.loc[k,'CAGR'])} / {f3(xx.loc[k,'Calmar'])}" for k in ('SMA rule', '1x hold', 'Matched weight (ex ante)', 'Vol target 30%')]
                + [f"{xx.loc['SMA rule','MeanCostPerFill_bp']:.1f}"])
out['costs'] = md(rows, ['ETF', 'Scenario', 'SMA rule', '1x hold', 'Matched (ex ante)', 'Vol 30%', 'SMA mean cost/fill (bp)'], ['l', 'l', 'r', 'r', 'r', 'r', 'r'])
# --- synthetic stress
st = pd.read_csv(R / 'synthetic_stress.csv'); rows = []
for (lev, sc), x in st.groupby(['ETF', 'Scenario'], sort=False):
    xx = x.set_index('Rule')
    rows.append([lev, sc, f"{pc(xx.loc['SMA rule','CAGR'])} / {f3(xx.loc['SMA rule','Calmar'])}", f"{pc(xx.loc['Vol target 30%','CAGR'])} / {f3(xx.loc['Vol target 30%','Calmar'])}",
                 f"{pc(xx.loc['3x hold','CAGR'])}", pc(xx.loc['SMA rule', 'Return_DotCom']), pc(xx.loc['SMA rule', 'Return_GFC']),
                 pc(xx.loc['3x hold', 'Return_DotCom']), pc(xx.loc['3x hold', 'Return_GFC'])])
out['stress'] = md(rows, ['ETF', 'Scenario (1999-2026, hypothetical)', 'SMA CAGR / Calmar', 'Vol 30% CAGR / Calmar', '3x hold CAGR', 'SMA dot-com', 'SMA GFC', '3x hold dot-com', '3x hold GFC'],
                   ['l', 'l'] + ['r'] * 7)
# --- mechanism
me = pd.read_csv(R / 'mechanism_decomposition.csv')
out['mech'] = md([[r.Window, r.ETF, r.Comparison, pp(r.LogGrowthDiff), pp(r.MeanReturnPart), pp(r.VarianceDragPart)] for _, r in me.iterrows()],
                 ['Window', 'ETF', 'Comparison', 'Δ log growth (pp/yr)', 'from mean return', 'from variance drag'], ['l', 'l', 'l', 'r', 'r', 'r'])
mb = pd.read_csv(R / 'mechanism_by_state.csv')
out['mech_state'] = md([[r.Window, r.ETF, r.Grouping, r.Group, r.Days, f'{r.Contribution_pp_per_year:+.1f}'] for _, r in mb.iterrows()],
                       ['Window', 'ETF', 'Grouping', 'Group', 'Days', 'Timing effect contribution (pp/yr)'], ['l', 'l', 'l', 'l', 'r', 'r'])
sc = pd.read_csv(R / 'state_conditional.csv'); sc = sc[sc.Window == 'real']; rows = []
for (lev, dim, state), x in sc.groupby(['ETF', 'Dimension', 'State'], sort=False):
    xx = x.set_index('Versus')
    rows.append([lev, dim, state, int(xx.Days.iloc[0])] + [f"{pp(xx.loc[k,'AnnualisedMeanDiff'])} ({xx.loc[k,'NeweyWest_t']:+.1f})" for k in ('Matched weight (ex ante)', 'Vol target 30%', '1x hold')])
out['states'] = md(rows, ['ETF', 'Dimension', 'State at close t−1', 'Days', 'vs matched (ex ante)', 'vs vol 30%', 'vs 1x hold'], ['l', 'l', 'l', 'r', 'r', 'r', 'r'])
fg = pd.read_csv(R / 'frontier_gap.csv'); fg = fg[fg.RiskMeasure.isin(['MaxDrawdown', 'ES99', 'UlcerIndex'])]
rows = []
for (per, lev, rule), x in fg.groupby(['Window', 'ETF', 'Rule'], sort=False):
    xx = x.set_index(['Family', 'RiskMeasure'])
    rows.append([per, lev, rule] + [pp(xx.loc[(f, k), 'Gap_pp'] / 100) for f in ('fixed weight', 'vol target') for k in ('MaxDrawdown', 'ES99', 'UlcerIndex')])
out['frontier'] = md(rows, ['Window', 'ETF', 'Rule', 'Fixed: MaxDD', 'Fixed: ES99', 'Fixed: Ulcer', 'Vol: MaxDD', 'Vol: ES99', 'Vol: Ulcer'], ['l', 'l', 'l'] + ['r'] * 6)
cv = pd.read_csv(R / 'calibration_validation.csv'); rows = []
for _, r in cv.iterrows():
    if 'test' in r.Window:
        rows.append([r.Ticker, r.Window, f'{1e4*r.Spread_s:.0f} bp', f'synthetic {pc2(r.SyntheticCAGR)} vs real {pc2(r.RealCAGR)}; max DD {pc(r.SyntheticMaxDD)} vs {pc(r.RealMaxDD)}; corr {r.DailyCorrelation:.4f}'])
    else:
        rows.append([r.Ticker, r.Window, f'{1e4*r.Spread_s:.0f} bp', f'residual s.d. {r.ResidualDailyStd_bp:.1f} bp/day'])
out['calib'] = md(rows, ['ETF', 'Window', 'Spread s', 'Check'], ['l', 'l', 'r', 'l'])
T.mkdir(parents=True, exist_ok=True)
for k, v in out.items(): (T / f'{k}.md').write_text(v)
print('tables:', ', '.join(out))
