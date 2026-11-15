#!/usr/bin/env python3
"""EXITS3 (History Miner, Nov 15, 2026): three fixed exits (T, S, M) beside hold on each card's own entries.
Spec EXITS3_SPEC_NOV15.md (140aa224); hand case EXITS3_HAND_CASE_NOV15.md. Reads Forensics' cut extracts (sqlite, tables market and candle) only.

Usage (python3 -I, from outside the data folder):
  python3 -I exits3.py <card> <extract.sqlite> <out.json>      card: OIREL | OICORE | XRPFAV6 | XRPFAV10
Prints and writes, per variant and haircut, n, PF, halves, mean, z and exits by reason. Upper bound, not fill-checked."""
import json, math, os, sqlite3, statistics, sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

C = 10                      # contracts per order (the cards' own size)
HS = (0.0, 0.01, 0.02)
VARIANTS = ("hold", "T", "S", "M")
EPS = 1e-9


def fee(p, c=C):
    return math.ceil(round(100 * 0.07 * c * p * (1 - p), 9)) / 100


def side_ask(q, side):
    b, a = q[0], q[1]
    if side == "yes":
        return a
    return None if b is None else round(1 - b, 6)


def side_bid(q, side):
    b, a = q[0], q[1]
    if side == "yes":
        return b
    return None if a is None else round(1 - a, 6)


def two_sided(q):
    """C1 (rule 18): 0 < yes_bid < yes_ask < 1."""
    return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1


def sellable(q, side):
    v = side_bid(q, side)
    return v is not None and 0 < v < 1


def exit_mark(cands, entry_end, close, side, e, variant):
    """(sale mark end, raw bid) or (None, reason). cands: {end: (bid, ask, vol, oi)}; marks after the entry candle, at or before close - 60."""
    marks = sorted(k for k in cands if entry_end < k <= close - 60)
    if variant == "hold":
        return None, "held"
    trig = None
    for k in marks:
        b = side_bid(cands[k], side)
        if variant == "T" and b is not None and b >= min(2 * e, 0.90) - EPS:
            trig = k; break
        if variant == "S" and b is not None and b <= e / 2 + EPS:
            trig = k; break
        if variant == "M" and k == close - 180:
            trig = k; break
    if trig is None:
        return None, ("M n/a, held" if variant == "M" and not (entry_end < close - 180) else "held")
    for k in marks:
        if k >= trig and sellable(cands[k], side):
            return k, side_bid(cands[k], side)
    return None, "triggered, not sold"


def net(e, h, sale, result, side, c=C):
    """Per contract. sale None = held to settlement. c = the card's contracts per order (fee rounded per order)."""
    ent = min(0.99, e + h)
    fin = fee(ent, c) / c
    if sale is not None:
        s = max(0.01, sale - h)
        return s - ent - fin - fee(s, c) / c
    if result not in ("yes", "no"):
        return -fin                                     # void: price refunded, fee kept
    return (1.0 if result == side else 0.0) - ent - fin


def pf(xs):
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 else (g / l)


def dayz(days, xs):
    d = defaultdict(float)
    for k, x in zip(days, xs):
        d[k] += x
    v = list(d.values())
    if len(v) < 3:
        return None
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else None


def summary(trades):
    """trades sorted by close; each has 'net' and 'day'."""
    xs = [t["net"] for t in trades]; n = len(xs); h = n // 2
    return {"n": n, "pf": pf(xs) if n else None, "pf_half1": pf(xs[:h]) if h else None, "pf_half2": pf(xs[h:]) if n - h else None,
            "mean_c": 100 * statistics.mean(xs) if n else None, "z_day": dayz([t["day"] for t in trades], xs)}


# ---- entry rules (the cards' own, from the code that printed their figures)
OICORE_THRESH = 86299.56000000001
OIREL_RTHR = 0.26764675317954373


def oi_entry(card, cands, close):
    s, p = cands.get(close - 180), cands.get(close - 360)
    if s is None or p is None or s[3] is None or p[3] is None:
        return None
    doi = s[3] - p[3]
    if card == "OICORE":
        if not doi > OICORE_THRESH:
            return None
    else:
        if not p[3] or p[3] <= 0 or not s[3]:
            return None
        if not doi / p[3] > OIREL_RTHR:
            return None
    if not two_sided(s):
        return "not two-sided"                          # C1 on the signal (decision) candle
    side = next((sd for sd in ("yes", "no") if 0.05 <= side_ask(s, sd) <= 0.50), None)
    if side is None:
        return None
    f = cands.get(close - 120)
    if f is None:
        return None
    if not two_sided(f):
        return "not two-sided"                          # C1 on the fill candle, whose ask is the entry price
    fill = side_ask(f, side)
    if fill is None or not 0 < fill < 1:
        return None
    return {"side": side, "e": float(fill), "entry_end": close - 120}


