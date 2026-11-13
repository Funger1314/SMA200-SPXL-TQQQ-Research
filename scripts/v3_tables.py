# LEGACY (v3) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Render markdown tables for the v3 manuscript directly from data/v3_results."""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1]/'data/v3_results'; T=Path(__file__).resolve().parents[1]/'paper/tables'
pc=lambda x:f'{100*x:.2f}%'; pp=lambda x:f'{100*x:+.1f}'; f3=lambda x:f'{x:.3f}'
def md(df,align=None):
    cols=list(df.columns); a=align or ['l']+['r']*(len(cols)-1)
    s='| '+' | '.join(cols)+' |\n|'+'|'.join(':--' if x=='l' else '--:' for x in a)+'|\n'
    return s+''.join('| '+' | '.join(str(v) for v in r)+' |\n' for r in df.values)
out={}
m=pd.read_csv(R/'main_metrics.csv')
for per in('real','full'):
    d=m[m.Period==per]; rows=[]
    for _,r in d.iterrows():
        rows.append([r.Ticker,r.Strategy,pc(r.CAGR),pc(r.MaxDrawdown),f3(r.Calmar),f3(r.Sharpe),pc(r.CDaR10),f3(r.UlcerIndex),f'{r.AverageWeight:.2f}',int(r.NumOrders)])
    out[f'main_{per}']=md(pd.DataFrame(rows,columns=['ETF','Rule','CAGR','Max DD','Calmar','Sharpe (excess)','CDaR 10%','Ulcer','Avg weight','Orders']),['l','l']+['r']*8)
c=pd.read_csv(R/'calibration_spread.csv');rows=[]
for _,r in c.iterrows():
    if 'test' in r.Window: rows.append([r.Ticker,r.Window,f'{1e4*r.Spread_s:.0f} bp','—',f'synthetic {pc(r.SyntheticCAGR)} vs real {pc(r.RealCAGR)}; MDD {pc(r.SyntheticMaxDD)} vs {pc(r.RealMaxDD)}; corr {r.DailyCorrelation:.4f}; TE {pc(r.AnnualTrackingError)}'])
    else: rows.append([r.Ticker,r.Window,f'{1e4*r.Spread_s:.0f} bp',f'{r.ResidualDailyStd_bp:.1f} bp','—'])
out['calibration']=md(pd.DataFrame(rows,columns=['ETF','Window','Spread s','Residual daily s.d.','Out-of-sample check']),['l','l','r','r','l'])
f=pd.read_csv(R/'frontier_gap.csv');rows=[]
for _,r in f.iterrows(): rows.append([r.Period,r.Ticker,r.Family,{'MaxDrawdown':'Max DD','CDaR10':'CDaR 10%','UlcerIndex':'Ulcer'}[r.RiskMeasure],pc(r.SMA_CAGR),pc(r.Frontier_CAGR_at_same_risk),pp(r.SMA_minus_frontier_CAGR)])
out['frontier']=md(pd.DataFrame(rows,columns=['Window','ETF','Non-timing family','Risk held equal','SMA CAGR','Frontier CAGR','SMA − frontier (pp)']),['l','l','l','l','r','r','r'])
a=pd.read_csv(R/'attribution_v1_to_v3.csv');rows=[]
for (t,s),g in a.groupby(['Ticker','Step'],sort=False):
    x=g.set_index('Strategy');rows.append([t,s,pc(x.loc['SMA rule','CAGR']),pc(x.loc['SMA rule','MaxDrawdown']),int(x.loc['SMA rule','NumOrders']),pc(x.loc['3x hold','CAGR']),pc(x.loc['3x hold','MaxDrawdown'])])
