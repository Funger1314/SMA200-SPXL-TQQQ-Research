"""Strict validation of vendor OHLCV files.

* `nyse_trading_days(start, end)`: the NYSE trading calendar built from explicit
  holiday rules and the special closures of 1993-2026 (no third-party package).
* `validate_ohlcv(df, ticker)`: returns a list of check records and raises
  `DataValidationError` on any FATAL failure.

FATAL  - unsorted/duplicate dates, weekend bars, missing or non-positive prices,
         High/Low inconsistent with Open/Close, Adj Close above Close (beyond
         rounding), an implausible single-day adjustment-factor jump, calendar
         gaps versus the NYSE calendar, or bars on NYSE holidays.
WARN   - zero volume, extreme daily moves (listed for manual review), and
         adjacent sign-reversing return pairs (closing price vs NAV noise).
"""
from __future__ import annotations
from datetime import date, timedelta
import numpy as np
import pandas as pd

SPECIAL_CLOSURES = {
    '1994-04-27': 'Nixon national day of mourning',
    '2001-09-11': 'September 11', '2001-09-12': 'September 11', '2001-09-13': 'September 11',
    '2001-09-14': 'September 11',
    '2004-06-11': 'Reagan national day of mourning', '2007-01-02': 'Ford national day of mourning',
    '2012-10-29': 'Hurricane Sandy', '2012-10-30': 'Hurricane Sandy',
    '2018-12-05': 'G.H.W. Bush national day of mourning', '2025-01-09': 'Carter national day of mourning',
}


class DataValidationError(ValueError):
    pass


def _easter(y: int) -> date:
    a = y % 19; b, c = divmod(y, 100); d, e = divmod(b, 4); f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i, k = divmod(c, 4); l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451; month = (h + l - 7 * m + 114) // 31; day = (h + l - 7 * m + 114) % 31 + 1
    return date(y, month, day)


def _nth_weekday(y, month, weekday, n):
    d = date(y, month, 1); d += timedelta((weekday - d.weekday()) % 7); return d + timedelta(7 * (n - 1))


def _last_weekday(y, month, weekday):
    d = date(y, month + 1, 1) - timedelta(1) if month < 12 else date(y, 12, 31)
    return d - timedelta((d.weekday() - weekday) % 7)


def _observed(d: date, new_year=False):
    if d.weekday() == 5:
        return None if new_year else d - timedelta(1)   # NYSE does not observe Sat New Year on Fri
    if d.weekday() == 6:
        return d + timedelta(1)
    return d


def nyse_holidays(y: int) -> dict[date, str]:
    h = {}
    def add(d, name):
        if d is not None: h[d] = name
    add(_observed(date(y, 1, 1), new_year=True), "New Year's Day")
    if y >= 1998: add(_nth_weekday(y, 1, 0, 3), 'Martin Luther King Jr. Day')
    add(_nth_weekday(y, 2, 0, 3), "Washington's Birthday")
    add(_easter(y) - timedelta(2), 'Good Friday')
    add(_last_weekday(y, 5, 0), 'Memorial Day')
    if y >= 2022: add(_observed(date(y, 6, 19)), 'Juneteenth')
    add(_observed(date(y, 7, 4)), 'Independence Day')
    add(_nth_weekday(y, 9, 0, 1), 'Labor Day')
    add(_nth_weekday(y, 11, 3, 4), 'Thanksgiving')
    add(_observed(date(y, 12, 25)), 'Christmas')
    return h


def nyse_trading_days(start, end) -> pd.DatetimeIndex:
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    hol = set()
    for y in range(start.year, end.year + 1):
        hol |= {pd.Timestamp(d) for d in nyse_holidays(y)}
    hol |= {pd.Timestamp(d) for d in SPECIAL_CLOSURES}
    days = pd.bdate_range(start, end)
    return days[~days.isin(list(hol))]


