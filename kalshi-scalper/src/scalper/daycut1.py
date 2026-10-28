"""DAYCUT1 (README, Pre-registration: DAYCUT1): would a daily profit target or a time cutoff have helped L1? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Usage: python -m scalper.daycut1 run (once)."""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .paths import DATA_DIR

RESULT = DATA_DIR / "daycut1_result.txt"
LIVE = "/tmp/claude-0/-home-user-shwoopnet/cbbea649-50b2-5b08-81d5-2b9a4664b7f3/scratchpad/orders_export4.csv"
CT, ET = ZoneInfo("America/Chicago"), ZoneInfo("America/New_York")
BASE, UNIT = 500.0, 11
RULES = [("target +0.5%", "t", 0.005), ("target +1%", "t", 0.01), ("target +2%", "t", 0.02), ("cutoff 12:00 CT", "h", 12), ("cutoff 16:00 CT", "h", 16), ("cutoff 20:00 CT", "h", 20)]
MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}


def close_of(tk):
    m = re.search(r"-(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)", tk)
    yy, mon, dd, hh, mi = m.groups()
    return datetime(2000 + int(yy), MON[mon], int(dd), int(hh), int(mi), tzinfo=ET).timestamp()


def live():
    out = []
    for r in csv.DictReader(open(LIVE)):
        try:
            if float(r["fillCount"] or 0) <= 0 or r["pnl"] in ("", None):
                continue
        except ValueError:
            continue
        t = datetime.fromisoformat(r["time"].replace("Z", "+00:00")).timestamp()
        out.append((t, close_of(r["ticker"]), float(r["pnl"])))
    return sorted(out)


def history():
    from . import feat1 as F
    from .flat_r import load_rep
    from .fwd_reads import load_fresh
    from .hs1 import load
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1].endswith("15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    return sorted((r["close_ts"] - 360, r["close_ts"], UNIT * r["net"]) for r in rows)


def day(ts):
    return datetime.fromtimestamp(ts, CT).strftime("%Y-%m-%d")


def apply(ent, rule):
    _, kind, v = rule
    kept, removed = [], []
    byday = defaultdict(list)
    for e in ent:
        byday[day(e[0])].append(e)
    for d, es in byday.items():
        stopped = False
        for i, (t, c, p) in enumerate(es):
            if kind == "h":
                cut = datetime.fromtimestamp(t, CT).hour >= v
            else:
                real = sum(p2 for t2, c2, p2 in es[:i] if c2 <= t)
                stopped = stopped or real >= v * BASE
                cut = stopped
            (removed if cut else kept).append((t, c, p))
    return kept, removed


def stats(ent):
    w = sum(p for *_, p in ent if p > 0); l = -sum(p for *_, p in ent if p < 0)
    bd = defaultdict(float)
    for t, _, p in ent:
        bd[day(t)] += p
    return {"pf": w / l if l else 99.0, "net": w - l, "worst": min(bd.values()) if bd else 0.0, "days": len(bd), "n": len(ent)}


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print("Refusing to run again"); return
    W = {"LIVE": live(), "HISTORY": history()}
    lines = []; res = defaultdict(dict)
    for wname, ent in W.items():
        b = stats(ent)
        lines.append(f"{wname}: {b['n']} entries over {b['days']} US Central days, {datetime.fromtimestamp(ent[0][0], CT):%Y-%m-%d} to {datetime.fromtimestamp(ent[-1][0], CT):%Y-%m-%d}; before: PF {b['pf']:.2f}, net ${b['net']:+.2f}, worst day ${b['worst']:+.2f}")
        for rule in RULES:
            k, r = apply(ent, rule); a = stats(k)
            aff = len({day(t) for t, _, _ in r})
            lw = [p for *_, p in r if p < 0]; ww = [p for *_, p in r if p > 0]
            ok = a["pf"] >= b["pf"] + 0.10 and a["net"] >= b["net"] and a["worst"] >= b["worst"]
            res[rule[0]][wname] = ok
            lines.append(f"  {rule[0]:16s} days affected {aff}, entries removed {len(r)}; losses avoided {len(lw)} (${-sum(lw):.2f}), wins given up {len(ww)} (${sum(ww):.2f}) | PF {b['pf']:.2f} -> {a['pf']:.2f}, net ${b['net']:+.2f} -> ${a['net']:+.2f}, worst day ${b['worst']:+.2f} -> ${a['worst']:+.2f} {'(better on all three)' if ok else ''}")
    live_days = stats(W["LIVE"])["days"]
    verdicts = {}
    for rule in RULES:
        h, l = res[rule[0]]["HISTORY"], res[rule[0]]["LIVE"]
        verdicts[rule[0]] = "FALSIFIED" if not h else ("NOT_ENOUGH_DATA" if live_days < 30 else ("NOT_YET_FALSIFIED" if l else "FALSIFIED"))
    lines.insert(0, "DAYCUT1 verdicts: " + "; ".join(f"{k} {v}" for k, v in verdicts.items()))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
