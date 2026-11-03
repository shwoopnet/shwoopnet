"""TODSEAS1 (workers/TODSEAS1_REGISTRATION.md): do the cheap sides (ask 0.05 to 0.30, hard fill limit 0.30) of the 15 minute FX, metals and
energy markets win more than their price implies in windows closing at a known exchange clock time, against the neighbouring windows
(30 and 60 minutes either side) of the same series? Research only; nothing here places an order, reads a key or decides anything live.
    PYTHONPATH=src python -m scalper.todseas1 counts   (outcome-free: eligible trades per slot and third; reads NO result)
    PYTHONPATH=src python -m scalper.todseas1 score    (once: W1 and W2 only; the W3 holdout is never loaded)
    PYTHONPATH=src python -m scalper.todseas1 score --w3   (once, only after a slot passed W1 and W2)
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import event1, gen6, streaks
from .calibration import cluster_mean_z
from .event1 import Cal, calendar, pf
from .oicorex1 import load_series
from .paths import DATA_DIR

UTC = timezone.utc
ET, LON, TYO = ZoneInfo("America/New_York"), ZoneInfo("Europe/London"), ZoneInfo("Asia/Tokyo")
OUT = DATA_DIR / "todseas1_score.json"
SERIES = ["KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXPLATINUM15M", "KXPALLADIUM15M"]
FX = ["KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M"]
CMD = ["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXPLATINUM15M", "KXPALLADIUM15M"]
CLASS = {s: "fx" for s in FX} | {"KXSILVER15M": "metals", "KXCOPPER15M": "metals", "KXPLATINUM15M": "metals", "KXPALLADIUM15M": "metals",
                                 "KXWTI15M": "energy", "KXNATGAS15M": "energy"}
LOOK, FILL, LO, HI, MAX_SPREAD = 180, 120, 0.05, 0.30, 0.10
FLOOR_N, MIN_WINDOW_N, Z_BAR = 150, 30, 5.27
MON_THU, MON_FRI = (0, 1, 2, 3), (0, 1, 2, 3, 4)
# id: (zone, hour, minute, weekdays, series)
SLOTS = {
    "S1": ("HALT_IN", ET, 17, 0, MON_THU, CMD),
    "S2": ("HALT_OUT", ET, 18, 15, MON_THU, CMD),
    "S3": ("FX_ROLL", ET, 17, 0, MON_THU, FX),
    "S4": ("TOKYO_FIX", TYO, 10, 0, MON_FRI, ["KXUSDJPY15M"]),
    "S5": ("TOKYO_CLOSE", TYO, 15, 30, MON_FRI, SERIES),
    "S6": ("PRE_LONDON", LON, 7, 0, MON_FRI, SERIES),
    "S7": ("LSE_CLOSE", LON, 16, 30, MON_FRI, SERIES),
    "S8": ("PRE_US", ET, 9, 0, MON_FRI, SERIES),
    "S9": ("NY_MIDDAY", ET, 12, 0, MON_FRI, SERIES),
    "S10": ("US_LATE", ET, 15, 0, MON_FRI, SERIES),
}
HALT_SLOTS = ("S1", "S2", "S3")
NEIGHBOURS = (-3600, -1800, 1800, 3600)


def slot_of(series, ct):
    """The slot id a window closing at ct belongs to for this series, or None. Zone rules (summer time) apply."""
    for sid, (_, tz, hh, mm, days, ser) in SLOTS.items():
        if series not in ser:
            continue
        d = datetime.fromtimestamp(ct, tz)
        if d.hour == hh and d.minute == mm and d.weekday() in days:
            return sid
    return None


def in_halt_hour(ct):
    """17:00 < ET time <= 18:00 (windows closing inside the CME daily break); excluded as control for the halt slots."""
    d = datetime.fromtimestamp(ct, ET)
    m = d.hour * 60 + d.minute
    return 17 * 60 < m <= 18 * 60


def window_trade(cs, ct):
    """('trade', dict) or (reason, None). Quotes only. Same as event1.window_trade but the band and the hard fill limit are 0.30."""
    s, f = cs.get(ct - LOOK), cs.get(ct - FILL)
    if s is None or s[0] is None or s[1] is None or not 0 < s[0] < s[1] < 1:
        return "gap", None
    if s[1] - s[0] > MAX_SPREAD + 1e-9:
        return "nocheap", None
    side = next((sd for sd in ("yes", "no") if LO - 1e-9 <= event1.side_ask(s, sd) <= HI + 1e-9), None)
    if side is None:
        return "nocheap", None
    if f is None or f[0] is None or f[1] is None or not 0 < f[0] < f[1] < 1:
        return "gap", None
    fill = event1.side_ask(f, side)
    if fill > HI + 1e-9:
        return "limit", None
    if fill <= 0:
        return "gap", None
    return "trade", {"side": side, "fill": float(fill)}


def worst_loss_dollars(c=10):
    return (c * HI * 100 + math.ceil(0.07 * c * HI * (1 - HI) * 100 - 1e-9)) / 100


net_c = event1.net_c


def build(hi_ts, with_result=False):
    """Rows for every settled window before hi_ts: series, ct, trade (or reason), slot id, event flag. Result only when with_result."""
    cal = Cal(calendar())
    rows = []
    for sr in SERIES:
        for tk, (ct, res, cs, f) in load_series(sr, event1.LO_TS, hi_ts).items():
            if res not in ("yes", "no"):
                continue
            why, tr = window_trade(cs, ct)
            ev = bool(cal.types_for(ct) or cal.types_open(ct) or event_near(cal, ct))
            row = {"series": sr, "ct": ct, "why": why, "tr": tr, "slot": slot_of(sr, ct), "ev": ev, "day": event1.day_of(ct)}
            if tr is not None and with_result:
                row["win"] = (res == "yes") == (tr["side"] == "yes")
            rows.append(row)
    rows.sort(key=lambda r: (r["ct"], r["series"]))
    return rows


def event_near(cal, ct):
    """The registered event filter: any calendar event e with ct - 900 <= e <= ct."""
    import bisect
    i, j = bisect.bisect_left(cal.ts, ct - 900), bisect.bisect_right(cal.ts, ct)
    return j > i


def slot_trades(rows):
    """Slot windows after the event filter, with a trade, keyed by slot id."""
    out = defaultdict(list)
    for r in rows:
        if r["slot"] and not r["ev"] and r["tr"] is not None:
            out[r["slot"]].append(r)
    return out


def control_pool(rows):
    """{(series, ct): row} of eligible trades that may serve as a neighbour control: not in a slot, not an event window."""
    return {(r["series"], r["ct"]): r for r in rows if r["tr"] is not None and not r["ev"] and r["slot"] is None}


def control_mean(t, pool, all_series_by_ct, sid):
    """Mean net of neighbours of slot trade t: own series first; else every series at the same neighbour times; else None."""
    own, other = [], []
    for sh in NEIGHBOURS:
        cc = t["ct"] + sh
        if sid in HALT_SLOTS and in_halt_hour(cc):
            continue
        r = pool.get((t["series"], cc))
        if r is not None:
            own.append(net_c(r["tr"]["fill"], r["win"]))
        for r2 in all_series_by_ct.get(cc, []):
            if r2["series"] != t["series"]:
                other.append(net_c(r2["tr"]["fill"], r2["win"]))
    v = own or other
    return (sum(v) / len(v)) if v else None


def stats(T):
    return event1.stats(T) if T else {"n": 0}


def diff_stats(T, pool, by_ct, sid):
    res, dropped = [], 0
    for t in T:
        cm = control_mean(t, pool, by_ct, sid)
        if cm is None:
            dropped += 1
            continue
        res.append((t["day"], net_c(t["tr"]["fill"], t["win"]) - cm))
    if len(res) < 2:
        return {"diff_c": 0.0, "diff_z": 0.0, "n_used": len(res), "dropped": dropped}
    m, se, z = cluster_mean_z(res)
    return {"diff_c": m, "diff_z": z, "n_used": len(res), "dropped": dropped}


def third(ct):
    return event1.third_of(ct)


def verdict(sr):
    """sr = {'W1': stats+diff, 'W2': ...}. Registered rules 1 and 2 (the W3 read is separate)."""
    w1, w2 = sr["W1"], sr["W2"]
    n = w1.get("n", 0) + w2.get("n", 0)
    if n < FLOOR_N:
        return "NOT_ENOUGH_DATA"
    if w1.get("n", 0) < MIN_WINDOW_N or w2.get("n", 0) < MIN_WINDOW_N:
        return "NOT_ENOUGH_DATA"
    if w1["pf"] < 1.5 or w2["pf"] < 1.5 or w1["diff_c"] <= 0 or w2["diff_c"] <= 0 or w1["pf_x12"] <= 1.0 or w2["pf_x12"] <= 1.0:
        return "FALSIFIED"
    return "PASSES_W1_W2"


def probe_flag(sr):
    w1, w2 = sr["W1"], sr["W2"]
    return all(w.get("n", 0) > 0 and w["mean_c"] > 0 and w["diff_c"] > 0 for w in (w1, w2))


def summarise(T, pool, by_ct, sid):
    s = stats(T)
    if T:
        s.update(diff_stats(T, pool, by_ct, sid))
    return s


def run(hi_ts):
    rows = build(hi_ts, with_result=True)
    pool = control_pool(rows)
    by_ct = defaultdict(list)
    for r in pool.values():
        by_ct[r["ct"]].append(r)
    ST = slot_trades(rows)
    out = {"slots": {}, "series": {}, "baseline": {}, "counts": {}}
    ST["FAM"] = [t for sid in SLOTS for t in ST[sid]]
    for sid in list(SLOTS) + ["FAM"]:
        T = ST[sid]
        by_win = {"W1": [t for t in T if third(t["ct"]) == 1], "W2": [t for t in T if third(t["ct"]) == 2], "W3": [t for t in T if third(t["ct"]) == 3]}
        ent = {w: summarise(by_win[w], pool, by_ct, sid if sid != "FAM" else "S9") for w in ("W1", "W2") if True}
        # FAM control uses each trade's own slot for the halt-hour exclusion
        if sid == "FAM":
            for w in ("W1", "W2"):
                res, dropped = [], 0
                for t in by_win[w]:
                    cm = control_mean(t, pool, by_ct, t["slot"])
                    if cm is None:
                        dropped += 1
                        continue
                    res.append((t["day"], net_c(t["tr"]["fill"], t["win"]) - cm))
                if len(res) >= 2:
                    m, se, z = cluster_mean_z(res)
                    ent[w].update({"diff_c": m, "diff_z": z, "n_used": len(res), "dropped": dropped})
        allv = by_win["W1"] + by_win["W2"]
        out["slots"][sid] = {"W1": ent["W1"], "W2": ent["W2"], "pooled": summarise(allv, pool, by_ct, sid if sid != "FAM" else "S9"),
                             "verdict": verdict(ent), "probe_flag": probe_flag(ent) if ent["W1"].get("n") and ent["W2"].get("n") else False}
        if allv:
            wr = out["slots"][sid]["pooled"]["win"]
            out["slots"][sid]["streak"] = streaks_line(wr, len(allv))
    base = [r for r in rows if r["tr"] is not None and not r["ev"] and r["slot"] is None and third(r["ct"]) <= 2]
    out["baseline"] = {"W1": stats([r for r in base if third(r["ct"]) == 1]), "W2": stats([r for r in base if third(r["ct"]) == 2])}
    for sr_ in SERIES:
        T = [t for t in ST["FAM"] if t["series"] == sr_ and third(t["ct"]) <= 2]
        out["series"][sr_] = stats(T)
    for cl in ("fx", "metals", "energy"):
        T = [t for t in ST["FAM"] if CLASS[t["series"]] == cl and third(t["ct"]) <= 2]
        out["series"]["class_" + cl] = stats(T)
    return out


def streaks_line(win, n):
    try:
        return {"p": round(win, 4), "n": n}
    except Exception:
        return {}


def counts():
    rows = build(event1.CUT2)
    ST = slot_trades(rows)
    print("eligible slot trades (ask 0.05 to 0.30, hard limit 0.30; event-free) by third; outcome-free")
    for sid in SLOTS:
        W = [r for r in rows if r["slot"] == sid]
        T = ST[sid]
        print(f"{sid:4s} {SLOTS[sid][0]:12s} windows {len(W):5d} event-dropped {sum(1 for r in W if r['ev']):4d} trades W1 {sum(1 for t in T if third(t['ct']) == 1):4d} W2 {sum(1 for t in T if third(t['ct']) == 2):4d}")
    print("W3 never loaded by counts or score (hi_ts = start of W3)")


def main(argv):
    if not argv or argv[0] not in ("counts", "score"):
        print(__doc__)
        return 2
    if argv[0] == "counts":
        counts()
        return 0
    w3 = "--w3" in argv
    marker = DATA_DIR / ("todseas1_score_w3.json" if w3 else "todseas1_score.json")
    if marker.exists():
        print("refusing: already scored once", marker)
        return 3
    if w3:
        print("W3 read: not implemented before a slot passes W1 and W2 (registered rule 3)")
        return 4
    res = run(event1.CUT2)
    marker.write_text(json.dumps(res, indent=1, default=str))
    for sid, v in res["slots"].items():
        p = v["pooled"]
        print(sid, v["verdict"], "probe" if v["probe_flag"] else "", {k: (round(x, 3) if isinstance(x, float) else x) for k, x in p.items() if k in ("n", "win", "avg_fill", "payoff", "pf", "pf_x12", "mean_c", "z", "diff_c", "diff_z")})
        for w in ("W1", "W2"):
            q = v[w]
            print("   ", w, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in q.items() if k in ("n", "win", "avg_fill", "pf", "pf_x12", "mean_c", "z", "diff_c", "diff_z", "n_used", "dropped")})
    print("baseline", {w: {k: round(x, 3) for k, x in v.items() if k in ("n", "win", "avg_fill", "pf", "mean_c")} for w, v in res["baseline"].items()})
    for k, v in res["series"].items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a in ("n", "win", "avg_fill", "pf", "mean_c")})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
