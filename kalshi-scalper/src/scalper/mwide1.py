"""MWIDE1: passive bids on wide-spread daily/weekly/monthly markets (research only, no orders).

census:  python3 -I src/scalper/mwide1.py census      (quotes only, no outcome, no tape)
fetch:   python3 -I src/scalper/mwide1.py fetch       (tape for triggered markets only; run after registration is pushed)
score:   python3 -I src/scalper/mwide1.py score       (refuses a second run)
Registration: workers/MWIDE1_REGISTRATION.md
"""
from __future__ import annotations
import collections, datetime, json, math, os, sqlite3, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CUT = 1791043200  # 2026-10-03T16:00Z, frozen third starts here: never fetch
DB = "data/newlist1.sqlite"
MIN_SPREAD, LO, HI = 0.04, 0.03, 0.30
LIFE_MIN_S, MARGIN_S = 12 * 3600, 2 * 3600
TAPE = "data/mwide1_tape.json"
OUT = "data/mwide1_result.txt"


def load():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    mk = {t: (s, cat, o, cl) for t, s, e, cat, cr, o, cl in c.execute("select * from mk")}
    cd = collections.defaultdict(list)
    for t, e, b, a, v in c.execute("select ticker,end_ts,bid,ask,vol from cd order by ticker,end_ts"):
        cd[t].append((e, b, a, v))
    return c, mk, cd


def trigger(t, mk, cd):
    """First priced hourly candle with spread >= 4c whose cheap side bid is 3c..30c.
    Returns (post_ts, side, bid_price, spread) or None. Quotes only, no outcome."""
    s, cat, o, cl = mk[t]
    if cl >= CUT or cat == "Sports" or cl - o < LIFE_MIN_S:
        return None
    for e, b, a, v in cd[t]:
        if e < o + MARGIN_S or e > cl - MARGIN_S:
            continue
        if not (b >= 0.01 and a <= 0.99 and a > b) or a - b < MIN_SPREAD - 1e-9:
            continue
        yb, nb = round(b, 4), round(1 - a, 4)
        ok_y, ok_n = LO <= yb <= HI, LO <= nb <= HI
        if ok_y and ok_n:
            return (e, "Y" if yb <= nb else "N", min(yb, nb), round(a - b, 4))
        if ok_y:
            return (e, "Y", yb, round(a - b, 4))
        if ok_n:
            return (e, "N", nb, round(a - b, 4))
    return None


def triggers():
    c, mk, cd = load()
    out = {}
    for t in cd:
        r = trigger(t, mk, cd)
        if r:
            out[t] = r + (mk[t][0], mk[t][3])
    return c, mk, out


def fee10(p):
    return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 100 / 10  # per contract, order of 10


def census():
    c, mk, tr = triggers()
    cls = sorted(v[5] for v in tr.values())
    mid = cls[len(cls) // 2]
    print("orders", len(tr), "median close", mid, datetime.datetime.utcfromtimestamp(mid).isoformat())
    print("by side", collections.Counter(v[1] for v in tr.values()))
    print("families", len({v[4] for v in tr.values()}))
    return mid


if __name__ == "__main__":
    {"census": census}[sys.argv[1]]()
