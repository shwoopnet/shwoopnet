"""MM1 (README, "Pre-registration: MM1"; scorer choices in workers/MM1S_AMENDMENT.md): QUOTE1's two-sided
passive quoting card on gold's 15 minute market (KXGOLD15M), last 150 seconds of each recorded window, flat
20 s before the close. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
    python -m scalper.mm1 count   (windows recorded and usable by coverage; no quote is replayed, nothing scored)
    python -m scalper.mm1 run     (refused below 300 usable windows; fetches the tape, scores once, writes
                                   data/mm1_result.txt; refused a second time)
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import math
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median

from .paths import DATA_DIR

REPO = "/home/user/shwoopnet"
SERIES = "KXGOLD15M"
RESULT = DATA_DIR / "mm1_result.txt"
TAPE = DATA_DIR / "mm1" / "tape.json"
NEEDED = 300
FLAT_S = 20             # cancel and flatten this many seconds before the close
LIVE_DELAY_S = 0.25     # our order is live one round trip after the posting poll (amendment 1)
MIN_LEAD_S = 120        # the posting poll must be at least this long before the close (amendment 9)
MIN_OK = 0.80           # ok polls / polls (amendment 9)
SIZES = (1, 10)
VERDICT_RATE, MAKER_RATE = 0.07, 0.0175
Z_BAR = 5.17
EPS = 5e-5              # prices are dollars on a deci-cent grid


# ---------------------------------------------------------------- fees

def order_fee(rate: float, q: float, p: float) -> float:
    """Kalshi's formula rate x C x p x (1-p), rounded UP to the cent per order (dollars)."""
    if q <= 0:
        return 0.0
    raw = rate * q * p * (1 - p) * 100
    return math.ceil(raw - 1e-9) / 100


# ---------------------------------------------------------------- one window

def simulate(quotes, trades, close, size=1, offset_s=0.0):
    """Replay one window. quotes: [(t_recv_s local, bid, ask, bid_size, ask_size)] (bid or ask may be None);
    trades: [(t_s exchange, yes_price, count, side)] with side -1 = taker sold YES (hits bids),
    +1 = taker bought YES (hits asks). Returns None if no two-sided quote was posted, else a dict of the
    fills and the gross pieces; fees are applied by `pnl`.
    Queue rule (amendment 2 to 4): join behind all displayed size; only trades at our price, a print
    through our price, or the opposite quote crossing our price can fill us; cancels never move us up."""
    q = sorted((t + offset_s, b, a, bs, as_) for t, b, a, bs, as_ in quotes)
    flat_t = close - FLAT_S
    post = next((x for x in q if x[1] is not None and x[2] is not None and 0 < x[1] < x[2] < 1), None)
    if post is None:
        return None
    t0, b0, a0, qb, qa = post
    qb, qa = qb or 0.0, qa or 0.0
    live = t0 + LIVE_DELAY_S
    fb = fs = 0.0           # contracts filled on our buy and our sell
    cb = ca = 0.0           # taker volume at our price since we went live
    ev = [(t, 0, (p, n, s)) for t, p, n, s in trades if live <= t <= flat_t]
    ev += [(x[0], 1, x) for x in q if live <= x[0] <= flat_t]
    for t, kind, x in sorted(ev, key=lambda e: (e[0], e[1])):
        if kind == 0:
            p, n, s = x
            if s == -1:
                if abs(p - b0) < EPS:
                    cb += n
                    fb = max(fb, min(size, max(0.0, cb - qb)))
                elif p < b0 - EPS:
                    fb = size
            elif s == 1:
                if abs(p - a0) < EPS:
                    ca += n
                    fs = max(fs, min(size, max(0.0, ca - qa)))
                elif p > a0 + EPS:
                    fs = size
        else:
            _, b, a, _, _ = x
            if a is not None and a <= b0 + EPS:
                fb = size
            if b is not None and b >= a0 - EPS:
                fs = size
    last = [x for x in q if x[0] <= flat_t]
    lb = last[-1][1] if last else None
    la = last[-1][2] if last else None
    inv = fb - fs
    m = min(fb, fs)
    spread = m * (a0 - b0)
    if inv > 0:
        fp = lb if lb is not None else 0.0      # amendment 6: missing side = worst case
        flat = inv * (fp - b0)
    elif inv < 0:
        fp = la if la is not None else 1.0
        flat = -inv * (a0 - fp)
    else:
        fp, flat = None, 0.0
    return {"b0": b0, "a0": a0, "qb": qb, "qa": qa, "fb": fb, "fs": fs, "inv": inv, "flat_price": fp,
            "spread": spread, "flat": flat, "gross": spread + flat, "trades": sum(1 for e in ev if e[1] == 0)}


