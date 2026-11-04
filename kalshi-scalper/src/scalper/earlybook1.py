"""EARLYBOOK1: college basketball cheap side at EARLY looks (-3h, -1h) vs DraftKings OPEN line (tradable) and CLOSE line (diagnostic only).

Registration: workers/EARLYBOOK1_REGISTRATION.md.  Cheap side only: no favourite-side result is computed.
Reuses the BOOKNCAA1 cache (/tmp/bookncaa1).  Verbs: census (no outcomes), entries (hashes entries.json), score (needs results).
The ESPN odds payload has NO timestamp for the open line; availability at the early look is an assumption, stated in the registration.
"""
from __future__ import annotations
import hashlib, json, math, os, sys
from pathlib import Path

CACHE = Path(os.environ.get("BOOKNCAA1_CACHE", "/tmp/bookncaa1"))
OUT = Path(os.environ.get("EARLYBOOK1_OUT", "/tmp/earlybook1")); 
CUT_TS = 1790956800  # 2026-10-03T16:00:00Z; every NCAAB event here is far earlier, kept as a guard
LO, HI, RATIO, C = 0.03, 0.30, 3.0, 10
LOOKS = (3 * 3600, 1 * 3600)


def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win, ask, mult=1.0):
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def implied(ml):
    ml = float(ml)
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def devig(h, a):
    ph, pa = implied(h), implied(a)
    return ph / (ph + pa), pa / (ph + pa)


def valid(q):
    return q is not None and q[0] is not None and q[1] is not None and 0 <= q[0] < q[1] <= 1 and q[1] - q[0] <= 0.10


def look_at(candles, start, lead):
    ts = [t for t, q in candles.items() if t <= start - lead and valid(q)]
    return max(ts) if ts else None


def lines(path, kind):
    """(home_ml, away_ml) american for kind 'open' or 'close' from the first DraftKings-like item."""
    try:
        d = json.load(open(path))
    except Exception:
        return None
    for it in d.get("items", []):
        try:
            return (float(it["homeTeamOdds"][kind]["moneyLine"]["american"]), float(it["awayTeamOdds"][kind]["moneyLine"]["american"]))
        except Exception:
            continue
    return None


def pf(xs):
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))] if v else None


def build(lead_s):
    """Rows for one early look.  Side = the cached side (close-line underdog); tradable rows additionally need the OPEN-line
    underdog to be the same side, so the side is known at the look."""
    games = json.load(open(CACHE / "games.json"))
    rows = []
    for p in sorted((CACHE / "candles").glob("*.json")):
        d = json.load(open(p))
        if "candles" not in d:
            continue
        e = p.stem
        g = games.get(e)
        if not g or d["st"] >= CUT_TS:
            continue
        op = lines(CACHE / "odds" / f"{g['gid']}.json", "open")
        cl = lines(CACHE / "odds" / f"{g['gid']}.json", "close")
        if not op or not cl:
            continue
        ch = {int(t): (tuple(v) if None not in v else None) for t, v in d["candles"].items()}
        t = look_at({k: v for k, v in ch.items() if v}, d["st"], lead_s)
        if t is None:
            continue
        ask = ch[t][1]
        side = d["side"]
        qo = devig(*op)[0 if side == "H" else 1]
        qc = devig(*cl)[0 if side == "H" else 1]
        qo_other = devig(*op)[1 if side == "H" else 0]
        rows.append(dict(event=e, ticker=d["ticker"], ask=ask, q_open=qo, q_close=qc, open_same_side=qo < qo_other,
                         st=d["st"], lead=(d["st"] - t) / 60))
    return rows


def gap_report(rows, key):
    g = [r[key] - r["ask"] for r in rows if LO <= r["ask"] <= HI]
    return len(g), (pct(g, .5) * 100 if g else None), (pct(g, .9) * 100 if g else None)


def treated(rows, key="q_open"):
    return [r for r in rows if LO <= r["ask"] <= HI and r["open_same_side"] and r[key] >= RATIO * r["ask"]]


def census():
    for lead in LOOKS:
        rows = build(lead)
        cand = [r for r in rows if LO <= r["ask"] <= HI]
        print(f"look -{lead // 3600}h: events with quote {len(rows)}; cheap candidates (ask 3-30c) {len(cand)}; open-line same side {sum(r['open_same_side'] for r in cand)}")
        for k in ("q_open", "q_close"):
            n, m, p9 = gap_report(rows, k)
            print(f"  gap {k}-ask: n {n} median {m:+.2f}c p90 {p9:+.2f}c; expected treated ({k}>=3x ask) {len(treated(rows, k))}")


def score(rows, res, label):
    for r in rows:
        r["win"] = res[r["ticker"]]
    out = []
    cand = [r for r in rows if LO <= r["ask"] <= HI and r["open_same_side"]]
    x = [net(r["win"], r["ask"]) for r in cand]
    out.append(f"{label}: control (all open-side cheap candidates) n {len(cand)} win {sum(r['win'] for r in cand) / max(1, len(cand)):.3f} vs ask {sum(r['ask'] for r in cand) / max(1, len(cand)):.3f}; mean net {sum(x) / max(1, len(x)) * 100:+.2f}c PF {pf(x):.2f}")
    tr = sorted(treated(rows), key=lambda r: r["st"])
    tx = [net(r["win"], r["ask"]) for r in tr]
    out.append(f"{label}: treated n {len(tr)}")
    if tr:
        h = len(tr) // 2
        out.append(f"  win {sum(r['win'] for r in tr) / len(tr):.3f} vs ask {sum(r['ask'] for r in tr) / len(tr):.3f} vs q_open {sum(r['q_open'] for r in tr) / len(tr):.3f}; mean net {sum(tx) / len(tx) * 100:+.2f}c PF {pf(tx):.2f}; fees x1.2 {sum(net(r['win'], r['ask'], 1.2) for r in tr) / len(tr) * 100:+.2f}c")
        out.append(f"  D1 {sum(tx[:h]) / max(1, h) * 100:+.2f}c (n {h}); D2 {sum(tx[h:]) / max(1, len(tx) - h) * 100:+.2f}c (n {len(tx) - h})")
    if len(tr) < 150:
        out.append("NOT_ENOUGH_DATA: under 150 treated")
    else:
        fal = (not tx) or sum(tx[:len(tx)//2]) <= 0 or sum(tx[len(tx)//2:]) <= 0 or pf(tx) < 1.5
        out.append("FALSIFIED" if fal else "PASS_FOR_FORWARD_ONLY")
    return out


if __name__ == "__main__":
    if sys.argv[1] == "census":
        census()
