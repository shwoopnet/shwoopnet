"""PUB20 (workers/PUB20_REGISTRATION.md): ten published rules (P01 to P10) on held data, no crypto, no gold. Research only; nothing here
places an order, reads a key or decides anything live.
    PYTHONPATH=src python -m scalper.pub20 counts   (outcome-free: trigger and trade counts per rule and third; reads NO result)
    PYTHONPATH=src python -m scalper.pub20 score    (once: W1 and W2; W3 only for a rule that passes both; refuses a second run)
Universe A: 15 minute EURUSD, GBPUSD, USDJPY, silver, copper, WTI, natural gas, platinum, palladium (strike = spot at the window open).
Universe B: hourly KXINXU and KXNASDAQ100U ladders (data/inx1.sqlite, 4 pm closes).
Cheap-side trade = event1.window_trade (ask 0.05 to 0.50 at close-180, fill ask at close-120, hard limit 0.50, held). C = 10, fee
7% x C x p x (1-p) rounded up (gen6.fee). Cost: event1.net_c.
"""
from __future__ import annotations

import bisect
import json
import math
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

from . import event1
from .calibration import cluster_mean_z
from .event1 import net_c, pf, side_ask, third_of, day_of, stats as e1stats, UTC, LO_TS, END_TS
from .oicorex1 import ALT_FILES
from .paths import DATA_DIR

A_SERIES = ["KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXPLATINUM15M",
            "KXPALLADIUM15M"]
FX = ("KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M")
B_SERIES = ("KXINXU", "KXNASDAQ100U")
NY, LON = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
CT_ZONE = ZoneInfo("America/Chicago")
OUT = DATA_DIR / "pub20_score.json"
FLOOR_N = 150
Z_BAR = 5.27
STEP = 900
DAY = 86400
MAX_SPREAD = 0.10
MONTH_ENDS = {"2026-08-28", "2026-08-31", "2026-09-29", "2026-09-30", "2026-10-29", "2026-10-30"}
SETTLE = {"KXSILVER15M": (13, 30), "KXCOPPER15M": (13, 0), "KXWTI15M": (14, 30), "KXNATGAS15M": (14, 30)}   # US Eastern close of the window
RULES = ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10"]
CALENDAR = ("P03", "P06", "P07", "P09", "P10")


# ------------------------------------------------------------------ loading