def pnl(w, maker_rate, mult=1.0):
    """Window P/L in dollars: maker fills at maker_rate, the flatten crossing at the taker rate, each order
    rounded up to the cent; mult scales every fee (the x1.2 stress)."""
    f = order_fee(maker_rate, w["fb"], w["b0"]) + order_fee(maker_rate, w["fs"], w["a0"])
    if w["inv"]:
        f += order_fee(VERDICT_RATE, abs(w["inv"]), w["flat_price"])
    return w["gross"] - mult * f


# ---------------------------------------------------------------- statistics

def pf(xs):
    w = sum(x for x in xs if x > 0)
    lo = -sum(x for x in xs if x < 0)
    return w / lo if lo else (float("inf") if w else 0.0)


def clustered_z(vals, keys):
    n = len(vals)
    if n < 2:
        return 0.0
    mu = sum(vals) / n
    by = defaultdict(float)
    for v, k in zip(vals, keys):
        by[k] += v - mu
    var = sum(s * s for s in by.values()) / (n * n)
    return mu / math.sqrt(var) if var > 0 else 0.0


def central_date(close):
    # US Central: CDT (UTC-5) until 2026-11-01 07:00 UTC, CST (UTC-6) after
    off = 5 if close < datetime(2026, 11, 1, 7, tzinfo=timezone.utc).timestamp() else 6
    return (datetime.fromtimestamp(close, timezone.utc) - timedelta(hours=off)).date().isoformat()


