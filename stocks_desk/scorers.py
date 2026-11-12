"""Scoring functions for the seven first-wave cards (S1 to S7). Pure functions of frames.
Each returns a per-event net pnl Series in bp indexed by the ENTRY date, plus meta.
Nothing here fetches data. Registered rules are in STOCKS_CARDS.md; any change = new registration.
"""
import numpy as np
import pandas as pd
from . import common as C

def _pivot(daily, col):
    return daily.pivot(index="date", columns="symbol", values=col).sort_index()

# ---------- S1 overnight vs intraday, index ETFs: buy official close, sell next official open
def s1_overnight_etf(daily, cost_bp=C.COST_BP["index_etf"]):
    d = C.drop_splits(daily)
    o, c = _pivot(d, "open"), _pivot(d, "close")
    ret = (o.shift(-1) / c - 1) * 1e4                      # close t -> open t+1, bp
    net = ret - 2 * cost_bp - C.SEC_SELL_BP                 # buy + sell, SEC on the sell
    pnl = net.mean(axis=1, skipna=True).dropna()            # equal weight across ETFs, one value per day
    per_etf = {k: net[k].dropna() for k in net.columns}     # Amendment 3: each ETF also reported separately
    return pnl, {"control_intraday_gross_bp": float(((c / o - 1) * 1e4).mean(axis=1).mean()),
                 "dropped_name_days": int(len(daily) - len(d)), "per_etf_pnl": per_etf}

# ---------- S2 overnight/intraday clientele in single names
def s2_signal(d, lookback=60):
    """Signal for the MOC trade at close t. LAGGED ONE DAY: uses days <= t-1 only, because an order to trade
    at the official close t must be placed before close t is known (Amendment 2)."""
    o, c = _pivot(d, "open"), _pivot(d, "close")
    overnight = o / c.shift(1) - 1
    intraday = c / o - 1
    return (overnight - intraday).rolling(lookback, min_periods=lookback).mean().shift(1)

def s2_clientele(daily, long_only=False, lookback=60, decile=0.1,
                 cost_bp=C.COST_BP["large_cap"], borrow=C.BORROW_ANNUAL):
    d = C.drop_splits(daily)
    o, c = _pivot(d, "open"), _pivot(d, "close")
    diff = s2_signal(d, lookback)
    fwd = (o.shift(-1) / c - 1)                                                 # close t -> open t+1
    rows = {}
    for t in diff.index:
        s = diff.loc[t].dropna(); f = fwd.loc[t]
        if len(s) < 50 or f.isna().all(): continue
        k = max(1, int(len(s) * decile))
        top = s.nlargest(k).index; bot = s.nsmallest(k).index
        lg = f[top].dropna().mean() * 1e4 - 2 * cost_bp - C.SEC_SELL_BP
        if long_only:
            rows[t] = lg
        else:
            # short leg: sold at the close (SEC on that sell), covered at the open, one overnight of borrow
            sh = -f[bot].dropna().mean() * 1e4 - 2 * cost_bp - C.SEC_SELL_BP - borrow / 365 * 1e4
            rows[t] = (lg + sh)
    return pd.Series(rows).dropna(), {"mode": "long" if long_only else "long_short", "dropped_name_days": int(len(daily) - len(d))}

# ---------- S3 one-week reversal in illiquid names (Friday close to next Friday close)
def s3_signal(d):
    """5-day return and 60-day dollar volume as known BEFORE close t (days <= t-1): the entry is the official
    close t, whose price is not known when the order is placed (Amendment 2)."""
    c, v = _pivot(d, "close"), _pivot(d, "volume")
    dv = (c * v).rolling(60, min_periods=60).mean().shift(1)
    r5 = c.shift(1) / c.shift(6) - 1
    return r5, dv

def s3_reversal(daily, long_short=False, cost_bp=C.COST_BP["illiquid"], borrow=C.BORROW_ANNUAL):
    d = C.drop_splits(daily)
    c, v = _pivot(d, "close"), _pivot(d, "volume")
    r5full, dv = s3_signal(d)
    last_days = c.index.to_series().groupby(c.index.to_period("W")).max().values
    rows = {}
    for i in range(1, len(last_days) - 1):
        t, tn = last_days[i], last_days[i + 1]
        liq = dv.loc[t].dropna()
        if len(liq) < 50: continue
        low = liq[liq <= liq.quantile(0.2)].index
        r5 = r5full.loc[t, low].dropna()
        if len(r5) < 10: continue
        k = max(1, int(len(r5) * 0.1))
        buy = r5.nsmallest(k).index; sell = r5.nlargest(k).index
        fwd = (c.loc[tn] / c.loc[t] - 1)
        g = fwd[buy].dropna().mean() * 1e4 - 2 * cost_bp - C.SEC_SELL_BP
        if long_short:
            g += -fwd[sell].dropna().mean() * 1e4 - 2 * cost_bp - C.SEC_SELL_BP - borrow * 7 / 365 * 1e4
        rows[t] = g
    return pd.Series(rows).dropna(), {"mode": "long_short" if long_short else "long", "dropped_name_days": int(len(daily) - len(d))}

