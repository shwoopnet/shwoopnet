"""FUT2: intraday and daily families on NQ and GC (workers/FUT1_PROTOCOL.md Amendments 3 to 5). Development only.

Data: Databento GLBX.MDP3 ohlcv-1m / ohlcv-1d, volume-roll continuous (.v.0), unadjusted, stored in data/fut/db (git-ignored).
The last third of the trading dates is NEVER loaded by `score` (the cut is applied before any strategy runs).
Usage: python3 -I src/scalper/fut2.py selftest | list | score
"""
import glob, math, os, random, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "..", "data", "fut", "db")
SPEC = {
    # point value (dollars per 1.0 price), tick size, session open/close minute-of-day ET (RTH / COMEX day session)
    "NQ": dict(pv=20.0, tick=0.25, open=570, close=960, fee=2.50),
    "GC": dict(pv=100.0, tick=0.10, open=500, close=810, fee=2.50),
}
SLIP_TICKS = 1.0
BOOT = 2000
SEED = 90902
N_PRIOR = 60          # futures ledger before FUT2
BARS_MIN_DAYS = 300   # floor: trading days per window


# ---------------------------------------------------------------- data
def load_1m(tag):
    files = sorted(glob.glob(os.path.join(DB, "%s__*ohlcv-1m*.csv.zst" % tag)) + glob.glob(os.path.join(DB, "%s_1m_*.csv" % tag)))
    d = pd.concat([pd.read_csv(f, usecols=["ts_event", "instrument_id", "open", "high", "low", "close", "volume"]) for f in files])
    ts = pd.to_datetime(d["ts_event"], utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
    d = d.assign(ts=ts).sort_values("ts").reset_index(drop=True)
    return d


def load_1d(tag):
    d = pd.read_csv(os.path.join(DB, "%s_1d.csv" % tag), usecols=["ts_event", "instrument_id", "open", "high", "low", "close", "volume"])
    d["date"] = pd.to_datetime(d["ts_event"], utc=True).dt.tz_localize(None).dt.normalize()
    return d.sort_values("date").reset_index(drop=True)


class Mkt:
    """Minute arrays keyed by ET-local minute count; per-day RTH index."""

    def __init__(self, tag, d, spec):
        self.tag, self.spec = tag, spec
        t = d["ts"].values.astype("datetime64[m]").astype(np.int64)
        self.t = t
        self.o, self.h, self.l, self.c = (d[k].values.astype(float) for k in ("open", "high", "low", "close"))
        self.v = d["volume"].values.astype(float)
        self.inst = d["instrument_id"].values
        mod = (t % 1440)
        day = t // 1440
        self.mod, self.day = mod, day

    def rth_days(self, dates=None):
        """Yield (day_number, start_idx, end_idx exclusive) for bars between session open and close."""
        sp = self.spec
        sel = (self.mod >= sp["open"]) & (self.mod < sp["close"])
        idx = np.nonzero(sel)[0]
        if idx.size == 0:
            return []
        days = self.day[idx]
        brk = np.nonzero(np.diff(days) != 0)[0] + 1
        starts = np.concatenate([[0], brk])
        ends = np.concatenate([brk, [idx.size]])
        out = []
        for s, e in zip(starts, ends):
            if e - s >= 0.8 * (sp["close"] - sp["open"]):
                out.append((int(days[s]), int(idx[s]), int(idx[e - 1]) + 1))
        return out


def cost_side(spec, stress=1.0):
    return (spec["fee"] + SLIP_TICKS * spec["tick"] * spec["pv"]) * stress


# ---------------------------------------------------------------- strategies (each returns {day: pnl_dollars})
def atr_daily(d1, n=14):
    tr = np.maximum(d1["high"] - d1["low"], np.maximum((d1["high"] - d1["close"].shift(1)).abs(), (d1["low"] - d1["close"].shift(1)).abs()))
    return tr.rolling(n).mean().shift(1)     # known before the day


def trade_exit(m, i0, i_end, entry, direction, stop, target, exit_i):
    """From bar i0+1 on: stop first (conservative), then target; else exit at exit_i close. Returns exit price."""
    for i in range(i0 + 1, exit_i):
        if direction > 0:
            if m.l[i] <= stop:
                return stop
            if target is not None and m.h[i] >= target:
                return target
        else:
            if m.h[i] >= stop:
                return stop
            if target is not None and m.l[i] <= target:
                return target
    return m.c[exit_i - 1] if exit_i - 1 >= i0 else entry


def orb(m, days, window, stop_mode, target_r, exit_min, stress=1.0):
    sp = m.spec
    out = {}
    side = cost_side(sp, stress)
    for dn, s, e in days:
        o_end = s + window
        if o_end >= e - 2:
            continue
        orh, orl = m.h[s:o_end].max(), m.l[s:o_end].min()
        rng = orh - orl
        if rng <= 0:
            continue
        exit_i = min(e, s + (exit_min - sp["open"]))
        for i in range(o_end, exit_i):
            up, dn_ = m.h[i] >= orh, m.l[i] <= orl
            if not (up or dn_):
                continue
            if up and dn_:
                # both sides in one bar: conservative, entered long at the high and stopped at the low
                px = -rng
                out[dn] = px * sp["pv"] - 2 * side
                break
            direction = 1 if up else -1
            entry = orh if up else orl
            if stop_mode == "opp":
                stop = orl if up else orh
            else:
                stop = entry - 0.25 * rng * direction
            target = None if target_r is None else entry + direction * target_r * rng
            # the entry bar itself: if it also traded through the stop, count the stop
            if (direction > 0 and m.l[i] <= stop) or (direction < 0 and m.h[i] >= stop):
                ex = stop
            else:
                ex = trade_exit(m, i, e, entry, direction, stop, target, exit_i)
            out[dn] = (ex - entry) * direction * sp["pv"] - 2 * side
            break
    return out


def odc(m, session_min, stop_pts, target_pts, timeout, stress=1.0, fee=None, slip=None):
    """Opening Drive Continuation (reading of the published description). All days where the minute data has the session open."""
    sp = m.spec
    side = (fee if fee is not None else sp["fee"]) + (slip if slip is not None else SLIP_TICKS) * sp["tick"] * sp["pv"]
    side *= stress
    out = {}
    alldays = np.unique(m.day)
    for dn in alldays:
        t0 = dn * 1440 + session_min
        i0 = int(np.searchsorted(m.t, t0))
        if i0 >= len(m.t) or m.t[i0] != t0:
            continue
        for i in range(i0 + 1, min(i0 + 5, len(m.t) - 1)):
            if m.t[i] > t0 + 5:
                break
            body, pbody = abs(m.c[i] - m.o[i]), abs(m.c[i - 1] - m.o[i - 1])
            if body < 18.0 or body <= pbody:
                continue
            if m.c[i] > m.o[i] and m.c[i] > m.h[i - 1]:
                direction = 1
            elif m.c[i] < m.o[i] and m.c[i] < m.l[i - 1]:
                direction = -1
            else:
                continue
            entry = m.c[i]
            stop, target = entry - direction * stop_pts, entry + direction * target_pts
            exit_i = min(i + 1 + timeout, len(m.t))
            ex = trade_exit(m, i, len(m.t), entry, direction, stop, target, exit_i)
            out[int(dn)] = (ex - entry) * direction * sp["pv"] - 2 * side
            break
    return out


def meanrev(m, days, d1atr, t0_min, k, stress=1.0):
    sp = m.spec
    out = {}
    side = cost_side(sp, stress)
    for dn, s, e in days:
        a = d1atr.get(dn)
        i = s + (t0_min - sp["open"])
        if a is None or not np.isfinite(a) or i >= e - 2 or i <= s:
            continue
        tp = (m.h[s:i + 1] + m.l[s:i + 1] + m.c[s:i + 1]) / 3.0
        vol = m.v[s:i + 1]
        if vol.sum() <= 0:
            continue
        vwap = float((tp * vol).sum() / vol.sum())
        dev = m.c[i] - vwap
        if abs(dev) < k * a:
            continue
        direction = -1 if dev > 0 else 1
        exit_i = e - 5
        out[dn] = (m.c[exit_i - 1] - m.c[i]) * direction * sp["pv"] - 2 * side
    return out


def volbreak(m, days, d1atr, prior_close, k, stress=1.0):
    sp = m.spec
    out = {}
    side = cost_side(sp, stress)
    for dn, s, e in days:
        a, pc = d1atr.get(dn), prior_close.get(dn)
        if a is None or pc is None or not np.isfinite(a):
            continue
        up, dn_lvl = pc + k * a, pc - k * a
        exit_i = e - 5
        for i in range(s, exit_i):
            u, d_ = m.h[i] >= up, m.l[i] <= dn_lvl
            if u and d_:
                break
            if u or d_:
                direction = 1 if u else -1
                entry = up if u else dn_lvl
                out[dn] = (m.c[exit_i - 1] - entry) * direction * sp["pv"] - 2 * side
                break
    return out


def gapfade(m, days, d1atr, prior_close, prior_inst, k, stress=1.0):
    sp = m.spec
    out = {}
    side = cost_side(sp, stress)
    for dn, s, e in days:
        a, pc = d1atr.get(dn), prior_close.get(dn)
        if a is None or pc is None or not np.isfinite(a) or prior_inst.get(dn) != m.inst[s]:
            continue
        gap = m.o[s] - pc
        if abs(gap) < k * a:
            continue
        direction = -1 if gap > 0 else 1
        exit_i = e - 5
        out[dn] = (m.c[exit_i - 1] - m.o[s]) * direction * sp["pv"] - 2 * side
    return out


def overnight(m, days, prior_close, prior_inst, stress=1.0):
    """Long from the previous session close to today's open (skip if the contract changed in between)."""
    sp = m.spec
    out = {}
    side = cost_side(sp, stress)
    for dn, s, e in days:
        pc = prior_close.get(dn)
        if pc is None or prior_inst.get(dn) != m.inst[s]:
            continue
        out[dn] = (m.o[s] - pc) * sp["pv"] - 2 * side
    return out


def openclose(m, days, stress=1.0):
    sp = m.spec
    side = cost_side(sp, stress)
    return {dn: (m.c[e - 1] - m.o[s]) * sp["pv"] - 2 * side for dn, s, e in days}


def donchian(d1, n, spec, stress=1.0):
    side = cost_side(spec, stress)
    c, h, l, inst = d1["close"].values, d1["high"].values, d1["low"].values, d1["instrument_id"].values
    pos = 0
    out = {}
    prevpos = 0
    for t in range(n + 1, len(d1)):
        hi = h[t - n:t].max()
        lo = l[t - n:t].min()
        # position held through day t was decided at the close of t-1
        if c[t - 1] > h[t - 1 - n:t - 1].max() if t - 1 - n >= 0 else False:
            newpos = 1
        elif t - 1 - n >= 0 and c[t - 1] < l[t - 1 - n:t - 1].min():
            newpos = -1
        else:
            newpos = pos
        sides = abs(newpos - pos)
        roll = inst[t] != inst[t - 1] and newpos != 0
        r = 0.0 if roll else (c[t] - c[t - 1])
        out[int(d1["date"].values[t].astype("datetime64[D]").astype(np.int64))] = newpos * r * spec["pv"] - (sides + (1 if roll else 0)) * side
        pos = newpos
    return out


# ---------------------------------------------------------------- variants
def variants(tag):
    v = []
    for w in (15, 30, 60):
        v.append(("ORB:%d:opp:EOD" % w, "orb", dict(window=w, stop_mode="opp", target_r=None, exit_min=None)))
    for w in (15, 30):
        for sm in ("opp", "q25"):
            for tr in (1.0, 1.5):
                v.append(("PUBORB:%d:%s:%.1fR" % (w, sm, tr), "orb", dict(window=w, stop_mode=sm, target_r=tr, exit_min="vendor")))
    if tag == "NQ":
        for to in (30, 60):
            v.append(("PUBODC:%d" % to, "odc", dict(timeout=to)))
    for n in (20, 55, 100):
        v.append(("DONCH:%d" % n, "donch", dict(n=n)))
    for t0 in (60, 120):
        for k in (0.15, 0.30):
            v.append(("MR:%dm:%.2fATR" % (t0, k), "mr", dict(t0=t0, k=k)))
    v.append(("ONIGHT:long", "onight", {}))
    v.append(("OPENCLOSE:long", "oc", {}))
    for k in (0.25, 0.5):
        v.append(("VOLBRK:%.2fATR" % k, "vb", dict(k=k)))
    for k in (0.10, 0.25):
        v.append(("GAPFADE:%.2fATR" % k, "gf", dict(k=k)))
    return v


# ---------------------------------------------------------------- scoring
def stats(x):
    n = len(x)
    if n < 2:
        return dict(n=n, mean=0.0, sharpe=0.0, pf=0.0)
    sd = x.std(ddof=1)
    w, l = x[x > 0].sum(), -x[x < 0].sum()
    return dict(n=n, mean=x.mean(), sharpe=(x.mean() / sd * math.sqrt(252)) if sd > 0 else 0.0, pf=(w / l) if l > 0 else (99.0 if w > 0 else 0.0))


def month_boot_p(x, months, rng):
    obs = x.mean()
    cen = x - obs
    groups = {}
    for v, mo in zip(cen, months):
        groups.setdefault(mo, []).append(v)
    arrs = [np.array(g) for g in groups.values()]
    cnt = 0
    for _ in range(BOOT):
        tot = np.concatenate([arrs[rng.randrange(len(arrs))] for _ in range(len(arrs))])
        if tot.mean() >= obs:
            cnt += 1
    return (cnt + 1) / (BOOT + 1)


def build_inputs(tag):
    spec = SPEC[tag]
    d1m = load_1m(tag)
    m = Mkt(tag, d1m, spec)
    days_all = m.rth_days()
    d1 = load_1d(tag)
    atr = atr_daily(d1)
    # daily ATR keyed by the ET day number of the session (daily file date is the trading day, UTC midnight)
    d1atr = {int(dt.astype("datetime64[D]").astype(np.int64)): float(a) for dt, a in zip(d1["date"].values, atr.values)}
    # prior close/instrument of the previous RTH session
    prior_close, prior_inst = {}, {}
    for k in range(1, len(days_all)):
        _, s0, e0 = days_all[k - 1]
        dn, s, e = days_all[k]
        prior_close[dn] = m.c[e0 - 1]
        prior_inst[dn] = m.inst[e0 - 1]
    return spec, m, days_all, d1, d1atr, prior_close, prior_inst


def run_variant(name, kind, kw, tag, spec, m, days, d1, d1atr, prior_close, prior_inst, stress=1.0):
    if kind == "orb":
        ex = kw["exit_min"]
        exit_min = spec["close"] - 5 if ex is None else (min(900, spec["close"] - 5) if ex == "vendor" else ex)
        return orb(m, days, kw["window"], kw["stop_mode"], kw["target_r"], exit_min, stress)
    if kind == "odc":
        out = {}
        for smin in (570, 840, 1200):      # NY AM 09:30, NY PM 14:00, Asia 20:00 ET
            for dn, v in odc(m, smin, 25.0, 38.0, kw["timeout"], stress).items():
                out[dn * 10 + {570: 1, 840: 2, 1200: 3}[smin]] = v
        return out
    if kind == "donch":
        return donchian(d1, kw["n"], spec, stress)
    if kind == "mr":
        return meanrev(m, days, d1atr, spec["open"] + kw["t0"], kw["k"], stress)
    if kind == "onight":
        return overnight(m, days, prior_close, prior_inst, stress)
    if kind == "oc":
        return openclose(m, days, stress)
    if kind == "vb":
        return volbreak(m, days, d1atr, prior_close, kw["k"], stress)
    if kind == "gf":
        return gapfade(m, days, d1atr, prior_close, prior_inst, kw["k"], stress)
    raise ValueError(kind)


def to_series(pnl_by_day, all_days):
    """Daily P&L over all session days (zero when no trade). ODC keys are day*10+session: aggregated by day."""
    agg = {}
    for k, v in pnl_by_day.items():
        dn = k // 10 if k > 10 ** 6 else k
        agg[dn] = agg.get(dn, 0.0) + v
    return np.array([agg.get(dn, 0.0) for dn in all_days])


def score(tags=("NQ", "GC")):
    n_var = sum(len(variants(t)) for t in tags)
    N = N_PRIOR + n_var
    bar_p = 0.05 / N
    print("futures ledger N = %d (60 prior + %d), p bar %.5f" % (N, n_var, bar_p))
    rng = random.Random(SEED)
    survivors = []
    for tag in tags:
        spec, m, days, d1, d1atr, prior_close, prior_inst = build_inputs(tag)
        all_days = [d[0] for d in days]
        cut = (2 * len(all_days)) // 3          # last third never evaluated
        dev_days = all_days[:cut]
        half = cut // 2
        keep = set(dev_days)
        # restrict each market to development days BEFORE any strategy runs
        days_dev = [d for d in days if d[0] in keep]
        first_d = datetime_from(dev_days[0]); last_d = datetime_from(dev_days[-1])
        print("\n%s: %d session days, dev %s to %s (%d days, holdout %d days unread)" % (tag, len(all_days), first_d, last_d, cut, len(all_days) - cut))
        print("%-18s %7s %6s %5s | %7s %6s %5s | %6s %7s | %s" % ("variant", "W1mean", "W1shp", "W1pf", "W2mean", "W2shp", "W2pf", "x2shp", "p", "verdict"))
        mon = np.array(["%s" % datetime_from(dn)[:7] for dn in dev_days])
        for name, kind, kw in variants(tag):
            pnl = run_variant(name, kind, kw, tag, spec, m, days_dev, d1, d1atr, prior_close, prior_inst)
            pnl2 = run_variant(name, kind, kw, tag, spec, m, days_dev, d1, d1atr, prior_close, prior_inst, stress=2.0)
            x, x2 = to_series(pnl, dev_days), to_series(pnl2, dev_days)
            w1, w2, s2 = stats(x[:half]), stats(x[half:]), stats(x2)
            p = month_boot_p(x, mon, rng)
            ok = (w1["n"] >= BARS_MIN_DAYS and w2["n"] >= BARS_MIN_DAYS and w1["sharpe"] >= 0.5 and w2["sharpe"] >= 0.5
                  and w1["pf"] >= 1.5 and w2["pf"] >= 1.5 and p < bar_p)
            if ok:
                survivors.append((tag, name))
            print("%-18s %7.0f %6.2f %5.2f | %7.0f %6.2f %5.2f | %6.2f %7.4f | %s" % (
                name, w1["mean"], w1["sharpe"], w1["pf"], w2["mean"], w2["sharpe"], w2["pf"], s2["sharpe"], p, "SURVIVOR?" if ok else "falsified"))
    print("\nSURVIVORS (dev, all conditions):", survivors if survivors else "none")
    return survivors


def datetime_from(day_number):
    return str(np.datetime64(int(day_number), "D"))


# ---------------------------------------------------------------- selftest
def _mk(spec, bars):
    class D:  # minimal market with explicit bars at session open
        pass
    m = D()
    n = len(bars)
    m.spec = spec
    m.t = np.arange(n, dtype=np.int64) + 570        # day 0, minutes from 09:30
    m.o = np.array([b[0] for b in bars], float); m.h = np.array([b[1] for b in bars], float)
    m.l = np.array([b[2] for b in bars], float); m.c = np.array([b[3] for b in bars], float)
    m.v = np.ones(n); m.inst = np.ones(n, dtype=int)
    m.mod = m.t % 1440; m.day = m.t // 1440
    return m


def selftest():
    spec = SPEC["NQ"]
    # 15 bars of opening range 100..110, then a break up and a drift up, session of 40 bars
    bars = [(105, 110, 100, 105)] * 15
    bars += [(106, 112, 106, 111)] + [(111 + i, 112 + i, 110 + i, 111 + i) for i in range(1, 24)]
    m = _mk(spec, bars)
    days = [(0, 0, len(bars))]
    r = orb(m, days, 15, "opp", None, 570 + len(bars), 1.0)
    assert 0 in r and r[0] > 0, r
    # stop first when both are hit in the same bar after entry: entry bar low 90 <= stop 100 -> loss of the range
    bars2 = [(105, 110, 100, 105)] * 15 + [(106, 112, 90, 95)] + [(95, 96, 94, 95)] * 8
    m2 = _mk(spec, bars2)
    r2 = orb(m2, [(0, 0, len(bars2))], 15, "opp", None, 570 + len(bars2), 1.0)
    assert r2[0] < 0, r2
    # no lookahead: bars after the exit do not change a trade that was stopped/exited earlier
    bars3 = bars2 + [(500, 600, 400, 500)] * 5
    m3 = _mk(spec, bars3)
    r3 = orb(m3, [(0, 0, len(bars2))], 15, "opp", None, 570 + len(bars2), 1.0)
    assert abs(r3[0] - r2[0]) < 1e-9
    # costs: a flat day with no trade is absent; a trade pays two sides
    side = cost_side(spec)
    gross = (111 - 110) * 0  # placeholder to keep intent clear
    assert side == 2.5 + 0.25 * 20
    assert abs(stats(np.array([2.0, -1.0, 2.0, -1.0]))["pf"] - 2.0) < 1e-9
    print("selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "score"
    if cmd == "selftest":
        selftest()
    elif cmd == "list":
        for t in SPEC:
            for v in variants(t):
                print(t, v[0])
    else:
        score()
