# LEGACY (v1) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Build audited paper tables and figures from this run's stored snapshots.

Does not pretend that month-end snapshots are daily price observations.
The chart is a monthly sampled view of actual daily equity curves.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from decode_snapshot import decode_monthly

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'data/results'; FIG=ROOT/'figures'
FIG.mkdir(exist_ok=True)

def build_tables():
    summary=[
      ('1999-12 to 2026-11','SPXL','SMA200',464787.61,15.378,-52.88,.591,77,70.82,2634.33),
      ('1999-12 to 2026-11','TQQQ','SMA200',313784.27,13.702,-90.49,.510,119,70.70,2126.69),
      ('1999-12 to 2026-11','SPXL','BuyHold',55780.57,6.614,-97.81,.400,1,100.0,9.99),
      ('1999-12 to 2026-11','TQQQ','BuyHold',9213.25,-.305,-99.96,.397,1,100.0,9.99),
      ('2010-02 to 2026-11','SPXL','SMA200',247070.35,21.141,-52.88,.720,53,79.72,1352.49),
      ('2010-02 to 2026-11','TQQQ','SMA200',539595.90,26.934,-62.09,.746,71,80.55,3570.81),
      ('2010-02 to 2026-11','SPXL','BuyHold',701252.28,28.939,-76.86,.754,1,100.0,9.99),
      ('2010-02 to 2026-11','TQQQ','BuyHold',3093420.50,40.906,-81.66,.864,1,100.0,9.99),
    ]
    df=pd.DataFrame(summary,columns=['Period','Ticker','Strategy','FinalWealthUSD','CAGR_pct','MaxDD_pct','Sharpe_rf0','OrderCount','DaysExposed_pct','TotalTradeFrictionUSD'])
    df.insert(4,'TotalReturn_pct',100*(df.FinalWealthUSD/10000-1))
    df.to_csv(RES/'snapshot_summary_metrics.csv',index=False,float_format='%.5f')
    vals={
      'SPXL':{
        150:([17.14,18.42,18.91,14.05,18.46,18.65,8.77,15.17,14.48],[-52,-55.1,-58.5,-47.3,-49.3,-51.7,-46,-43.6,-49.7]),
        200:([22.17,22.54,20.25,18.16,21.14,19.48,16.43,17.42,15.98],[-50.9,-52.5,-57.7,-48.6,-52.9,-52.9,-47.3,-51.7,-52.8]),
        250:([15.67,16.67,17.74,16.87,18.89,16.54,13.53,16.5,13.56],[-52.9,-63.1,-53.9,-49.2,-53.5,-55.5,-52.7,-51.7,-61.1]),
      },
      'TQQQ':{
        150:([27.70,30.01,25.73,27.61,29.91,22.86,23.03,28.39,19.76],[-64.4,-61.7,-65.4,-53.8,-53.8,-62.1,-55.7,-55.7,-62.1]),
        200:([24.87,26.04,27.48,26.07,26.93,24.77,24.64,24.93,24.36],[-63.8,-62.1,-62.1,-53.8,-62.1,-62.1,-56.6,-62.1,-62.1]),
        250:([24.54,26.72,31.12,24.80,27.71,29.74,24.44,29.09,29.73],[-61.3,-62.1,-62.1,-56,-62.1,-62.1,-54.2,-62.1,-62.1]),
      }
    }
    records=[]
    for etf in vals:
        for window,(returns,drawdowns) in vals[etf].items():
            ix=0
            for b in [2,4,6]:
                for ex in [-1,-3,-5]:
                    records.append((etf,window,b,ex,returns[ix],drawdowns[ix]))
                    ix+=1
    grid=pd.DataFrame(records,columns=['LeveragedETF','SMADays','EntryBufferPct','ExitBufferPct','CAGR_pct','MaxDD_pct'])
    grid.to_csv(RES/'snapshot_parameter_grid_2010.csv',index=False)
    costs=[]
    for ticker, rec in {
      'SPXL':[(5,21.20,-52.8,249171),(10,21.14,-52.9,247070),(20,21.02,-53.0,242923),(50,20.65,-53.3,230894)],
      'TQQQ':[(5,27.02,-62.1,545967),(10,26.93,-62.1,539596),(20,26.76,-62.1,527076),(50,26.22,-62.1,491231)]
    }.items():
      for bps,cagr,dd,end in rec:costs.append((ticker,bps,cagr,dd,end))
    pd.DataFrame(costs,columns=['LeveragedETF','OneWayCost_bps','CAGR_pct','MaxDD_pct','FinalWealthUSD']).to_csv(RES/'snapshot_cost_sensitivity.csv',index=False)
    epochs=[]
    for ticker,rec in {
      'SPXL':[(2010,2017,25.06,-42.3),(2018,2026,17.03,-52.9),(1999,2008,3.76,-41.7)],
      'TQQQ':[(2010,2017,25.85,-53.8),(2018,2026,26.51,-62.1),(1999,2008,-12.23,-90.5)]
    }.items():
      for yr0,yr1,cagr,dd in rec:epochs.append((ticker,yr0,yr1,cagr,dd,yr0==1999))
    pd.DataFrame(epochs,columns=['LeveragedETF','StartYear','EndYear','CAGR_pct','MaxDD_pct','ContainsSynthetic']).to_csv(RES/'snapshot_regime_split.csv',index=False)
    return grid


