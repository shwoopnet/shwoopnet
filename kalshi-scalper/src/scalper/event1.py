"""EVENT1 (workers/EVENT1_REGISTRATION.md): do the cheap sides (ask 0.05 to 0.50) of the 15 minute commodity, FX and alt-crypto markets
that are NOT traded by L1 or OICORE win more than their price implies in windows next to a scheduled public event? Research only;
nothing here places an order, reads a key or decides anything live.
    PYTHONPATH=src python -m scalper.event1 calendar   (writes workers/EVENT1_CALENDAR.csv; no market data)
    PYTHONPATH=src python -m scalper.event1 counts     (events, windows and eligible trades per month; reads NO result)
    PYTHONPATH=src python -m scalper.event1 score      (once: W1 and W2; W3 only if both pass the screen; refuses a second run)
Trade: cheaper side whose ask is 0.05 to 0.50 at the candle ending 180 s before the close (YES first), fill at that side's ask on the
candle ending 120 s before the close with a HARD LIMIT at 0.50 (a fill ask above it is no trade), held to settlement, C = 10,
fee 7% x C x p x (1-p) rounded up per order (gen6.fee).
"""
from __future__ import annotations

import bisect
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import gen6, streaks
from .calibration import cluster_mean_z
from .oicorex1 import load_series
from .paths import DATA_DIR

ROOT = Path(__file__).resolve().parents[2]
CAL_IN = ROOT / "studies" / "EVENT_CALENDAR_2026.csv"
CAL_OUT = ROOT / "workers" / "EVENT1_CALENDAR.csv"
OUT = DATA_DIR / "event1_score.json"
UTC = timezone.utc
NY, LON, TYO, HKG = (ZoneInfo(z) for z in ("America/New_York", "Europe/London", "Asia/Tokyo", "Asia/Hong_Kong"))

SERIES = ["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M"]
CLASS = {"KXSILVER15M": "metals", "KXCOPPER15M": "metals", "KXWTI15M": "energy", "KXEURUSD15M": "fx", "KXGBPUSD15M": "fx",
         "KXUSDJPY15M": "fx", "KXHYPE15M": "crypto", "KXBNB15M": "crypto"}
LOOK, FILL = 180, 120
LO, HI = 0.05, 0.50            # signal band; HI is also the hard fill limit
MAX_SPREAD = 0.10               # liquidity rule on the signal candle, chosen on metadata, applies to event and control alike
PRE, POST = 300, 0              # a window with close c is an EVENT window when c - 300 < e <= c (see the registration)
FLOOR_N = 150
Z_BAR = 5.27
CTRL_MIN = 10                   # a slot control needs this many trades, else the +-2 hour slots, else the trade is dropped from the diff
SHIFTS = (-7200, 7200)


def _ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=UTC).timestamp())


LO_TS, END_TS = _ts(2026, 8, 6), 2 ** 40
CUT1, CUT2 = _ts(2026, 9, 5), _ts(2026, 10, 5)        # W1 Aug 6 to Sep 4, W2 Sep 5 to Oct 4, W3 Oct 5 to the end of the data
US_HOLIDAYS = {date(2026, 9, 7), date(2026, 11, 26), date(2026, 12, 25)}
NYSE_EARLY = {date(2026, 11, 27), date(2026, 12, 24)}   # 13:00 ET close


# ---------------------------------------------------------------- calendar

CAL_MAP = {"CPI": "CPI", "PPI": "PPI", "JOBS": "JOBS", "GDP": "GDP_PCE", "PCE": "GDP_PCE", "RETAIL": "RETAIL", "CLAIMS": "CLAIMS",
           "FOMC": "FOMC", "EIA_WPSR": "EIA"}
GROUP = {"CPI": "DATA830", "PPI": "DATA830", "JOBS": "DATA830", "GDP_PCE": "DATA830", "RETAIL": "DATA830", "CLAIMS": "DATA830",
         "ISM_MFG": "DATA1000", "ISM_SVC": "DATA1000", "CONF_BOARD": "DATA1000", "FOMC": "FOMC", "EIA": "EIA",
         "US_OPEN": "US_OPEN", "US_CLOSE": "US_CLOSE", "LONDON_OPEN": "LONDON_OPEN", "TOKYO_OPEN": "ASIA_OPEN", "HK_OPEN": "ASIA_OPEN"}
