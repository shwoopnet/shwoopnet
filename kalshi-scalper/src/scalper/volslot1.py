"""VOLSLOT1 (workers/VOLSLOT1_REGISTRATION.md): buy the FAVOURITE (ask 0.85 to 0.97, hard fill limit 0.97) of the non-crypto non-gold 15 minute
series in the QUIETEST clock slots (trailing realised-move quartile), held to settlement, against the loudest quartile and all slots.
Research only; nothing here places an order, reads a key or decides anything live.
    PYTHONPATH=src python -m scalper.volslot1 counts   (outcome-free: eligible favourite trades per class and third; reads NO result)
    PYTHONPATH=src python -m scalper.volslot1 score    (once: W1 and W2 only; the W3 holdout is never loaded)
"""
from __future__ import annotations

import bisect
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import event1, gen6, streaks
from .calibration import cluster_mean_z
from .event1 import net_c, pf
from .oicorex1 import load_series
from .paths import DATA_DIR

UTC, ET = timezone.utc, ZoneInfo("America/New_York")
OUT = DATA_DIR / "volslot1_score.json"
SERIES = ["KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXPLATINUM15M", "KXPALLADIUM15M"]
LOOK, FILL, LO, HI, MAX_SPREAD = 180, 120, 0.85, 0.97, 0.10
TRAIL_DAYS, MIN_OBS, MIN_DELTAS = 30, 8, 8
FLOOR_N, MIN_WINDOW_N, Z_BAR = 150, 30, 5.27
QUARTILE = 0.25


def slot_of(ct):
    """(ET quarter-hour of the close in minutes, weekday class) -> slot key. Weekday class: Mon-Fri vs Sat-Sun, ET."""
    d = datetime.fromtimestamp(ct, ET)
    return (d.hour * 60 + d.minute) // 15, d.weekday() < 5


def path_move(cs, ct):
    """Outcome-free realised move of one window: sum of |change of the YES mid| over consecutive 1 minute candles from the open to the
    look (end_ts in (ct-900, ct-180]). None if fewer than MIN_DELTAS consecutive pairs. Uses quotes only, never the result."""
    tot, k = 0.0, 0
    prev = None
    for e in range(ct - 900 + 60, ct - LOOK + 1, 60):
        q = cs.get(e)
        if q is None or q[0] is None or q[1] is None or not 0 < q[0] < q[1] < 1:
            prev = None
            continue
        m = (q[0] + q[1]) / 2
        if prev is not None:
            tot += abs(m - prev)
            k += 1
        prev = m
    return tot if k >= MIN_DELTAS else None


def window_trade(cs, ct):
    """('trade', dict) or (reason, None). Favourite = side with ask 0.85 to 0.97 at ct-180; fill at that side's ask at ct-120, hard limit 0.97."""
    s, f = cs.get(ct - LOOK), cs.get(ct - FILL)
    if s is None or s[0] is None or s[1] is None or not 0 < s[0] < s[1] < 1:
        return "gap", None
    if s[1] - s[0] > MAX_SPREAD + 1e-9:
        return "wide", None
    side = next((sd for sd in ("yes", "no") if LO - 1e-9 <= event1.side_ask(s, sd) <= HI + 1e-9), None)
    if side is None:
        return "nofav", None
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