def chart_equity(df,window,path):
    fig,ax=plt.subplots(figsize=(11.2,5.7))
    colors=['#147d8a','#df7d39','#1d5372','#a94f62']
    for (name,color) in zip(df.columns,colors):
        ax.plot(df.index,df[name]/10000,label=name.replace('_',' '),linewidth=1.9 if 'strategy' in name else 1.2,color=color,alpha=1 if 'strategy' in name else .65)
    ax.set_yscale('log')
    ax.set_ylabel('Growth of $1 (log scale)')
    ax.set_title(window+' | Month-end equity curves')
    ax.grid(alpha=.23)
    ax.legend(ncol=2,fontsize=9)
    fig.text(.12,.02,'Each line is a monthly sampled NAV from the daily, next-open simulation. Synthetic pre-inception history shown only in full panel.',size=8,color='dimgray')
    fig.tight_layout(rect=(0,.04,1,1))
    fig.savefig(path,dpi=200)
    plt.close(fig)


def chart_underwater(df,window,path):
    fig,ax=plt.subplots(figsize=(11.2,5.3))
    for name in ['SPXL_strategy','TQQQ_strategy']:
        dd=100*(df[name]/df[name].cummax()-1)
        ax.plot(dd.index,dd.values,label=name.replace('_',' '),linewidth=1.7)
    ax.set_title(window+' | Month-end sampled drawdowns')
    ax.set_ylabel('Drawdown from month-end peak (%)')
    ax.grid(alpha=.2);ax.legend()
    fig.text(.12,.02,'Daily maximum drawdowns in paper tables can be more severe than month-end sampled drawdowns.',size=8,color='dimgray')
    fig.tight_layout(rect=(0,.04,1,1))
    fig.savefig(path,dpi=200)
    plt.close(fig)


def chart_grid(grid,path):
    fig,axs=plt.subplots(1,2,figsize=(11.2,5.0),sharey=True)
    for ticker,ax in zip(['SPXL','TQQQ'],axs):
        z=grid[(grid.LeveragedETF==ticker)&(grid.ExitBufferPct==-3)].pivot(index='EntryBufferPct',columns='SMADays',values='CAGR_pct')
        a=z.to_numpy()
        im=ax.imshow(a,origin='lower',aspect='auto',cmap='viridis',vmin=8,vmax=31)
        ax.set_xticks([0,1,2],['150','200','250']);ax.set_yticks([0,1,2],['+2%','+4%','+6%'])
        ax.set_title(f'{ticker}: annual CAGR (%)')
        ax.set_xlabel('Moving-average window')
        for i in range(3):
            for j in range(3):ax.text(j,i,f'{a[i,j]:.1f}',ha='center',va='center',color='white',fontweight='bold')
    axs[0].set_ylabel('Entry threshold')
    fig.colorbar(im,ax=list(axs),shrink=.8,label='Annualized return, %')
    fig.suptitle('Retrospective parameter neighborhood | Exit fixed at -3%')
    fig.savefig(path,dpi=200,bbox_inches='tight')
    plt.close(fig)


def chart_annual(df,path):
    annual={}
    for s in ['SPXL_strategy','TQQQ_strategy']:
        a=df[s].resample('YE').last()
        r=a.pct_change().dropna()*100
        annual[s]=r
    y=pd.concat(annual,axis=1).dropna()
    fig,ax=plt.subplots(figsize=(11.2,5.2))
    xx=np.arange(len(y));width=.38
    ax.bar(xx-width/2,y['SPXL_strategy'],width,label='SPXL 200-SMA')
    ax.bar(xx+width/2,y['TQQQ_strategy'],width,label='TQQQ 200-SMA')
    ax.axhline(0,color='dimgray',linewidth=.7)
    ax.set_xticks(xx,[str(x.year) for x in y.index],rotation=45)
    ax.set_ylabel('Calendar-year strategy return (%)')
    ax.set_title('Year-over-year performance | Common actual ETF window')
    ax.legend();ax.grid(alpha=.2,axis='y');fig.tight_layout();fig.savefig(path,dpi=200);plt.close(fig)


def main():
    grid=build_tables()
    for key,months,start in [('1999',324,'1999-12'),('2010',202,'2010-02')]:
        d=decode_monthly(start,months,f'monthly_{key}.packed')
        label='1999-12 to 2026-11' if key=='1999' else '2010-02 to 2026-11'
        chart_equity(d,label,FIG/f'equity_{key}.png')
        chart_underwater(d,label,FIG/f'underwater_monthly_{key}.png')
        if key=='2010':chart_annual(d,FIG/'annual_returns_2010.png')
    chart_grid(grid,FIG/'parameter_grid_2010.png')
    print('Figures:',*[p.name for p in FIG.glob('*.png')])

if __name__=='__main__':main()
