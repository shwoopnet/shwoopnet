"""ESPORTM1 (workers/ESPORTM1_REGISTRATION.md): the CHEAP side (ask 3c to 30c) of Kalshi esports MATCH-winner markets (KXLOLGAME, KXCS2GAME,
KXVALORANTGAME) against a walk-forward Elo built only from Kalshi's own settled matches. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED,
NOT_ENOUGH_DATA. Nothing here means trade; no promote verb. Cheap side only: no favourite-side result is computed or printed anywhere in this file.

    python -m scalper.esportm1 list     (listings; results stored separately, used only by fit and run)
    python -m scalper.esportm1 fit      (K from the first two thirds by log-loss of outcomes; no price)
    python -m scalper.esportm1 fetch    (resumable, md5-ordered prefix, time boxed)
    python -m scalper.esportm1 run      (the one scored read; refused a second time)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .tennis1 import fee, net_cents, profit_factor, summary, treated   # same fee, side and trade rules as the registered sibling

ET = ZoneInfo("America/New_York")
CUT = "2026-10-03T16:00"
SCALE, INIT, MIN_PRIOR, KGRID = 400.0, 1500.0, 8, (16.0, 24.0, 32.0, 48.0)
LOOK_S = 120
BAR_PF, MIN_TRADES = 1.5, 150
SERIES = ("KXLOLGAME", "KXCS2GAME", "KXVALORANTGAME")
EV = re.compile(r"^[A-Z0-9]+-(\d{2}[A-Z]{3}\d{6})(.+)$")
D = Path(os.environ.get("ESPORTM1_DIR", "/tmp/e1m"))   # cache lives outside the repo
FIELDS = ("ticker", "event_ticker", "close_time", "yes_sub_title")


def ts(s: str) -> int:
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def cheap_side(yes_bid, yes_ask):
    """The side with ask 3c to 30c (rounded to 0.0001 so 1 - 0.70 counts as 0.30), or None. ('yes'|'no', ask); needs a two-sided quote."""
    if yes_bid is None or yes_ask is None or not (0 < yes_bid < yes_ask < 1):
        return None
    ya, na = round(yes_ask, 4), round(1 - yes_bid, 4)
    if 0.03 <= ya <= 0.30:
        return "yes", ya
    if 0.03 <= na <= 0.30:
        return "no", na
    return None


def elo_p(ra, rb):
    return 1.0 / (1.0 + 10 ** ((rb - ra) / SCALE))


class Elo:
    def __init__(self, k):
        self.k = k
        self.r = defaultdict(lambda: INIT)
        self.n = defaultdict(int)

    def ready(self, a, b):
        return self.n[a] >= MIN_PRIOR and self.n[b] >= MIN_PRIOR

    def prob(self, a, b):
        return elo_p(self.r[a], self.r[b])

    def update(self, w, l):
        pw = elo_p(self.r[w], self.r[l])
        self.r[w] += self.k * (1 - pw)
        self.r[l] -= self.k * (1 - pw)
        self.n[w] += 1
        self.n[l] += 1


def parse_start(ev: str):
    m = EV.match(ev)
    if not m:
        return None
    try:
        dt = datetime.strptime(m.group(1), "%y%b%d%H%M")
    except ValueError:
        return None
    return int(dt.replace(tzinfo=ET).timestamp())


def group(markets):
    """event -> dict(series, first, names{ticker: team}, close (earliest close_time unix), start). Two-market events with a parsed start only."""
    by = defaultdict(dict)
    for tk, m in markets.items():
        by[m["event_ticker"]][tk] = m
    out = {}
    for ev, mk in by.items():
        if len(mk) != 2:
            continue
        st = parse_start(ev)
        if st is None:
            continue
        first = sorted(mk)[0]
        out[ev] = dict(event=ev, series=mk[first]["series"], first=first, src=mk[first]["src"], start=st,
                       names={t: m["yes_sub_title"] for t, m in mk.items()}, close=min(ts(m["close_time"]) for m in mk.values()))
    return out


def winner_of(g, results):
    """(winner team, loser team) from the settled result of the event's first market, or None."""
    r = results.get(g["first"])
    if r not in ("yes", "no"):
        return None
    other = [t for t in g["names"] if t != g["first"]][0]
    w = g["first"] if r == "yes" else other
    l = other if r == "yes" else g["first"]
    return g["names"][w], g["names"][l]