def load_a(with_result=False):
    """{series: [dict(ct, K, res, cs)] sorted by ct}; cs = {end_ts: (bid_c, ask_c, volume, oi)}. First file wins per ticker."""
    out = {}
    for sr in A_SERIES:
        seen, lst = set(), []
        for name in ALT_FILES:
            p = DATA_DIR / f"{name}.sqlite"
            if not p.exists():
                continue
            db = sqlite3.connect(p)
            try:
                mk = db.execute("select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
                                (sr, LO_TS, END_TS)).fetchall()
            except sqlite3.Error:
                continue
            for tk, ct, res, K in mk:
                if tk in seen:
                    continue
                cs = {r[0]: (r[1], r[2], r[3] or 0.0, r[4]) for r in db.execute(
                    "select end_ts, bid_c, ask_c, volume, oi from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
                if not cs or res not in ("yes", "no") or not K or K <= 0:
                    continue
                seen.add(tk)
                lst.append({"ct": ct, "K": float(K), "res": res if with_result else None, "cs": cs, "tk": tk})
        lst.sort(key=lambda w: w["ct"])
        out[sr] = lst
    return out


def moves(wins):
    """{ct: ln(K(ct)/K(ct-900))} where both windows exist (contiguous)."""
    K = {w["ct"]: w["K"] for w in wins}
    return {ct: math.log(k / K[ct - STEP]) for ct, k in K.items() if ct - STEP in K}


def trailing(ms, cts_sorted, ct, lo_off, hi_off, key=abs):
    i = bisect.bisect_left(cts_sorted, ct - lo_off)
    j = bisect.bisect_right(cts_sorted, ct - hi_off)
    return [key(ms[c]) for c in cts_sorted[i:j]]


# ------------------------------------------------------------------ trades

def cheap(cs, ct):
    why, tr = event1.window_trade(cs, ct)
    return tr


def directional(cs, ct, side, lo, hi, look=180, fill=120):
    s, f = cs.get(ct - look), cs.get(ct - fill)
    if s is None or f is None:
        return None
    for q in (s, f):
        if q[0] is None or q[1] is None or not 0 < q[0] < q[1] < 1:
            return None
    if s[1] - s[0] > MAX_SPREAD + 1e-9:
        return None
    p = side_ask(f, side)
    if not (lo - 1e-9 <= p <= hi + 1e-9):
        return None
    return {"side": side, "fill": float(p)}


def mk_trade(series, ct, tr, res):
    t = {"series": series, "ct": ct, "day": day_of(ct), "tr": tr, "third": third_of(ct)}
    if res is not None:
        t["win"] = (res == "yes") == (tr["side"] == "yes")
    return t


def et(ct):
    return datetime.fromtimestamp(ct, NY)


def loc(ct, z):
    return datetime.fromtimestamp(ct, z)


# ------------------------------------------------------------------ rules on universe A

def cheap_rows(A):
    """Every window's cheap-side trade (or None) with its series and close."""
    rows = []
    for sr, wins in A.items():
        for w in wins:
            tr = cheap(w["cs"], w["ct"])
            if tr is not None:
                rows.append(mk_trade(sr, w["ct"], tr, w["res"]))
    rows.sort(key=lambda t: (t["ct"], t["series"]))
    return rows


def nr7_flag(ms, ct):
    """True if |move at ct| is strictly smaller than each of the 6 before it (7 contiguous moves)."""
    v = []
    for j in range(7):
        m = ms.get(ct - STEP * j)
        if m is None:
            return False
        v.append(abs(m))
    return v[0] < min(v[1:])


def volexp_flag(ms, cts, ct):
    v4 = []
    for j in range(4):
        m = ms.get(ct - STEP * j)
        if m is None:
            return False
        v4.append(abs(m))
    tr = trailing(ms, cts, ct, DAY - 1, 0)       # (ct - 24h, ct]
    if len(tr) < 48:
        return False
    med = statistics.median(tr)
    return med > 0 and sum(v4) / 4 >= 1.5 * med


def rule_p01_p02(A, cheap_by):
    out = {"P01": [], "P02": []}
    for sr, wins in A.items():
        ms = moves(wins)
        cts = sorted(ms)
        for w in wins:
            t = cheap_by.get((sr, w["ct"]))
            if t is None:
                continue
            ct = w["ct"]
            if nr7_flag(ms, ct):
                out["P01"].append(t)
            if volexp_flag(ms, cts, ct):
                out["P02"].append(t)
    return out


def rule_p04(A, with_result):
    ms = {sr: moves(w) for sr, w in A.items()}
    cts = {sr: sorted(m) for sr, m in ms.items()}
    byct = defaultdict(dict)
    for sr, wins in A.items():
        for w in wins:
            byct[w["ct"]][sr] = w
    out = []
    for ct in sorted(byct):
        z = {}
        for sr, w in byct[ct].items():
            m = ms[sr].get(ct)
            if m is None:
                continue
            tr = trailing(ms[sr], cts[sr], ct, DAY, STEP)     # [ct - 24h, ct - 900]
            if len(tr) < 48:
                continue
            sd = statistics.pstdev([ms[sr][c] for c in cts[sr][bisect.bisect_left(cts[sr], ct - DAY):bisect.bisect_right(cts[sr], ct - STEP)]])
            if sd > 0:
                z[sr] = m / sd
        if len(z) < 5:
            continue
        lo = min(z, key=z.get)
        hi = max(z, key=z.get)
        for sr, side, ok in ((lo, "yes", z[lo] <= -1.5), (hi, "no", z[hi] >= 1.5)):
            if not ok:
                continue
            w = byct[ct][sr]
            tr = directional(w["cs"], ct, side, 0.20, 0.80)
            if tr is not None:
                out.append(mk_trade(sr, ct, tr, w["res"]))
    return out


def calendar_diff(cheap_all, ev_key, ctrl_key):
    """Per third: for each event trade, net minus the mean net of control trades with the same key (>= 10 control trades, else dropped).
    Returns {third: {"ev": [trade], "diffs": [(day, diff)], "dropped": n}}."""
    res = {}
    for th in (1, 2, 3):
        ev = [t for t in cheap_all if t["third"] == th and ev_key(t) is not None]
        ctl = defaultdict(list)
        for t in cheap_all:
            if t["third"] != th:
                continue
            k = ctrl_key(t)
            if k is not None and ev_key(t) is None:
                ctl[k].append(t)
        diffs, dropped = [], 0
        for t in ev:
            c = ctl.get(ev_key(t), [])
            if len(c) < 10:
                dropped += 1
                continue
            if "win" not in t:           # counts mode: nothing about the result is read
                continue
            mc = sum(net_c(x["tr"]["fill"], x["win"]) for x in c) / len(c)
            diffs.append((t["day"], net_c(t["tr"]["fill"], t["win"]) - mc))
        res[th] = {"ev": ev, "diffs": diffs, "dropped": dropped}
    return res


def eastern_slot(ct):
    d = et(ct)
    return d.hour * 60 + d.minute


def ev_p03(t):
    d = et(t["ct"])
    mins = d.hour * 60 + d.minute
    return (t["series"],) if d.weekday() == 4 and 12 * 60 < mins <= 17 * 60 else None


def ctrl_p03(t):
    d = et(t["ct"])
    mins = d.hour * 60 + d.minute
    return (t["series"],) if d.weekday() in (1, 2, 3) and 12 * 60 < mins <= 17 * 60 else None


def fix_name(series, ct):
    """P06 fix windows, weekdays only, exact close time."""
    if series in FX:
        l = loc(ct, LON)
        if l.weekday() < 5 and (l.hour, l.minute) == (16, 0):
            return "LON16"
        n = et(ct)
        if n.weekday() < 5 and (n.hour, n.minute) == (10, 0):
            return "NY10"
    if series == "KXSILVER15M":
        l = loc(ct, LON)
        if l.weekday() < 5 and (l.hour, l.minute) == (12, 0):
            return "LON12"
    return None


def settle_name(series, ct):
    hm = SETTLE.get(series)
    if hm is None:
        return None
    d = et(ct)
    return "SET" if d.weekday() < 5 and (d.hour, d.minute) == hm else None


def build_offset_rule(A, cheap_all, namer):
    ev_times = defaultdict(dict)       # (series) -> {ct: name}
    for sr, wins in A.items():
        for w in wins:
            nm = namer(sr, w["ct"])
            if nm:
                ev_times[sr][w["ct"]] = nm
    ctl_times = defaultdict(dict)
    for sr, d in ev_times.items():
        for ct, nm in d.items():
            for off in (-7200, 7200):
                if ct + off not in d:
                    ctl_times[sr][ct + off] = nm
    ev_key = lambda t: (t["series"], ev_times[t["series"]][t["ct"]]) if t["ct"] in ev_times.get(t["series"], {}) else None
    ctrl_key = lambda t: (t["series"], ctl_times[t["series"]][t["ct"]]) if t["ct"] in ctl_times.get(t["series"], {}) else None
    return ev_key, ctrl_key


def ev_p07(t):
    d = et(t["ct"])
    return (t["series"], d.hour) if d.strftime("%Y-%m-%d") in MONTH_ENDS and d.weekday() < 5 else None


def ctrl_p07(t):
    d = et(t["ct"])
    return (t["series"], d.hour) if d.weekday() < 5 else None


def reopen_events(A):
    """{series: {ct: slot}} for windows whose open is within 60 minutes after a gap of at least 90 minutes between the previous
    window's close and this window's open (a daily 60 minute break is not a gap). slot = 0..3."""
    out = {}
    for sr, wins in A.items():
        cts = sorted(w["ct"] for w in wins)
        d, R = {}, None
        prev = None
        for ct in cts:
            op = ct - STEP
            if prev is not None and op - prev >= 5400:
                R = op
            if R is not None and 0 <= op - R < 3600:
                d[ct] = int((op - R) // STEP)
            prev = ct
        out[sr] = d
    return out


def build_reopen(A):
    ev = reopen_events(A)
    ev_key = lambda t: (t["series"], loc(t["ct"], CT_ZONE).hour) if t["ct"] in ev.get(t["series"], {}) else None
    ctrl_key = lambda t: ((t["series"], loc(t["ct"], CT_ZONE).hour)
                          if loc(t["ct"], CT_ZONE).weekday() in (0, 1, 2, 3) else None)
    return ev_key, ctrl_key


# ------------------------------------------------------------------ universe B (index ladders)

def load_b():
    """{(index, close_ts): {"res": {strike: result}, "cs": {strike: {end_ts: (bid, ask, vol)}}}} from data/inx1.sqlite (4 pm closes)."""
    db = sqlite3.connect(DATA_DIR / "inx1.sqlite")
    ev = {}
    for tk, sr, ct, res, K in db.execute("select ticker, series, close_ts, result, strike from market where series in ('KXINXU','KXNASDAQ100U')"):
        e = ev.setdefault((sr, ct), {"res": {}, "cs": {}})
        e["res"][K] = res
        e["cs"][K] = {r[0]: (r[1], r[2], r[3] or 0.0) for r in db.execute(
            "select end_ts, bid_c, ask_c, volume from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
    return ev


def last_before(cs, t, back):
    """The latest candle with end in (t - back, t]."""
    ks = [k for k in cs if t - back < k <= t]
    return cs[max(ks)] if ks else None


def first_after(cs, t, fwd):
    ks = [k for k in cs if t < k <= t + fwd]
    return cs[min(ks)] if ks else None


def valid(q, max_spread):
    return q is not None and 0 < q[0] < q[1] < 1 and q[1] - q[0] <= max_spread + 1e-9


PROBIT = statistics.NormalDist().inv_cdf
PHI = statistics.NormalDist().cdf


def fit_leave_one_out(Ks, ps, i):
    """Fitted probability at strike i from a quadratic of probit(p) on strike over the others."""
    ks = np.array([k for j, k in enumerate(Ks) if j != i], dtype=float)
    ys = np.array([PROBIT(p) for j, p in enumerate(ps) if j != i], dtype=float)
    mu, sd = ks.mean(), ks.std() or 1.0
    c = np.polyfit((ks - mu) / sd, ys, 2)
    return PHI(float(np.polyval(c, (Ks[i] - mu) / sd)))


def rule_p08(B, with_result):
    out = []
    for (sr, ct), e in sorted(B.items(), key=lambda x: x[0][1]):
        Lk = ct - 1800
        q = {}
        for K, cs in e["cs"].items():
            c = last_before(cs, Lk, 300)
            if valid(c, 0.06) and 0.05 <= (c[0] + c[1]) / 2 <= 0.95:
                q[K] = c
        if len(q) < 7:
            continue
        Ks = sorted(q)
        mids = [(q[K][0] + q[K][1]) / 2 for K in Ks]
        for i, K in enumerate(Ks):
            fit = fit_leave_one_out(Ks, mids, i)
            c = q[K]
            f = first_after(e["cs"][K], Lk, 300)
            if not valid(f, 0.10):
                continue
            side = None
            if c[1] <= fit - 0.04 and f[1] <= fit - 0.02:
                side = "yes"
            elif (1 - c[0]) <= (1 - fit) - 0.04 and (1 - f[0]) <= (1 - fit) - 0.02:
                side = "no"
            if side is None:
                continue
            p = f[1] if side == "yes" else round(1 - f[0], 6)
            if not 0.10 - 1e-9 <= p <= 0.90 + 1e-9:
                continue
            res = e["res"][K] if with_result else None
            out.append(mk_trade(sr + ":" + str(K), ct, {"side": side, "fill": float(p)}, res))
    return out


def atm(e, Lk):
    best = None
    for K, cs in e["cs"].items():
        c = last_before(cs, Lk, 300)
        if valid(c, 0.10) and c[2] > 0:
            m = (c[0] + c[1]) / 2
            if 0.02 < m < 0.98 and (best is None or abs(m - 0.5) < best[0]):
                best = (abs(m - 0.5), K, m)
    return best


def rule_p05(B, with_result):
    out = []
    closes = sorted({ct for (_, ct) in B})
    for ct in closes:
        if ("KXINXU", ct) not in B or ("KXNASDAQ100U", ct) not in B:
            continue
        Lk = ct - 1800
        mv, pick = {}, {}
        for sr in B_SERIES:
            e = B[(sr, ct)]
            a = atm(e, Lk)
            if a is None:
                continue
            c0 = last_before(e["cs"][a[1]], ct - 3600, 300)
            if not valid(c0, 0.10) or not 0.02 < (c0[0] + c0[1]) / 2 < 0.98:
                continue
            mv[sr] = PROBIT(a[2]) - PROBIT((c0[0] + c0[1]) / 2)
            pick[sr] = a[1]
        if len(mv) < 2:
            continue
        for lead, lag in (("KXNASDAQ100U", "KXINXU"), ("KXINXU", "KXNASDAQ100U")):
            if abs(mv[lead]) >= 0.5:
                sgn = 1 if mv[lead] > 0 else -1
                if sgn * mv[lag] <= 0.15:
                    e = B[(lag, ct)]
                    K = pick[lag]
                    f = first_after(e["cs"][K], Lk, 300)
                    if not valid(f, 0.10):
                        continue
                    side = "yes" if sgn > 0 else "no"
                    p = f[1] if side == "yes" else round(1 - f[0], 6)
                    if 0.20 - 1e-9 <= p <= 0.80 + 1e-9:
                        out.append(mk_trade(lag + ":" + str(K), ct, {"side": side, "fill": float(p)}, e["res"][K] if with_result else None))
    return out


# ------------------------------------------------------------------ assembly

def build_all(with_result):
    A = load_a(with_result)
    cheap_all = cheap_rows(A)
    cheap_by = {(t["series"], t["ct"]): t for t in cheap_all}
    R = {}
    R.update({k: {"trades": v, "diff": None} for k, v in rule_p01_p02(A, cheap_by).items()})
    R["P03"] = {"diff": calendar_diff(cheap_all, ev_p03, ctrl_p03)}
    R["P04"] = {"trades": rule_p04(A, with_result), "diff": None}
    B = load_b()
    R["P05"] = {"trades": rule_p05(B, with_result), "diff": None}
    k1, k2 = build_offset_rule(A, cheap_all, fix_name)
    R["P06"] = {"diff": calendar_diff(cheap_all, k1, k2)}
    R["P07"] = {"diff": calendar_diff(cheap_all, ev_p07, ctrl_p07)}
    R["P08"] = {"trades": rule_p08(B, with_result), "diff": None}
    k1, k2 = build_offset_rule(A, cheap_all, settle_name)
    R["P09"] = {"diff": calendar_diff(cheap_all, k1, k2)}
    k1, k2 = build_reopen(A)
    R["P10"] = {"diff": calendar_diff(cheap_all, k1, k2)}
    for k, v in R.items():
        if v.get("diff") is not None:
            v["trades"] = [t for th in (1, 2, 3) for t in v["diff"][th]["ev"]]
    return R


def counts():
    R = build_all(False)
    print("rule  trades W1 W2 W3 (no result read)")
    for k in RULES:
        T = R[k]["trades"]
        print(k, len(T), [sum(1 for t in T if t["third"] == th) for th in (1, 2, 3)],
              ("dropped no control: " + str([R[k]["diff"][th]["dropped"] for th in (1, 2, 3)])) if R[k]["diff"] else "")


# ------------------------------------------------------------------ verdict

def third_report(rule, R, th):
    T = [t for t in R[rule]["trades"] if t["third"] == th]
    st = e1stats(T) if T else {"n": 0}
    out = {"stats": st}
    if rule in CALENDAR:
        d = R[rule]["diff"][th]["diffs"]
        mean, se, z = cluster_mean_z(d) if d else (0.0, float("inf"), 0.0)
        out.update({"excess_c": mean if d else None, "excess_z": z if d else None, "diff_n": len(d), "dropped": R[rule]["diff"][th]["dropped"]})
        out["excess"] = mean if d else None
    else:
        out["excess"] = st.get("mean_c") if st.get("n") else None
    return out


def passes(rep):
    st = rep["stats"]
    return bool(st.get("n")) and st["pf"] >= 1.5 and rep["excess"] is not None and rep["excess"] >= 0


def verdict(w1, w2, w3, n12):
    """Registered kill rule. w3 is None while unread."""
    if n12 < FLOOR_N:
        return "NOT_ENOUGH_DATA"
    if not (passes(w1) and passes(w2)):
        return "FALSIFIED"
    if w3 is None or not passes(w3):
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def score():
    if OUT.exists():
        print("Refusing to run again: the outcome was already read")
        return
    R = build_all(True)
    out = {}
    for k in RULES:
        w1, w2 = third_report(k, R, 1), third_report(k, R, 2)
        n12 = (w1["stats"].get("n") or 0) + (w2["stats"].get("n") or 0)
        both = n12 >= FLOOR_N and passes(w1) and passes(w2)
        w3 = third_report(k, R, 3) if both else None
        res = {"verdict": verdict(w1, w2, w3, n12), "n12": n12, "W1": w1, "W2": w2, "W3": w3 if w3 else "unread"}
        pos = [rep["stats"].get("mean_c") for rep in (w1, w2)]
        res["positive_both_halves"] = all(p is not None and p > 0 for p in pos)
        T12 = [t for t in R[k]["trades"] if t["third"] in (1, 2)]
        res["pooled"] = e1stats(T12) if T12 else {"n": 0}
        res["max_fill"] = max((t["tr"]["fill"] for t in T12), default=None)
        res["trades_per_day"] = (len(T12) / len({t["day"] for t in T12})) if T12 else None
        res["days"] = len({t["day"] for t in T12})
        out[k] = res
    OUT.write_text(json.dumps(out, indent=1, default=str))
    for k in RULES:
        r = out[k]
        p = r["pooled"]
        print(k, r["verdict"], "n12", r["n12"], "W1", r["W1"]["stats"].get("n"), "PF", _f(r["W1"]["stats"].get("pf")), "exc", _f(r["W1"]["excess"]),
              "| W2", r["W2"]["stats"].get("n"), "PF", _f(r["W2"]["stats"].get("pf")), "exc", _f(r["W2"]["excess"]),
              "| pooled win", _f(p.get("win")), "fill", _f(p.get("avg_fill")), "PF", _f(p.get("pf")), "mean", _f(p.get("mean_c")), "z", _f(p.get("z")),
              "posboth" if r["positive_both_halves"] else "")


def _f(x):
    return "na" if x is None else f"{x:.3f}"


if __name__ == "__main__":
    {"counts": counts, "score": score}[sys.argv[1]]()