def summarise(rows, maker_rate, mult=1.0):
    """rows: [(close, window dict)] in time order. Returns the figures the verdict reads."""
    rows = sorted(rows, key=lambda r: r[0])
    v = [pnl(w, maker_rate, mult) for _, w in rows]
    n = len(v)
    thirds = [v[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    halves = [v[:n // 2], v[n // 2:]]
    spread = sum(w["spread"] for _, w in rows)
    flat_loss = -sum(min(0.0, w["flat"]) for _, w in rows)
    return {"n": n, "pf": pf(v), "thirds": [pf(t) for t in thirds], "halves": [pf(h) for h in halves],
            "net": sum(v), "per": (sum(v) / n if n else 0.0), "loss_rate": (sum(1 for x in v if x < 0) / n if n else 0.0),
            "z": clustered_z(v, [central_date(c) for c, _ in rows]), "spread": spread, "flat_loss": flat_loss}


def passes(s, stress):
    return (s["n"] >= NEEDED and s["pf"] >= 1.5 and all(t >= 1.5 for t in s["thirds"]) and all(h > 1 for h in s["halves"])
            and s["per"] > 0 and stress["pf"] > 1 and s["flat_loss"] < 0.5 * s["spread"] and s["z"] >= Z_BAR)


# ---------------------------------------------------------------- recorder data

def _git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True).stdout


def _csv(path):
    raw = _git("show", f"origin/quote-data:{path}")
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


def runs():
    _git("fetch", "-q", "origin", "quote-data")
    files = _git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split()
    return sorted({f.rsplit("/", 1)[0] for f in files if f.startswith("quotes/") and f.endswith("quotes.csv.gz")})


def windows():
    """{ticker: (close_ts, run, coverage row)} for gold windows, from coverage files only."""
    out = {}
    for r in runs():
        for row in _csv(f"{r}/coverage.csv.gz"):
            if row["ticker"].startswith(SERIES + "-"):
                close = int(datetime.fromisoformat(row["window_close_utc"].replace("Z", "+00:00")).timestamp())
                out[row["ticker"]] = (close, r, row)
    return out


def usable_by_coverage(close, row):
    polls, ok = int(row["polls"] or 0), int(row["ok_polls"] or 0)
    first = int(row["first_recv_ms"] or 0) / 1000
    last = int(row["last_recv_ms"] or 0) / 1000
    return polls > 0 and ok / polls >= MIN_OK and first and first <= close - MIN_LEAD_S and last >= close - FLAT_S - 5


def count():
    ws = windows()
    use = [t for t, (c, _, row) in ws.items() if usable_by_coverage(c, row)]
    closes = sorted(c for c, _, _ in ws.values())
    span = f", closes {datetime.fromtimestamp(closes[0], timezone.utc):%Y-%m-%d %H:%M} to {datetime.fromtimestamp(closes[-1], timezone.utc):%Y-%m-%d %H:%M} UTC" if closes else ""
    line = f"MM1 count: {len(ws)} recorded gold windows, {len(use)} usable by coverage ({NEEDED} needed){span}"
    print(line)
    return len(ws), len(use)


def fetch_tape(tickers_close):
    from . import api
    TAPE.parent.mkdir(parents=True, exist_ok=True)
    have = json.loads(TAPE.read_text()) if TAPE.exists() else {}
    for i, (tk, close) in enumerate(sorted(tickers_close.items())):
        if tk in have:
            continue
        cur, rows = None, []
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": close - 170, "max_ts": close}
            if cur:
                p["cursor"] = cur
            d = api._get("/markets/trades", p)
            for t in d.get("trades", []):
                side = 1 if t["taker_outcome_side"] == "yes" else -1
                rows.append((datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp(),
                             float(t["yes_price_dollars"]), float(t["count_fp"]), side))
            cur = d.get("cursor")
            if not cur or not d.get("trades"):
                break
            time.sleep(0.5)
        have[tk] = rows
        if i % 20 == 0:
            TAPE.write_text(json.dumps(have))
        time.sleep(0.5)
    TAPE.write_text(json.dumps(have))
    return have


def _num(x):
    return float(x) if x not in (None, "") else None


def run():
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists.")
        return
    ws = windows()
    use = {t: v for t, v in ws.items() if usable_by_coverage(v[0], v[2])}
    if len(use) < NEEDED:
        print(f"Refusing: {len(use)} usable gold windows, {NEEDED} needed.")
        return
    tape = fetch_tape({t: v[0] for t, v in use.items()})
    byrun = defaultdict(list)
    for t, (c, r, _) in use.items():
        byrun[r].append(t)
    rows, no_post, no_trades = [], 0, 0
    sims = {C: [] for C in SIZES}
    for r, tks in sorted(byrun.items()):
        offs = [float(x["offset_ms"]) for x in _csv(f"{r}/clock.csv.gz") if x.get("offset_ms") not in (None, "")]
        off = median(offs) / 1000 if offs else 0.0
        qs = defaultdict(list)
        want = set(tks)
        for x in _csv(f"{r}/quotes.csv.gz"):
            if x["ticker"] in want:
                qs[x["ticker"]].append((int(x["t_recv_ms"]) / 1000, _num(x["yes_bid"]), _num(x["yes_ask"]), _num(x["bid_size"]), _num(x["ask_size"])))
        for tk in tks:
            close = use[tk][0]
            q = [x for x in qs.get(tk, []) if close - 155 <= x[0] + off <= close]
            # amendment 9: the posting poll must be at least MIN_LEAD_S before the close
            first2 = next((x for x in sorted(q) if x[1] is not None and x[2] is not None and 0 < x[1] < x[2] < 1), None)
            if first2 is None or first2[0] + off > close - MIN_LEAD_S:
                no_post += 1
                continue
            tr = tape.get(tk, [])
            if not tr:
                no_trades += 1
            for C in SIZES:
                w = simulate(q, tr, close, C, off)
                if w is not None:
                    w["has_trades"] = bool(tr)
                    sims[C].append((close, w))
    lines = []
    posted = len(sims[1])
    verdict_ok = posted >= NEEDED
    all_pass = True
    for C in SIZES:
        for label, rate, mult in (("VERDICT maker fee = taker 7%", VERDICT_RATE, 1.0), ("stress 7% x1.2", VERDICT_RATE, 1.2),
                                  ("info maker 1.75%", MAKER_RATE, 1.0), ("info zero maker fee", 0.0, 1.0)):
            s = summarise(sims[C], rate, mult)
            lines.append(f"C={C:>2} {label}: windows {s['n']}, PF {s['pf']:.2f} (thirds {' / '.join(f'{t:.2f}' for t in s['thirds'])}; "
                         f"halves {' / '.join(f'{h:.2f}' for h in s['halves'])}), loss rate {100 * s['loss_rate']:.0f}%, "
                         f"net {100 * s['per']:+.3f}c per window, total ${s['net']:+.2f}, z {s['z']:+.2f}, spread earned ${s['spread']:.2f}, flatten loss ${s['flat_loss']:.2f}")
        s = summarise(sims[C], VERDICT_RATE)
        all_pass &= passes(s, summarise(sims[C], VERDICT_RATE, 1.2))
        ex = [r for r in sims[C] if r[1]["has_trades"]]
        se = summarise(ex, VERDICT_RATE)
        lines.append(f"C={C:>2} verdict fee, windows with no trades excluded: windows {se['n']}, PF {se['pf']:.2f}, net {100 * se['per']:+.3f}c per window")
        ws1 = [w for _, w in sims[C]]
        lines.append(f"C={C:>2} fills: buy filled (any) {sum(1 for w in ws1 if w['fb'] > 0)}, sell filled {sum(1 for w in ws1 if w['fs'] > 0)}, "
                     f"cycles {sum(1 for w in ws1 if w['fb'] > 0 and w['fs'] > 0)}, flattened {sum(1 for w in ws1 if w['inv'] != 0)}")
    verdict = "NOT_ENOUGH_DATA" if not verdict_ok else ("NOT_YET_FALSIFIED" if all_pass else "FALSIFIED")
    lines.insert(0, f"MM1 {verdict} (usable windows {len(use)}, posted {posted}, no two-sided post {no_post}, no trades {no_trades}; "
                    f"minimum {NEEDED} posted; z bar {Z_BAR}; tries 6)")
    RESULT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv):
    if len(argv) < 2 or argv[1] not in ("count", "run"):
        print(__doc__)
        return
    count() if argv[1] == "count" else run()


if __name__ == "__main__":
    main(sys.argv)