class Trail:
    """Trailing slot volatility per series, as of the start of each window's ET date: mean path_move of the same slot (same weekday class)
    in the 30 days before that date, at least MIN_OBS windows; quartile rank among the series' slots with a value on that date."""

    def __init__(self, obs):
        # obs: {series: [(ct, v)]} sorted by ct
        self.by = {}
        for sr, L in obs.items():
            d = defaultdict(list)
            for ct, v in sorted(L):
                d[slot_of(ct)].append((ct, v))
            self.by[sr] = {k: ([a for a, _ in x], [b for _, b in x]) for k, x in d.items()}
        self.cache = {}

    def table(self, sr, ct):
        dd = datetime.fromtimestamp(ct, ET)
        day0 = int(datetime(dd.year, dd.month, dd.day, tzinfo=ET).timestamp())
        wk = dd.weekday() < 5
        key = (sr, day0, wk)
        if key in self.cache:
            return self.cache[key]
        lo = day0 - TRAIL_DAYS * 86400
        vals = {}
        for (q, w), (ts, vs) in self.by.get(sr, {}).items():
            if w != wk:
                continue
            i, j = bisect.bisect_left(ts, lo), bisect.bisect_left(ts, day0)
            if j - i >= MIN_OBS:
                vals[q] = sum(vs[i:j]) / (j - i)
        order = sorted(vals.values())
        self.cache[key] = (vals, order)
        return self.cache[key]

    def klass(self, sr, ct):
        vals, order = self.table(sr, ct)
        q = slot_of(ct)[0]
        if q not in vals or len(order) < 8:
            return None
        v = vals[q]
        lo_n = bisect.bisect_left(order, v)
        hi_n = bisect.bisect_right(order, v)
        r = ((lo_n + hi_n - 1) / 2) / (len(order) - 1)      # mid rank in [0, 1]
        return "quiet" if r <= QUARTILE else ("loud" if r >= 1 - QUARTILE else "mid")


def build(hi_ts, with_result=False):
    data, obs = {}, {}
    for sr in SERIES:
        M = load_series(sr, event1.LO_TS, hi_ts)
        data[sr] = M
        obs[sr] = [(ct, v) for tk, (ct, res, cs, f) in M.items() if res in ("yes", "no") and (v := path_move(cs, ct)) is not None]
    trail = Trail(obs)
    rows = []
    for sr in SERIES:
        for tk, (ct, res, cs, f) in data[sr].items():
            if res not in ("yes", "no"):
                continue
            why, tr = window_trade(cs, ct)
            row = {"series": sr, "ct": ct, "why": why, "tr": tr, "klass": trail.klass(sr, ct), "day": event1.day_of(ct)}
            if tr is not None and with_result:
                row["win"] = (res == "yes") == (tr["side"] == "yes")
            rows.append(row)
    rows.sort(key=lambda r: (r["ct"], r["series"]))
    return rows


def third(ct):
    return event1.third_of(ct)


def diff(A, B):
    """Mean net of A minus mean net of B (cents), day-clustered, z from both standard errors."""
    if len(A) < 2 or len(B) < 2:
        return {"diff_c": 0.0, "diff_z": 0.0}
    ma, sa, _ = cluster_mean_z([(t["day"], net_c(t["tr"]["fill"], t["win"])) for t in A])
    mb, sb, _ = cluster_mean_z([(t["day"], net_c(t["tr"]["fill"], t["win"])) for t in B])
    se = math.hypot(sa, sb)
    return {"diff_c": ma - mb, "diff_z": (ma - mb) / se if se > 0 else 0.0}


def summarise(T):
    return event1.stats(T) if T else {"n": 0}


def groups(rows):
    T = [r for r in rows if r["tr"] is not None]
    return {"quiet": [r for r in T if r["klass"] == "quiet"], "loud": [r for r in T if r["klass"] == "loud"],
            "mid": [r for r in T if r["klass"] == "mid"], "all": T}


def verdict(q1, q2):
    n = q1.get("n", 0) + q2.get("n", 0)
    if n < FLOOR_N or q1.get("n", 0) < MIN_WINDOW_N or q2.get("n", 0) < MIN_WINDOW_N:
        return "NOT_ENOUGH_DATA"
    if q1["pf"] < 1.5 or q2["pf"] < 1.5 or q1["diff_c"] <= 0 or q2["diff_c"] <= 0 or q1["pf_x12"] <= 1.0 or q2["pf_x12"] <= 1.0:
        return "FALSIFIED"
    return "PASSES_W1_W2"