# ---------- S4 opening gap fade (no-news filter uses only PRIOR-day volume: today's volume is not known at the open)
def s4_gap_fade(daily, direction="both", thr=0.02, cost_open=C.COST_BP["large_cap"],
                cost_close=C.COST_BP["index_etf"] + 0.0, borrow=C.BORROW_ANNUAL):
    d = C.drop_splits(daily)
    o, c, v = _pivot(d, "open"), _pivot(d, "close"), _pivot(d, "volume")
    gap = o / c.shift(1) - 1
    prior_vol_ratio = v.shift(1) / v.shift(1).rolling(20, min_periods=20).mean().shift(1)
    ev = (gap.abs() > thr) & (prior_vol_ratio < 2.0)
    if direction == "up": ev &= gap > 0
    if direction == "down": ev &= gap < 0
    side = -np.sign(gap)                                            # fade
    intr = (c / o - 1) * 1e4
    pnl = side * intr - cost_open - cost_close - C.SEC_SELL_BP
    pnl = pnl.where(ev & side.notna())
    pnl = pnl.where(~((side < 0) & ev), pnl - borrow / 365 * 1e4)   # short leg pays borrow (intraday approx 1 day)
    rows = pnl.stack().dropna()
    by_day = rows.groupby(level=0).mean()
    return by_day, {"name_events": int(len(rows)), "event_days": int(len(by_day)), "dropped_name_days": int(len(daily) - len(d))}

# ---------- S5 post-gap drift: event detected on day t from bars; enter close t+1, exit close t+21
def s5_post_gap(daily, gap_thr=0.05, vol_mult=3.0, hold=20, cost_bp=C.COST_BP["large_cap"],
                extra_slip=10.0, borrow=C.BORROW_ANNUAL):
    d = C.drop_splits(daily)
    o, c, v = _pivot(d, "open"), _pivot(d, "close"), _pivot(d, "volume")
    gap = o / c.shift(1) - 1
    vr = v / v.shift(1).rolling(20, min_periods=20).mean()          # gap day volume vs PRIOR 20-day mean
    ev = (gap.abs() > gap_thr) & (vr > vol_mult)
    idx = c.index; rows = []
    for sym in c.columns:
        busy_until = -1
        for i in np.where(ev[sym].values)[0]:
            if i <= busy_until or i + 1 + hold >= len(idx): continue
            ent, ext = c[sym].iloc[i + 1], c[sym].iloc[i + 1 + hold]
            if not (ent > 0 and ext > 0): continue
            side = np.sign(gap[sym].iloc[i])
            g = side * (ext / ent - 1) * 1e4 - 2 * (cost_bp + extra_slip) - C.SEC_SELL_BP
            if side < 0: g -= borrow * hold / 252 * 1e4 + C.SEC_SELL_BP
            rows.append((idx[i + 1], sym, g)); busy_until = i + 1 + hold
    df = pd.DataFrame(rows, columns=["date", "symbol", "pnl"])
    if df.empty: return pd.Series(dtype=float), {"name_events": 0, "dropped_name_days": int(len(daily) - len(d))}
    wk = df.groupby(df["date"].dt.to_period("W-SUN"))["pnl"].mean()   # cluster: one value per week
    wk.index = wk.index.start_time
    return wk, {"name_events": int(len(df)), "event_weeks": int(len(wk)), "dropped_name_days": int(len(daily) - len(d))}

# ---------- minute helpers for S6 and S7
def _at(minute, hhmm, col):
    m = minute.copy(); m["day"] = m["ts"].dt.normalize(); m["hm"] = m["ts"].dt.strftime("%H:%M")
    x = m[m["hm"] == hhmm]
    return x.set_index("day")[col]

def s6_lev_etf(minute, daily_spy, thr=0.01, cost_bp=C.COST_BP["index_etf"]):
    """Signal: SPY return prior official close -> close of the 15:29 bar (information available at 15:30).
    Entry: open of the 15:30 bar. Exit: official close (daily close)."""
    c = daily_spy.set_index("date")["close"].sort_index()
    prev = c.shift(1)
    sig_px = _at(minute, "15:29", "close"); ent = _at(minute, "15:30", "open")
    df = pd.concat([prev.rename("prev"), sig_px.rename("sig"), ent.rename("ent"), c.rename("close")], axis=1).dropna()
    ret = df["sig"] / df["prev"] - 1
    side = np.where(ret > thr, 1, np.where(ret < -thr, -1, 0))
    gross = side * (df["close"] / df["ent"] - 1) * 1e4
    pnl = (gross - 2 * cost_bp - C.SEC_SELL_BP)[side != 0]
    return pnl, {"qualifying_days": int((side != 0).sum()), "long_days": int((side > 0).sum()), "short_days": int((side < 0).sum())}

def s7_first30_last30(minute, daily_spy, cost_bp=C.COST_BP["index_etf"]):
    """Signal: sign of (close of the 09:59 bar / open of the 09:30 bar - 1). Entry open of 15:30 bar, exit official close."""
    c = daily_spy.set_index("date")["close"].sort_index()
    o930 = _at(minute, "09:30", "open"); c959 = _at(minute, "09:59", "close"); ent = _at(minute, "15:30", "open")
    df = pd.concat([o930.rename("o"), c959.rename("s"), ent.rename("ent"), c.rename("close")], axis=1).dropna()
    side = np.sign(df["s"] / df["o"] - 1)
    gross = side * (df["close"] / df["ent"] - 1) * 1e4
    pnl = (gross - 2 * cost_bp - C.SEC_SELL_BP)[side != 0]
    return pnl, {"days": int(len(pnl))}