MACRO = ("DATA830", "DATA1000", "FOMC", "EIA")


def _loc(tz, d, hh, mm):
    return int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz).timestamp())


def _business_days(y, m):
    d, out = date(y, m, 1), []
    while d.month == m:
        if d.weekday() < 5 and d not in US_HOLIDAYS:
            out.append(d)
        d += timedelta(days=1)
    return out


def calendar(cal_in=CAL_IN):
    """[(ts, type, source)] sorted. Dates from the CAL worker's verified file (BLS, BEA, Census, Federal Reserve, EIA pages) for the
    data releases and FOMC; official recurring rules for ISM, Conference Board, exchange opens and closes (see EVENT1_CALENDAR.csv)."""
    ev = []
    for r in csv.DictReader(open(cal_in)):
        k = CAL_MAP.get(r["event"])
        if k is None or r["status"] == "unverified":
            continue
        ts = int(datetime.strptime(r["release_utc"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC).timestamp())
        ev.append((ts, k, f"{r['source_url']} ({r['status']}, retrieved {r['retrieved']})"))
    for m in range(8, 13):
        bd = _business_days(2026, m)
        ev.append((_loc(NY, bd[0], 10, 0), "ISM_MFG", "rule: ISM Manufacturing PMI, first business day 10:00 ET"))
        ev.append((_loc(NY, bd[2], 10, 0), "ISM_SVC", "rule: ISM Services PMI, third business day 10:00 ET"))
        d = date(2026, m, 28)
        while d.month == m or (d + timedelta(days=1)).month == m:
            d += timedelta(days=1)
        d -= timedelta(days=1)
        while d.weekday() != 1:
            d -= timedelta(days=1)
        ev.append((_loc(NY, d, 10, 0), "CONF_BOARD", "rule: Conference Board Consumer Confidence, last Tuesday 10:00 ET"))
    d = date(2026, 8, 1)
    while d < date(2027, 1, 1):
        if d.weekday() < 5:
            if d not in US_HOLIDAYS:
                ev.append((_loc(NY, d, 9, 30), "US_OPEN", "rule: NYSE regular session opens 9:30 ET"))
                ev.append((_loc(NY, d, 13 if d in NYSE_EARLY else 16, 0), "US_CLOSE", "rule: NYSE regular session closes 16:00 ET (13:00 early close days)"))
            ev.append((_loc(LON, d, 8, 0), "LONDON_OPEN", "rule: LSE opens 08:00 London time (UK bank holidays not removed)"))
            ev.append((_loc(TYO, d, 9, 0), "TOKYO_OPEN", "rule: TSE opens 09:00 JST (Japan holidays not removed)"))
            ev.append((_loc(HKG, d, 9, 30), "HK_OPEN", "rule: HKEX opens 09:30 HKT (Hong Kong holidays not removed)"))
        d += timedelta(days=1)
    return sorted(set(ev))


def write_calendar():
    ev = calendar()
    with open(CAL_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "utc_time", "event", "source"])
        for ts, k, src in ev:
            dt = datetime.fromtimestamp(ts, UTC)
            w.writerow([dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M"), k, src])
    return len(ev)


class Cal:
    def __init__(self, events):
        self.ev = sorted(events)
        self.ts = [e[0] for e in self.ev]

    def types_for(self, ct):
        """Try A (primary): event types whose time e satisfies ct - PRE < e <= ct + POST."""
        i, j = bisect.bisect_right(self.ts, ct - PRE), bisect.bisect_right(self.ts, ct + POST)
        return {self.ev[k][1] for k in range(i, j)}

    def types_open(self, ct):
        """Try B (information only): the event falls in the first 5 minutes of the window, ct - 900 <= e < ct - 600."""
        i, j = bisect.bisect_left(self.ts, ct - 900), bisect.bisect_left(self.ts, ct - 600)
        return {self.ev[k][1] for k in range(i, j)}


# ---------------------------------------------------------------- trade

def side_ask(q, side):
    return q[1] if side == "yes" else round(1 - q[0], 6)


def window_trade(cs, ct):
    """('trade', dict) or (reason, None). Quotes and volume only; never the result.
    reasons: gap (signal or fill candle missing or one-sided), nocheap (no side in the band or a wide spread), limit (fill ask above 0.50)."""
    s, f = cs.get(ct - LOOK), cs.get(ct - FILL)
    if s is None or s[0] is None or s[1] is None or not 0 < s[0] < s[1] < 1:
        return "gap", None
    if s[1] - s[0] > MAX_SPREAD + 1e-9:
        return "nocheap", None
    side = next((sd for sd in ("yes", "no") if LO - 1e-9 <= side_ask(s, sd) <= HI + 1e-9), None)
    if side is None:
        return "nocheap", None
    if f is None or f[0] is None or f[1] is None or not 0 < f[0] < f[1] < 1:
        return "gap", None
    fill = side_ask(f, side)
    if fill > HI + 1e-9:
        return "limit", None
    if fill <= 0:
        return "gap", None
    return "trade", {"side": side, "fill": float(fill), "zv": (s[2] or 0) <= 0 or (f[2] or 0) <= 0}


def net_c(fill, win, c=10, m=1.0):
    """Cents per contract after the entry fee (no sell fee, held)."""
    return 100 * ((1.0 if win else 0.0) - fill - gen6.fee(fill, c, m))


def worst_loss_dollars(c):
    return (c * HI * 100 + math.ceil(0.07 * c * HI * (1 - HI) * 100 - 1e-9)) / 100


def day_of(ts):
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d")


def month_of(ts):
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m")


def third_of(ct):
    return 1 if ct < CUT1 else (2 if ct < CUT2 else 3)


def slot_key(series, ct):
    d = datetime.fromtimestamp(ct, UTC)
    return series, (d.hour * 3600 + d.minute * 60) // 900 * 900, d.weekday() < 5


def build(cal, series=SERIES, with_result=False):
    """One row per settled window: series, ct, trade (or reason), event types. Result is attached only when with_result."""
    rows = []
    for sr in series:
        for tk, (ct, res, cs, f) in load_series(sr, LO_TS, END_TS).items():
            if res not in ("yes", "no"):
                continue
            why, tr = window_trade(cs, ct)
            row = {"series": sr, "ct": ct, "why": why, "types": cal.types_for(ct), "typesB": cal.types_open(ct), "tr": tr, "day": day_of(ct)}
            if tr is not None and with_result:
                row["win"] = (res == "yes") == (tr["side"] == "yes")
            rows.append(row)
    rows.sort(key=lambda r: (r["ct"], r["series"]))
    return rows


# ---------------------------------------------------------------- stats

def pf(v):
    w = sum(x for x in v if x > 0)
    l = -sum(x for x in v if x < 0)
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def stats(T):
    if not T:
        return {"n": 0}
    v = [net_c(t["tr"]["fill"], t["win"]) for t in T]
    vs = [net_c(t["tr"]["fill"], t["win"], 10, 1.2) for t in T]
    wins = [t for t in T if t["win"]]
    loss = [t for t in T if not t["win"]]
    aw = sum(100 * (1 - t["tr"]["fill"] - gen6.fee(t["tr"]["fill"], 10)) for t in wins) / len(wins) if wins else 0.0
    al = sum(100 * (t["tr"]["fill"] + gen6.fee(t["tr"]["fill"], 10)) for t in loss) / len(loss) if loss else 0.0
    mean, se, z = cluster_mean_z([(t["day"], x) for t, x in zip(T, v)])
    return {"n": len(T), "days": len({t["day"] for t in T}), "win": len(wins) / len(T), "avg_fill": sum(t["tr"]["fill"] for t in T) / len(T),
            "avg_win_c": aw, "avg_loss_c": al, "payoff": aw / al if al else 0.0, "pf": pf(v), "pf_x12": pf(vs), "mean_c": mean, "z": z,
            "implied_win": sum(t["tr"]["fill"] for t in T) / len(T), "net_usd_c10": sum(v) / 10.0}


def diff_vs_slot(ev_trades, ctl_trades):
    """Each event trade's net minus the mean net of non-event trades in the same (series, 15 minute slot, weekday class); if that slot has
    fewer than CTRL_MIN, the mean of the slots 2 hours before and after; if still fewer, the trade is dropped. Returns
    (mean diff in cents, z, n used, n dropped)."""
    by = defaultdict(list)
    for t in ctl_trades:
        by[slot_key(t["series"], t["ct"])].append(net_c(t["tr"]["fill"], t["win"]))
    res, dropped = [], 0
    for t in ev_trades:
        sr, sl, wk = slot_key(t["series"], t["ct"])
        v = by.get((sr, sl, wk), [])
        if len(v) < CTRL_MIN:
            v = [x for sh in SHIFTS for x in by.get((sr, (sl + sh) % 86400, wk), [])]
        if len(v) < CTRL_MIN:
            dropped += 1
            continue
        res.append((t["day"], net_c(t["tr"]["fill"], t["win"]) - sum(v) / len(v)))
    if len(res) < 2:
        return 0.0, 0.0, len(res), dropped
    mean, se, z = cluster_mean_z(res)
    cse = cluster_mean_z([(t["day"], net_c(t["tr"]["fill"], t["win"])) for t in ctl_trades])[1] if len(ctl_trades) > 1 else 0.0
    tot = math.sqrt(se * se + cse * cse)
    return mean, (mean / tot if tot > 0 and tot != float("inf") else 0.0), len(res), dropped


# ---------------------------------------------------------------- counts

def counts():
    cal = Cal(calendar())
    rows = build(cal)
    ev = cal.ev
    print("calendar events by type and month (all of Aug 2026 to Dec 2026):")
    tm = defaultdict(lambda: defaultdict(int))
    for ts, k, _ in ev:
        tm[k][month_of(ts)] += 1
    for k in sorted(tm):
        print(f"  {k:12s}", dict(sorted(tm[k].items())))
    print("\nper series: settled windows / event windows / eligible event trades / eligible non-event trades, by month")
    for sr in SERIES:
        R = [r for r in rows if r["series"] == sr]
        if not R:
            print(sr, "none"); continue
        print(sr, "windows", len(R), "first", day_of(min(r["ct"] for r in R)), "last", day_of(max(r["ct"] for r in R)))
        mm = defaultdict(lambda: [0, 0, 0, 0])
        for r in R:
            m = mm[month_of(r["ct"])]
            m[0] += 1
            if r["types"]:
                m[1] += 1
                m[2] += r["why"] == "trade"
            else:
                m[3] += r["why"] == "trade"
        for k, v in sorted(mm.items()):
            print(f"   {k}: {v[0]:5d} {v[1]:5d} {v[2]:5d} {v[3]:5d}")
    T = [r for r in rows if r["why"] == "trade"]
    E = [r for r in T if r["types"]]
    print("\nreasons (all windows):", {w: sum(1 for r in rows if r["why"] == w) for w in ("trade", "gap", "nocheap", "limit")})
    print("event trades", len(E), "of", len(T), "eligible trades; by third:", {k: sum(1 for r in E if third_of(r["ct"]) == k) for k in (1, 2, 3)})
    span_days = (max(r["ct"] for r in rows) - min(r["ct"] for r in rows)) / 86400
    print("span days", round(span_days, 1), "event trades per 30 days", round(len(E) / span_days * 30, 1),
          "months to 150 (all 8 series pooled)", round(150 / (len(E) / span_days * 30), 2))
    for g in sorted(set(GROUP.values())):
        Eg = [r for r in E if any(GROUP[t] == g for t in r["types"])]
        Wg = [r for r in rows if any(GROUP[t] == g for t in r["types"])]
        print(f"  group {g:12s} event windows {len(Wg):5d} eligible trades {len(Eg):5d}  per 30 days {len(Eg) / span_days * 30:6.1f}  months to 150: "
              f"{(150 / (len(Eg) / span_days * 30)) if Eg else float('inf'):7.2f}")
    EB = [r for r in T if r["typesB"]]
    print("Try B (event in the first 5 minutes of the window) eligible trades", len(EB), "by third", {k: sum(1 for r in EB if third_of(r["ct"]) == k) for k in (1, 2, 3)},
          "windows A and B at once", sum(1 for r in rows if r["types"] and r["typesB"]))
    M = [r for r in E if any(GROUP[t] in MACRO for t in r["types"])]
    print("  MACRO (data releases + FOMC + EIA) event trades", len(M), "per 30 days", round(len(M) / span_days * 30, 1))
    print("by series event trades:", {sr: sum(1 for r in E if r["series"] == sr) for sr in SERIES})
    print("by third and series event trades:", {sr: [sum(1 for r in E if r["series"] == sr and third_of(r["ct"]) == k) for k in (1, 2, 3)] for sr in SERIES})


# ---------------------------------------------------------------- score

def screen(st, diff):
    return st["n"] >= 30 and st["pf"] >= 1.5 and st["pf_x12"] > 1.0


def report(label, E, C):
    se_, sc = stats(E), stats(C)
    d, z, nu, nd = diff_vs_slot(E, C)
    return {"label": label, "event": se_, "control": sc, "diff_c": d, "diff_z": z, "diff_n": nu, "diff_dropped": nd}


def score():
    if OUT.exists():
        sys.exit("EVENT1 was already scored once; the registration refuses a second run (data/event1_score.json)")
    cal = Cal(calendar())
    rows = [r for r in build(cal, with_result=True) if r["why"] == "trade"]
    E = [r for r in rows if r["types"]]
    EB = [r for r in rows if r["typesB"]]
    C = [r for r in rows if not r["types"] and not r["typesB"]]
    out = {"windows": {}, "n_event_total": len(E), "n_tryB_total": len(EB)}
    for w in (1, 2):
        Ew = [r for r in E if third_of(r["ct"]) == w]
        Cw = [r for r in C if third_of(r["ct"]) == w]
        blk = {"ALL": report("ALL", Ew, Cw)}
        for sr in SERIES:
            blk[sr] = report(sr, [r for r in Ew if r["series"] == sr], [r for r in Cw if r["series"] == sr])
        for cl in sorted(set(CLASS.values())):
            blk["class:" + cl] = report(cl, [r for r in Ew if CLASS[r["series"]] == cl], [r for r in Cw if CLASS[r["series"]] == cl])
        for g in sorted(set(GROUP.values())):
            blk["group:" + g] = report(g, [r for r in Ew if any(GROUP[t] == g for t in r["types"])], Cw)
        out["windows"][f"W{w}"] = blk
        EBw = [r for r in EB if third_of(r["ct"]) == w]
        out["windows"][f"W{w}"]["TRY_B_ALL"] = report("TRY_B_ALL", EBw, Cw)
        for sr in SERIES:
            out["windows"][f"W{w}"]["TRY_B:" + sr] = report(sr, [r for r in EBw if r["series"] == sr], [r for r in Cw if r["series"] == sr])
    pooled = [r for r in E if third_of(r["ct"]) in (1, 2)]
    out["pooled_W1W2"] = stats(pooled)
    n = len(pooled)
    a, b = out["windows"]["W1"]["ALL"]["event"], out["windows"]["W2"]["ALL"]["event"]
    if n < FLOOR_N:
        verdict = "NOT_ENOUGH_DATA"
    elif a.get("pf", 0) < 1.5 or b.get("pf", 0) < 1.5:
        verdict = "FALSIFIED"
    else:
        verdict = "SCREEN_PASSED_W1_W2"
    out["verdict"] = verdict
    if verdict == "SCREEN_PASSED_W1_W2":
        Ew3 = [r for r in E if third_of(r["ct"]) == 3]
        out["windows"]["W3"] = {"ALL": report("ALL", Ew3, [r for r in C if third_of(r["ct"]) == 3])}
        s3 = out["windows"]["W3"]["ALL"]["event"]
        out["verdict"] = "NOT_YET_FALSIFIED" if s3.get("pf", 0) >= 1.5 and s3.get("pf_x12", 0) > 1.0 else "FALSIFIED"
    seq = [r["win"] for r in sorted(pooled, key=lambda r: (r["ct"], r["series"]))]
    if seq:
        p = sum(seq) / len(seq)
        es = streaks.empirical_streaks(seq)
        out["streaks"] = {"p_win": p, "empirical": es, "p10_in_100": streaks.prob_run_at_least(10, p, 100),
                          "dist100": {k: v for k, v in streaks.longest_losing_run_distribution(p, 100).items() if k in ("mean", "median", "p95", "p99")}}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    {"calendar": lambda: print(write_calendar(), "events"), "counts": counts, "score": score}[sys.argv[1]]()