out['attribution']=md(pd.DataFrame(rows,columns=['ETF','Step','SMA CAGR','SMA Max DD','SMA orders','3x hold CAGR','3x hold Max DD']),['l','l','r','r','r','r','r'])
g=pd.read_csv(R/'regime_nextday.csv');rows=[]
for _,r in g.iterrows(): rows.append([r.Period,r.SignalETF,r.RegimeAtClose_t,int(r.Days),pc(r.NextDayMeanAnnual),pc(r.NextDayVolAnnual),pc(r.Implied3xLogGrowth)])
out['regime']=md(pd.DataFrame(rows,columns=['Window','Signal','Regime at close t','Days','Next-day mean (ann.)','Next-day vol (ann.)','Implied 3x log growth']),['l','l','l','r','r','r','r'])
rt=pd.read_csv(R/'roundtrips.csv');rt=rt[rt.Period=='full'];rows=[]
for _,r in rt.iterrows(): rows.append([r.Ticker,r.ExitFill,r.ReentryFill,int(r.TradingDaysOut),pc(r.ForegoneLeveredReturn),'yes' if r.Synthetic else 'no'])
out['roundtrips']=md(pd.DataFrame(rows,columns=['ETF','Exit fill','First re-entry fill','Days out','Leveraged return while out','Synthetic']),['l','l','l','r','r','l'])
s=pd.read_csv(R/'rolling_starts_summary.csv');rows=[]
nm={'Hold3x':'3x hold','Fixed':'Matched fixed weight','Vol30':'Vol target 30%','Hold1x':'1x hold'}
for _,r in s.iterrows(): rows.append([{'real':'2010-02…2023-08','full':'1999-12…2023-08'}[r.Window],r.Ticker,nm[r.Versus],int(r.Starts),pp(r.Median_dCAGR),pp(r.Median_dMDD),f'{r.Median_dCalmar:+.3f}',f'{100*r.Share_SMA_higher_Calmar:.0f}%'])
out['rolling']=md(pd.DataFrame(rows,columns=['Start months','ETF','Versus','Starts','Median ΔCAGR (pp)','Median ΔMax DD (pp)','Median ΔCalmar','SMA higher Calmar']),['l','l','l','r','r','r','r','r'])
b=pd.read_csv(R/'bootstrap_daily_summary.csv');b=b[b.Metric.isin(['CAGR','MaxDrawdown','Calmar','Sharpe'])&(b.MeanBlockDays==252)];rows=[]
nm2={'Hold3x':'3x hold','Fixed':'Matched fixed','Vol30':'Vol target 30%'}
for _,r in b.iterrows():
    fm=(lambda x:f'{100*x:+.1f}') if r.Metric in('CAGR','MaxDrawdown') else (lambda x:f'{x:+.3f}')
    rows.append([r.Ticker,nm2[r.Versus],{'MaxDrawdown':'Max DD (pp)','CAGR':'CAGR (pp)'}.get(r.Metric,r.Metric),fm(r.Median_SMA_minus_benchmark),f'[{fm(r.CI2_5)}, {fm(r.CI97_5)}]',f'{100*r.Share_positive:.0f}%'])
out['bootstrap']=md(pd.DataFrame(rows,columns=['ETF','Versus','Metric (SMA − benchmark)','Median','95% interval','Share > 0']),['l','l','l','r','r','r'])
p=pd.read_csv(R/'parameter_grid.csv');rows=[]
for (per,t),x in p.groupby(['Period','Ticker']): rows.append([per,t,len(x),f'{pc(x.CAGR.min())} / {pc(x.CAGR.median())} / {pc(x.CAGR.max())}',f'{int(x.Beats_matched_Calmar.sum())} / {len(x)}',f'{int(x.Beats_matched_Sharpe.sum())} / {len(x)}'])
out['grid']=md(pd.DataFrame(rows,columns=['Window','ETF','Cells','CAGR min / median / max','Beat matched-weight Calmar','Beat matched-weight Sharpe']),['l','l','r','r','r','r'])
sp=pd.read_csv(R/'subperiod_metrics.csv');sp=sp[sp.Strategy.isin(['SMA rule','3x hold','Matched fixed weight','Vol target 30%'])];rows=[]
for _,r in sp.iterrows(): rows.append([r.Subperiod,r.Ticker,r.Strategy,pc(r.CAGR),pc(r.MaxDrawdown),f3(r.Calmar)])
out['subperiod']=md(pd.DataFrame(rows,columns=['Subperiod','ETF','Rule','CAGR','Max DD','Calmar']),['l','l','l','r','r','r'])
se=pd.read_csv(R/'sensitivity.csv');rows=[]
for _,r in se.iterrows(): rows.append([r.Test,r.Ticker,r.Setting,'SMA rule' if r.Strategy=='trend' else '3x hold',pc(r.CAGR),pc(r.MaxDrawdown)])
out['sensitivity']=md(pd.DataFrame(rows,columns=['Test','ETF','Setting','Rule','CAGR','Max DD']),['l','l','l','l','r','r'])
au=pd.read_csv(R/'data_audit.csv');out['audit']=md(au.assign(SHA256=au.SHA256.str[:16]+'…')[['Ticker','FirstDate','LastDate','Rows','SHA256']].rename(columns={'FirstDate':'First bar','LastDate':'Last bar','SHA256':'SHA-256 (prefix)'}))
for k,v in out.items(): (T/f'{k}.md').write_text(v)
print('\n'.join(f'== {k}\n{v}' for k,v in out.items()))
