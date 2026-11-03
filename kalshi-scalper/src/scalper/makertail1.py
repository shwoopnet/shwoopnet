"""MAKERTAIL1 (workers/MAKERTAIL1_REGISTRATION.md): a resting 1 contract buy at the best bid (1c to 15c) of the
far-tail strikes of the hourly Bitcoin ladder (KXBTCD), 25 minutes before the close, held to settlement, scored with the
recorded queue and tape. Research only; nothing here means trade; there is no promote verb.
    python -m scalper.makertail1 count   (events and orders by coverage and book prices; no outcome is read)
    python -m scalper.makertail1 run     (scores DEV once; the holdout only if DEV passes; writes data/makertail1_result.txt)
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
"""
from __future__ import annotations

import csv
import gzip
import io
import math
import sqlite3
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from .mm1 import central_date, clustered_z, pf
from .paths import DATA_DIR

REPO = "/home/user/shwoopnet"
SERIES = "KXBTCD"
RESULT = DATA_DIR / "makertail1_result.txt"
LOOK_S, LOOK_MAX_AGE_S, LIVE_DELAY_S, CANCEL_S = 1500, 20.0, 1.0, 60
BAND = (0.01, 0.15)
TAPE_GAP_S = 90.0
TAKER_C, TAKER_RATE = 10, 0.07
NEEDED = 150
Z_BAR = 5.27


def ts(y, mo, d, h=0):
    return datetime(y, mo, d, h, tzinfo=timezone.utc).timestamp()


DEV_FROM, DEV_TO = ts(2026, 10, 29), ts(2026, 11, 2)          # closes in [DEV_FROM, DEV_TO)
HOLD_FROM, HOLD_TO = ts(2026, 11, 2), ts(2026, 11, 3, 16)      # closes in [HOLD_FROM, HOLD_TO)
FWD_FROM = ts(2026, 11, 3, 16)


class Poll:
    __slots__ = ("t", "yp", "ys", "np", "ns")

    def __init__(self, t, yp, ys, np_, ns):
        self.t, self.yp, self.ys, self.np, self.ns = t, yp, ys, np_, ns


class Order:
    def __init__(self, ticker, close, side, price, q0, look_t, ask, ask_size):
        self.ticker, self.close, self.side, self.price, self.q0 = ticker, close, side, price, q0
        self.look_t, self.ask, self.ask_size = look_t, ask, ask_size
        self.won = None
        self.gap = False
        self.fill = {}          # bound -> bool


def best(px, sz):
    return (px[0], sz[0]) if px else (None, None)


def make_orders(ticker, close, polls):
    """polls: [Poll] time ordered (exchange seconds). Orders at the look poll; [] when there is no usable look or no tail bid."""
    target = close - LOOK_S
    look = None
    for p in polls:
        if p.t <= target:
            look = p
        else:
            break
    if look is None or target - look.t > LOOK_MAX_AGE_S:
        return []
    live = look.t + LIVE_DELAY_S
    fillp = next((p for p in polls if p.t >= live and p.t - live <= LOOK_MAX_AGE_S), None)
    out = []
    for side, px, sz, opx, osz in (("yes", look.yp, look.ys, look.np, look.ns), ("no", look.np, look.ns, look.yp, look.ys)):
        b, q = best(px, sz)
        if b is None or not (BAND[0] - 1e-9 <= b <= BAND[1] + 1e-9):
            continue
        ask = ask_size = None
        if fillp is not None:
            fp, fs = (fillp.np, fillp.ns) if side == "yes" else (fillp.yp, fillp.ys)
            if fp:
                ask, ask_size = round(1 - fp[0], 4), fs[0]
        out.append(Order(ticker, close, side, b, q, look.t, ask, ask_size))
    return out


def filled(order, trades, bound, poll_times=None):
    """trades: [(t, yes_price, count, taker_side)]. bound: 'pess' (queue never cancels), 'opt' (queue all cancels), 'mid' (half)."""
    t0, t1 = order.look_t + LIVE_DELAY_S, order.close - CANCEL_S
    ahead = {"pess": order.q0, "opt": 0.0, "mid": order.q0 / 2}[bound]
    if bound != "opt" and order.gap:
        return False                       # registered: a tape gap counts as not filled (pess, mid); opt excludes it elsewhere
    cum = 0.0
    for t, yp, c, side in sorted(trades):
        if t <= t0 or t > t1:
            continue
        if order.side == "yes":
            if side != "no":
                continue
            px = yp
        else:
            if side != "yes":
                continue
            px = 1 - yp                    # the NO price the taker's counterparty (our bid) pays
        if px < order.price - 1e-9:
            return True                    # through our price: our level was cleared
        if abs(px - order.price) < 1e-9:
            cum += c
            if cum > ahead + 1e-9 or (bound == "opt"):
                return True
    return False


