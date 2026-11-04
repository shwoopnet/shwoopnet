"""TENNIS1 (workers/TENNIS1_REGISTRATION.md): the CHEAP side (ask 3c to 30c) of Kalshi ATP and WTA tour-level match-winner markets against a walk-forward
Elo built only from ESPN's completed tour-level results. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.
Nothing here means trade; no promote verb. Cheap side only: no favourite-side result is computed or printed anywhere in this file.

    python -m scalper.tennis1 census   (listings and names only: how many Kalshi matches match an ESPN match with Elo ready; no candle, no outcome)
    python -m scalper.tennis1 fetch    (resumable; candles of the registered universe only, before the frozen cut)
    python -m scalper.tennis1 run      (the one scored read; refused a second time)
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone

CUT = datetime(2026, 10, 3, 16, 0, tzinfo=timezone.utc)   # frozen last third: matches from here are never fetched or joined
K0, K_EXP, K_OFF, SCALE, INIT, MIN_PRIOR = 250.0, 0.4, 5.0, 400.0, 1500.0, 10
ASK_LO, ASK_HI, RATIO, HARD_LIMIT = 0.03, 0.30, 3.0, 0.30
C, LEAD_S = 10, 600
BAR_PF, MIN_TRADES = 1.5, 150
SUFFIX = {"jr": 1, "sr": 1, "ii": 1, "iii": 1}


def norm(name: str) -> str:
    """Lower case, accents removed, punctuation to spaces, suffixes dropped; the same function is applied to Kalshi's and ESPN's names."""
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return " ".join(w for w in s.split() if w not in SUFFIX)


def elo_p(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / SCALE))


class Elo:
    """Per-tour walk-forward Elo. K = K0 / (n + K_OFF) ** K_EXP, n = the player's earlier matches (a new player moves fast)."""

    def __init__(self):
        self.r = defaultdict(lambda: INIT)
        self.n = defaultdict(int)

    def prob(self, a: str, b: str) -> float:
        return elo_p(self.r[a], self.r[b])

    def ready(self, a: str, b: str) -> bool:
        return self.n[a] >= MIN_PRIOR and self.n[b] >= MIN_PRIOR

    def update(self, winner: str, loser: str) -> None:
        pw = elo_p(self.r[winner], self.r[loser])
        kw = K0 / (self.n[winner] + K_OFF) ** K_EXP
        kl = K0 / (self.n[loser] + K_OFF) ** K_EXP
        self.r[winner] += kw * (1 - pw)
        self.r[loser] -= kl * (1 - pw)
        self.n[winner] += 1
        self.n[loser] += 1


def fee(price: float, contracts: int = C) -> float:
    """Kalshi taker fee: 7% x C x p x (1-p), rounded UP to the cent, in dollars for the order."""
    return math.ceil(round(0.07 * contracts * price * (1 - price) * 100, 6)) / 100


def cheap_side(yes_bid: float, yes_ask: float):
    """The side with ask 3c to 30c, or None. Returns ('yes'|'no', ask). NO ask is 1 - YES bid. Needs a two-sided quote."""
    if yes_bid is None or yes_ask is None or not (0 < yes_bid < yes_ask < 1):
        return None
    if ASK_LO <= yes_ask <= ASK_HI:
        return "yes", yes_ask
    no_ask = 1 - yes_bid
    if ASK_LO <= no_ask <= ASK_HI:
        return "no", no_ask
    return None


def net_cents(ask: float, won: bool, contracts: int = C) -> float:
    """Net per contract, in cents, after the fee on the order (buy at the ask, hold to settlement)."""
    gross = (1.0 - ask) if won else -ask
    return (gross * contracts - fee(ask, contracts)) / contracts * 100


def treated(p_side: float, ask: float) -> bool:
    return ask <= HARD_LIMIT and p_side >= RATIO * ask - 1e-9


