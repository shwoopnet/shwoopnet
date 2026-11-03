"""COUNT1B: which counting definition reproduces Kalshi's winning Truth Social bracket. Measurement only."""
from __future__ import annotations
import json, re, bisect
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from . import count1
ET = ZoneInfo("America/New_York")
CUT = datetime(2026, 10, 20, tzinfo=timezone.utc)
URL = re.compile(r"https?://\S+")

def load():
    d = json.loads((count1.CACHE / "truth.json").read_text())
    out = []
    for x in d:
        t = (x.get("content") or "").strip()
        out.append((datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")), t,
                    not t, t.startswith("RT"), bool(URL.fullmatch(t))))
    out.sort(key=lambda r: r[0]); return out

DEFS = {  # name: (exclude_empty, exclude_rt, exclude_url, utc)
 "D1": (0,0,0,0), "D2": (1,0,0,0), "D3": (0,1,0,0), "D4": (1,1,0,0),
 "D5": (1,0,1,0), "D6": (0,1,1,0), "D7": (0,0,0,1), "D8": (1,1,0,1)}

def count(posts, d, s, e):
    ex_e, ex_r, ex_u, utc = DEFS[d]
    if utc:  # same calendar dates at 00:00 UTC
        s = datetime(*s.astimezone(ET).timetuple()[:3], tzinfo=timezone.utc)
        e = datetime(*(e.astimezone(ET) - timedelta(seconds=1)).timetuple()[:3], tzinfo=timezone.utc) + timedelta(days=1)
    n = 0
    for ts, t, emp, rt, url in posts:
        if ts < s: continue
        if ts >= e: break
        if (ex_e and emp) or (ex_r and rt) or (ex_u and url): continue
        n += 1
    return n

def inb(m, c):
    t = m["strike_type"]; lo = m.get("floor_strike"); hi = m.get("cap_strike")
    if t == "between": return lo <= c <= hi
    if t == "less": return c < hi
    if t == "greater": return c > lo
    if t == "greater_or_equal": return c >= lo
    return False

def main():
    allm = json.loads((count1.CACHE / "count_all.json").read_text()); posts = load()
    ev = []
    for series in ("KXTRUTHSOCIAL", "KXTRUTHSOCIALD"):
        g = {}
        for m in allm[series]: g.setdefault(m["event_ticker"], []).append(m)
        for e, L in g.items():
            per = count1.parse_period(L[0]); w = [m for m in L if m["result"] == "yes"]
            if not per or len(w) != 1 or per[0] >= CUT: continue
            ev.append((per[0], series, e, per, w[0]))
    ev.sort(key=lambda x: x[0]); h = len(ev) // 2
    halves = {"SEL": ev[:h], "CONF": ev[h:]}
    res = {}
    for d in DEFS:
        for hn, E in halves.items():
            ok = [(s, inb(w, count(posts, d, p[0], p[1]))) for _, s, e, p, w in E]
            res[(d, hn)] = ok
    print("events", len(ev), {k: len(v) for k, v in halves.items()},
          "weekly", sum(1 for x in ev if x[1]=="KXTRUTHSOCIAL"), "daily", sum(1 for x in ev if x[1]=="KXTRUTHSOCIALD"))
    print("open-ended winners", sum(1 for x in ev if x[4]["strike_type"] != "between"))
    for d in DEFS:
        row = []
        for hn in ("SEL", "CONF"):
            ok = res[(d, hn)]; row.append(f"{hn} {sum(o for _, o in ok)}/{len(ok)}={sum(o for _, o in ok)/len(ok):.3f}")
            for s in ("KXTRUTHSOCIAL", "KXTRUTHSOCIALD"):
                z = [o for ss, o in ok if ss == s]; row.append(f"{s[-2:]}:{sum(z)}/{len(z)}")
        print(d, " | ".join(row))
    best = max(DEFS, key=lambda d: (sum(o for _, o in res[(d, "SEL")]) / len(res[(d, "SEL")]), -int(d[1:])))
    c = res[(best, "CONF")]
    print("CHOSEN", best, "CONF rate", sum(o for _, o in c) / len(c), "n", len(c))
main()