def qualified(groups, k=None):
    """Events whose both teams have >= MIN_PRIOR earlier settled matches (close time at or before the look = start - LOOK_S) in the same series.
    Returns {event: dict(p={ticker: P(team wins)})} when k is given (needs results via groups[ev]['res']); counts only when k is None."""
    evs = sorted(groups.values(), key=lambda g: g["close"])
    looks = sorted(groups.values(), key=lambda g: g["start"] - LOOK_S)
    elos = {s: Elo(k or 24.0) for s in SERIES}
    cnt = {s: defaultdict(int) for s in SERIES}
    i, out = 0, {}
    for g in looks:
        T = g["start"] - LOOK_S
        while i < len(evs) and evs[i]["close"] <= T:
            e = evs[i]
            w = e.get("res")
            if w:
                elos[e["series"]].update(*w)
            else:
                for nm in e["names"].values():
                    cnt[e["series"]][nm] += 1
            i += 1
        a, b = [g["names"][t] for t in sorted(g["names"])]
        el = elos[g["series"]]
        ok = el.ready(a, b) if k else (cnt[g["series"]][a] >= MIN_PRIOR and cnt[g["series"]][b] >= MIN_PRIOR)
        if ok and g["start"] < ts(CUT + ":00Z"):
            out[g["event"]] = dict(g) | {"p": {t: el.prob(g["names"][t], [n for q, n in g["names"].items() if q != t][0]) for t in g["names"]}} if k else dict(g)
    return out


def fit_k(groups, results):
    """Pick K from KGRID by log-loss of the walk-forward Elo on the qualified matches of the first two thirds (by close time)."""
    for g in groups.values():
        g["res"] = winner_of(g, results)
    gs = {e: g for e, g in groups.items() if g["res"]}
    q = sorted(qualified({e: dict(g, res=None) for e, g in gs.items()}).values(), key=lambda g: g["close"])
    cutoff = q[2 * len(q) // 3 - 1]["close"]
    best = None
    qset = {x["event"] for x in q}
    for k in KGRID:
        elos = {s: Elo(k) for s in SERIES}
        ll, n = 0.0, 0
        for g in sorted(gs.values(), key=lambda g: g["close"]):
            w, l = g["res"]
            el = elos[g["series"]]
            if g["event"] in qset and g["close"] <= cutoff and el.ready(w, l):
                p = min(max(el.prob(w, l), 1e-6), 1 - 1e-6)
                ll += -math.log(p)
                n += 1
            el.update(w, l)
        print(f"K {k}: log-loss {ll / n:.5f} on {n}")
        if best is None or ll / n < best[1]:
            best = (k, ll / n, n)
    return best


def md5_key(ev):
    return hashlib.md5(ev.encode()).hexdigest()


def list_markets(with_result):
    from . import api
    out = {}
    for s in SERIES:
        for path, live in (("/historical/markets", False), ("/markets", True)):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000}
                if live:
                    p["status"] = "settled"
                if cur:
                    p["cursor"] = cur
                d = api._get(path, p)
                for m in d.get("markets", []):
                    if (m.get("close_time") or "") < CUT and m.get("result") in ("yes", "no"):
                        row = {k: m.get(k) for k in FIELDS} | {"series": s, "src": "live" if live else "hist"}
                        if with_result:
                            row["result"] = m["result"]
                        out[m["ticker"]] = row
                cur = d.get("cursor")
                if not cur or not d.get("markets"):
                    break
    return out