def run(hi_ts):
    rows = build(hi_ts, with_result=True)
    G = groups(rows)
    out = {"groups": {}, "classes": {}}
    for name in ("quiet", "loud", "mid", "all"):
        T = G[name]
        out["groups"][name] = {w: summarise([t for t in T if third(t["ct"]) == i]) for w, i in (("W1", 1), ("W2", 2))}
        out["groups"][name]["pooled"] = summarise([t for t in T if third(t["ct"]) <= 2])
    for w, i in (("W1", 1), ("W2", 2)):
        Q = [t for t in G["quiet"] if third(t["ct"]) == i]
        for ctl in ("loud", "all"):
            C = [t for t in G[ctl] if third(t["ct"]) == i]
            out["groups"]["quiet"][w].update({f"diff_{ctl}_c": diff(Q, C)["diff_c"], f"diff_{ctl}_z": diff(Q, C)["diff_z"]})
        out["groups"]["quiet"][w].update({"diff_c": out["groups"]["quiet"][w]["diff_loud_c"] if Q else 0.0})
    Qa = [t for t in G["quiet"] if third(t["ct"]) <= 2]
    out["pooled_diff_loud"] = diff(Qa, [t for t in G["loud"] if third(t["ct"]) <= 2])
    out["pooled_diff_all"] = diff(Qa, [t for t in G["all"] if third(t["ct"]) <= 2])
    out["verdict"] = verdict(out["groups"]["quiet"]["W1"], out["groups"]["quiet"]["W2"])
    qp = out["groups"]["quiet"]["pooled"]
    if qp.get("n"):
        out["streak100"] = streaks.longest_losing_run_distribution(qp["win"], 100)
    out["probe_flag"] = all(out["groups"]["quiet"][w].get("n", 0) > 0 and out["groups"]["quiet"][w]["mean_c"] > 0 and out["groups"]["quiet"][w]["diff_c"] > 0 for w in ("W1", "W2"))
    for sr in SERIES:
        out["classes"][sr] = summarise([t for t in G["quiet"] if t["series"] == sr and third(t["ct"]) <= 2])
    out["worst_loss_usd_c10"] = worst_loss_dollars(10)
    out["unclassified"] = sum(1 for r in rows if r["tr"] is not None and r["klass"] is None and third(r["ct"]) <= 2)
    return out


def counts():
    rows = build(event1.CUT2)
    G = groups(rows)
    print("eligible favourite trades (ask 0.85 to 0.97, hard limit 0.97) by volatility class and third; outcome-free")
    for name in ("quiet", "mid", "loud", "all"):
        print(f"{name:6s}", {w: sum(1 for t in G[name] if third(t["ct"]) == i) for w, i in (("W1", 1), ("W2", 2))})
    print("unclassified trades", sum(1 for r in rows if r["tr"] is not None and r["klass"] is None))
    print("W3 never loaded (hi_ts = start of W3)")


def main(argv):
    if not argv or argv[0] not in ("counts", "score"):
        print(__doc__)
        return 2
    if argv[0] == "counts":
        counts()
        return 0
    if OUT.exists():
        print("refusing: already scored once", OUT)
        return 3
    res = run(event1.CUT2)
    OUT.write_text(json.dumps(res, indent=1, default=str))
    r = lambda d: {k: (round(x, 3) if isinstance(x, float) else x) for k, x in d.items() if k in ("n", "win", "avg_fill", "payoff", "pf", "pf_x12", "mean_c", "z", "diff_loud_c", "diff_loud_z", "diff_all_c", "diff_all_z")}
    for name, g in res["groups"].items():
        for w in ("W1", "W2", "pooled"):
            print(name, w, r(g[w]))
    print("pooled quiet-loud", res["pooled_diff_loud"], "quiet-all", res["pooled_diff_all"])
    print("verdict", res["verdict"], "probe_flag", res["probe_flag"], "unclassified", res["unclassified"], "worst loss $", res["worst_loss_usd_c10"])
    for sr, v in res["classes"].items():
        print(sr, r(v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