def profit_factor(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf") if g > 0 else 0.0


def summary(rows):
    """rows: (cluster, net_cents, won, ask). Returns n, mean, win rate, mean ask, PF."""
    if not rows:
        return dict(n=0, mean=None, win=None, ask=None, pf=None)
    n = len(rows)
    return dict(n=n, mean=sum(r[1] for r in rows) / n, win=sum(1 for r in rows if r[2]) / n,
                ask=sum(r[3] for r in rows) / n, pf=profit_factor([r[1] for r in rows]))


def verdict(treated_rows, midpoint):
    """FALSIFIED unless mean net > 0 in BOTH halves (split by match start at midpoint) and PF >= 1.5; NOT_ENOUGH_DATA under 150 trades."""
    n = len(treated_rows)
    if n < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    h1 = [r[1] for r in treated_rows if r[4] < midpoint]
    h2 = [r[1] for r in treated_rows if r[4] >= midpoint]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    pf = profit_factor([r[1] for r in treated_rows])
    return "NOT_YET_FALSIFIED" if (m1 > 0 and m2 > 0 and pf >= BAR_PF) else "FALSIFIED"


def build_matches(espn_rows):
    """ESPN completed singles rows -> list sorted by start time of (start_iso, name_a, name_b, winner_index). Retirements and walkovers are kept
    out of the Elo only if ESPN marks them not final; every STATUS_FINAL result updates the ratings."""
    out = []
    for r in espn_rows:
        if r.get("status") != "STATUS_FINAL" or "Singles" not in (r.get("grp") or ""):
            continue
        if r["win"].count(True) != 1:
            continue
        a, b = r["names"]
        out.append((r["date"], norm(a), norm(b), 0 if r["win"][0] else 1, r["id"]))
    out.sort()
    return out


def elo_before(matches, t_iso):
    """Yield-style helper: returns a function advancing the Elo to just before t_iso (ISO strings compare lexically in this format)."""
    elo = Elo()
    i = [0]

    def advance(t):
        while i[0] < len(matches) and matches[i[0]][0] < t:
            _, a, b, w, _id = matches[i[0]]
            elo.update(a if w == 0 else b, b if w == 0 else a)
            i[0] += 1
        return elo
    return advance


# ---------------------------------------------------------------- data
SERIES = ("KXATPMATCH", "KXWTAMATCH")
EV = re.compile(r"-(\d{2}[A-Z]{3}\d{2})")
D = __import__("pathlib").Path(os.environ.get("TENNIS1_DIR", "/tmp/t1/tennis1"))   # cache lives outside the repo
ESPN_DIR = __import__("pathlib").Path(os.environ.get("TENNIS1_ESPN", "/tmp/t1/espn"))
RESULT = D / "tennis1_result.txt"
FIELDS = ("ticker", "event_ticker", "close_time", "open_time", "yes_sub_title")


def list_markets(with_result: bool):
    """Settled markets before the cut, live and historical. with_result is False until the one scored read."""
    from . import api
    cut = CUT.strftime("%Y-%m-%dT%H:%M")
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
                    if (m.get("close_time") or "") < cut and m.get("result") in ("yes", "no"):
                        row = {k: m.get(k) for k in FIELDS} | {"series": s, "src": "live" if live else "hist"}
                        if with_result:
                            row["result"] = m["result"]
                        out[m["ticker"]] = row
                cur = d.get("cursor")
                if not cur or not d.get("markets"):
                    break
    return out


def espn_matches():
    """{'Men': [...], 'Women': [...]} of (start, a, b, winner_idx, id) rated matches, de-duplicated by competition id across both feeds."""
    seen, rows = set(), []
    for t in ("atp", "wta"):
        for r in json.loads((ESPN_DIR / f"{t}.json").read_text()):
            if r["id"] not in seen:
                seen.add(r["id"])
                rows.append(r)
    allm = {}
    for r in rows:
        g = "Men" if "Men" in (r.get("grp") or "") else "Women"
        allm.setdefault(g, []).append(r)
    rated = {g: build_matches(v) for g, v in allm.items()}
    # every singles result (final, retired, walkover) is a candidate for matching a Kalshi event; only final ones rate
    cand = defaultdict(list)
    for g, v in allm.items():
        for r in v:
            if "Singles" in (r.get("grp") or "") and r["win"].count(True) == 1:
                cand[frozenset(map(norm, r["names"]))].append((r["date"], g))
    return rated, cand


def event_date(ev: str):
    m = EV.search(ev)
    return datetime.strptime(m.group(1), "%y%b%d").replace(tzinfo=timezone.utc) if m else None


def universe(markets, rated, cand):
    """One row per Kalshi event matched to an ESPN match with both players ready: first market ticker, start unix, side names, Elo p for each market."""
    byev = defaultdict(dict)
    for tk, m in markets.items():
        byev[m["event_ticker"]][tk] = m
    advs = {g: elo_before(rated[g], None) for g in rated}
    work = []
    for ev, mk in byev.items():
        if len(mk) != 2:
            continue
        d = event_date(ev)
        if d is None:
            continue
        names = {tk: norm(m["yes_sub_title"]) for tk, m in mk.items()}
        c = [(t, g) for t, g in cand.get(frozenset(names.values()), []) if abs((datetime.strptime(t[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc) - d).days) <= 2]
        if not c:
            continue
        t, g = sorted(c)[0]
        start = datetime.strptime(t, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        if start >= CUT:
            continue
        work.append((t, g, ev, mk, names, int(start.timestamp())))
    work.sort(key=lambda x: x[0])
    uni = {}
    for t, g, ev, mk, names, start in work:
        e = advs[g](t)
        a, b = list(names.values())
        if not e.ready(a, b):
            continue
        first = sorted(mk)[0]
        uni[ev] = dict(event=ev, series=mk[first]["series"], src=mk[first]["src"], first=first, start=start, gender=g, startiso=t,
                       p={tk: e.prob(names[tk], [n for k, n in names.items() if k != tk][0]) for tk in mk})
    return uni


def fetch():
    from . import api
    from .candlefield import quote_close
    from concurrent.futures import ThreadPoolExecutor
    D.mkdir(parents=True, exist_ok=True)
    mp = D / "markets.json"
    if not mp.exists():
        mp.write_text(json.dumps(list_markets(False)))
    markets = json.loads(mp.read_text())
    rated, cand = espn_matches()
    uni = universe(markets, rated, cand)
    (D / "universe.json").write_text(json.dumps(uni))
    print(len(uni), "events in the universe", flush=True)
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}

    def one(ev):
        u = uni[ev]
        path = f"/historical/markets/{u['first']}/candlesticks" if u["src"] == "hist" else f"/series/{u['series']}/markets/{u['first']}/candlesticks"
        try:
            d = api._get(path, {"start_ts": u["start"] - 86400, "end_ts": u["start"], "period_interval": 1})
        except Exception:
            return ev, None
        return ev, [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in d.get("candlesticks", [])]

    todo = [e for e in uni if e not in have]
    def paced(ev):
        time.sleep(3.3)   # one thread, about 17 requests a minute: measured 2026-11-04, faster than that returns 429 on 40% of calls
        return one(ev)
    with ThreadPoolExecutor(1) as ex:
        for i, (ev, v) in enumerate(ex.map(paced, todo)):
            if v is not None:
                have[ev] = v
            if i % 25 == 0:
                cp.write_text(json.dumps(have))
                print(i, len(todo), flush=True)
    cp.write_text(json.dumps(have))
    print("done", len(have), flush=True)


def look(candles, start):
    """Last candle ending at or before start - 600 with a valid two-sided quote: (yes_bid, yes_ask) or None."""
    best = None
    for end, b, a in candles:
        if end <= start - LEAD_S and b is not None and a is not None and 0 < b < a < 1:
            if best is None or end > best[0]:
                best = (end, b, a)
    return (best[1], best[2]) if best else None


def build_rows(uni, candles, results):
    """Cheap-side rows: (event, net_cents, won, ask, start, p_side, treated). results is ticker -> 'yes'|'no' (None until the scored read)."""
    rows, nolook, nocheap = [], 0, 0
    for ev, u in uni.items():
        q = look(candles.get(ev, []), u["start"]) if ev in candles else None
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
        win_tk = tk if side == "yes" else other
        if results is None:
            rows.append((ev, None, None, ask, u["start"], p_side, treated(p_side, ask)))
            continue
        # side "yes" wins if the first market resolved yes; side "no" wins if it resolved no
        won = (results[tk] == "yes") if side == "yes" else (results[tk] == "no")
        rows.append((ev, net_cents(ask, won), won, ask, u["start"], p_side, treated(p_side, ask)))
    return rows, nolook, nocheap


def cluster_z(obs):
    from .calibration import cluster_mean_z
    return cluster_mean_z(obs)


def run():
    if RESULT.exists():
        print("refused: the scored read was already run (", RESULT, ")")
        return
    uni = json.loads((D / "universe.json").read_text())
    candles = json.loads((D / "candles.json").read_text())
    markets = list_markets(True)
    results = {tk: m["result"] for tk, m in markets.items()}
    uni = {e: u for e, u in uni.items() if u["first"] in results}
    rows, nolook, nocheap = build_rows(uni, candles, results)
    tr = [r for r in rows if r[6]]
    ctl = rows
    lines = [f"universe events {len(uni)}, no look {nolook}, no cheap side {nocheap}, cheap-side rows {len(rows)}, treated {len(tr)}"]
    for tag, rs in (("treated", tr), ("control", ctl)):
        s = summary([(r[0], r[1], r[2], r[3]) for r in rs])
        if s["n"]:
            m, se, z = cluster_z([(r[0], r[1]) for r in rs])
            lines.append(f"{tag}: n {s['n']} mean {s['mean']:+.2f}c win {s['win']:.3f} vs mean ask {s['ask']:.3f} PF {s['pf']:.2f} cluster z {z:+.2f}")
    if tr:
        starts = sorted(r[4] for r in tr)
        mid = starts[len(starts) // 2]
        h1 = [r[1] for r in tr if r[4] < mid]
        h2 = [r[1] for r in tr if r[4] >= mid]
        lines.append(f"halves {len(h1)}/{sum(h1)/max(len(h1),1):+.2f}c, {len(h2)}/{sum(h2)/max(len(h2),1):+.2f}c")
        v = verdict([(r[0], r[1], r[2], r[3], r[4]) for r in tr], mid)
        m, se, z = cluster_z([(r[0], r[1]) for r in tr])
        cm = sum(r[1] for r in ctl) / len(ctl)
        if v == "NOT_YET_FALSIFIED" and not (z >= 5.27 and m >= 2.0 and m > cm):
            v = "FALSIFIED"
        lines.append("VERDICT " + v)
    else:
        lines.append("VERDICT NOT_ENOUGH_DATA")
    RESULT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "run":
        run()
    else:
        print(__doc__)
