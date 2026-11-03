"""BOOKS1: cheap side vs DraftKings closing moneyline (de-vigged), held to settlement.

Registration: workers/BOOKS1_REGISTRATION.md (sha256 prefix c673b39a45af255f).
Reads data/espn1.sqlite and a cache of ESPN odds JSON (directory given as argv).
Cheap side only: no favourite-side result is computed.  W3 (frozen) is never read.
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "espn1.sqlite"
W2_START = int(datetime(2026, 9, 13, 1, tzinfo=timezone.utc).timestamp())
W3_START = int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp())
LO, HI, RATIO, C, LEAD = 0.03, 0.30, 3.0, 10, 120


def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win, ask, mult=1.0):
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def implied(ml):
    ml = float(ml)
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def devig(ml_home, ml_away):
    h, a = implied(ml_home), implied(ml_away)
    return h / (h + a), a / (h + a)


def valid(q):
    return q is not None and 0 <= q[0] < q[1] <= 1 and q[1] - q[0] <= 0.10


def look(ch, hch, start):
    """Last timestamp <= start-LEAD at which both tickers have a valid candle."""
    ts = [t for t in ch if t <= start - LEAD and t in hch and valid(ch[t]) and valid(hch[t])]
    return max(ts) if ts else None


def moneylines(path):
    """(home_ml, away_ml) closing, from the first provider with both; None otherwise."""
    try:
        d = json.load(open(path))
    except Exception:
        return None
    for it in d.get("items", []):
        try:
            h = it["homeTeamOdds"]["close"]["moneyLine"]["american"]
            a = it["awayTeamOdds"]["close"]["moneyLine"]["american"]
            return float(h), float(a)
        except Exception:
            continue
    return None


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def pick(qh, qa, home_q, away_q):
    """Cheap candidate from (bid,ask) pairs: lower ask in [LO,HI], ties skipped.
    Returns ('H'|'A', ask, q_book) or None."""
    ah, aa = home_q[1], away_q[1]
    if ah == aa:
        return None
    side, ask, q = ("H", ah, qh) if ah < aa else ("A", aa, qa)
    if not (LO <= ask <= HI):
        return None
    return side, ask, q


def main(cache):
    cache = Path(cache)
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    games = c.execute(
        """select m.series,e.id,e.start_ts,m.home_ticker,m.away_ticker from match m
           join egame e on e.id=m.egame and e.series=m.series where e.start_ts<?""", (W3_START,)).fetchall()
    rows, skipped = [], defaultdict(int)
    for s, gid, st, ht, at in games:
        ml = moneylines(cache / f"{gid}.json")
        if ml is None:
            skipped["no line"] += 1
            continue
        ch = {t: (b, a) for t, b, a in c.execute("select end_ts,bid,ask from candle where ticker=? and bid is not null and ask is not null", (ht,))}
        ca = {t: (b, a) for t, b, a in c.execute("select end_ts,bid,ask from candle where ticker=? and bid is not null and ask is not null", (at,))}
        t = look(ch, ca, st)
        if t is None:
            skipped["no look"] += 1
            continue
        qh, qa = devig(*ml)
        p = pick(qh, qa, ch[t], ca[t])
        if p is None:
            skipped["not cheap"] += 1
            continue
        side, ask, q = p
        tk = ht if side == "H" else at
        r = c.execute("select result from kmarket where ticker=?", (tk,)).fetchone()
        if not r or r[0] not in ("yes", "no"):
            skipped["no result"] += 1
            continue
        rows.append(dict(series=s, st=st, ask=ask, q=q, win=r[0] == "yes",
                         day=datetime.fromtimestamp(st, timezone.utc).date().isoformat(),
                         w=1 if st < W2_START else 2, lead=(st - t) / 60))
    out = [f"games with W1/W2 start {len(games)}; skipped {dict(skipped)}; cheap sides {len(rows)}"]
    gaps = sorted(r["q"] - r["ask"] for r in rows)
    if gaps:
        n = len(gaps)
        out.append(f"gap q-ask (cheap sides): median {gaps[n//2]*100:+.2f}c p90 {gaps[9*n//10]*100:+.2f}c n {n}; |gap| median {sorted(abs(g) for g in gaps)[n//2]*100:.2f}c")
        for s in sorted({r['series'] for r in rows}):
            g = sorted(r["q"] - r["ask"] for r in rows if r["series"] == s)
            out.append(f"  {s}: n {len(g)} median gap {g[len(g)//2]*100:+.2f}c p90 {g[9*len(g)//10]*100:+.2f}c")
        out.append(f"control: n {n}, win {sum(r['win'] for r in rows)/n:.3f} vs mean ask {sum(r['ask'] for r in rows)/n:.3f} vs mean q {sum(r['q'] for r in rows)/n:.3f}; mean net {sum(net(r['win'],r['ask']) for r in rows)/n*100:+.2f}c")
    tr = sorted([r for r in rows if r["q"] >= RATIO * r["ask"]], key=lambda r: r["st"])
    xs = [net(r["win"], r["ask"]) for r in tr]
    out.append(f"treated (q >= {RATIO:g} x ask): n {len(tr)} (W1 {sum(r['w']==1 for r in tr)}, W2 {sum(r['w']==2 for r in tr)})")
    if tr:
        h = len(tr) // 2
        out.append(f"  win {sum(r['win'] for r in tr)/len(tr):.3f} vs mean ask {sum(r['ask'] for r in tr)/len(tr):.3f}; mean net {sum(xs)/len(xs)*100:+.2f}c; PF {pf(xs):.2f}; fees x1.2 mean {sum(net(r['win'],r['ask'],1.2) for r in tr)/len(tr)*100:+.2f}c")
        out.append(f"  half1 mean {sum(xs[:h])/max(1,h)*100:+.2f}c (n {h}); half2 mean {sum(xs[h:])/max(1,len(xs)-h)*100:+.2f}c (n {len(xs)-h})")
    # months to go
    if len(tr) < 150:
        per_month = len(tr) / 2.0
        out.append(f"NOT_ENOUGH_DATA: {len(tr)} of 150; rate {per_month:.1f}/month over the 2 month file; "
                   + (f"about {(150-len(tr))/per_month:.0f} more months" if per_month > 0 else "no rate to extrapolate"))
    print("\n".join(out))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