XRPFAV = {"XRPFAV6": (330, 400, 0.02), "XRPFAV10": (570, 640, None)}    # regime_b2.py: left window, max spread


def fav_entry(card, cands, close):
    """XRPFAV6/10 (research branch src/scalper/regime_b2.py): the LAST candle with left in [lo, hi]; two-sided; spread cap (XRPFAV6);
    favourite = YES if ask >= 1 - bid else NO, at that side's ask, kept if 0.88 to 0.92 inclusive."""
    lo, hi, msp = XRPFAV[card]
    pick = None
    for k in sorted(cands):
        if lo <= close - k <= hi:
            pick = k
    if pick is None:
        return None
    q = cands[pick]
    if not two_sided(q):
        return "not two-sided"
    b, a = q[0], q[1]
    if msp is not None and a - b > msp:
        return None
    side, p = ("yes", a) if a >= 1 - b else ("no", round(1 - b, 6))
    if not (0.88 <= p <= 0.92):
        return None
    return {"side": side, "e": float(p), "entry_end": pick}


ENTRY = {"OICORE": lambda cands, close: oi_entry("OICORE", cands, close), "OIREL": lambda cands, close: oi_entry("OIREL", cands, close),
         "XRPFAV6": lambda cands, close: fav_entry("XRPFAV6", cands, close), "XRPFAV10": lambda cands, close: fav_entry("XRPFAV10", cands, close)}
SERIES = {"OICORE": "KXBTC15M", "OIREL": "KXBTC15M", "XRPFAV6": "KXXRP15M", "XRPFAV10": "KXXRP15M"}
CONTRACTS = {"OICORE": 10, "OIREL": 10, "XRPFAV6": 1, "XRPFAV10": 1}
# primary haircut per variant: OIREL and OICORE enter and exit in the last 2 minutes (C8); XRPFAV: hold and M 1c, T and S 2c (exit can fall in the last 2 minutes)
PRIMARY_H = {"OICORE": {"hold": 0.02, "T": 0.02, "S": 0.02, "M": 0.02}, "OIREL": {"hold": 0.02, "T": 0.02, "S": 0.02, "M": 0.02},
             "XRPFAV6": {"hold": 0.01, "T": 0.02, "S": 0.02, "M": 0.01}, "XRPFAV10": {"hold": 0.01, "T": 0.02, "S": 0.02, "M": 0.01}}


def load(db, series):
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    mk = {t: (close, res) for t, close, res in con.execute("select ticker, close_ts, result from market where series=?", (series,))}
    cd = defaultdict(dict)
    for t, e, b, a, v, oi in con.execute("select ticker, end_ts, bid_c, ask_c, volume, oi from candle"):
        if t in mk and e <= mk[t][0]:                  # README: drop candles after the close
            cd[t][e] = (b, a, v, oi)
    return mk, cd


def run_card(card, mk, cd):
    rows, skipped = [], 0
    for t in sorted(mk, key=lambda x: (mk[x][0], x)):
        close, res = mk[t]
        en = ENTRY[card](cd.get(t, {}), close)
        if en == "not two-sided":
            skipped += 1
        elif en:
            rows.append((t, close, res, en))
    out = {"card": card, "entries": len(rows), "not_two_sided": skipped, "primary_h": PRIMARY_H[card], "contracts": CONTRACTS[card],
           "label": "upper bound, not fill-checked; per-order rounded fee at %d contract(s)" % CONTRACTS[card], "variants": {}}
    for v in VARIANTS:
        reasons = defaultdict(int)
        exits = []
        for t, close, res, en in rows:
            k, x = exit_mark(cd.get(t, {}), en["entry_end"], close, en["side"], en["e"], v)
            reasons[x if k is None else v] += 1
            exits.append(None if k is None else x)
        out["variants"][v] = {"exits_by_reason": dict(reasons)}
        for h in HS:
            tr = [{"net": net(en["e"], h, ex, res, en["side"], CONTRACTS[card]), "day": datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d")}
                  for (t, close, res, en), ex in zip(rows, exits)]
            out["variants"][v]["h%d" % round(h * 100)] = summary(tr)
    out["voids"] = sum(1 for r in rows if r[2] not in ("yes", "no"))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 3 or a[0] not in ENTRY:
        print(__doc__); sys.exit(2)
    hm_guard.refuse_all(a[1:])
    mk, cd = load(a[1], SERIES[a[0]])
    res = run_card(a[0], mk, cd)
    json.dump(res, open(a[2], "w"), indent=1, sort_keys=True)
    print(json.dumps(res, sort_keys=True)[:3000])
