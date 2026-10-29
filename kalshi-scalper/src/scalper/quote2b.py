"""QUOTE2B (workers/Q2B_REGISTRATION.md): resting two-sided quotes on the Bitcoin hourly ladder (KXBTCD), the
book recorder's strikes, 50 to 10 minutes before each hourly close, with a real queue model from recorded depth
and the recorded tape; flattened by crossing at T-10 min, never held to settlement. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade.
    python -m scalper.quote2b count   (files and usable hourly closes from coverage only; no book or trade row is read)
    python -m scalper.quote2b run     (refused before 2026-11-12 00:00 UTC, below 300 usable closes, or a second time;
                                       scores once and writes data/quote2b_result.txt)

Scorer reading of the registration, fixed before any recorded row was read: minute boundaries T-50..T-11 manage
the book (cancel and convert to closing orders), but new pairs are posted only at boundaries T-50..T-15; a posting
poll must be within 30 s after its boundary; a stop executes at the strike's next poll after the triggering one.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from statistics import median

from .mm1 import central_date, clustered_z, order_fee, pf
from .paths import DATA_DIR

REPO = "/home/user/shwoopnet"
SERIES = "KXBTCD"
RESULT = DATA_DIR / "quote2b_result.txt"
TAPE = DATA_DIR / "quote2b" / "refetch.json"
READ_NOT_BEFORE = datetime(2026, 11, 12, tzinfo=timezone.utc).timestamp()
NEEDED = 300
POST_FROM, POST_TO, MANAGE_TO, FLAT_AT = 50 * 60, 15 * 60, 11 * 60, 10 * 60   # seconds before the close
LIVE_DELAY_S = 1.0          # the Date header has 1 s resolution
POST_GAP_S = 30.0           # the posting poll must be this close after its boundary
MID_LO, MID_HI = 0.20, 0.80
MAX_ACTIVE = 3
STOP = 0.05
SIZES = (1, 10)
TAKER, MAKER = 0.07, 0.0175
Z_BAR = 5.17
EPS = 5e-5
TRUNC_ROWS = 500            # amendment: re-fetch a strike-hour's tape if one recorded read held this many rows
MIN_STRIKES, MIN_OK = 3, 0.80


# ---------------------------------------------------------------- one hour

class Poll:
    __slots__ = ("t", "yb", "ybs", "nb", "nbs")

    def __init__(self, t, yb, ybs, nb, nbs):
        self.t, self.yb, self.ybs, self.nb, self.nbs = t, list(yb), list(ybs), list(nb), list(nbs)

    @property
    def bid(self):
        return self.yb[0] if self.yb else None

    @property
    def ask(self):
        return 1 - self.nb[0] if self.nb else None

    @property
    def mid(self):
        b, a = self.bid, self.ask
        return (b + a) / 2 if b is not None and a is not None else None

    def walk(self, sell, q):
        """Cross for q contracts: sell into the YES bids or buy from the YES asks (1 - NO bids), best first.
        Returns ([(price, qty)], qty beyond the 5 recorded levels). Beyond-depth size is priced at the last level;
        an empty side is priced at the worst case (0 for a sale, 1 for a purchase)."""
        lv = list(zip(self.yb, self.ybs)) if sell else [(1 - p, s) for p, s in zip(self.nb, self.nbs)]
        legs, left = [], q
        for p, s in lv:
            if left <= 0:
                break
            take = min(left, s)
            if take > 0:
                legs.append((p, take))
                left -= take
        beyond = left
        if left > 0:
            legs.append((lv[-1][0] if lv else (0.0 if sell else 1.0), left))
        return legs, beyond


class Pair:
    """One posted pair on one strike: a buy at b and a sell at a, C each, behind qb / qa displayed size."""

    def __init__(self, strike, t_post, b, a, qb, qa, size):
        self.strike, self.b, self.a, self.qb, self.qa = strike, b, a, qb, qa
        self.live = t_post + LIVE_DELAY_S
        self.cap_b = self.cap_a = size
        self.cb = self.ca = 0.0
        self.fb = self.fs = 0.0
        self.buy_on = self.sell_on = True
        self.taker = []          # [(price, qty, sell)] crossing legs
        self.beyond = 0.0
        self.end = None          # "cycle", "stop", "flatten", "none"
        self.fills = []          # [(t, side, qty, price)]; side +1 our buy, -1 our sell

    @property
    def inv(self):
        return self.fb - self.fs

    def _fill(self, t, side, new):
        old = self.fb if side == 1 else self.fs
        new = min(new, self.cap_b if side == 1 else self.cap_a)
        if new > old + 1e-12:
            self.fills.append((t, side, new - old, self.b if side == 1 else self.a))
            if side == 1:
                self.fb = new
            else:
                self.fs = new

    def trade(self, t, p, n, s):
        if t < self.live:
            return
        if s == -1 and self.buy_on:            # a taker selling YES hits resting YES bids
            if abs(p - self.b) < EPS:
                self.cb += n
                self._fill(t, 1, max(self.fb, self.cb - self.qb))
            elif p < self.b - EPS:
                self._fill(t, 1, self.cap_b)
        elif s == 1 and self.sell_on:          # a taker buying YES hits resting NO bids (our YES sell)
            if abs(p - self.a) < EPS:
                self.ca += n
                self._fill(t, -1, max(self.fs, self.ca - self.qa))
            elif p > self.a + EPS:
                self._fill(t, -1, self.cap_a)

    def quote(self, poll):
        """A recorded opposite quote at or through our price: the level was cleared, so the remainder fills."""
        if poll.t < self.live:
            return
        if self.buy_on and poll.ask is not None and poll.ask <= self.b + EPS:
            self._fill(poll.t, 1, self.cap_b)
        if self.sell_on and poll.bid is not None and poll.bid >= self.a - EPS:
            self._fill(poll.t, -1, self.cap_a)

    def stop_hit(self, poll):
        m, i = poll.mid, self.inv
        if m is None or abs(i) < 1e-12:
            return False
        return (i > 0 and m <= self.b - STOP + EPS) or (i < 0 and m >= self.a + STOP - EPS)

    def to_closing(self):
        """Net inventory at a boundary: cancel the side that filled more; the other closes exactly the net."""
        if self.inv > 0:
            self.buy_on, self.cap_a = False, self.fb
        elif self.inv < 0:
            self.sell_on, self.cap_b = False, self.fs

    def cross(self, poll, why):
        i = self.inv
        self.buy_on = self.sell_on = False
        if abs(i) > 1e-12:
            legs, beyond = poll.walk(i > 0, abs(i))
            self.taker += [(p, q, i > 0) for p, q in legs]
            self.beyond += beyond
            if i > 0:
                self.fs += abs(i)
            else:
                self.fb += abs(i)
        self.end = why

    # P/L pieces
    def matched(self):
        mk = min(self.fb - sum(q for _, q, sl in self.taker if not sl), self.fs - sum(q for _, q, sl in self.taker if sl))
        return max(0.0, mk)

    def gross(self):
        mb = self.fb - sum(q for _, q, sl in self.taker if not sl)
        ms = self.fs - sum(q for _, q, sl in self.taker if sl)
        cash = -mb * self.b + ms * self.a
        cash += sum((p * q if sl else -p * q) for p, q, sl in self.taker)
        return cash

    def spread(self):
        return self.matched() * (self.a - self.b)

    def fees(self, maker_rate):
        mb = self.fb - sum(q for _, q, sl in self.taker if not sl)
        ms = self.fs - sum(q for _, q, sl in self.taker if sl)
        f = order_fee(maker_rate, mb, self.b) + order_fee(maker_rate, ms, self.a)
        if self.taker:
            raw = sum(TAKER * q * p * (1 - p) for p, q, _ in self.taker) * 100
            f += _ceil_cent(raw)
        return f


def _ceil_cent(raw_cents):
    import math
    return math.ceil(raw_cents - 1e-9) / 100 if raw_cents > 0 else 0.0


def simulate_hour(strikes, close, size=1):
    """strikes: {strike: (polls [Poll] in exchange time, trades [(t, yes_price, count, side)])} for one close.
    side -1 = taker sold YES ("no"), +1 = taker bought YES ("yes"). Returns {"pairs": [...], "trades": n,
    "polls": {strike: [Poll]}}. Pure: no I/O."""
    ev = {}
    for k, (polls, trades) in strikes.items():
        e = [(t, 0, (p, n, s)) for t, p, n, s in trades] + [(p.t, 1, p) for p in polls]
        e.sort(key=lambda x: (x[0], x[1]))
        ev[k] = e
    ptr = {k: 0 for k in strikes}
    pairs, open_ = [], {}           # open_: strike -> Pair
    stopped, pending_stop = set(), set()
    n_trades = sum(len(tr) for _, tr in strikes.values())

    def advance(until):
        for k, e in ev.items():
            i = ptr[k]
            while i < len(e) and e[i][0] <= until:
                t, kind, x = e[i]
                pr = open_.get(k)
                if pr is not None:
                    if kind == 0:
                        pr.trade(t, *x)
                    else:
                        if k in pending_stop:
                            pr.cross(x, "stop")
                            pending_stop.discard(k)
                            stopped.add(k)
                            del open_[k]
                        else:
                            pr.quote(x)
                            if pr.stop_hit(x):
                                pending_stop.add(k)
                i += 1
            ptr[k] = i

    def first_poll_after(k, t, within=None):
        for p in strikes[k][0]:
            if p.t >= t:
                return p if within is None or p.t <= t + within else None
        return None

    b = close - POST_FROM
    while b <= close - MANAGE_TO:
        advance(b)
        for k, pr in list(open_.items()):
            if k in pending_stop:
                continue
            if abs(pr.inv) < 1e-12:
                pr.buy_on = pr.sell_on = False
                pr.end = "cycle" if pr.fb > 0 else "none"
                del open_[k]
            else:
                pr.to_closing()
        if b <= close - POST_TO:
            slots = MAX_ACTIVE - len(open_)
            cands = []
            for k in strikes:
                if k in open_ or k in stopped or slots <= 0:
                    continue
                p = first_poll_after(k, b, POST_GAP_S)
                if p is None or p.bid is None or p.ask is None or not (p.bid < p.ask - EPS):
                    continue
                if not (MID_LO <= p.mid <= MID_HI):
                    continue
                cands.append((abs(p.mid - 0.5), k, p))
            for _, k, p in sorted(cands, key=lambda c: (c[0], c[1]))[:max(0, slots)]:
                pr = Pair(k, p.t, p.bid, p.ask, p.ybs[0], p.nbs[0], size)
                open_[k] = pr
                pairs.append(pr)
        b += 60
    advance(close - FLAT_AT)
    for k, pr in list(open_.items()):
        if abs(pr.inv) < 1e-12:
            pr.buy_on = pr.sell_on = False
            pr.end = "cycle" if pr.fb > 0 else "none"
        else:
            p = first_poll_after(k, close - FLAT_AT)
            if p is None:
                p = Poll(close - FLAT_AT, [], [], [], [])     # no quote at all: worst case
            pr.cross(p, "stop" if k in pending_stop else "flatten")
        del open_[k]
    return {"pairs": pairs, "trades": n_trades, "polls": {k: v[0] for k, v in strikes.items()}}


def hour_pnl(h, maker_rate, mult=1.0):
    return sum(p.gross() - mult * p.fees(maker_rate) for p in h["pairs"])


def markouts(h, horizon):
    """[(signed move in dollars per contract, qty)] at `horizon` seconds after each maker fill; + = our way."""
    out = []
    for pr in h["pairs"]:
        polls = h["polls"][pr.strike]
        for t, side, q, px in pr.fills:
            p = next((x for x in polls if x.t >= t + horizon and x.mid is not None), None)
            if p is None or p.t > t + horizon + 60:
                continue
            out.append(((p.mid - px) if side == 1 else (px - p.mid), q))
    return out


# ---------------------------------------------------------------- statistics

def summarise(rows, maker_rate, mult=1.0):
    rows = sorted(rows, key=lambda r: r[0])
    v = [hour_pnl(h, maker_rate, mult) for _, h in rows]
    n = len(v)
    thirds = [v[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    halves = [v[:n // 2], v[n // 2:]]
    prs = [p for _, h in rows for p in h["pairs"]]
    spread = sum(p.spread() for p in prs)
    rest_loss = -sum(min(0.0, p.gross() - p.spread()) for p in prs)
    return {"n": n, "pf": pf(v), "thirds": [pf(t) for t in thirds], "halves": [pf(x) for x in halves],
            "net": sum(v), "per": sum(v) / n if n else 0.0, "loss_rate": sum(1 for x in v if x < 0) / n if n else 0.0,
            "z": clustered_z(v, [central_date(c) for c, _ in rows]), "spread": spread, "rest_loss": rest_loss,
            "pairs": len(prs), "fill_b": sum(1 for p in prs if p.fb - sum(q for _, q, s in p.taker if not s) > 0),
            "fill_s": sum(1 for p in prs if p.fs - sum(q for _, q, s in p.taker if s) > 0),
            "cycles": sum(1 for p in prs if p.end == "cycle"), "stops": sum(1 for p in prs if p.end == "stop"),
            "flattens": sum(1 for p in prs if p.end == "flatten"), "beyond": sum(p.beyond for p in prs),
            "fees": sum(mult * p.fees(maker_rate) for p in prs), "series": v}


def passes(s, stress):
    return (s["n"] >= NEEDED and s["pf"] >= 1.5 and all(t >= 1.5 for t in s["thirds"]) and all(h > 1 for h in s["halves"])
            and s["per"] > 0 and stress["net"] > 0 and stress["pf"] > 1.2 and s["rest_loss"] < 0.5 * s["spread"]
            and s["z"] >= Z_BAR)


def account(rows, maker_rate, start=500.0):
    rows = sorted(rows, key=lambda r: r[0])
    eq, peak, dd = start, start, 0.0
    day = defaultdict(float)
    for c, h in rows:
        x = hour_pnl(h, maker_rate)
        eq += x
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
        day[central_date(c)] += x
    return eq, dd, (min(day.values()) if day else 0.0)


def markout_line(rows, horizon):
    xs = [(c, m, q) for c, h in rows for m, q in markouts(h, horizon)]
    if not xs:
        return f"markout {horizon}s: no fills"
    tot = sum(q for _, _, q in xs)
    mean = sum(m * q for _, m, q in xs) / tot
    z = clustered_z([m for _, m, _ in xs], [central_date(c) for c, _, _ in xs])
    return f"markout {horizon}s: {len(xs)} fills, {tot:.0f} contracts, mean {100 * mean:+.2f}c per contract (our way +), z {z:+.2f}"


# ---------------------------------------------------------------- recorder data

def _git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True).stdout


def _csv(path):
    raw = _git("show", f"origin/quote-data:{path}")
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


def _ts(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def runs():
    _git("fetch", "-q", "origin", "quote-data")
    files = _git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split()
    return sorted({f.rsplit("/", 1)[0] for f in files if f.startswith("book/") and f.endswith("coverage.csv.gz")}), \
        sum(1 for f in files if f.startswith("book/"))


def closes():
    """{close_ts: (run, coverage row)} from coverage files only."""
    out = {}
    rs, _ = runs()
    for r in rs:
        for row in _csv(f"{r}/coverage.csv.gz"):
            out[int(_ts(row["close_time"]))] = (r, row)
    return out


def usable_by_coverage(close, row):
    polls, ok = int(row["polls"] or 0), int(row["ok_polls"] or 0)
    first, last = int(row["first_ms"] or 0) / 1000, int(row["last_ms"] or 0) / 1000
    return (int(row["tickers"] or 0) >= MIN_STRIKES and polls > 0 and ok / polls >= MIN_OK
            and 0 < first <= close - POST_FROM and last >= close - FLAT_AT + 30)


def ready_date(n_usable, last_close):
    need = max(0, NEEDED - n_usable)
    est = max(READ_NOT_BEFORE, (last_close or time.time()) + need * 3600)
    return datetime.fromtimestamp(est, timezone.utc)


def count():
    cs = closes()
    _, nfiles = runs()
    use = sorted(c for c, (_, row) in cs.items() if usable_by_coverage(c, row))
    last = max(cs) if cs else None
    span = (f", closes {datetime.fromtimestamp(min(cs), timezone.utc):%Y-%m-%d %H:%M} to "
            f"{datetime.fromtimestamp(last, timezone.utc):%Y-%m-%d %H:%M} UTC") if cs else ""
    print(f"QUOTE2B count: {nfiles} files, {len(cs)} recorded hourly closes, {len(use)} usable by coverage "
          f"({NEEDED} needed){span}; earliest read (no gaps from here) {ready_date(len(use), last):%Y-%m-%d %H:%M} UTC")
    return len(cs), len(use)


def _offset(rows):
    d = []
    for x in rows:
        h = x.get("server_date_header")
        if h:
            try:
                d.append(parsedate_to_datetime(h).timestamp() + 0.5 - int(x["poll_ts_local_ms"]) / 1000)
            except (TypeError, ValueError):
                pass
    return median(d) if d else None


def _f(x):
    return float(x) if x not in (None, "") else None


def _poll(x, off):
    lv = lambda pre: [(_f(x[f"{pre}_px_{i}"]), _f(x[f"{pre}_sz_{i}"])) for i in range(1, 6)]
    yb = [(p, s) for p, s in lv("yes_bid") if p is not None and s is not None]
    nb = [(p, s) for p, s in lv("no_bid") if p is not None and s is not None]
    return Poll(int(x["poll_ts_local_ms"]) / 1000 + off, [p for p, _ in yb], [s for _, s in yb], [p for p, _ in nb], [s for _, s in nb])


def refetch(ticker, close):
    from . import api
    TAPE.parent.mkdir(parents=True, exist_ok=True)
    have = json.loads(TAPE.read_text()) if TAPE.exists() else {}
    key = f"{ticker}@{close}"
    if key not in have:
        cur, rows = None, []
        while True:
            p = {"ticker": ticker, "limit": 1000, "min_ts": int(close - POST_FROM - 60), "max_ts": int(close - FLAT_AT + 60)}
            if cur:
                p["cursor"] = cur
            d = api._get("/markets/trades", p)
            for t in d.get("trades", []):
                rows.append((_ts(t["created_time"]), float(t["yes_price_dollars"]), float(t["count_fp"]),
                             1 if t["taker_outcome_side"] == "yes" else -1))
            cur = d.get("cursor")
            if not cur or not d.get("trades"):
                break
            time.sleep(0.5)
        have[key] = rows
        TAPE.write_text(json.dumps(have))
        time.sleep(0.5)
    return [tuple(r) for r in have[key]]


def run(now=None):
    now = time.time() if now is None else now
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists.")
        return
    if now < READ_NOT_BEFORE:
        print(f"Refusing: the read date is {datetime.fromtimestamp(READ_NOT_BEFORE, timezone.utc):%Y-%m-%d %H:%M} UTC.")
        return
    cs = closes()
    use = {c: v for c, v in cs.items() if usable_by_coverage(c, v[1])}
    if len(use) < NEEDED:
        print(f"Refusing: {len(use)} usable hourly closes, {NEEDED} needed.")
        return
    byrun = defaultdict(list)
    for c, (r, _) in use.items():
        byrun[r].append(c)
    hours = {}            # close -> {strike: (polls, trades)}
    no_clock = refetched = 0
    bad_hours = set()
    for r, cl in sorted(byrun.items()):
        book = _csv(f"{r}/book.csv.gz")
        if book and set(book[0]) != set(_csv_cols()):
            print("NOT_RUNNABLE: recorder schema changed")
            return
        off = _offset(book)
        if off is None:
            no_clock += len(cl)
            continue
        want = {datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"): c for c in cl}
        polls = defaultdict(list)
        strike_of = {}
        for x in book:
            c = want.get(x["close_time"])
            if c is None:
                continue
            polls[(c, x["ticker"])].append(_poll(x, off))
            strike_of[x["ticker"]] = float(x["strike"] or 0)
        trades, per_read = defaultdict(list), defaultdict(int)
        tick_close = {tk: c for (c, tk) in polls}
        for x in _csv(f"{r}/trades.csv.gz"):
            c = tick_close.get(x["ticker"])
            if c is None:
                continue
            per_read[(x["ticker"], x["poll_ts_local_ms"])] += 1
            trades[(c, x["ticker"])].append((_ts(x["created_time"]), float(x["yes_price_dollars"]), float(x["count_fp"]),
                                             1 if x["taker_outcome_side"] == "yes" else -1))
        heavy = {tk for (tk, _), n in per_read.items() if n >= TRUNC_ROWS}
        for (c, tk), ps in polls.items():
            tr = trades.get((c, tk), [])
            if tk in heavy:
                try:
                    tr = refetch(tk, c)
                    refetched += 1
                except RuntimeError:
                    bad_hours.add(c)
                    continue
            hours.setdefault(c, {})[strike_of[tk]] = (sorted(ps, key=lambda p: p.t), tr)
    excluded = sorted(bad_hours)
    hours = {c: v for c, v in hours.items() if v and c not in bad_hours}
    if (no_clock + len(excluded)) > 0.2 * len(use):
        print(f"NOT_RUNNABLE: {no_clock} hours without a clock, {len(excluded)} without a complete tape, of {len(use)}")
        return
    sims = {C: [(c, simulate_hour(st, c, C)) for c, st in sorted(hours.items())] for C in SIZES}
    lines = []
    all_pass = True
    posted = sum(1 for _, h in sims[1] if h["pairs"])
    for C in SIZES:
        rows = sims[C]
        for label, rate, mult in (("VERDICT maker fee = taker 7%", TAKER, 1.0), ("stress 7% x1.2", TAKER, 1.2),
                                  ("info maker 1.75%", MAKER, 1.0), ("info zero maker fee", 0.0, 1.0)):
            s = summarise(rows, rate, mult)
            lines.append(f"C={C:>2} {label}: hours {s['n']}, PF {s['pf']:.2f} (thirds {' / '.join(f'{t:.2f}' for t in s['thirds'])}; "
                         f"halves {' / '.join(f'{x:.2f}' for x in s['halves'])}), loss rate {100 * s['loss_rate']:.0f}%, "
                         f"net {100 * s['per']:+.3f}c per hour, total ${s['net']:+.2f}, z {s['z']:+.2f}, fees ${s['fees']:.2f}, "
                         f"spread earned ${s['spread']:.2f}, stop and flatten loss ${s['rest_loss']:.2f}")
        s = summarise(rows, TAKER)
        all_pass &= passes(s, summarise(rows, TAKER, 1.2))
        lines.append(f"C={C:>2} pairs {s['pairs']}, buy side filled {s['fill_b']}, sell side filled {s['fill_s']}, cycles {s['cycles']}, "
                     f"stops {s['stops']}, flattens {s['flattens']}, contracts beyond 5 levels {s['beyond']:.0f}")
        ex = [(c, h) for c, h in rows if h["trades"]]
        se = summarise(ex, TAKER)
        lines.append(f"C={C:>2} verdict fee, hours with no trades excluded: hours {se['n']}, PF {se['pf']:.2f}, net {100 * se['per']:+.3f}c per hour")
        lines.append(f"C={C:>2} {markout_line(rows, 30)}; {markout_line(rows, 300)}")
    eq, dd, worst = account(sims[10], TAKER)
    lines.append(f"account $500, C=10, verdict fee: end ${eq:.2f}, max drawdown ${dd:.2f}, worst Central day ${worst:+.2f}")
    verdict = "NOT_ENOUGH_DATA" if posted < NEEDED or len(hours) < NEEDED else ("NOT_YET_FALSIFIED" if all_pass else "FALSIFIED")
    lines.insert(0, f"QUOTE2B {verdict} (usable closes {len(use)}, scored {len(hours)}, with a pair posted {posted}, no clock {no_clock}, "
                    f"tape re-fetched {refetched}, tape incomplete {len(excluded)}; minimum {NEEDED}; z bar {Z_BAR}; tries 6)")
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def _csv_cols():
    return (["poll_ts_local_ms", "server_date_header", "ticker", "strike", "close_time"]
            + [f"yes_bid_px_{i}" for i in range(1, 6)] + [f"yes_bid_sz_{i}" for i in range(1, 6)]
            + [f"no_bid_px_{i}" for i in range(1, 6)] + [f"no_bid_sz_{i}" for i in range(1, 6)])


def main(argv):
    if len(argv) < 2 or argv[1] not in ("count", "run"):
        print(__doc__)
        return
    count() if argv[1] == "count" else run()


if __name__ == "__main__":
    main(sys.argv)
