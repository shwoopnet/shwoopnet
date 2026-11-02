"""ESPORT1 (workers/ESPORT1_REGISTRATION.md): Kalshi esports map-1 winner markets against a walk-forward Elo built only from Kalshi's own settled maps.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade; no promote verb.
    python -m scalper.esport1 fetch   (resumable: market listings, then 1 minute candles of the registered universe, into data/esport1/)
    python -m scalper.esport1 run     (the one scored read; refused a second time)
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import api
from .calibration import cluster_mean_z
from .candlefield import quote_close
from .econnew1 import fee, line, pnl, stats
from .paths import DATA_DIR

from pathlib import Path

D = Path(os.environ["ESPORT1_DIR"]) if os.environ.get("ESPORT1_DIR") else DATA_DIR / "esport1"
RESULT = D / "esport1_result.txt"
UTC, ET = timezone.utc, ZoneInfo("America/New_York")
TRY_A = ("KXCS2MAP",)
TRY_B = ("KXLOLMAP", "KXDOTA2MAP", "KXVALORANTMAP")
ALL = TRY_A + TRY_B
K, SCALE, BURN, LEAD_S = 24.0, 400.0, 5, 600
GAP, MAX_SPREAD, UNIV = 0.08, 0.10, (0.10, 0.90)
BAR_PF, BAR_Z, MIN_MEAN_C, MIN_TRADES, N_RUN = 1.5, 5.27, 2.0, 150, 728708
EV = re.compile(r"^[A-Z0-9]+-(\d{2}[A-Z]{3}\d{6})(.+)-(\d+)$")
RULE = re.compile(r"scheduled for (\w+ \d+, \d{4}) at (\d+:\d+ [AP]M) E[SD]T")


def parse_event(ev):
    """(scheduled start unix seconds in US Eastern, map number) or None."""
    m = EV.match(ev)
    if not m:
        return None
    try:
        dt = datetime.strptime(m.group(1), "%y%b%d%H%M")
    except ValueError:
        return None
    return int(dt.replace(tzinfo=ET).timestamp()), int(m.group(3)), dt


def rule_start_matches(rules, dt):
    t = RULE.search(rules or "")
    if not t:
        return False
    try:
        return datetime.strptime(t.group(1) + " " + t.group(2), "%b %d, %Y %I:%M %p") == dt
    except ValueError:
        return False


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** ((rb - ra) / SCALE))


def group_events(markets):
    """{event: [market rows]} for rows of the registered series."""
    g = defaultdict(list)
    for m in markets.values():
        if m["series"] in ALL:
            g[m["event_ticker"]].append(m)
    return g


def map_results(groups):
    """Per series, a time sorted list of (result_time, winner, loser) for every settled map (any map number) with two markets, two different team names and exactly one yes."""
    out = defaultdict(list)
    for ev, ms in groups.items():
        if len(ms) != 2:
            continue
        a, b = ms
        na, nb = (a.get("yes_sub_title") or "").strip(), (b.get("yes_sub_title") or "").strip()
        if not na or not nb or na == nb or {a["result"], b["result"]} != {"yes", "no"}:
            continue
        w, l = (na, nb) if a["result"] == "yes" else (nb, na)
        out[a["series"]].append((max(ts(a["close_time"]), ts(b["close_time"])), w, l))
    for s in out:
        out[s].sort()
    return out


class Elo:
    """Walk-forward Elo: advance(t) applies only maps whose result time is at or before t."""

    def __init__(self, results):
        self.r, self.n, self.res, self.i = defaultdict(lambda: 1500.0), defaultdict(int), results, 0

    def advance(self, t):
        while self.i < len(self.res) and self.res[self.i][0] <= t:
            _, w, l = self.res[self.i]
            e = expected(self.r[w], self.r[l])
            self.r[w] += K * (1 - e)
            self.r[l] -= K * (1 - e)
            self.n[w] += 1
            self.n[l] += 1
            self.i += 1

    def fair(self, x, other):
        if self.n[x] < BURN or self.n[other] < BURN:
            return None
        return expected(self.r[x], self.r[other])


def universe(markets):
    """{ticker: row} of map-1 events past burn-in. Chosen market = the team whose name sorts first. Uses only metadata and earlier results."""
    groups = group_events(markets)
    res = map_results(groups)
    elo = {s: Elo(res[s]) for s in ALL}
    cand = []
    for ev, ms in groups.items():
        if len(ms) != 2:
            continue
        p = parse_event(ev)
        if not p or p[1] != 1:
            continue
        a, b = sorted(ms, key=lambda m: (m.get("yes_sub_title") or ""))
        if not a.get("yes_sub_title") or a["yes_sub_title"] == b.get("yes_sub_title"):
            continue
        if not rule_start_matches(a.get("rules_primary"), p[2]):
            continue
        cand.append((p[0], ev, a, b))
    cand.sort(key=lambda x: (x[0], x[1]))
    uni = {}
    for start, ev, a, b in cand:
        T = start - LEAD_S
        e = elo[a["series"]]
        e.advance(T)
        f = e.fair(a["yes_sub_title"].strip(), b["yes_sub_title"].strip())
        if f is None or not (UNIV[0] <= f <= UNIV[1]):
            continue
        uni[a["ticker"]] = {"t": a["ticker"], "event": ev, "series": a["series"], "start": start, "fair": f, "res": a["result"], "src": a["src"]}
    return uni


def quote(cs, start):
    """First valid two-sided candle ending in [T, start] (candles: end_ts, bid, ask)."""
    T = start - LEAD_S
    for c in sorted(cs):
        if T <= c[0] <= start and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1:
            return c[1], c[2]
    return None


def entry(f, bid, ask, gap=GAP):
    if ask - bid > MAX_SPREAD + 1e-9:
        return None
    if f - ask - 0.07 * ask * (1 - ask) >= gap:
        return "yes", ask
    if bid - f - 0.07 * bid * (1 - bid) >= gap:
        return "no", 1 - bid
    return None


def eligible(uni, cands):
    """Events with a usable quote at entry and spread at most 10c (price based, not outcome based)."""
    out = {}
    for tk, m in uni.items():
        q = quote(cands.get(tk, []), m["start"])
        if q and q[1] - q[0] <= MAX_SPREAD + 1e-9:
            out[tk] = (m, q)
    return out


def thirds(starts):
    ev = sorted(starts)
    n = len(ev)
    cut1, cut2 = ev[n // 3], ev[(2 * n) // 3]
    return lambda s: "W1" if s < cut1 else ("W2" if s < cut2 else "W3")


def collect(elig, win, mult=1.0, gap=GAP):
    rows = defaultdict(list)
    for tk, (m, q) in elig.items():
        e = entry(m["fair"], q[0], q[1], gap)
        if e:
            rows[win(m["start"])].append((m["event"], pnl(e[0], e[1], m["res"], mult)))
    return rows


def brier(elig):
    mod = mkt = n = 0
    for m, q in elig.values():
        y = 1.0 if m["res"] == "yes" else 0.0
        mod += (m["fair"] - y) ** 2
        mkt += ((q[0] + q[1]) / 2 - y) ** 2
        n += 1
    return (mod / n, mkt / n, n) if n else (None, None, 0)


# ---------------------------------------------------------------- data
FIELDS = ("ticker", "event_ticker", "result", "open_time", "close_time", "yes_sub_title", "rules_primary")


def list_all():
    out = {}
    for s in ALL:
        for path, key in (("/historical/markets", "hist"), ("/markets", "live")):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000}
                if key == "live":
                    p["status"] = "settled"
                if cur:
                    p["cursor"] = cur
                d = api._get(path, p)
                for m in d.get("markets", []):
                    if m.get("result") in ("yes", "no"):
                        out[m["ticker"]] = {k: m.get(k) for k in FIELDS} | {"series": s, "src": key}
                cur = d.get("cursor")
                if not cur or not d.get("markets"):
                    break
    return out


def fetch():
    D.mkdir(parents=True, exist_ok=True)
    mp = D / "markets.json"
    if not mp.exists():
        mp.write_text(json.dumps(list_all()))
    markets = json.loads(mp.read_text())
    uni = universe(markets)
    (D / "universe.json").write_text(json.dumps(uni))
    print(len(uni), "events in the universe", flush=True)
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}

    def one(tk):
        m = uni[tk]
        path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{m['series']}/markets/{tk}/candlesticks"
        try:
            d = api._get(path, {"start_ts": m["start"] - LEAD_S - 60, "end_ts": m["start"] + 60, "period_interval": 1})
        except Exception:
            return tk, None
        return tk, [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in d.get("candlesticks", [])]

    todo = [t for t in uni if t not in have]
    with ThreadPoolExecutor(5) as ex:
        for i, (tk, v) in enumerate(ex.map(one, todo)):
            if v is not None:
                have[tk] = v
            if i % 200 == 0:
                cp.write_text(json.dumps(have))
                print(i, len(todo), flush=True)
    cp.write_text(json.dumps(have))
    print("done", len(have), flush=True)


def verdict_for(tag, elig):
    out = []
    win = thirds([m["start"] for m, _ in elig.values()]) if elig else None
    if not elig:
        return ["%s: no eligible events" % tag, f"VERDICT {tag} NOT_RUNNABLE: no candles with a quote"]
    mb, kb, nb = brier(elig)
    out.append(f"{tag}: eligible events {len(elig)}; Brier Elo {mb:.4f} market mid {kb:.4f}")
    r1, r12 = collect(elig, win), collect(elig, win, 1.2)
    S, S12, ok = {}, {}, True
    for w in ("W1", "W2"):
        S[w], S12[w] = stats(r1[w]), stats(r12[w])
        out.append(line(f"{tag} {w}", S[w]) + f" | fees x1.2 PF {S12[w]['pf']:.2f}")
        ok = ok and S[w]["pf"] >= BAR_PF
    pooled = [x for w in ("W1", "W2") for x in r1[w]]
    ntr = sum(S[w]["n"] for w in S)
    if ok and mb < kb:
        S["W3"], S12["W3"] = stats(r1["W3"]), stats(r12["W3"])
        out.append(line(f"{tag} W3 (holdout, read because W1 and W2 passed)", S["W3"]) + f" | fees x1.2 PF {S12['W3']['pf']:.2f}")
        pooled += r1["W3"]
        ntr += S["W3"]["n"]
    else:
        out.append(f"{tag} W3 holdout NOT read (W1 and W2 did not both pass, or Elo Brier not better than the market)")
    ps = stats(pooled)
    out.append(line(f"{tag} pooled read windows", ps))
    for g in (0.05, 0.12):
        rr = collect(elig, win, 1.0, g)
        out.append(f"{tag} info gap {g}: " + " ".join(f"{w} n {len(rr[w])} PF {stats(rr[w])['pf']:.2f}" for w in ("W1", "W2")))
    why = []
    if ntr < MIN_TRADES:
        v, why = "NOT_ENOUGH_DATA", [f"{ntr} trades under {MIN_TRADES}"]
    else:
        if any(S[w]["pf"] < BAR_PF for w in S):
            why.append("PF under 1.5 in a window")
        if any(S12[w]["pf"] < 1.0 for w in S12):
            why.append("not positive at fees x1.2")
        if not (mb < kb):
            why.append("Elo Brier not better than the market")
        if ps["z"] < BAR_Z:
            why.append(f"pooled z {ps['z']:.2f} under {BAR_Z}")
        if ps["mean"] < MIN_MEAN_C:
            why.append("pooled mean under 2c")
        v = "FALSIFIED" if why else "NOT_YET_FALSIFIED"
    out.append(f"VERDICT {tag} {v}: " + "; ".join(why))
    return out


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT)
        return
    uni = json.loads((D / "universe.json").read_text())
    cands = json.loads((D / "candles.json").read_text())
    out = [f"ESPORT1 run {datetime.now(UTC).isoformat()} N={N_RUN} z bar {BAR_Z} cost 7% x C x p x (1-p) rounded up, C 10, taker at the ask",
           f"universe events {len(uni)}, with candles {sum(1 for t in uni if t in cands)}"]
    for tag, ss in (("A KXCS2MAP", TRY_A), ("B LOL+DOTA2+VALORANT", TRY_B)):
        sub = {t: m for t, m in uni.items() if m["series"] in ss}
        out += verdict_for(tag, eligible(sub, cands))
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