def fetch(budget_s=2.5 * 3600):
    from . import api
    from .candlefield import quote_close
    markets = json.loads((D / "markets.json").read_text())
    q = qualified(group(markets))
    order = sorted(q, key=md5_key)
    (D / "qualified_order.json").write_text(json.dumps(order))
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    t0 = time.time()
    print(len(order), "qualified events; time box", budget_s, flush=True)
    for i, ev in enumerate(order):
        if time.time() - t0 > float(os.environ.get("E1M_BUDGET_S", budget_s)):
            print("time box reached", len(have), flush=True)
            break
        if ev in have:
            continue
        g = q[ev]
        path = f"/historical/markets/{g['first']}/candlesticks" if g["src"] == "hist" else f"/series/{g['series']}/markets/{g['first']}/candlesticks"
        try:
            d = api._get(path, {"start_ts": g["start"] - 6 * 3600, "end_ts": g["start"], "period_interval": 1})
            have[ev] = [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
        except Exception as e:
            print("skip", ev, e, flush=True)
        time.sleep(3.3)
        if len(have) % 25 == 0:
            cp.write_text(json.dumps(have))
            print(len(have), "of", len(order), f"{(time.time() - t0) / 60:.0f} min", flush=True)
    cp.write_text(json.dumps(have))
    print("done", len(have), flush=True)


def look(candles, start):
    """Last candle ending at or before start - LOOK_S with a valid two-sided quote: (yes_bid, yes_ask) or None."""
    best = None
    for end, b, a in candles:
        if end <= start - LOOK_S and b is not None and a is not None and 0 < b < a < 1 and (best is None or end > best[0]):
            best = (end, b, a)
    return (best[1], best[2]) if best else None


def build_rows(uni, candles, results):
    """Cheap-side rows (event, net_cents, won, ask, start, p_side, treated, close). results ticker->'yes'|'no' or None."""
    rows, nolook, nocheap = [], 0, 0
    for ev, u in uni.items():
        if ev not in candles:
            continue
        q = look(candles[ev], u["start"])
        if q is None:
            nolook += 1
            continue
        cs = cheap_side(*q)
        if cs is None:
            nocheap += 1
            continue
        side, ask = cs
        tk = u["first"]
        other = [t for t in u["p"] if t != tk][0]
        p_side = u["p"][tk] if side == "yes" else u["p"][other]
        if results is None:
            rows.append((ev, None, None, ask, u["start"], p_side, treated(p_side, ask), u["close"]))
            continue
        won = (results[tk] == "yes") if side == "yes" else (results[tk] == "no")
        rows.append((ev, net_cents(ask, won), won, ask, u["start"], p_side, treated(p_side, ask), u["close"]))
    return rows, nolook, nocheap


def verdict(trows, midpoint, test_mean):
    """FALSIFIED unless mean net > 0 in BOTH halves (split by start at midpoint) and in the test third, and PF >= 1.5; NOT_ENOUGH_DATA under 150."""
    if len(trows) < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    h1 = [r[1] for r in trows if r[4] < midpoint]
    h2 = [r[1] for r in trows if r[4] >= midpoint]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    pf = profit_factor([r[1] for r in trows])
    return "NOT_YET_FALSIFIED" if (m1 > 0 and m2 > 0 and pf >= BAR_PF and test_mean is not None and test_mean > 0) else "FALSIFIED"


def run():
    from .calibration import cluster_mean_z
    res_path = D / "esportm1_result.txt"
    if res_path.exists():
        print("refused: already run")
        return
    k = float((D / "k.txt").read_text())
    ms = list_markets(True)
    results = {t: m["result"] for t, m in ms.items()}
    groups = group(ms)
    for g in groups.values():
        g["res"] = winner_of(g, results)
    q = qualified(groups, k)
    candles = json.loads((D / "candles.json").read_text())
    q = {e: u for e, u in q.items() if u["first"] in results}
    rows, nolook, nocheap = build_rows(q, candles, results)
    tr = [r for r in rows if r[6]]
    L = [f"K {k}; qualified events {len(q)} (fetched {len(candles)}), no look {nolook}, no cheap side {nocheap}, cheap-side rows {len(rows)}, treated {len(tr)}"]
    by_day = lambda r: (datetime.fromtimestamp(r[4], ZoneInfo("America/Chicago"))).strftime("%Y-%m-%d")
    for tag, rs in (("treated", tr), ("control", rows)):
        s = summary([(r[0], r[1], r[2], r[3]) for r in rs])
        if s["n"]:
            m, se, z = cluster_mean_z([(r[0], r[1]) for r in rs])
            md, sd, zd = cluster_mean_z([(by_day(r), r[1]) for r in rs])
            L.append(f"{tag}: n {s['n']} mean {s['mean']:+.2f}c win {s['win']:.3f} vs mean ask {s['ask']:.3f} PF {s['pf']:.2f} z(match) {z:+.2f} z(day) {zd:+.2f}")
            L.append(f"  fees x1.2 PF {profit_factor([r[1] - 0.2 * fee(r[3]) / 10 * 100 for r in rs]):.2f}")
    # test third: last third of qualified matches by close time
    closes = sorted(u["close"] for u in q.values())
    cut3 = closes[2 * len(closes) // 3]
    tt = [r for r in tr if r[7] > cut3]
    test_mean = sum(r[1] for r in tt) / len(tt) if tt else None
    L.append(f"test third (close after the first two thirds): treated n {len(tt)} mean {test_mean if test_mean is None else round(test_mean, 2)}")
    if tr:
        starts = sorted(r[4] for r in tr)
        mid = starts[len(starts) // 2]
        h1 = [r[1] for r in tr if r[4] < mid]
        h2 = [r[1] for r in tr if r[4] >= mid]
        L.append(f"halves {len(h1)}/{sum(h1) / max(len(h1), 1):+.2f}c, {len(h2)}/{sum(h2) / max(len(h2), 1):+.2f}c")
        v = verdict(tr, mid, test_mean)
        m, se, z = cluster_mean_z([(r[0], r[1]) for r in tr])
        cm = sum(r[1] for r in rows) / len(rows)
        if v == "NOT_YET_FALSIFIED" and not (z >= 5.27 and m >= 2.0 and m > cm):
            v = "FALSIFIED"
        L.append("VERDICT " + v)
    else:
        L.append("VERDICT NOT_ENOUGH_DATA")
    frac = len(candles) / max(len(q), 1)
    L.append(f"fetched share of qualified {frac:.2f}; projected treated on all {len(tr) / max(frac, 1e-9):.0f}")
    res_path.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    D.mkdir(parents=True, exist_ok=True)
    if cmd == "list":
        (D / "markets.json").write_text(json.dumps(list_markets(False)))
        (D / "results.json").write_text(json.dumps({t: m["result"] for t, m in list_markets(True).items()}))
    elif cmd == "fit":
        ms = json.loads((D / "markets.json").read_text())
        res = json.loads((D / "results.json").read_text())
        k, ll, n = fit_k(group(ms), res)
        (D / "k.txt").write_text(str(k))
        print("K", k, ll, n)
    elif cmd == "fetch":
        fetch()
    elif cmd == "run":
        run()
    else:
        print(__doc__)
