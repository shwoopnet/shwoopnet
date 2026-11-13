"""OIVER shadow replay, BUILD 2 (History Miner, Nov 13, 2026): the three Bitcoin OIVER places (SPREAD, CAP30, DEPTH) logged against the OICORE parent
on R6 books, from Desk A's frozen sheet DESK_A_FROZEN_OIVER_SHADOW_DEFINITIONS_NOV13.md at 61fb9854 (sha256 cb45e79b, committed 2026-11-13T21:19:58Z)
and the wheel sheet's section 0 where it points there; Desk A's code was not read. Rules and the hand case in EXPECTED_BY_HAND.md (7feddce6), first.
R6 fill check: the next poll within 4 s. Shadow only: no order, no Kalshi call. Not run on real files until Auditor B is CLEAN and the Head says go.
Usage: python3 -I oiver_shadow2.py <log.csv> --oi <oi.csv> --oi-named-at <ISO> --books <book.csv.gz> ... --coverage <coverage.csv.gz> ... [--results <list.csv>]"""
import csv, gzip, json, math, os, statistics, sys, time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

EPS = 1e-9
COUNT_FROM = int(datetime(2026, 11, 13, 21, 19, 58, tzinfo=timezone.utc).timestamp())   # the frozen sheet's commit time (61fb9854)
READ_FROM = int(datetime(2026, 11, 21, tzinfo=timezone.utc).timestamp())   # no block read before 2026-11-21T00:00:00Z (computed, not typed)
SERIES = "KXBTC15M"
D_LAG, POLL_WIN = 180, 10            # D = close - 180 s; the decision poll is the last in [D - 10 s, D]
SECOND_LOOK = 4.0                    # R6: the next poll at most 4 s after the decision poll
OFFSET_ROWS = 120
OI_MIN = 86300
FLOOR, CEIL = 0.08, 0.50
C = 20
SPREAD_MAX, CAP, DEPTH_MIN = 0.03, 0.30, 40
VOID_AFTER = 7 * 86400
WEEK = 604800
CT = timezone(timedelta(hours=-6))   # US Central standard time; every block date here is after the Nov 1 change


class Stop(Exception):
    pass