def tape_gap(order, poll_times):
    """True when the recorded tape polls have a hole longer than TAPE_GAP_S inside the order's life, or none cover it."""
    t0, t1 = order.look_t + LIVE_DELAY_S, order.close - CANCEL_S
    pts = [t for t in poll_times if t0 - TAPE_GAP_S <= t <= t1 + TAPE_GAP_S]
    if not pts:
        return True
    pts = sorted(pts)
    if pts[0] - t0 > TAPE_GAP_S or t1 - pts[-1] > TAPE_GAP_S:
        return True
    return any(b - a > TAPE_GAP_S for a, b in zip(pts, pts[1:]))


def taker_fee_per_contract(p):
    cents = math.ceil(TAKER_RATE * TAKER_C * p * (1 - p) * 100 - 1e-9)
    return cents / 100 / TAKER_C


def summarise(orders, bound, mult=1.0):
    """Per resting order (unfilled = 0) and per fill, cents per contract. Maker fee 0."""
    rows = [o for o in orders if o.won is not None and not (bound == "opt" and o.gap)]
    fl = [o for o in rows if o.fill.get(bound)]
    nets = [(100 * ((1 if o.won else 0) - o.price)) for o in fl]
    per_order = [(100 * ((1 if o.won else 0) - o.price)) if o.fill.get(bound) else 0.0 for o in rows]
    keys = [central_date(o.close) for o in rows]
    return {"orders": len(rows), "fills": len(fl), "fill_rate": len(fl) / len(rows) if rows else 0.0,
            "win": sum(1 for o in fl if o.won) / len(fl) if fl else 0.0,
            "price": sum(o.price for o in fl) / len(fl) if fl else 0.0,
            "per_order": sum(per_order) / len(per_order) if per_order else 0.0,
            "per_fill": sum(nets) / len(nets) if nets else 0.0,
            "pf": pf(nets), "z": clustered_z(per_order, keys) if per_order else 0.0,
            "gap": sum(1 for o in orders if o.gap)}


def taker_summary(orders, mult=1.0):
    rows = [o for o in orders if o.won is not None and o.ask is not None and (o.ask_size or 0) >= 10]
    nets = [100 * ((1 if o.won else 0) - o.ask - mult * taker_fee_per_contract(o.ask)) for o in rows]
    return {"orders": len(rows), "per_order": sum(nets) / len(nets) if nets else 0.0, "pf": pf(nets),
            "win": sum(1 for o in rows if o.won) / len(rows) if rows else 0.0,
            "price": sum(o.ask for o in rows) / len(rows) if rows else 0.0}


def verdict(dev_pess, h1, h2):
    if dev_pess["fills"] < NEEDED:
        return "NOT_ENOUGH_DATA"
    ok = dev_pess["per_order"] > 0 and dev_pess["pf"] >= 1.5 and h1["per_order"] > 0 and h2["per_order"] > 0
    return "NOT_YET_FALSIFIED" if ok else "FALSIFIED"


# ---------------------------------------------------------------- recorder data (history of origin/quote-data)

def _git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True).stdout


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _levels(row, kind):
    pxs = [num(row.get(f"{kind}_px_{i}")) for i in range(1, 6)]
    szs = [num(row.get(f"{kind}_sz_{i}")) for i in range(1, 6)]
    pairs = [(p, s) for p, s in zip(pxs, szs) if p is not None and s is not None]
    return [p for p, _ in pairs], [s for _, s in pairs]


def book_files():
    """[(commit, path)] for every book/ file ever added to the branch (the tip carries only the newest runs)."""
    _git("fetch", "-q", "origin", "quote-data")
    out = _git("log", "origin/quote-data", "--diff-filter=A", "--name-only", "--format=C %H", "--", "book/").decode().splitlines()
    res, c = [], None
    for ln in out:
        if ln.startswith("C "):
            c = ln[2:]
        elif ln.strip():
            res.append((c, ln.strip()))
    return res


def _csv(commit, path):
    raw = _git("show", f"{commit}:{path}")
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


_CACHE = []


def load():
    if _CACHE:
        return _CACHE[0]
    _CACHE.append(_load())
    return _CACHE[0]


def _load():
    """Returns (polls {ticker: [Poll]}, close {ticker: ts}, trades {ticker: [(t, yp, count, side)]}, tape_polls {ticker or '*': [t]})."""
    polls, closes, trades, seen, seenp, tpolls = defaultdict(list), {}, defaultdict(list), set(), set(), set()
    for commit, path in book_files():
        if path.endswith("/book.csv.gz"):
            for r in _csv(commit, path):
                key = (r["ticker"], r["poll_ts_local_ms"])
                if key in seenp or not r["server_date_header"]:
                    continue
                seenp.add(key)
                try:
                    t = parsedate_to_datetime(r["server_date_header"]).timestamp()
                except Exception:
                    continue
                yp, ys = _levels(r, "yes_bid")
                np_, ns = _levels(r, "no_bid")
                polls[r["ticker"]].append(Poll(t, yp, ys, np_, ns))
                closes[r["ticker"]] = parse_iso(r["close_time"])
        elif path.endswith("/trades.csv.gz"):
            for r in _csv(commit, path):
                tpolls.add(int(r["poll_ts_local_ms"]) / 1000)
                if r["trade_id"] in seen:
                    continue
                seen.add(r["trade_id"])
                trades[r["ticker"]].append((parse_iso(r["created_time"]), float(r["yes_price_dollars"]), float(r["count_fp"]), r["taker_outcome_side"]))
    for v in polls.values():
        v.sort(key=lambda p: p.t)
    return polls, closes, trades, sorted(tpolls)