def validate_ohlcv(d: pd.DataFrame, ticker: str, leveraged: bool = False, strict: bool = True) -> list[dict]:
    recs = []
    def rec(check, status, n=0, detail=''):
        recs.append({'Ticker': ticker, 'Check': check, 'Status': status, 'Count': int(n), 'Detail': detail})
    idx = d.index
    rec('sorted ascending', 'PASS' if idx.is_monotonic_increasing else 'FATAL')
    rec('duplicate dates', 'PASS' if not idx.duplicated().any() else 'FATAL', idx.duplicated().sum())
    wk = (idx.dayofweek >= 5).sum(); rec('weekend bars', 'PASS' if wk == 0 else 'FATAL', wk)
    cols = [c for c in ('Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume') if c in d]
    missing_cols = {'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'} - set(cols)
    rec('required columns', 'PASS' if not missing_cols else 'FATAL', len(missing_cols), ','.join(sorted(missing_cols)))
    na = int(d[cols].isna().sum().sum()); rec('missing values', 'PASS' if na == 0 else 'FATAL', na)
    px = [c for c in ('Open', 'High', 'Low', 'Close', 'Adj Close') if c in d]
    npos = int((d[px] <= 0).sum().sum()); rec('non-positive prices', 'PASS' if npos == 0 else 'FATAL', npos)
    if {'Open', 'High', 'Low', 'Close'} <= set(cols):
        tol = 1e-6 * d.Close
        bad = ((d.High < d[['Open', 'Close']].max(axis=1) - tol) | (d.Low > d[['Open', 'Close']].min(axis=1) + tol)
               | (d.High < d.Low - tol))
        rec('OHLC consistency (L<=O,C<=H)', 'PASS' if not bad.any() else 'FATAL', bad.sum(),
            ','.join(str(x.date()) for x in idx[bad][:10]))
    if 'Adj Close' in d:
        f = d['Adj Close'] / d['Close']
        above = (f > 1 + 1e-6).sum(); rec('Adj Close <= Close', 'PASS' if above == 0 else 'FATAL', above)
        jump = f.pct_change().abs()
        # Large capital-gain distributions exist (e.g. SPXL 2009-11-20, ~12%); flag for review,
        # fail only on implausible (>50%) one-day factor changes.
        big = jump > 0.10; huge = jump > 0.50
        rec('adjustment-factor jump >50%/day', 'PASS' if not huge.any() else 'FATAL', huge.sum(),
            ','.join(str(x.date()) for x in idx[huge.fillna(False)][:10]))
        rec('adjustment-factor jump 10-50%/day (review)', 'PASS' if not big.any() else 'WARN', big.sum(),
            ';'.join(f'{x.date()}:{v:.1%}' for x, v in jump[big.fillna(False)].items()))
        divdays = (jump > 1e-5).sum(); rec('distribution (factor-change) days', 'INFO', divdays)
    cal = nyse_trading_days(idx[0], idx[-1])
    miss = cal.difference(idx); extra = idx.difference(cal)
    rec('missing NYSE sessions', 'PASS' if len(miss) == 0 else 'FATAL', len(miss), ','.join(str(x.date()) for x in miss[:10]))
    rec('bars on NYSE holidays/closures', 'PASS' if len(extra) == 0 else 'FATAL', len(extra), ','.join(str(x.date()) for x in extra[:10]))
    if 'Volume' in d:
        z = (d.Volume <= 0).sum(); rec('zero volume', 'PASS' if z == 0 else 'WARN', z)
    r = d.Close.pct_change()
    lim = 0.30 if leveraged else 0.10
    ext = r.abs() > lim
    rec(f'|close-to-close return| > {lim:.0%}', 'PASS' if not ext.any() else 'WARN', ext.sum(),
        ';'.join(f'{x.date()}:{v:+.1%}' for x, v in r[ext].items()))
    gap = (d.Open / d.Close.shift(1) - 1).abs() > lim
    rec(f'|overnight gap| > {lim:.0%}', 'PASS' if not gap.any() else 'WARN', gap.sum(),
        ';'.join(str(x.date()) for x in idx[gap.fillna(False)][:10]))
    if strict:
        fatal = [x for x in recs if x['Status'] == 'FATAL']
        if fatal:
            raise DataValidationError(f'{ticker}: ' + '; '.join(f"{x['Check']} ({x['Count']}) {x['Detail']}" for x in fatal))
    return recs


def reversal_pairs(lev: pd.Series, und: pd.Series, k: float = 3.0, thresh: float = 0.02) -> pd.DataFrame:
    """Days where leveraged return deviates from k x underlying by more than `thresh`
    and the next day's deviation has the opposite sign (price-vs-NAV noise)."""
    e = (lev.pct_change() - k * und.pct_change()).dropna()
    flag = (e.abs() > thresh)
    rows = []
    for t in e.index[flag]:
        i = e.index.get_loc(t)
        nxt = e.iloc[i + 1] if i + 1 < len(e) else np.nan
        prv = e.iloc[i - 1] if i > 0 else np.nan
        rows.append({'Date': str(t.date()), 'Deviation': e.loc[t],
                     'Reverses': bool((np.sign(nxt) == -np.sign(e.loc[t]) and abs(nxt) > thresh / 2) or
                                      (np.sign(prv) == -np.sign(e.loc[t]) and abs(prv) > thresh / 2))})
    return pd.DataFrame(rows)