def iso(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def date_s(v):
    try:
        d = parsedate_to_datetime(v)
    except (TypeError, ValueError, IndexError):
        return None
    return None if d is None or d.tzinfo is None else int(d.timestamp())


def fee_up_order(p, contracts=C):
    return math.ceil(0.07 * contracts * p * (1 - p) * 100 - 1e-9) / 100


def load_runs(paths):
    """{(ticker, close): [(exchange time, row)]} for KXBTC15M rows, exchange time by the offset formula, run by run."""
    polls = {}
    for p in paths:
        with gzip.open(p, "rt", newline="") as f:
            run = []
            for b in csv.DictReader(f):
                tr = num(b.get("t_recv_ms"))
                if tr is not None:
                    run.append((tr, b))
        run.sort(key=lambda x: x[0])
        terms = []
        for tr, b in run:
            d = date_s(b.get("server_date_header"))
            if d is not None:
                terms.append(d + 0.5 - tr / 1000.0)
            if not terms or b.get("series") != SERIES:
                continue
            try:
                key = (b["ticker"], iso(b["close_time"]))
            except (KeyError, TypeError, ValueError):
                continue
            polls.setdefault(key, []).append((tr / 1000.0 + statistics.median(terms[-OFFSET_ROWS:]), b))
    return polls


def ladder(b, side):
    """Asks of the ladder a buy of `side` meets: a YES buy meets the NO bids, a NO buy the YES bids; ask = 1 - bid price; sorted by ask."""
    k = "no" if side == "yes" else "yes"
    out = []
    for i in range(1, 6):
        px, sz = num(b.get("%s_bid_px_%d" % (k, i))), num(b.get("%s_bid_sz_%d" % (k, i)))
        if px is not None and sz is not None and sz > 0:
            out.append((round(1 - px, 9), sz))
    return sorted(out)


def offers(b, side, limit):
    return sum(sz for a, sz in ladder(b, side) if a <= limit + EPS) >= C - EPS


def walked(b, side):
    need, cost = C, 0.0
    for a, sz in ladder(b, side):
        take = min(sz, need); cost += take * a; need -= take
        if need <= EPS:
            return cost / C
    return None


def load_results(cov_paths, list_path):
    res = {}
    rows = []
    for p in cov_paths:
        with gzip.open(p, "rt", newline="") as f:
            rows += [(r.get("ticker"), (r.get("result") or "").strip()) for r in csv.DictReader(f)]
    if list_path:
        with open(list_path, newline="") as f:
            rows += [(r.get("ticker"), (r.get("result") or "").strip()) for r in csv.DictReader(f)]
    for t, v in rows:
        if v not in ("", "yes", "no"):
            raise Stop("result %r for %s" % (v, t))
        if v and res.get(t) and res[t] != v:
            raise Stop("results disagree for %s" % t)
        if v:
            res[t] = v
    return res


def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return None if not xs else (math.inf if l == 0 else w / l)


def shown(x):
    return None if x is None else ("inf" if x == math.inf else round(x, 6))


def report(trades, parent=None):
    xs = [t["cash"] for t in trades]; n = len(xs)
    days = {datetime.fromtimestamp(t["close"], CT).date() for t in trades}
    w = sum(1 for x in xs if x > 0); l = n - w
    out = {"n": n, "wins": w, "losses": l, "pf": shown(pf(xs)), "net": round(sum(xs), 6), "mean": round(sum(xs) / n, 6) if n else None, "central_days": len(days),
           "block_bar_met": n >= 60 and len(days) >= 7 and w >= 10 and l >= 10 and pf(xs) is not None and pf(xs) >= 1.3 - EPS,
           "label": "no evidence at n = %d" % n if n < 100 else "block read"}
    if parent is not None:
        px = [t["cash"] for t in parent]
        cl = [t["close"] for t in parent]
        weeks = max((max(cl) - min(cl)) / WEEK, 1.0) if cl else 1.0
        h, hp = n // 2, len(px) // 2
        out["vs_parent_info"] = {"pf_lift_ge_0.10": None if pf(xs) is None or pf(px) is None else pf(xs) >= pf(px) + 0.10 - EPS,
                                 "net_week_not_lower": sum(xs) / weeks >= sum(px) / weeks - EPS,
                                 "half2_not_worse": None if pf(xs[h:]) is None or pf(px[hp:]) is None else pf(xs[h:]) >= pf(px[hp:]) - EPS,
                                 "signals_ge_60": n >= 60}
    return out


def run(log_path, oi_path, oi_named_at, book_paths, cov_paths, list_path=None, now=None):
    now = time.time() if now is None else now
    if now < READ_FROM:
        raise Stop("block read refused before 2026-11-21T00:00Z")
    if not oi_named_at:
        raise Stop("the open interest source is not named: no place records a signal")
    hm_guard.refuse_all([log_path, oi_path] + list(book_paths) + list(cov_paths) + ([list_path] if list_path else []))
    start = max(COUNT_FROM, iso(oi_named_at))
    with open(oi_path, newline="") as f:
        oi = {r["ticker"]: num(r.get("oi_rise")) for r in csv.DictReader(f)}
    polls = load_runs(book_paths)
    res = load_results(cov_paths, list_path)
    counts = {k: 0 for k in ("windows", "before_count_from", "no_oi", "oi_below", "not_two_sided", "no_poll", "cheap", "out_of_band", "signals",
                             "miss_no_second_look", "miss_depth", "filled", "void", "scored")}
    places = {"SPREAD": {"skip": {}, "trades": []}, "CAP30": {"skip": {}, "trades": []}, "DEPTH": {"skip": {}, "trades": []}}
    parent, log, waiting = [], [], []
    for (t, close), ps in sorted(polls.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        counts["windows"] += 1
        D = close - D_LAG
        if D <= start:
            counts["before_count_from"] += 1; continue
        ps = sorted(ps, key=lambda x: x[0])
        cand = [i for i, (te, b) in enumerate(ps) if D - POLL_WIN - EPS <= te <= D + EPS]
        if not cand:
            counts["no_poll"] += 1; continue
        i = cand[-1]
        te, b = ps[i]
        yb, nb = num(b.get("yes_bid_px_1")), num(b.get("no_bid_px_1"))
        ya = None if nb is None else 1 - nb
        if yb is None or ya is None or not (yb > EPS and ya < 1 - EPS and yb < ya - EPS):
            counts["not_two_sided"] += 1; continue
        r = oi.get(t)
        if r is None:
            counts["no_oi"] += 1; continue
        if r < OI_MIN - EPS:
            counts["oi_below"] += 1; continue
        asks = {"yes": ya, "no": 1 - yb}
        side = "yes" if asks["yes"] <= asks["no"] + EPS else "no"
        ask = asks[side]
        if ask < FLOOR - EPS:
            counts["cheap"] += 1; continue
        if ask > CEIL + EPS:
            counts["out_of_band"] += 1; continue
        counts["signals"] += 1
        touch = num(b.get("no_bid_sz_1" if side == "yes" else "yes_bid_sz_1"))
        cond = {"SPREAD": None if ya - yb <= SPREAD_MAX + EPS else "spread_wide",
                "CAP30": None if ask <= CAP + EPS else "above_cap",
                "DEPTH": "size_unknown" if touch is None else (None if touch >= DEPTH_MIN - EPS else "depth_thin")}
        nxt = ps[i + 1] if i + 1 < len(ps) else None
        if nxt is None or nxt[0] - te > SECOND_LOOK + EPS:
            fill = "miss_no_second_look"
        elif not (offers(b, side, ask) and offers(nxt[1], side, ask)):
            fill = "miss_depth"
        else:
            fill = "filled"
        row = {"ticker": t, "close": close, "side": side, "ask": round(ask, 6), "fill": fill}
        for k, v in cond.items():
            row[k] = v or "pass"
            if v:
                places[k]["skip"][v] = places[k]["skip"].get(v, 0) + 1
        if fill != "filled":
            counts[fill] += 1; log.append(row); continue
        counts["filled"] += 1
        p = max(walked(b, side), walked(nxt[1], side))
        fe = fee_up_order(p) / C
        v = res.get(t, "")
        if v == "":
            if now - close >= VOID_AFTER:
                counts["void"] += 1
                row.update({"price": round(p, 6), "result": "void", "cash": round(-fe, 6)}); log.append(row); continue
            waiting.append(t); continue
        cash = round((1.0 if v == side else 0.0) - p - fe, 9)
        tr = {"ticker": t, "close": close, "cash": cash}
        counts["scored"] += 1
        parent.append(tr)
        for k, c in cond.items():
            if c is None:
                places[k]["trades"].append(tr)
        row.update({"price": round(p, 6), "result": v, "cash": round(cash, 6)}); log.append(row)
    if waiting:
        raise Stop("block waits: %d filled signals without a result and under 7 days old (%s)" % (len(waiting), ", ".join(waiting[:5])))
    cols = ["ticker", "close", "side", "ask", "fill", "SPREAD", "CAP30", "DEPTH", "price", "result", "cash"]
    with open(log_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader()
        for row in log:
            w.writerow({c: row.get(c, "") for c in cols})
    out = {"counts": counts, "parent": report(parent)}
    for k, v in places.items():
        out[k] = dict(report(v["trades"], parent), skips=v["skip"])
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(name, many=False):
        if name not in a:
            return [] if many else None
        i = a.index(name); vals = []
        for x in a[i + 1:]:
            if x.startswith("--"):
                break
            vals.append(x)
        return vals if many else (vals[0] if vals else None)
    try:
        print(json.dumps(run(a[0], opt("--oi"), opt("--oi-named-at"), opt("--books", True), opt("--coverage", True), opt("--results"))))
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
