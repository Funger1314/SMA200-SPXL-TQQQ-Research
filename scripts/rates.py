"""As-of safe monthly risk-free proxy derived from FRED DTB3.

Fixed vintage source: github.com/0xenriconagata/perp-carry-economics,
assets/DTB3.csv, Git blob e473e4a24beb3ef7fe6cad45a5871a57b6967a19.
DTB3 is a BANK-DISCOUNT quoted rate, percent per annum. We record only the
last AVAILABLE numeric quote of each month; the value is used STARTING NEXT
month, never during the month from which it was sampled. The -0.01% quotation
in September 2015 is explicitly restored from the losslessly checked source
(the packed monthly values otherwise use nonnegative 2-character encoding). The last
recorded quote is 2026-10-26, so November 2026 uses that last October rate.

This small derived historical interest-rate series is an audit proxy, not an
exact daily Treasury-bill return index. A full-vintage DTB3 download can be
substituted in future research if licensing allows. The 91-day bank discount
yield is converted to an approximate investment yield on a 365-day year.
"""
from __future__ import annotations
from datetime import date
import pandas as pd

BASE64='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
PACK=(
'G1G1HHG1G7HFHRHOHkHaHxIDIFIpIyI8I2IkI7JbJlJdJrJbI9HmHZGkGCFjFlFaFKDrDJCvCrCtCwCwCuCrCnCoCmCaCO'
'B4B4B0B2BwBvBtBZBeBgBdBeBbBdBaBeBdBgBqCDCOCdCoC7DbDaD4EQEREcElEyFOFYFbGFGCGPG1HDHEHRHaHnHxHsHdHv'
'HqHpHzH1HqHfHMHUHiGHF0GAE0FJDAC1CICNC5C7ClCpBaAsABALAYAaAVAOAOATASAPAOAFAGAGAIANAQAQAQASAPAOAQAM'
'ARAMAPAPAJAEAGADAKACACABABACAGAIAHAKAHAJALAJAKALAIAFAHALAHAFAEAEAEADACAEAGAHACAFAFADAEAEADADACABAC'
'AEACACADABABABAIAIAAAIAWAQAgAhAVAWAiAaAbAhAcAiAwAyA0A1BLBPBgBlBpBjBoBxB9CJCQCjCqC4C9C9DHDPDXDlDo'
'DwDsDwDrDuDmDQDMDDC4CXCcCYCYB9ALAJAOAQAJALAKAJAIAJAGAEADABABAFAGAEAEAFAFAGAYAlAzBTBxCmDqEfFCGWGr'
'GuHKHYHUHvIOIFIQIUIUIVINIIIKINILININIKIDHyHEG8G3GnGkGkGlGkGpGoGoGVGCF1F1FlFmFnFpFnFoF2FxF6GTGV')


def rates_table():
    months=pd.period_range('1998-12','2026-10',freq='M')
    assert len(months)==335 and len(PACK)==len(months)*2,(len(PACK),len(months))
    yields=[]
    for i in range(0,len(PACK),2):
        a=BASE64.index(PACK[i]);b=BASE64.index(PACK[i+1]);bps=a*64+b
        discount=bps/10000.0
        investment=(discount*365/360)/(1-discount*91/360)
        yields.append(investment)
    df=pd.DataFrame({'Month':months.astype(str),'DTB3DiscountYield':[(BASE64.index(PACK[i])*64+BASE64.index(PACK[i+1]))/10000 for i in range(0,len(PACK),2)],'InvestmentYield':yields}).set_index('Month')
    # Source observation 2015-09-30 = -0.01% annual on bank-discount basis.
    df.loc['2015-09','DTB3DiscountYield']=-0.0001
    z=-0.0001
    df.loc['2015-09','InvestmentYield']=(z*365/360)/(1-z*91/360)
    return df


def annual_cash_rate(index):
    """Rates available BEFORE the month in which returns accrue; no look-ahead."""
    tbl=rates_table()['InvestmentYield']
    dates=pd.DatetimeIndex(index)
    previous=(dates.to_period('M')-1).astype(str)
    if any(m not in tbl.index for m in previous):
        raise ValueError('risk-free rate source missing prior-month observation')
    return pd.Series(tbl.reindex(previous).to_numpy(),index=dates,name='risk_free_rate')


if __name__=='__main__':
    d=rates_table();print(d.head());print(d.tail())
