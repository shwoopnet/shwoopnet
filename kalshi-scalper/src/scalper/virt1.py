"""VIRT1 (workers/VIRT1_REGISTRATION.md): the CHEAP side (ask 3c to 30c) of Kalshi virtual-sports match winners (KXESOCCERGAME, KXEBASKETBALLGAME,
KXLIGAPROMATCH) against a walk-forward player+team rating from Kalshi's own settled results. Research only; no promote verb. Cheap side only: no
favourite-side result is computed or printed. The held-out third (start at or after HCUT) is never listed with results, fetched or rated by default.

    python -m scalper.virt1 list    (listings with NO result: markets.json)
    python -m scalper.virt1 fit     (results of development events only; K per series and dbar on D1)
    python -m scalper.virt1 fetch   (resumable, md5 order, time boxed)
    python -m scalper.virt1 run     (the one scored development read; refused a second time)
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

from .esportm1 import ET, elo_p, parse_start, ts          # same event-ticker parser (US Eastern, DST aware)
from .tennis1 import fee, net_cents, profit_factor, summary, treated   # same fee, side and trade rules as the registered siblings

HCUT = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())
DEVMID = int(datetime(2026, 10, 18, 12, tzinfo=timezone.utc).timestamp())
INIT, MIN_PRIOR, KGRID = 1500.0, 8, (16.0, 24.0, 32.0, 48.0)
LOOK_S, MAX_SPREAD = 120, 0.10
BAR_PF, MIN_TRADES = 1.5, 150
CAP_PER_SERIES, TIME_BOX_S, PACE_S = 1000, 100 * 60, 1.3
SERIES = ("KXESOCCERGAME", "KXEBASKETBALLGAME", "KXLIGAPROMATCH")
HAS_TEAM = {"KXESOCCERGAME": True, "KXEBASKETBALLGAME": True, "KXLIGAPROMATCH": False}
EXCLUDE = {"KXLIGAPROMATCH-26NOV061530KHASHI", "KXESOCCERGAME-26NOV062056DRAKZARO"}   # looked at before registering (held-out region)
D = Path(os.environ.get("VIRT1_DIR", "/tmp/virt1"))
PAREN = re.compile(r"^(.*?)\s*\(([^()]+)\)\s*$")


def split_name(s):
    """('Chelsea (Zaroth)') -> (team 'Chelsea', player 'Zaroth'); no parentheses -> (None, whole name)."""
    m = PAREN.match(s or "")
    return (m.group(1).strip(), m.group(2).strip()) if m else (None, (s or "").strip())


def group(markets):
    """event -> dict(series, start, close, mk{ticker: sub_title}, tie ticker or None, sides [(ticker, team, player)] for the two non-tie markets).
    Shapes other than 2 markets (basketball, Liga Pro) or 3 markets with exactly one TIE (soccer) are dropped (counted by caller)."""
    by = defaultdict(dict)
    for tk, m in markets.items():
        by[m["event_ticker"]][tk] = m
    out, dropped = {}, 0
    for ev, mk in by.items():
        s = next(iter(mk.values()))["series"]
        st = parse_start(ev)
        ties = [t for t, m in mk.items() if t.rsplit("-", 1)[-1] == "TIE"]
        ok = (s == "KXESOCCERGAME" and len(mk) == 3 and len(ties) == 1) or (s != "KXESOCCERGAME" and len(mk) == 2 and not ties)
        if st is None or not ok or ev in EXCLUDE:
            dropped += 1
            continue
        sides = [(t, *split_name(m["yes_sub_title"])) for t, m in sorted(mk.items()) if t not in ties]
        out[ev] = dict(event=ev, series=s, start=st, close=min(ts(m["close_time"]) for m in mk.values()),
                       tie=ties[0] if ties else None, sides=sides, tickers=sorted(mk))
    return out, dropped


class Rater:
    """Player + team ratings per series; side rating = player + team (team only when the series has one)."""
    def __init__(self, k):
        self.k = k
        self.rp = defaultdict(lambda: INIT)
        self.rt = defaultdict(lambda: INIT)
        self.n = defaultdict(int)

    def rating(self, s, team, player):
        r = self.rp[(s, player)]
        return r + (self.rt[(s, team)] - INIT if HAS_TEAM[s] and team else 0.0)

    def ready(self, s, a, b):
        return self.n[(s, a[1])] >= MIN_PRIOR and self.n[(s, b[1])] >= MIN_PRIOR

    def expect(self, s, a, b):
        return elo_p(self.rating(s, *a), self.rating(s, *b))

    def update(self, s, a, b, score_a):
        e = self.expect(s, a, b)
        d = self.k / 2 * (score_a - e)
        for side, sg in ((a, 1), (b, -1)):
            self.rp[(s, side[1])] += sg * d
            if HAS_TEAM[s] and side[0]:
                self.rt[(s, side[0])] += sg * d
            self.n[(s, side[1])] += 1


def score_a(g, results):
    """Score of the first side (sorted by ticker): 1, 0 or 0.5 (soccer draw); None if the event result is unreadable."""
    ta, tb = g["sides"][0][0], g["sides"][1][0]
    ra, rb = results.get(ta), results.get(tb)
    rt = results.get(g["tie"]) if g["tie"] else "no"
    if rt == "yes":
        return 0.5
    if ra == "yes" and rb == "no":
        return 1.0
    if rb == "yes" and ra == "no":
        return 0.0
    return None


def walk(groups, results, k):
    """Yield (event dict, E_A, ready) in order of look time (start - LOOK_S), applying every earlier-closed settled event first.
    results None: ratings never update (not used). Only events with a start before HCUT are ever passed in (caller filters)."""
    evs = sorted(groups.values(), key=lambda g: g["close"])
    looks = sorted(groups.values(), key=lambda g: g["start"] - LOOK_S)
    R, i = Rater(k), 0
    for g in looks:
        T = g["start"] - LOOK_S
        while i < len(evs) and evs[i]["close"] <= T:
            e = evs[i]
            sc = score_a(e, results) if results is not None else None
            if sc is not None:
                R.update(e["series"], e["sides"][0][1:], e["sides"][1][1:], sc)
            i += 1
        a, b = g["sides"][0][1:], g["sides"][1][1:]
        yield g, R.expect(g["series"], a, b), R.ready(g["series"], a, b)


def draw_p(e, dbar):
    return dbar * 2 * min(e, 1 - e)


def probs(g, e, dbar):
    """{ticker: P(market resolves YES)} from the expected score of the first side."""
    ta, tb = g["sides"][0][0], g["sides"][1][0]
    if g["tie"] is None:
        return {ta: e, tb: 1 - e}
    pd = draw_p(e, dbar)
    return {ta: e - pd / 2, tb: 1 - e - pd / 2, g["tie"]: pd}


def fit(groups, results):
    """Per series: K from KGRID by log-loss of outcomes on D1 ready events (3-way log-loss for soccer with dbar fitted at that K); no price."""
    d1 = {e: g for e, g in groups.items() if g["start"] < DEVMID}
    out = {}
    for s in SERIES:
        gs_all = {e: g for e, g in groups.items() if g["series"] == s}
        best = None
        for k in KGRID:
            rows = []
            for g, e, rdy in walk(gs_all, results, k):
                if rdy and g["start"] < DEVMID:
                    sc = score_a(g, results)
                    if sc is not None:
                        rows.append((g, e, sc))
            if not rows:
                continue
            dbar = 0.0
            if s == "KXESOCCERGAME":
                den = sum(2 * min(e, 1 - e) for _, e, _ in rows)
                dbar = min(max(sum(1 for *_, sc in rows if sc == 0.5) / den, 0.0), 0.95)
            ll = 0.0
            for g, e, sc in rows:
                p = probs(g, e, dbar)
                pw = p[g["tie"]] if sc == 0.5 else (p[g["sides"][0][0]] if sc == 1 else p[g["sides"][1][0]])
                ll += -math.log(min(max(pw, 1e-6), 1 - 1e-6))
            ll /= len(rows)
            print(f"{s} K {k}: log-loss {ll:.5f} n {len(rows)} dbar {dbar:.4f}", flush=True)
            if best is None or ll < best[1]:
                best = (k, ll, len(rows), dbar)
        out[s] = best
    return out


def md5_key(ev):
    return hashlib.md5(ev.encode()).hexdigest()


def list_markets():
    """Settled markets of the three series, NO result field kept."""
    from . import api
    out = {}
    for s in SERIES:
        cur = None
        while True:
            p = {"series_ticker": s, "limit": 1000, "status": "settled"}
            if cur:
                p["cursor"] = cur
            d = api._get("/markets", p)
            for m in d.get("markets", []):
                if m.get("result") in ("yes", "no"):
                    out[m["ticker"]] = {k: m.get(k) for k in ("ticker", "event_ticker", "close_time", "yes_sub_title")} | {"series": s}
            cur = d.get("cursor")
            time.sleep(PACE_S)
            if not cur or not d.get("markets"):
                break
    return out


def list_dev_results(dev_events):
    """Results of development events only (held-out results are dropped before they are stored)."""
    from . import api
    out = {}
    for s in SERIES:
        cur = None
        while True:
            p = {"series_ticker": s, "limit": 1000, "status": "settled"}
            if cur:
                p["cursor"] = cur
            d = api._get("/markets", p)
            for m in d.get("markets", []):
                if m.get("event_ticker") in dev_events and m.get("result") in ("yes", "no"):
                    out[m["ticker"]] = m["result"]
            cur = d.get("cursor")
            time.sleep(PACE_S)
            if not cur or not d.get("markets"):
                break
    return out


def ready_dev(groups):
    """Development events with both players at least MIN_PRIOR earlier settled games (counts only, by close order; no result needed)."""
    evs = sorted(groups.values(), key=lambda g: g["close"])
    looks = sorted(groups.values(), key=lambda g: g["start"] - LOOK_S)
    cnt, i, out = defaultdict(int), 0, []
    for g in looks:
        T = g["start"] - LOOK_S
        while i < len(evs) and evs[i]["close"] <= T:
            for sd in evs[i]["sides"]:
                cnt[(evs[i]["series"], sd[2])] += 1
            i += 1
        if all(cnt[(g["series"], sd[2])] >= MIN_PRIOR for sd in g["sides"]) and g["start"] < HCUT:
            out.append(g["event"])
    return out


def load_dev():
    ms = json.loads((D / "markets.json").read_text())
    groups, dropped = group(ms)
    dev = {e: g for e, g in groups.items() if g["start"] < HCUT}
    return dev, dropped


def fetch():
    from . import api
    from .candlefield import quote_close
    dev, _ = load_dev()
    rdy = set(ready_dev(dev))
    per = {s: sorted((e for e in rdy if dev[e]["series"] == s), key=md5_key)[:CAP_PER_SERIES] for s in SERIES}
    order = [e for tup in zip(*[per[s] + [None] * (CAP_PER_SERIES - len(per[s])) for s in SERIES]) for e in tup if e]
    (D / "fetch_order.json").write_text(json.dumps(order))
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    t0 = time.time()
    print({s: len(per[s]) for s in SERIES}, "ready dev events chosen;", len(order), "in order", flush=True)
    for ev in order:
        if time.time() - t0 > float(os.environ.get("V1_BUDGET_S", TIME_BOX_S)):
            print("time box reached", len(have), flush=True)
            break
        if ev in have:
            continue
        g = dev[ev]
        tks = g["tickers"] if g["tie"] else [g["sides"][0][0]]
        try:
            d = api._get("/markets/candlesticks", {"market_tickers": ",".join(tks), "start_ts": g["start"] - 3600, "end_ts": g["start"] - 60, "period_interval": 1})
            rec = {}
            for x in d.get("markets", []):
                rec[x["market_ticker"]] = [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in x.get("candlesticks", [])]
            have[ev] = rec
        except Exception as e:
            print("STOP on", ev, e, flush=True)
            break          # repeated block after api._get's own backoff: stop, never route around it
        time.sleep(PACE_S)
        if len(have) % 25 == 0:
            cp.write_text(json.dumps(have))
            print(len(have), "of", len(order), f"{(time.time() - t0) / 60:.0f} min", flush=True)
    cp.write_text(json.dumps(have))
    print("done", len(have), flush=True)


def cheap_side(yes_bid, yes_ask):
    """('yes'|'no', ask) with ask in [0.03, 0.30] (rounded to 4 places), needing 0 < bid < ask < 1 and ask - bid <= MAX_SPREAD; else None."""
    if yes_bid is None or yes_ask is None or not (0 < yes_bid < yes_ask < 1) or round(yes_ask - yes_bid, 4) > MAX_SPREAD:
        return None
    ya, na = round(yes_ask, 4), round(1 - yes_bid, 4)
    if 0.03 <= ya <= 0.30:
        return "yes", ya
    if 0.03 <= na <= 0.30:
        return "no", na
    return None


def look(candles, start):
    """Last candle ending at or before start - LOOK_S with a valid two-sided quote: (bid, ask) or None."""
    best = None
    for end, b, a in candles:
        if end <= start - LOOK_S and b is not None and a is not None and 0 < b < a < 1 and (best is None or end > best[0]):
            best = (end, b, a)
    return (best[1], best[2]) if best else None


def build_rows(dev_ev, probs_by_ev, candles, results):
    """Cheap-side rows (event, net_cents, won, ask, start, p_side, treated, ticker, side). One row per (market, cheap side) with a valid look."""
    rows, nolook, nocheap = [], 0, 0
    for ev, rec in candles.items():
        if ev not in probs_by_ev:
            continue
        g, p = dev_ev[ev], probs_by_ev[ev]
        for tk, cs in rec.items():
            q = look(cs, g["start"])
            if q is None:
                nolook += 1
                continue
            c = cheap_side(*q)
            if c is None:
                nocheap += 1
                continue
            side, ask = c
            if tk not in p or tk not in results:
                continue
            ps = p[tk] if side == "yes" else 1 - p[tk]
            won = (results[tk] == "yes") if side == "yes" else (results[tk] == "no")
            rows.append((ev, net_cents(ask, won), won, ask, g["start"], ps, treated(ps, ask), tk, side))
    return rows, nolook, nocheap


def one_per_event(rows):
    """Keep, per event, the treated row with the highest model/ask ratio."""
    best = {}
    for r in rows:
        if r[6] and (r[0] not in best or r[5] / r[3] > best[r[0]][5] / best[r[0]][3]):
            best[r[0]] = r
    return list(best.values())


def half_stats(rs):
    n = len(rs)
    return (n, sum(r[1] for r in rs) / n if n else 0.0, profit_factor([r[1] for r in rs]) if n else 0.0)


def verdict(tr):
    """FALSIFIED if PF < 1.5 in either half or mean not above 0 in both; NOT_ENOUGH_DATA under 150 treated."""
    if len(tr) < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    h = [half_stats([r for r in tr if r[4] < DEVMID]), half_stats([r for r in tr if r[4] >= DEVMID])]
    ok = all(n > 0 and m > 0 and pf >= BAR_PF for n, m, pf in h)
    return "NOT_YET_FALSIFIED" if ok else "FALSIFIED"


def run():
    from .calibration import cluster_mean_z
    res_path = D / "virt1_result.txt"
    if res_path.exists():
        print("refused: already run")
        return
    fits = json.loads((D / "fit.json").read_text())
    results = json.loads((D / "results.json").read_text())
    dev, _ = load_dev()
    candles = json.loads((D / "candles.json").read_text())
    probs_by_ev = {}
    for s in SERIES:
        k, _, _, dbar = fits[s]
        gs = {e: g for e, g in dev.items() if g["series"] == s}
        for g, e, rdy in walk(gs, results, k):
            if rdy and g["event"] in candles:
                probs_by_ev[g["event"]] = probs(g, e, dbar)
    rows, nolook, nocheap = build_rows(dev, probs_by_ev, candles, results)
    tr = one_per_event(rows)
    L = [f"fits {fits}", f"fetched events {len(candles)}, no look {nolook}, no cheap side {nocheap}, cheap-side rows {len(rows)}, treated (one per event) {len(tr)}"]
    by_day = lambda r: datetime.fromtimestamp(r[4], timezone.utc).strftime("%Y-%m-%d")
    arms = [("treated", tr), ("control", rows)]
    for tag, rs in arms:
        s = summary([(r[0], r[1], r[2], r[3]) for r in rs])
        if s["n"]:
            m, se, z = cluster_mean_z([(r[0], r[1]) for r in rs])
            md, sd, zd = cluster_mean_z([(by_day(r), r[1]) for r in rs])
            L.append(f"{tag}: n {s['n']} mean {s['mean']:+.2f}c win {s['win']:.3f} vs mean ask {s['ask']:.3f} PF {s['pf']:.2f} z(event) {z:+.2f} z(day) {zd:+.2f}")
            L.append(f"  fees x1.2 PF {profit_factor([r[1] - 0.2 * fee(r[3]) / 10 * 100 for r in rs]):.2f}")
            for nm, sub in (("D1", [r for r in rs if r[4] < DEVMID]), ("D2", [r for r in rs if r[4] >= DEVMID])):
                n, m_, pf = half_stats(sub)
                L.append(f"  {nm}: n {n} mean {m_:+.2f}c PF {pf:.2f}")
    for s in SERIES:     # descriptive only, not gates
        sub = [r for r in tr if dev[r[0]]["series"] == s]
        n, m_, pf = half_stats(sub)
        L.append(f"treated {s}: n {n} mean {m_:+.2f}c PF {pf:.2f}")
    sub = [r for r in tr if dev[r[0]]["series"] == "KXESOCCERGAME"]
    for nm, f_ in (("tie-yes", lambda r: dev[r[0]]["tie"] == r[7] and r[8] == "yes"), ("win-yes", lambda r: dev[r[0]]["tie"] != r[7] and r[8] == "yes"), ("no-side", lambda r: r[8] == "no")):
        ss = [r for r in sub if f_(r)]
        n, m_, pf = half_stats(ss)
        L.append(f"  eSoccer treated {nm}: n {n} mean {m_:+.2f}c PF {pf:.2f}")
    # Brier of the model vs the quote mid on events with a cheap-side-agnostic look (all fetched first-market quotes)
    bm, bq, nb = 0.0, 0.0, 0
    for ev, rec in candles.items():
        if ev not in probs_by_ev:
            continue
        g = dev[ev]
        tk = g["sides"][0][0]
        q = look(rec.get(tk, []), g["start"])
        if q and tk in results and (q[1] - q[0]) <= MAX_SPREAD:
            y = 1.0 if results[tk] == "yes" else 0.0
            bm += (probs_by_ev[ev][tk] - y) ** 2
            bq += ((q[0] + q[1]) / 2 - y) ** 2
            nb += 1
    L.append(f"Brier on first-market of fetched events (n {nb}): model {bm / max(nb, 1):.4f}, quote mid {bq / max(nb, 1):.4f}")
    v = verdict(tr)
    L.append("VERDICT " + v)
    ready_all = len(ready_dev(dev))
    frac = len(candles) / max(ready_all, 1)
    L.append(f"fetched share of ready dev events {frac:.2f} ({len(candles)}/{ready_all}); projected treated on all {len(tr) / max(frac, 1e-9):.0f}")
    res_path.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    D.mkdir(parents=True, exist_ok=True)
    if cmd == "list":
        (D / "markets.json").write_text(json.dumps(list_markets()))
    elif cmd == "fit":
        dev, dropped = load_dev()
        print("dev events", len(dev), "dropped shapes", dropped)
        res = list_dev_results(set(dev))
        (D / "results.json").write_text(json.dumps(res))
        f = fit(dev, res)
        (D / "fit.json").write_text(json.dumps(f))
        print(f)
    elif cmd == "fetch":
        fetch()
    elif cmd == "run":
        run()
    else:
        print(__doc__)
