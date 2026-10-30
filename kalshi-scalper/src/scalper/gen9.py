"""GEN9 (workers/GEN9_REGISTRATION.md): a generator of SUB-MINUTE ROUND TRIPS on KXBTC15M and KXGOLD15M from Kalshi's public
trade tape, binned into 10 second bars. Entry at a 10 s bar 840 to 240 s before the close, the side priced 20c to 80c by the
last trade, 1 to 3 conditions on tape features (signed taker flow, trade counts, price change, print size); exit by selling
30 to 180 s later (time, or take profit / stop on 10 s bars), never later than 120 s before the close and NEVER held to
settlement. Fills are APPROXIMATIONS from trade prices (last trade +/- half the candle spread +/- 1c), not a book.
Research only; nothing here places an order, reads a key or decides anything live. The settlement result is never read.
    python -m scalper.gen9 plan                     (day sample, market lists, fetch order; no tape)
    python -m scalper.gen9 fetch <A|B>              (stream A: gold, then Bitcoin from the tail; stream B: Bitcoin)
    python -m scalper.gen9 status
    python -m scalper.gen9 discovery <btc|gold>     (build discovery rows, generate, dedupe, screen, freeze)
    python -m scalper.gen9 validate <btc|gold>      (once, after the frozen files are committed and pushed)
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .gen7 import DISC, FILES, MARKETS, VAL, pf
from .paths import DATA_DIR

G = DATA_DIR / "gen9"
DAY_SEED, ORDER_SEED, SEED = 909, 919, 9
BUDGET_S = 6 * 3600                 # no new market is started 6 hours after the fetch start
FETCH_LO, FETCH_HI = 900, 120       # tape kept from close-900 (exclusive) to close-120 (inclusive)
BAR = 10
NBARS = (FETCH_LO - FETCH_HI) // BAR          # 78 bars; bar j ends at close - (900 - 10 (j+1))
ENTRY_LS = tuple(range(840, 239, -10))        # 61 entry bar ends (seconds left)
LOOKS = tuple(range(840, 239, -60))           # range bounds: 840, 780, ..., 240
RANGES = [(a, b) for a in LOOKS for b in LOOKS if b <= a]
ZONE = (20.0, 80.0)                           # side price in cents by the last trade
STALE = 60                                    # entry needs a trade in the last 60 s
HOLDS = (30, 60, 90, 120, 150, 180)
TPS = (None, 3.0, 5.0, 8.0, 12.0)
STOPS = (None, 5.0, 10.0)
EXITS = [(h, i, j) for i in range(len(TPS)) for j in range(len(STOPS)) for h in HOLDS]
LAST_EXIT = 120
C = 10
DEFAULT_HS = 1.5                              # half spread (cents) when no candle is available at an exit
TARGET, MAX_DRAWS, MIN_TRADES = 5000, 300_000, 30
N_PRIOR = 627_838
FEATS = ["f10", "f30", "f60", "i10", "i30", "i60", "c10", "c30", "c60", "burst", "dp10", "dp30", "dp60", "big30", "bigdir30", "px"]
MAKER4_LO = 750                               # MAKER4's cached tape covers (close-750, close-115]


def _ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


def day_of(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- plan (no tape)

def sample_days():
    def days(lo, hi):
        return [day_of(t) for t in range(lo, hi, 86400)]
    rng = random.Random(DAY_SEED)
    d = days(*DISC); v = days(*VAL)
    return sorted(rng.sample(d, math.ceil(len(d) / 2))), sorted(rng.sample(v, math.ceil(len(v) / 2)))


def market_list(series):
    """(ticker, close_ts) of settled markets of the series in the sampled days that have candles (first file wins)."""
    dd, vd = sample_days(); keep = set(dd) | set(vd)
    seen, out = set(), []
    for name in FILES:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for tk, ct, res in db.execute("select ticker, close_ts, result from market where series=? and close_ts >= ? and close_ts < ?",
                                      (series, DISC[0], VAL[1])).fetchall():
            if tk in seen or res not in ("yes", "no") or day_of(ct) not in keep:
                continue
            if db.execute("select 1 from candle where ticker=? and bid_c is not null limit 1", (tk,)).fetchone() is None:
                continue
            seen.add(tk); out.append((tk, int(ct)))
    out.sort()
    return out


def fetch_order(series):
    lst = market_list(series)
    rng = random.Random(ORDER_SEED + (1 if series == "KXBTC15M" else 2))
    rng.shuffle(lst)
    return lst


def plan():
    dd, vd = sample_days()
    print("discovery days", len(dd), dd)
    print("validation days", len(vd), vd)
    for key, se in MARKETS.items():
        o = fetch_order(se)
        nd = sum(1 for _, c in o if c < DISC[1])
        print(se, "markets", len(o), "discovery", nd, "validation", len(o) - nd, "first 5 in fetch order", [t for t, _ in o[:5]])


# ---------------------------------------------------------------- fetch (public tape, keyless)

BASE = "https://api.elections.kalshi.com/trade-api/v2"


def _get(path, params):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    wait = 3.0
    for i in range(60):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(wait); wait = min(wait * 2, 60.0); continue
            if e.code in (400, 404):
                return {"trades": []}
            time.sleep(5.0)
        except Exception:
            time.sleep(5.0)
    raise RuntimeError("GET failed " + path)


def _pages(path, tk, lo, hi):
    cur, rows = None, []
    while True:
        p = {"ticker": tk, "limit": 1000, "min_ts": lo, "max_ts": hi}
        if cur:
            p["cursor"] = cur
        d = _get(path, p)
        for t in d.get("trades", []):
            ts = datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp()
            rows.append((ts, float(t["yes_price_dollars"]) * 100, float(t["count_fp"]), 1 if t["taker_outcome_side"] == "yes" else -1))
        cur = d.get("cursor")
        time.sleep(0.5)
        if not cur or not d.get("trades"):
            return rows


def fetch_trades(tk, lo, hi, close):
    first = "/historical/trades" if close < _ts(2026, 10, 1) else "/markets/trades"
    second = "/markets/trades" if first == "/historical/trades" else "/historical/trades"
    rows = _pages(first, tk, lo, hi)
    if rows:
        return rows, first
    rows = _pages(second, tk, lo, hi)
    return rows, (second if rows else "empty")


def bars_of(trades, close):
    """78 bars of (n, vol_yes_taker, vol_no_taker, max_size, max_dir, last_yes_c, last_ts) from trades in (close-900, close-120]."""
    b = [[0, 0.0, 0.0, 0.0, 0, None, None] for _ in range(NBARS)]
    for ts, yc, sz, d in sorted(trades):
        if not (close - FETCH_LO < ts <= close - FETCH_HI):
            continue
        j = min(NBARS - 1, int(math.ceil((ts - (close - FETCH_LO)) / BAR)) - 1)
        x = b[j]
        x[0] += 1
        if d > 0:
            x[1] += sz
        else:
            x[2] += sz
        if sz > x[3]:
            x[3] = sz; x[4] = d
        x[5] = round(yc, 3); x[6] = round(ts, 3)
    return b


def _db():
    G.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(G / "bars.sqlite", timeout=120)
    db.execute("CREATE TABLE IF NOT EXISTS bars(ticker TEXT PRIMARY KEY, series TEXT, close INTEGER, ntr INTEGER, src TEXT, data TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS claim(ticker TEXT PRIMARY KEY, stream TEXT, at REAL)")
    db.commit()
    return db


def _maker4():
    out = {}
    for f in sorted((DATA_DIR / "maker4").glob("tape_*.json")):
        for k, v in json.loads(f.read_text()).items():
            if k.startswith("KXBTC15M") or k.startswith("KXGOLD15M"):
                out[k] = v
    return out


def fetch(stream):
    G.mkdir(parents=True, exist_ok=True)
    sf = G / "fetch_start.txt"
    if not sf.exists():
        sf.write_text(str(time.time()))
    deadline = float(sf.read_text()) + BUDGET_S
    btc = fetch_order("KXBTC15M"); gold = fetch_order("KXGOLD15M")
    jobs = [(t, c, "KXGOLD15M") for t, c in gold] + [(t, c, "KXBTC15M") for t, c in reversed(btc)] if stream == "A" \
        else [(t, c, "KXBTC15M") for t, c in btc]
    cache = _maker4()
    db = _db()
    for i, (tk, close, se) in enumerate(jobs):
        if time.time() > deadline:
            print(stream, "deadline reached", flush=True); break
        cur = db.execute("insert or ignore into claim values(?,?,?)", (tk, stream, time.time())); db.commit()
        if cur.rowcount == 0:
            continue
        lo, hi = close - FETCH_LO, close - FETCH_HI
        if tk in cache:
            part, src = fetch_trades(tk, lo, close - MAKER4_LO, close)
            tr = [r for r in part if r[0] <= close - MAKER4_LO] + \
                 [(r[0], float(r[1]), r[2], r[3]) for r in cache[tk] if close - MAKER4_LO < r[0] <= hi]
            src = "maker4+" + src
        else:
            tr, src = fetch_trades(tk, lo, hi, close)
        b = bars_of(tr, close)
        db.execute("insert or replace into bars values(?,?,?,?,?,?)", (tk, se, close, len(tr), src, json.dumps(b, separators=(",", ":"))))
        db.commit()
        if i % 10 == 0:
            print(stream, i, len(jobs), tk, len(tr), src, datetime.now(timezone.utc).strftime("%H:%M"), flush=True)
    print("stream", stream, "finished", flush=True)


def status():
    db = _db()
    sf = G / "fetch_start.txt"
    if sf.exists():
        print("elapsed h", round((time.time() - float(sf.read_text())) / 3600, 2))
    for se in MARKETS.values():
        r = db.execute("select count(*), sum(ntr), sum(close < ?), count(distinct date(close,'unixepoch')) from bars where series=?", (DISC[1], se)).fetchone()
        print(se, "fetched", r[0], "trades", r[1], "discovery", r[2], "days", r[3])
    print("claims", db.execute("select stream, count(*) from claim group by stream").fetchall())


# ---------------------------------------------------------------- rows

def load_candles(tickers):
    out, seen = {}, set()
    for name in FILES:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for tk in tickers:
            if tk in seen:
                continue
            cs = {r[0]: (r[1], r[2]) for r in db.execute("select end_ts, bid_c, ask_c from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if cs:
                seen.add(tk); out[tk] = cs
    return out


def half_spread(cs, t):
    """Half the median closing spread (cents) of the candles ending at E-120, E-60, E, where E ends the minute holding t."""
    E = int(math.ceil(t / 60.0) * 60)
    sp = [(cs[k][1] - cs[k][0]) * 100 for k in (E - 120, E - 60, E) if k in cs]
    sp = [s for s in sp if s >= 0]
    return float(np.median(sp)) / 2 if sp else None


class Tape:
    """As-of reads on one window's 10 s bars; times are seconds LEFT before the close (bar ends)."""

    def __init__(self, bars, close):
        self.b, self.close = bars, close
        self.last = []                     # as-of (price, trade ts) at each bar end
        cur = (None, None)
        for x in bars:
            if x[5] is not None:
                cur = (x[5], x[6])
            self.last.append(cur)

    def j(self, L):                        # bar index ending at L seconds left
        return (FETCH_LO - L) // BAR - 1

    def px(self, L):
        return self.last[self.j(L)]

    def window(self, L, w):                # bars ending in (L+w, L]
        j = self.j(L)
        return self.b[max(0, j - w // BAR + 1): j + 1]


def side_feats(T, L, yes):
    s = 1 if yes else -1
    p, _ = T.px(L)
    sp = p if yes else 100 - p
    f = []
    sums = {}
    for w in (10, 30, 60):
        bs = T.window(L, w)
        vy = sum(x[1] for x in bs); vn = sum(x[2] for x in bs)
        sums[w] = (vy, vn, sum(x[0] for x in bs))
    for w in (10, 30, 60):
        vy, vn, _ = sums[w]; f.append(s * (vy - vn))
    for w in (10, 30, 60):
        vy, vn, _ = sums[w]; f.append(s * (vy - vn) / (vy + vn) if vy + vn > 0 else np.nan)
    for w in (10, 30, 60):
        f.append(float(sums[w][2]))
    f.append(sums[10][2] / max(1.0, sums[60][2] / 6.0))
    for w in (10, 30, 60):
        q, _ = T.px(L + w) if L + w <= FETCH_LO - BAR else (None, None)
        f.append(np.nan if q is None else s * (p - q))
    bs = T.window(L, 30)
    mx = max(bs, key=lambda x: x[3])
    f.append(mx[3]); f.append(float(s * mx[4]) if mx[3] > 0 else 0.0)
    f.append(sp)
    return f


def _fee(p, c, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def _bids(T, cs, yes):
    """Approximate sale price (cents) at every bar end: side last trade - half spread - 1c (floor 0), with flags
    (stale: no trade in the last 60 s; dflt: no candle, 1.5c half spread used). Keyed by seconds left."""
    out = {}
    close = T.close
    for j in range(NBARS):
        Lx = FETCH_LO - BAR * (j + 1)
        p, pts = T.last[j]
        if p is None:
            out[Lx] = (0.0, True, True); continue
        sp = p if yes else 100 - p
        hs = half_spread(cs, close - Lx)
        dflt = hs is None
        hs = DEFAULT_HS if dflt else hs
        out[Lx] = (max(0.0, sp - hs - 1.0), (close - Lx) - pts > STALE, dflt)
    return out


def _exit(BD, L, e_c, ex):
    """Net per contract (cents) at C, stressed (fees x1.2), at C=1; plus flags (stale exit price, default spread).
    A sale price of 0 is booked at 0 with no exit fee."""
    H, ti, si = ex
    tp, st = TPS[ti], STOPS[si]
    Lend = L - H
    x = None
    if tp is not None or st is not None:
        for Lx in range(L - BAR, Lend - 1, -BAR):
            b = BD[Lx][0]
            if (tp is not None and b >= e_c + tp - 1e-9) or (st is not None and b <= e_c - st + 1e-9):
                x = BD[Lx]; break
    if x is None:
        x = BD[Lend]
    b, stl, df = x
    ein, eout = e_c / 100, b / 100
    out = []
    for c, m in ((C, 1.0), (C, 1.2), (1, 1.0)):
        fx = _fee(eout, c, m) if b > 0 else 0.0
        out.append(b - e_c - 100 * (_fee(ein, c, m) + fx))
    return out, stl, df


def window_rows(bars, close, cs):
    """Every (bar end, side) row with the side's last-trade price in [20, 80] and a trade in the last 60 s, in entry order
    (840 s first, YES before NO). Fill = side price + half spread + 1c. Shared by history and any later evaluator."""
    T = Tape(bars, close)
    BDS = {1: _bids(T, cs, 1), 0: _bids(T, cs, 0)}
    rows = []
    for L in ENTRY_LS:
        p, pts = T.px(L)
        if p is None or (close - L) - pts > STALE:
            continue
        hs = half_spread(cs, close - L)
        if hs is None:
            continue
        for yes in (1, 0):
            sp = p if yes else 100 - p
            if not (ZONE[0] - 1e-9 <= sp <= ZONE[1] + 1e-9):
                continue
            e_c = sp + hs + 1.0
            if not (0 < e_c < 100):
                continue
            nets, flags = [], []
            for ex in EXITS:
                if ex[0] > L - LAST_EXIT:
                    nets.append((np.nan, np.nan, np.nan)); flags.append((False, False)); continue
                n3, stl, df = _exit(BDS[yes], L, e_c, ex)
                nets.append(n3); flags.append((stl, df))
            rows.append({"L": L, "yes": yes, "feats": side_feats(T, L, yes), "fill": e_c, "nets": nets, "flags": flags})
    return rows


def build(series, lo, hi):
    db = _db()
    W = db.execute("select ticker, close, data from bars where series=? and close >= ? and close < ? order by close", (series, lo, hi)).fetchall()
    CS = load_candles([w[0] for w in W])
    X, meta, N10, NS, N1, STL, DFL = [], [], [], [], [], [], []
    wl = []
    for tk, close, data in W:
        if tk not in CS:
            continue
        wid = len(wl); wl.append((tk, close))
        day = day_of(close)
        for r in window_rows(json.loads(data), close, CS[tk]):
            X.append(r["feats"]); meta.append((wid, day, r["L"], r["yes"], r["fill"]))
            N10.append([n[0] for n in r["nets"]]); NS.append([n[1] for n in r["nets"]]); N1.append([n[2] for n in r["nets"]])
            STL.append([f[0] for f in r["flags"]]); DFL.append([f[1] for f in r["flags"]])
    days = sorted({m[1] for m in meta})
    di = {d: i for i, d in enumerate(days)}
    D = {"X": np.array(X, dtype=np.float64).reshape(-1, len(FEATS)),
         "wid": np.array([m[0] for m in meta], dtype=np.int64), "day": np.array([di[m[1]] for m in meta], dtype=np.int64),
         "L": np.array([m[2] for m in meta], dtype=np.int64), "yes": np.array([m[3] for m in meta], dtype=np.int64),
         "fill": np.array([m[4] for m in meta]), "n10": np.array(N10, dtype=np.float32).reshape(-1, len(EXITS)),
         "ns": np.array(NS, dtype=np.float32).reshape(-1, len(EXITS)), "n1": np.array(N1, dtype=np.float32).reshape(-1, len(EXITS)),
         "stale": np.array(STL, dtype=bool).reshape(-1, len(EXITS)), "dflt": np.array(DFL, dtype=bool).reshape(-1, len(EXITS)),
         "days": days, "nwin": len(wl), "windows": wl}
    return D


# ---------------------------------------------------------------- generator

def exit_allowed(e, L_lo):
    return EXITS[e][0] <= L_lo - LAST_EXIT


def exit_near(a, b):
    x, y = EXITS[a], EXITS[b]
    return abs(HOLDS.index(x[0]) - HOLDS.index(y[0])) <= 1 and abs(x[1] - y[1]) <= 1 and abs(x[2] - y[2]) <= 1


def draw(rng, Q):
    L_hi, L_lo = rng.choice(RANGES)
    s = {"side": rng.choice(("yes", "no", "both")), "L_hi": L_hi, "L_lo": L_lo, "e": rng.randrange(len(EXITS)), "conds": []}
    for f in rng.sample(FEATS, rng.randint(1, 3)):
        s["conds"].append((f, rng.choice(("le", "gt")), float(Q[f][rng.choice(range(10, 91, 10))])))
    return s


def trades(D, s):
    m = (D["L"] <= s["L_hi"]) & (D["L"] >= s["L_lo"])
    if s["side"] != "both":
        m &= D["yes"] == (1 if s["side"] == "yes" else 0)
    for f, op, q in s["conds"]:
        x = D["X"][:, FEATS.index(f)]
        with np.errstate(invalid="ignore"):
            m &= (x <= q) if op == "le" else (x > q)       # NaN fails both
    idx = np.nonzero(m)[0]
    if not len(idx):
        return idx
    _, first = np.unique(D["wid"][idx], return_index=True)
    return idx[first]


def dayz(v, d):
    if len(v) < 2:
        return 0.0
    mu = v.mean()
    s = np.bincount(d, weights=v - mu)
    den = math.sqrt(float((s ** 2).sum()))
    return float(v.sum() / den) if den > 0 else 0.0


def score(D, idx, e):
    v = D["n10"][idx, e].astype(np.float64); vs = D["ns"][idx, e].astype(np.float64); v1 = D["n1"][idx, e].astype(np.float64)
    return {"n": int(len(idx)), "days": int(len(set(D["day"][idx].tolist()))), "pf": pf(v), "mean": float(v.mean()) if len(v) else 0.0,
            "pfs": pf(vs), "pf1": pf(v1), "z": dayz(v, D["day"][idx]),
            "stale": float(D["stale"][idx, e].mean()) if len(idx) else 0.0, "dflt": float(D["dflt"][idx, e].mean()) if len(idx) else 0.0}


def desc(s):
    H, ti, si = EXITS[s["e"]]
    ex = f"sell {H}s after" if TPS[ti] is None and STOPS[si] is None else f"TP {TPS[ti]} stop {STOPS[si]} else {H}s"
    c = " & ".join(f"{f} {'<=' if op == 'le' else '>'} {q:.4g}" for f, op, q in s["conds"])
    return f"{s['side']} {s['L_hi']}..{s['L_lo']}s, {c}, {ex}"


def base_info(D):
    out = {}
    for H in HOLDS:
        e = EXITS.index((H, 0, 0))
        s = {"side": "both", "L_hi": 840, "L_lo": max(240, H + LAST_EXIT), "e": e, "conds": []}
        idx = trades(D, s)
        out[str(H)] = score(D, idx, e)
    return out


def _key(key):
    return MARKETS[key]


def discovery(key):
    series = _key(key)
    D = build(series, *DISC)
    print(series, "discovery windows", D["nwin"], "rows", len(D["wid"]), "days", len(D["days"]), flush=True)
    if D["nwin"] < 300 or len(D["days"]) < 15:
        print("NOT_ENOUGH_DATA"); (G / f"{key}_disc_info.json").write_text(json.dumps({"nwin": D["nwin"], "days": len(D["days"]), "verdict": "NOT_ENOUGH_DATA"})); return
    Q = {f: np.nanpercentile(D["X"][:, i], list(range(101))) for i, f in enumerate(FEATS)}
    nw = D["nwin"]
    rng = random.Random(SEED * 1000 + (1 if key == "btc" else 2))
    kept, kbits, ksz, kexit = [], [], [], []
    gen = rej_exit = rej_small = rej_dup = 0
    while len(kept) < TARGET and gen < MAX_DRAWS:
        s = draw(rng, Q); gen += 1
        if not exit_allowed(s["e"], s["L_lo"]):
            rej_exit += 1; continue
        idx = trades(D, s)
        if len(idx) < MIN_TRADES:
            rej_small += 1; continue
        ws = D["wid"][idx]
        bits = 0
        for w in ws.tolist():
            bits |= 1 << w
        n = len(ws); dup = False
        for kb, kn, ke in zip(kbits, ksz, kexit):
            if not exit_near(s["e"], ke):
                continue
            inter = (kb & bits).bit_count()
            if inter / (kn + n - inter) > 0.5:
                dup = True; break
        if dup:
            rej_dup += 1; continue
        kbits.append(bits); ksz.append(n); kexit.append(s["e"])
        kept.append((s, score(D, idx, s["e"])))
        if len(kept) % 500 == 0:
            print("distinct", len(kept), "generated", gen, flush=True)
    size = lambda sc: sc["n"] >= 100 and sc["days"] >= 15
    ok = lambda sc: sc["pf"] >= 1.5 and sc["stale"] <= 0.2
    surv = [{"strategy": s, "disc": sc} for s, sc in kept if size(sc) and ok(sc)]
    ctrl = [{"strategy": s, "disc": sc} for s, sc in kept if size(sc) and not ok(sc)]
    pfs = np.array([sc["pf"] for _, sc in kept]) if kept else np.array([0.0])
    big = np.array([sc["pf"] for _, sc in kept if size(sc)])
    info = {"series": series, "generated": gen, "distinct": len(kept),
            "rejected": {"exit_not_allowed": rej_exit, "under_30_trades": rej_small, "duplicate": rej_dup},
            "disc_windows": nw, "disc_rows": int(len(D["wid"])), "disc_days": len(D["days"]),
            "pf_median": float(np.median(pfs)), "pf_p95": float(np.percentile(pfs, 95)),
            "mean_median": float(np.median([sc["mean"] for _, sc in kept])) if kept else 0.0,
            "at_size": int(len(big)), "at_size_pf_ge_1": int((big >= 1.0).sum()), "at_size_pf_ge_1_3": int((big >= 1.3).sum()),
            "best_at_size": float(big.max()) if len(big) else 0.0, "survivors_n": len(surv), "controls_n": len(ctrl),
            "base_info": base_info(D), "frozen_at": datetime.now(timezone.utc).isoformat()}
    G.mkdir(parents=True, exist_ok=True)
    (G / f"{key}_distinct.json").write_text(json.dumps({"info": info, "distinct": [{"strategy": s, "disc": sc} for s, sc in kept]}))
    (G / f"{key}_controls.json").write_text(json.dumps({"info": info, "controls": ctrl}))
    fz = json.dumps({"info": info, "survivors": surv}, indent=1)
    (G / f"{key}_frozen.json").write_text(fz)
    print(json.dumps(info, indent=1))
    for r in sorted(kept, key=lambda r: -(r[1]["pf"] if size(r[1]) else 0))[:12]:
        print(desc(r[0]), {k: round(v, 3) for k, v in r[1].items()})
    for name in ("frozen", "controls", "distinct"):
        print(name, hashlib.sha256((G / f"{key}_{name}.json").read_bytes()).hexdigest())


def _vpass(vs):
    return vs["pf"] >= 1.3 and vs["n"] >= 50 and vs["pfs"] > 1.0 and vs["stale"] <= 0.2


def _tup(s):
    s["conds"] = [tuple(c) for c in s["conds"]]
    return s


def validate(key):
    series = _key(key)
    out = G / f"{key}_validation.json"
    if out.exists():
        print("Refusing to run again: validation already read"); return
    fz = json.loads((G / f"{key}_frozen.json").read_text())
    ct = json.loads((G / f"{key}_controls.json").read_text())
    ds = json.loads((G / f"{key}_distinct.json").read_text())
    D = build(series, *VAL)
    print(series, "validation windows", D["nwin"], "rows", len(D["wid"]), "days", len(D["days"]), flush=True)
    res = {"windows": D["nwin"], "days": len(D["days"]), "survivors": [], "controls_n": len(ct["controls"]), "controls_pass": 0,
           "base_info": base_info(D)}
    for r in fz["survivors"]:
        s = _tup(r["strategy"]); vs = score(D, trades(D, s), s["e"])
        res["survivors"].append({"desc": desc(s), "disc": r["disc"], "val": vs, "pass": _vpass(vs)})
    cp = []
    for r in ct["controls"]:
        s = _tup(r["strategy"]); vs = score(D, trades(D, s), s["e"])
        cp.append(vs["pf"])
        if _vpass(vs):
            res["controls_pass"] += 1
    res["controls_val_pf_median"] = float(np.median(cp)) if cp else None
    res["controls_val_pf_p95"] = float(np.percentile(cp, 95)) if cp else None
    size = lambda sc: sc["n"] >= 100 and sc["days"] >= 15
    best = sorted([r for r in ds["distinct"] if size(r["disc"])], key=lambda r: -r["disc"]["pf"])[:10]
    res["best10"] = []
    for r in best:
        s = _tup(r["strategy"]); vs = score(D, trades(D, s), s["e"])
        res["best10"].append({"desc": desc(s), "disc": r["disc"], "val": vs})
    ns = len(res["survivors"])
    res["survivor_pass_rate"] = sum(x["pass"] for x in res["survivors"]) / ns if ns else None
    res["control_pass_rate"] = res["controls_pass"] / res["controls_n"] if res["controls_n"] else None
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "plan":
        plan()
    elif cmd == "fetch":
        fetch(sys.argv[2])
    elif cmd == "status":
        status()
    elif cmd == "discovery":
        discovery(sys.argv[2])
    elif cmd == "validate":
        validate(sys.argv[2])