def results():
    c = sqlite3.connect(str(DATA_DIR / "conf2_lad.sqlite"))
    return {t: r for t, r in c.execute("select ticker, result from market where series=?", (SERIES,))}


def build(span, with_outcome):
    polls, closes, trades, tpolls = load()
    res = results() if with_outcome else {}
    orders = []
    for tk, cl in closes.items():
        if not (span[0] <= cl < span[1]):
            continue
        for o in make_orders(tk, cl, polls[tk]):
            o.gap = tape_gap(o, tpolls)
            if with_outcome:
                r = res.get(tk)
                o.won = None if r not in ("yes", "no") else (r == o.side)
                for b in ("pess", "opt", "mid"):
                    o.fill[b] = filled(o, trades.get(tk, []), b)
            orders.append(o)
    return orders


def count():
    for name, span in (("DEV", (DEV_FROM, DEV_TO)), ("HOLDOUT", (HOLD_FROM, HOLD_TO)), ("FORWARD", (FWD_FROM, 4e9))):
        o = build(span, False)
        days = (len({o_.close for o_ in o}))
        print(name, "orders", len(o), "events with an order", days, "yes", sum(1 for x in o if x.side == "yes"), "no", sum(1 for x in o if x.side == "no"))


def fmt(s):
    return ("orders %d fills %d fill %.1f%% win %.1f%% at mean price %.1f%% per order %+.2fc per fill %+.2fc PF %.2f z %.2f gap-orders %d"
            % (s["orders"], s["fills"], 100 * s["fill_rate"], 100 * s["win"], 100 * s["price"], s["per_order"], s["per_fill"], s["pf"], s["z"], s["gap"]))


def buckets(orders, bound):
    out = []
    for lo, hi in ((0.01, 0.04), (0.05, 0.09), (0.10, 0.15)):
        sub = [o for o in orders if lo - 1e-9 <= o.price <= hi + 1e-9]
        s = summarise(sub, bound)
        out.append("  bid %2d-%2dc: %s" % (round(lo * 100), round(hi * 100), fmt(s)))
    return out


def run():
    if RESULT.exists():
        sys.exit("refused: MAKERTAIL1 DEV was already scored once (data/makertail1_result.txt)")
    dev = build((DEV_FROM, DEV_TO), True)
    mid_t = sorted({o.close for o in dev})
    cut = mid_t[len(mid_t) // 2] if mid_t else 0
    h1, h2 = [o for o in dev if o.close < cut], [o for o in dev if o.close >= cut]
    lines = ["MAKERTAIL1 DEV (closes 2026-10-29 to 2026-11-01), %d orders, %d without a result" % (len(dev), sum(1 for o in dev if o.won is None))]
    S = {b: summarise(dev, b) for b in ("pess", "opt", "mid")}
    for b in ("pess", "opt", "mid"):
        lines.append("%s: %s" % (b, fmt(S[b])))
    lines.append("pess halves: H1 " + fmt(summarise(h1, "pess")))
    lines.append("            H2 " + fmt(summarise(h2, "pess")))
    for side in ("yes", "no"):
        lines.append("pess %s side: %s" % (side, fmt(summarise([o for o in dev if o.side == side], "pess"))))
    lines.append("pess by bid price:")
    lines += buckets(dev, "pess")
    lines.append("opt by bid price:")
    lines += buckets(dev, "opt")
    for m in (1.0, 1.2):
        t = taker_summary(dev, m)
        lines.append("taker at the ask (fee x%.1f, size>=10): orders %d win %.1f%% at mean ask %.1f%% per order %+.2fc PF %.2f" % (m, t["orders"], 100 * t["win"], 100 * t["price"], t["per_order"], t["pf"]))
    v = verdict(S["pess"], summarise(h1, "pess"), summarise(h2, "pess"))
    lines.append("VERDICT (pessimistic bound): " + v)
    days = max(1, len({central_date(o.close) for o in dev}))
    lines.append("pessimistic fills per day %.1f; days to %d fills %.0f" % (S["pess"]["fills"] / days, NEEDED, NEEDED / max(S["pess"]["fills"] / days, 1e-9)))
    if v == "NOT_YET_FALSIFIED":
        ho = build((HOLD_FROM, HOLD_TO), True)
        lines.append("HOLDOUT pess: " + fmt(summarise(ho, "pess")))
    else:
        lines.append("HOLDOUT not opened (DEV did not pass)")
    RESULT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv):
    if len(argv) > 1 and argv[1] == "count":
        count()
    elif len(argv) > 1 and argv[1] == "run":
        run()
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
