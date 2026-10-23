"""IDEAS100 (README, Pre-registration: IDEAS100): one hundred Bitcoin and Ethereum entry rules from fifteen families, backtested on the same data, split and bars at two entries each.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade. A survivor is only a candidate for a forward paper test.
Usage: python -m scalper.ideas100 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import ideas20 as I
from . import lstrats as L
from .paths import DATA_DIR

# ---- fixed in the README before any outcome was scored ----
COINS = ("KXBTC15M", "KXETH15M")
ENTRIES = {"E540": (540, (0.80, 0.93)), "L1360": (360, (0.88, 0.97))}
MIN_DISC, MIN_CONF, DISC_Z = 150, 70, 3.0
WIN = 900
RESULT = DATA_DIR / "ideas100_result.txt"


def utc(m):
    return datetime.fromtimestamp(m["close"], timezone.utc)


def side_mid(c, side):
    return (c["bid"] + c["ask"]) / 2 if side == "yes" else 1 - (c["bid"] + c["ask"]) / 2


class Ctx:
    """Everything a rule may read, all known at the decision candle: this market's earlier candles, the same coin's previous windows (by close time) and the other coin's market for the same window."""
    def __init__(self, mk_by_close, coin):
        self.by_close, self.coin = mk_by_close, coin

    def prior(self, m, k):
        return self.by_close[self.coin].get(m["close"] - WIN * k)

    def other(self, m):
        oc = next(c for c in self.by_close if c != self.coin)
        return self.by_close[oc].get(m["close"])


def first(m):
    return m["c"][0]


def path(m, c, e, side):
    return [side_mid(x, side) for x in e] + [side_mid(c, side)]


def changes(v):
    return [b - a for a, b in zip(v, v[1:])]


FEATS = {
    "drift": lambda ctx, m, c, e, f: side_mid(c, f[0]) - side_mid(first(m), f[0]),
    "dd": lambda ctx, m, c, e, f: max(path(m, c, e, f[0])) - side_mid(c, f[0]),
    "rvol": lambda ctx, m, c, e, f: st.pstdev(changes(path(m, c, e, f[0]))) if len(e) >= 4 else None,
    "oi_growth": lambda ctx, m, c, e, f: c["oi"] / first(m)["oi"] if first(m)["oi"] > 0 else None,
    "oi_level": lambda ctx, m, c, e, f: c["oi"] if c["oi"] > 0 else None,
}


def compute_cuts(mks, left, band):
    """Quartile cuts of each FEATS value over all baseline entries (both coins) of one entry type: features only, no outcome is read."""
    by_close = {coin: {m["close"]: m for m in mk.values()} for coin, mk in mks.items()}
    vals = {k: [] for k in FEATS}
    for coin, mk in mks.items():
        ctx = Ctx(by_close, coin)
        for m in mk.values():
            c, e = I.at(m, left)
            if c is None:
                continue
            f = L.favorite(c["bid"], c["ask"], band)
            if not f:
                continue
            for k, fn in FEATS.items():
                v = fn(ctx, m, c, e, f)
                if v is not None:
                    vals[k].append(v)
    cuts = {}
    for k, v in vals.items():
        v.sort()
        cuts[k] = (v[len(v) // 4], v[len(v) // 2], v[(3 * len(v)) // 4])
    return cuts


def build_rules():
    R = []

    def add(name, fn):
        R.append((name, fn))

    def need_fav(fn):
        def rule(ctx, m, c, e, band, left):
            f = L.favorite(c["bid"], c["ask"], band)
            return (f if fn(ctx, m, c, e, f) else None) if f else None
        return rule

    def fav_ctx(fn):
        return need_fav(lambda ctx, m, c, e, f: fn(ctx, m, c, e, f))

    # A. three hour blocks of the close time (8) and weekday (7)
    for h in range(0, 24, 3):
        add(f"HOURBLOCK_{h:02d}_{h + 3:02d}", need_fav(lambda ctx, m, c, e, f, h=h: h <= utc(m).hour < h + 3))
    for d in range(7):
        add(f"DOW_{d}", need_fav(lambda ctx, m, c, e, f, d=d: utc(m).weekday() == d))
    # C, D, V, OI. quartiles (cuts from the entry's own baseline features): drift since open, drawdown from peak, realised volatility, open-interest growth and level (20)
    def quart(feat, i):
        def fn(ctx, m, c, e, f):
            v = FEATS[feat](ctx, m, c, e, f)
            if v is None:
                return False
            q = ctx.cuts[feat]
            lo = -1e18 if i == 0 else q[i - 1]
            hi = 1e18 if i == 3 else q[i]
            return lo < v <= hi          # ties at a cut (a drawdown of exactly 0 is common) stay in the lower bucket
        return need_fav(fn)
    for feat, label in (("drift", "DRIFT"), ("dd", "DD"), ("rvol", "RVOL"), ("oi_growth", "OIGROWTH"), ("oi_level", "OILEVEL")):
        for i in range(4):
            add(f"{label}_Q{i + 1}", quart(feat, i))
    # E. path shape (8)
    def flips(v):
        s = [x for x in changes(v) if abs(x) > 0.004]
        return sum(1 for a, b in zip(s, s[1:]) if (a > 0) != (b > 0))
    for nm, lo, hi in (("0", 0, 1), ("1", 1, 2), ("2", 2, 3), ("GE3", 3, 99)):
        add(f"FLIPS_{nm}", need_fav(lambda ctx, m, c, e, f, lo=lo, hi=hi: len(e) >= 4 and lo <= flips(path(m, c, e, f[0])) < hi))
    def upshare(m, c, e, f):
        ch = changes(path(m, c, e, f[0]))
        mv = [x for x in ch if abs(x) > 0.004]
        return None if len(mv) < 2 else sum(1 for x in mv if x > 0) / len(mv)
    add("UPSHARE_GE70", need_fav(lambda ctx, m, c, e, f: (u := upshare(m, c, e, f)) is not None and u >= 0.7))
    add("UPSHARE_LE30", need_fav(lambda ctx, m, c, e, f: (u := upshare(m, c, e, f)) is not None and u <= 0.3))
    add("LAST3_UP", need_fav(lambda ctx, m, c, e, f: len(changes(path(m, c, e, f[0]))) >= 3 and all(x > 0.004 for x in changes(path(m, c, e, f[0]))[-3:])))
    add("LAST3_DOWN", need_fav(lambda ctx, m, c, e, f: len(changes(path(m, c, e, f[0]))) >= 3 and all(x < -0.004 for x in changes(path(m, c, e, f[0]))[-3:])))
    # F. results in the previous 8 and 4 windows (6)
    def yes_count(ctx, m, k):
        ps = [ctx.prior(m, i) for i in range(1, k + 1)]
        return None if any(p is None for p in ps) else sum(1 for p in ps if p["res"] == "yes")
    add("YES8_GE6_FAVYES", need_fav(lambda ctx, m, c, e, f: (n := yes_count(ctx, m, 8)) is not None and n >= 6 and f[0] == "yes"))
    add("YES8_GE6_FAVNO", need_fav(lambda ctx, m, c, e, f: (n := yes_count(ctx, m, 8)) is not None and n >= 6 and f[0] == "no"))
    add("YES8_LE2_FAVYES", need_fav(lambda ctx, m, c, e, f: (n := yes_count(ctx, m, 8)) is not None and n <= 2 and f[0] == "yes"))
    add("YES8_LE2_FAVNO", need_fav(lambda ctx, m, c, e, f: (n := yes_count(ctx, m, 8)) is not None and n <= 2 and f[0] == "no"))
    add("YES4_3_FAVYES", need_fav(lambda ctx, m, c, e, f: (n := yes_count(ctx, m, 4)) is not None and n >= 3 and f[0] == "yes"))
    add("YES4_1_FAVNO", need_fav(lambda ctx, m, c, e, f: (n := yes_count(ctx, m, 4)) is not None and n <= 1 and f[0] == "no"))
    # G. cross-asset: the other coin's yes-mid drift since open minus this coin's (6), and the other coin's price on our side (2)
    def rel(ctx, m, c, left):
        o = ctx.other(m)
        if o is None:
            return None
        oc, _ = I.at(o, left)
        if oc is None:
            return None
        return (((oc["bid"] + oc["ask"]) / 2 - (first(o)["bid"] + first(o)["ask"]) / 2) - ((c["bid"] + c["ask"]) / 2 - (first(m)["bid"] + first(m)["ask"]) / 2))
    def gmk(cond):
        def rule(ctx, m, c, e, band, left):
            f = L.favorite(c["bid"], c["ask"], band)
            if not f:
                return None
            r = rel(ctx, m, c, left)
            return f if r is not None and cond(r, f) else None
        return rule
    for nm, cond in (("OTHER_STRONGER_FAVYES", lambda r, f: r >= 0.05 and f[0] == "yes"), ("OTHER_STRONGER_FAVNO", lambda r, f: r >= 0.05 and f[0] == "no"),
                     ("OTHER_WEAKER_FAVYES", lambda r, f: r <= -0.05 and f[0] == "yes"), ("OTHER_WEAKER_FAVNO", lambda r, f: r <= -0.05 and f[0] == "no"),
                     ("OTHER_SAME_FAVYES", lambda r, f: abs(r) < 0.02 and f[0] == "yes"), ("OTHER_SAME_FAVNO", lambda r, f: abs(r) < 0.02 and f[0] == "no")):
        add(f"G_{nm}", gmk(cond))
    def other_price_gap(ctx, m, left, f):
        o = ctx.other(m)
        if o is None:
            return None
        oc, _ = I.at(o, left)
        return None if oc is None else I.ask_side(oc, f[0]) - f[1]
    def opk(sign):
        def rule(ctx, m, c, e, band, left):
            f = L.favorite(c["bid"], c["ask"], band)
            if not f:
                return None
            g = other_price_gap(ctx, m, left, f)
            return f if g is not None and sign * g >= 0.03 else None
        return rule
    add("OTHER_PRICE_HIGHER", opk(1))
    add("OTHER_PRICE_LOWER", opk(-1))
    # H. candle microstructure (2) and last spread (1)
    add("ASK_FELL_BACK", need_fav(lambda ctx, m, c, e, f: c["ask_h"] is not None and c["ask_h"] - c["ask"] >= 0.02))
    add("BID_BOUNCED", need_fav(lambda ctx, m, c, e, f: c["bid_l"] is not None and c["bid"] - c["bid_l"] >= 0.02))
    add("SPREAD_GE2", need_fav(lambda ctx, m, c, e, f: c["ask"] - c["bid"] >= 0.02))
    # I. strike moves against the previous window (4); prior window reversed or clean (2)
    def sdir(ctx, m):
        p = ctx.prior(m, 1)
        return None if not p or not p["strike"] or not m["strike"] else m["strike"] / p["strike"] - 1
    add("STRIKE_UP_FAVYES", need_fav(lambda ctx, m, c, e, f: (r := sdir(ctx, m)) is not None and r >= 0.0005 and f[0] == "yes"))
    add("STRIKE_UP_FAVNO", need_fav(lambda ctx, m, c, e, f: (r := sdir(ctx, m)) is not None and r >= 0.0005 and f[0] == "no"))
    add("STRIKE_DOWN_FAVYES", need_fav(lambda ctx, m, c, e, f: (r := sdir(ctx, m)) is not None and r <= -0.0005 and f[0] == "yes"))
    add("STRIKE_DOWN_FAVNO", need_fav(lambda ctx, m, c, e, f: (r := sdir(ctx, m)) is not None and r <= -0.0005 and f[0] == "no"))
    def prior_state(ctx, m):
        p = ctx.prior(m, 1)
        if not p:
            return None
        x = next((q for q in p["c"] if q["end"] == p["close"] - 120), None)
        if x is None:
            return None
        mid = (x["bid"] + x["ask"]) / 2
        lead = "yes" if mid >= 0.8 else ("no" if mid <= 0.2 else None)
        return None if lead is None else (lead == p["res"])
    add("PRIOR_REVERSED", need_fav(lambda ctx, m, c, e, f: prior_state(ctx, m) is False))
    add("PRIOR_CLEAN", need_fav(lambda ctx, m, c, e, f: prior_state(ctx, m) is True))
    # J. stale quotes (2), K. spread history (2), M. volume tilt (2)
    def stale(e, c):
        v = (e + [c])[-5:]
        return sum(1 for a, b in zip(v, v[1:]) if a["bid"] == b["bid"] and a["ask"] == b["ask"])
    add("STALE_GE2", need_fav(lambda ctx, m, c, e, f: len(e) >= 4 and stale(e, c) >= 2))
    add("STALE_0", need_fav(lambda ctx, m, c, e, f: len(e) >= 4 and stale(e, c) == 0))
    add("SPREAD_AT_MIN", need_fav(lambda ctx, m, c, e, f: len(e) >= 4 and c["ask"] - c["bid"] <= min(x["ask"] - x["bid"] for x in e) + 1e-9))
    add("SPREAD_AT_MAX", need_fav(lambda ctx, m, c, e, f: len(e) >= 4 and c["ask"] - c["bid"] >= max(x["ask"] - x["bid"] for x in e) - 1e-9 and c["ask"] - c["bid"] > 0.01))
    def vt(e, c):
        v = [x["vol"] for x in e]
        return None if len(v) < 4 or sum(v[:2]) == 0 else (sum(v[-2:]) / 2) / (sum(v[:2]) / 2)
    add("VOLTILT_UP", need_fav(lambda ctx, m, c, e, f: (r := vt(e, c)) is not None and r >= 1.5))
    add("VOLTILT_DOWN", need_fav(lambda ctx, m, c, e, f: (r := vt(e, c)) is not None and r <= 0.67))
    # N. position in the hour (3), side (2), last-minute move (2), dip (2), avoid-lists (3), time above 0.8 (2)
    for mi in (15, 45):
        add(f"MIN_{mi}", need_fav(lambda ctx, m, c, e, f, mi=mi: utc(m).minute == mi))
    add("MIN_00_OR_30", need_fav(lambda ctx, m, c, e, f: utc(m).minute in (0, 30)))
    add("SIDE_YES", need_fav(lambda ctx, m, c, e, f: f[0] == "yes"))
    add("SIDE_NO", need_fav(lambda ctx, m, c, e, f: f[0] == "no"))
    add("D1_UP2", need_fav(lambda ctx, m, c, e, f: bool(e) and side_mid(c, f[0]) - side_mid(e[-1], f[0]) >= 0.02))
    add("D1_DOWN2", need_fav(lambda ctx, m, c, e, f: bool(e) and side_mid(c, f[0]) - side_mid(e[-1], f[0]) <= -0.02))
    add("DIP_LT50", need_fav(lambda ctx, m, c, e, f: bool(e) and min(path(m, c, e, f[0])) < 0.50))
    add("DIP_GE70", need_fav(lambda ctx, m, c, e, f: bool(e) and min(path(m, c, e, f[0])) >= 0.70))
    add("NOT_00_06", need_fav(lambda ctx, m, c, e, f: utc(m).hour >= 6))
    add("NOT_WEEKEND", need_fav(lambda ctx, m, c, e, f: utc(m).weekday() < 5))
    add("NOT_US_OPEN", need_fav(lambda ctx, m, c, e, f: not (13.25 <= utc(m).hour + utc(m).minute / 60 < 15.0)))
    add("ABOVE80_MAJORITY", need_fav(lambda ctx, m, c, e, f: len(e) >= 4 and sum(1 for v in path(m, c, e, f[0]) if v >= 0.80) / len(path(m, c, e, f[0])) >= 0.5))
    add("ABOVE80_MINORITY", need_fav(lambda ctx, m, c, e, f: len(e) >= 4 and sum(1 for v in path(m, c, e, f[0]) if v >= 0.80) / len(path(m, c, e, f[0])) < 0.5))
    # side x session (8) and side x weekend (2)
    for side in ("yes", "no"):
        for lo, hi in ((0, 6), (6, 12), (12, 18), (18, 24)):
            add(f"{side.upper()}_{lo:02d}_{hi:02d}", need_fav(lambda ctx, m, c, e, f, side=side, lo=lo, hi=hi: f[0] == side and lo <= utc(m).hour < hi))
        add(f"{side.upper()}_WEEKEND", need_fav(lambda ctx, m, c, e, f, side=side: f[0] == side and utc(m).weekday() >= 5))
    return R


def rule_fn(name, fn, lo=None, hi=None):
    return fn


def price_quartile_rules():
    """The four PRICE_Qxx rules: the favourite's ask in a quarter of the entry band (the band is entry specific, so the cut is made at run time)."""
    out = []
    for i in range(4):
        def rule(ctx, m, c, e, band, left, i=i):
            f = L.favorite(c["bid"], c["ask"], band)
            if not f:
                return None
            lo, hi = band[0] + (band[1] - band[0]) * i / 4, band[0] + (band[1] - band[0]) * (i + 1) / 4
            return f if lo <= f[1] < hi + (1e-9 if i == 3 else 0) else None
        out.append((f"PRICE_Q{i}", rule))
    return out


def all_rules():
    return build_rules() + price_quartile_rules()


def rows_for(mks, name, fn, left, band, cut, cuts):
    by_close = {coin: {m["close"]: m for m in mk.values()} for coin, mk in mks.items()}
    out = []
    for coin, mk in mks.items():
        ctx = Ctx(by_close, coin)
        ctx.cuts = cuts
        base = I.entries(mk, left, lambda m, c, e, ps: L.favorite(c["bid"], c["ask"], band))
        b = {}
        for part in (True, False):
            sel = [r for r in base if (r["day"] < cut) == part]
            b[part] = (st.mean(r["net"] for r in sel), st.mean(r["stress"] for r in sel)) if sel else (0.0, 0.0)
        for r in I.entries(mk, left, lambda m, c, e, ps: fn(ctx, m, c, e, band, left)):
            adj = b[r["day"] < cut]
            out.append({**r, "raw": r["net"], "net": r["net"] - adj[0], "stress": r["stress"] - adj[1], "series": coin})
    return out


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mks = {c: I.load_btc(c) for c in COINS}
    cut = I.cut_day({tk: m for mk in mks.values() for tk, m in mk.items()})
    rules = all_rules()
    out = [f"IDEAS100: {len(rules)} rules x {len(ENTRIES)} entries, Bitcoin {len(mks['KXBTC15M'])} and Ethereum {len(mks['KXETH15M'])} markets, discovery before {cut}"]
    for ename, (left, band) in ENTRIES.items():
        cuts = compute_cuts(mks, left, band)
        for name, fn in rules:
            rows = rows_for(mks, name, fn, left, band, cut, cuts)
            j = I.judge(rows, cut, [{**r, "net": r["raw"]} for r in rows], MIN_DISC, MIN_CONF, DISC_Z)
            pos = sum(1 for s in COINS if (v := [x["net"] for x in rows if x["series"] == s]) and st.mean(v) > 0)
            if j["verdict"] == "NOT_YET_FALSIFIED" and pos < 2:
                j["verdict"] = "NOT_ENOUGH_DATA"
            out.append(f"{ename:5s} {name:22s} {j['verdict']:18s} disc n={j['nd']:5d} {100 * j['dm']:+6.2f}c z {j['dz']:+5.2f} | conf n={j['nc']:5d} {100 * j['cm']:+6.2f}c z {j['cz']:+5.2f} | all {100 * j['am']:+6.2f}c z {j['az']:+5.2f} PF {j['pf']:.2f} coins+ {pos}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out[:1]), "\n", sum(1 for x in out if "NOT_YET_FALSIFIED" in x), "NOT_YET_FALSIFIED;", sum(1 for x in out if " FALSIFIED " in x), "FALSIFIED;", sum(1 for x in out if "NOT_ENOUGH_DATA" in x), "NOT_ENOUGH_DATA")


if __name__ == "__main__":
    main(sys.argv)
