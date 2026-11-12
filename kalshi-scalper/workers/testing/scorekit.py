#!/usr/bin/env python3
"""scorekit: the one shared loader and scorer skeleton for the next cards (T3, Testing Desk, Nov 12, 2026).
Research only. Reads kalshi-pull run folders (manifest.json + NNNN.json.gz) and scores lists of trades. Sends nothing, opens no data by itself.
A card plugs in by writing ONE function that turns loaded rows into Trade records; everything after that (windows, PF, clustered z, haircut line, labels, the read-once guard) is here.

LOAD   iter_answers(folder) | candles(folders) | markets(folders) | books(folders)        (shapes below; a card never re-parses pull files)
SCORE  score(trades, cfg)  ->  dict with n and cash PF by window, event-clustered z, cost lines, haircut line, labels
GUARD  Cutoff(date_ts, marker_file, marker_prefix).check(trades) and .mark_read(...)      (a cutoff is a date constant; the read-once marker is a committed line)

Trade = dict(event=str, cluster=str, ts=int (decision time, epoch s), price=float (what was paid, dollars, 0..1), win=bool, fee_mult=1.0 optional)
  One contract, hold to settlement. Cash result: win -> 1 - price - fee, loss -> -(price) - fee, fee = 0.07 * fee_mult * p * (1 - p) unrounded, paid once (settlement is free).
  A trade that exits early is not this shape: give it `net` (cash result after fees, dollars) and the scorer uses that.
Basis rules enforced here, from the Head's standing rules: z bar 5.46 at N about 2,113,000 and cash PF 1.5 in each of three windows to call PASS (research bar);
  under 100 trades the label is 'no evidence at n = x' (30 for the slow-family paper screen); FALSIFIED means cash PF under 1.0 at 100 or more;
  every taker rule prints the haircut line (a third of orders at the ask seen do not fill) and, when given, a book-replay line; price source and freshness are printed, never assumed.
"""
import gzip, json, math, os, re, statistics as st, time

Z_BAR, N_SHARED, PF_BAR, MIN_N, SLOW_MIN_N = 5.46, 2113000, 1.5, 100, 30
# Haircut table: Forensics' HOW_TO_PRICE_A_PAPER_TRADE.md (722ef2d) section 3, rule 2 (no book recorded: cut the COUNT, and add 1c to the price paid on the rest as the worst case).
HAIRCUT_DROP = 0.34          # limit at the price seen, a slow 5 to 10 s arrival: about a third (0.34)
HAIRCUT_DROP_PLUS1C = 0.25   # limit +1c, slow arrival (5 to 10 s)
HAIRCUT_LINES = {"at the price seen (about a third)": 1 / 3.0, "slow arrival 5 to 10 s, at the price seen": 0.34, "+1c limit, 2 s arrival": 0.15, "+1c limit, 6 s arrival": 0.23, "+1c limit, slow arrival": 0.25}
# Where an order book IS recorded, do not use these: replay with fill_ioc (the company convention) at 2 s and 6 s and report both lines.


# ---------- LOAD ----------
def iter_answers(folder):
    """Yield (row, parsed body) for every stored 200 answer of one kalshi-pull run folder, in request order."""
    m = json.load(open(os.path.join(folder, "manifest.json")))
    for row in m["rows"]:
        if row.get("status") == 200 and row.get("file") and not row.get("truncated"):
            yield row, json.load(gzip.open(os.path.join(folder, row["file"])))


def manifest(folder):
    return json.load(open(os.path.join(folder, "manifest.json")))


def price(node, key, absolute=False):
    """A price from a candle price object. VERIFIED shapes (Nov 12, against landed pull answers): binary-market candles carry '<key>_dollars' strings (open_dollars, high_dollars, low_dollars, close_dollars);
    perp candles carry plain 'open','high','low','close' strings that are ABSOLUTE price levels (AAPL perp about 6.8, never cents): pass absolute=True and no cents rule is applied.
    The cents fallback below ('<key>' as cents when above 1.0) is for the /historical endpoint and is UNVERIFIED (no historical candle answer has landed). None if absent."""
    if not isinstance(node, dict):
        return None
    for k in (key + "_dollars", key):
        try:
            v = float(node[k])
        except (KeyError, TypeError, ValueError):
            continue
        return v / 100.0 if (k == key and v > 1.0 and not absolute) else v
    return None


def iso(s):
    try:
        import calendar
        return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception:
        return None


def candles(folders):
    """{ticker: [candle]} sorted by time. candle = dict(ts, bid, ask, bid_low, ask_low, bid_high, ask_high, price, volume, oi), prices in dollars (None if absent).
    Accepts the batched answer ({'markets':[{'market_ticker':..,'candlesticks':[..]}]}), the single-market answer and the historical answer; the request id is the ticker fallback."""
    out = {}
    for f in ([folders] if isinstance(folders, str) else folders):
        for row, body in iter_answers(f):
            nodes = body.get("markets") if isinstance(body, dict) and isinstance(body.get("markets"), list) else [body]
            for n in nodes:
                if not isinstance(n, dict) or not isinstance(n.get("candlesticks"), list):
                    continue
                t = n.get("market_ticker") or n.get("ticker") or row["id"]
                for c in n["candlesticks"]:
                    try:
                        ts = int(c["end_period_ts"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    vol = c.get("volume_fp", c.get("volume"))
                    perp = "bid" in c and "yes_bid" not in c          # perp candle: {'bid': {...}, 'ask': {...}} absolute levels
                    bn, an = (c.get("bid"), c.get("ask")) if perp else (c.get("yes_bid"), c.get("yes_ask"))
                    out.setdefault(t, {})[ts] = {"ts": ts, "bid": price(bn, "close", perp), "ask": price(an, "close", perp),
                                                 "bid_low": price(bn, "low", perp), "ask_low": price(an, "low", perp),
                                                 "bid_high": price(bn, "high", perp), "ask_high": price(an, "high", perp),
                                                 "price": price(c.get("price"), "close", perp), "volume": _f(vol), "oi": _f(c.get("open_interest_fp", c.get("open_interest")))}
    return {t: [d[k] for k in sorted(d)] for t, d in out.items()}


def perp_csv(path):
    """{ticker: [candle]} from a perp-data `kalshi1m/<date>.csv.gz` file (VERIFIED header: ticker,end_period_ts,bid_open,bid_high,bid_low,bid_close,ask_open,...,ask_close,price_open..price_previous,open_interest,volume).
    Same candle dict as candles(); prices are absolute levels. end_period_ts is the END of the minute (Head, from Forensics' descriptive check)."""
    import csv
    op = gzip.open if str(path).endswith(".gz") else open
    out = {}
    with op(path, "rt") as fh:
        for r in csv.DictReader(fh):
            ts = int(r["end_period_ts"])
            out.setdefault(r["ticker"], {})[ts] = {"ts": ts, "bid": _f(r.get("bid_close")), "ask": _f(r.get("ask_close")), "bid_low": _f(r.get("bid_low")), "ask_low": _f(r.get("ask_low")),
                                                   "bid_high": _f(r.get("bid_high")), "ask_high": _f(r.get("ask_high")), "price": _f(r.get("price_close")), "volume": _f(r.get("volume")), "oi": _f(r.get("open_interest"))}
    return {t: [d[k] for k in sorted(d)] for t, d in out.items()}


def r6_book(path, offset_s=0.0):
    """{ticker: [poll]} from a recorder book file (`book15r6/<date>/<HHMM>/book.csv.gz`, VERIFIED header: t_send_ms,t_recv_ms,server_date_header,ticker,series,close_time,
    yes_bid_px_1..5,yes_bid_sz_1..5,no_bid_px_1..5,no_bid_sz_1..5). poll = dict(t (t_recv_ms/1000 + offset_s, the recorder's clock offset from clock.csv if the card applies it), yes_bids, no_bids) with
    levels as (price dollars, size) best first; empty cells (missing levels) are skipped, never read as zero. A YES buy meets the NO bids (ask = 1 - no bid price)."""
    import csv
    op = gzip.open if str(path).endswith(".gz") else open
    out = {}
    with op(path, "rt") as fh:
        for r in csv.DictReader(fh):
            def lv(pre):
                res = []
                for i in range(1, 6):
                    p, z = _f(r.get("%s_px_%d" % (pre, i))), _f(r.get("%s_sz_%d" % (pre, i)))
                    if p is not None and z is not None:
                        res.append((p, z))
                return res
            out.setdefault(r["ticker"], []).append({"t": int(r["t_recv_ms"]) / 1000.0 + offset_s, "yes_bids": lv("yes_bid"), "no_bids": lv("no_bid")})
    return {t: sorted(v, key=lambda p: p["t"]) for t, v in out.items()}


def fill_ioc(polls, side, limit, t0, delay):
    """THE company book-replay convention (Desk A's, e1a034f9 on claude/idea-desk-a, Head's ruling Nov 12; this is the same rule, not a second one): an immediate-or-cancel buy of 1 contract in total,
    walking up to 5 levels at or below `limit`; only the FIRST poll at or after t0 + delay counts, and only if it is within 4 s of that instant (no poll in that span is no trade); not enough size at or
    below the limit is no trade. Returns the average price paid, or None. side 'yes' meets the NO bids (ask = 1 - no bid price); side 'no' meets the YES bids. polls from r6_book (sorted by t)."""
    import bisect
    times = [p["t"] for p in polls]
    j = bisect.bisect_left(times, t0 + delay)
    if j >= len(polls) or times[j] - t0 - delay > 4:
        return None
    lv = polls[j]["no_bids"] if side == "yes" else polls[j]["yes_bids"]
    need, cost = 1.0, 0.0
    for a, sz in sorted(((1 - px, sz) for px, sz in lv), key=lambda x: x[0]):
        if a > limit + 1e-9:
            break
        take = min(need, sz); cost += take * a; need -= take
        if need <= 1e-12:
            return cost
    return None


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def markets(folders):
    """{ticker: dict(ticker, event, series, open, close, result, type, floor, cap, volume, title)} from market-list answers (settled lists); later pages and folders overwrite earlier."""
    out = {}
    for f in ([folders] if isinstance(folders, str) else folders):
        for row, body in iter_answers(f):
            for m in body.get("markets", []) if isinstance(body, dict) else []:
                if isinstance(m, dict) and m.get("ticker"):
                    out[m["ticker"]] = {"ticker": m["ticker"], "event": m.get("event_ticker", ""), "series": m["ticker"].split("-")[0], "open": iso(m.get("open_time", "")), "close": iso(m.get("close_time", "")),
                                        "result": m.get("result"), "type": m.get("strike_type"), "floor": _f(m.get("floor_strike")), "cap": _f(m.get("cap_strike")),
                                        "volume": _f(m.get("volume_fp", m.get("volume"))), "title": m.get("title", "")}
    return out


def books(folders):
    """{ticker: [snapshot]} from kalshi-pull ORDER BOOK answers: snapshot = dict(ts, yes_bids, no_bids) levels (price dollars, size) best first.
    SHAPE: taken from the recorder's own parser (scripts/record_15m_book.py: batch answer {'orderbooks': [{'ticker', 'orderbook_fp': {'yes_dollars': [[price, size]], 'no_dollars': [...]}}]}, or one market
    {'orderbook_fp': {...}}). NOT VERIFIED against a landed pull answer: no pull answer of this kind has landed yet (COMBO1_OPENBOOK holds market lists only). For book files the recorder already wrote, use r6_book()."""
    out = {}
    for f in ([folders] if isinstance(folders, str) else folders):
        for row, body in iter_answers(f):
            if not isinstance(body, dict):
                continue
            items = body.get("orderbooks") if isinstance(body.get("orderbooks"), list) else [dict(body, ticker=body.get("ticker", row["id"]))]
            for it in items:
                ob = it.get("orderbook_fp") or it.get("orderbook") if isinstance(it, dict) else None
                if not isinstance(ob, dict):
                    continue
                def lv(key):
                    res = []
                    for p, z in ob.get(key + "_dollars") or ob.get(key) or []:
                        p = float(p); res.append((p / 100.0 if p > 1.0 else p, float(z)))
                    return sorted(res, key=lambda x: -x[0])
                out.setdefault(it.get("ticker") or row["id"], []).append({"ts": int(body.get("ts", 0) or 0), "yes_bids": lv("yes"), "no_bids": lv("no")})
    return out


# ---------- SCORE ----------
def fee(p, mult=1.0):
    return 0.07 * mult * p * (1 - p)


def net_of(t, slip=0.0):
    if "net" in t:
        return float(t["net"]) - slip
    p = t["price"] + slip
    return (1 - p - fee(p, t.get("fee_mult", 1.0))) if t["win"] else (-p - fee(p, t.get("fee_mult", 1.0)))


def pf(nets):
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return (w / l) if l > 0 else (None if w == 0 else float("inf"))


def windows(trades, k=3):
    """k chronological windows by decision time (equal counts, ties kept in order). k=3 for the research bar, k=2 for the slow-family halves."""
    ts = sorted(trades, key=lambda t: (t["ts"], t["event"]))
    n = len(ts)
    return [ts[i * n // k:(i + 1) * n // k] for i in range(k)]


def cluster_z(trades, slip=0.0):
    """Event-clustered z: mean of the per-cluster mean net per contract over its standard error across clusters (equal-weight clusters). Needs 2+ clusters."""
    by = {}
    for t in trades:
        by.setdefault(t.get("cluster", t["event"]), []).append(net_of(t, slip))
    cm = [sum(v) / len(v) for v in by.values()]
    k = len(cm)
    if k < 2:
        return {"z": None, "clusters": k, "mean_per_cluster": cm[0] if cm else None}
    sd = st.stdev(cm)
    return {"z": (sum(cm) / k) / (sd / math.sqrt(k)) if sd > 0 else None, "clusters": k, "mean_per_cluster": sum(cm) / k}


def stats(trades, slip=0.0):
    nets = [net_of(t, slip) for t in trades]
    return {"n": len(nets), "net": round(sum(nets), 4), "mean": round(sum(nets) / len(nets), 5) if nets else None, "pf": None if not nets else (None if pf(nets) is None else round(pf(nets), 3))}


def score(trades, cfg=None):
    """cfg: dict(name, slow=False (30 and halves), price_source, freshness, book_replay=None (a dict or text the card computes from books), z_bar, pf_bar, registered_bar=dict(pf=.., z=..) optional)."""
    cfg = cfg or {}
    slow = cfg.get("slow", False)
    min_n = SLOW_MIN_N if slow else MIN_N
    trades = list(trades)
    n = len(trades)
    wins = windows(trades, 2 if slow else 3)
    by_win = [stats(w) for w in wins]
    allst, plus1 = stats(trades), stats(trades, 0.01)
    cz = cluster_z(trades)
    zbar, pfbar = cfg.get("z_bar", Z_BAR), cfg.get("pf_bar", PF_BAR)
    n_h = n * (1 - HAIRCUT_DROP)
    def label(nn):
        if nn < min_n:
            return "no evidence at n = %d" % round(nn)
        p = allst["pf"]
        if slow:
            return "on the paper list (unproven)" if (p is not None and p >= 1.3 and all(w["net"] > 0 for w in by_win)) else "off the list (failed the screen)"
        if p is not None and p < 1.0:
            return "FALSIFIED (cash PF %.2f at n = %d)" % (p, round(nn))
        research = cz["z"] is not None and cz["z"] >= zbar and all(w["pf"] is not None and w["pf"] >= pfbar for w in by_win)
        if research:
            return "PASS (research bar: z %.2f >= %.2f and cash PF >= %.1f in each of 3 windows)" % (cz["z"], zbar, pfbar)
        rb = cfg.get("registered_bar")
        if rb and p is not None and p >= rb.get("pf", 0) and (cz["z"] or 0) >= rb.get("z", 0):
            return "cleared its registered bar (NOT the research bar)"
        return "NO SURVIVOR / not cleared (cash PF %s, z %s)" % (p, None if cz["z"] is None else round(cz["z"], 2))
    lines = {name: {"n_after_drop": round(n * (1 - d), 1), "label": label(n * (1 - d))} for name, d in HAIRCUT_LINES.items()}
    out = {"name": cfg.get("name", ""), "n": n, "windows": by_win, "all": allst, "plus_1c": plus1, "cluster_z": cz, "label": label(n),
           "haircut_table_no_book": lines, "haircut_note": "the missed trades are NOT random: a limit keeps the signals the market moved against and loses the ones it moved with (Forensics, section 3 point 3); dropping at random may still be generous. Add 1c to the price paid on the rest as the worst case.",
           "haircut_line": {"n_after_drop": round(n_h, 1), "label_on_this_line": label(n_h) if n_h < min_n else "n %.0f after a %d percent fill drop (headline label stands only if this line also clears %d)" % (n_h, round(100 * HAIRCUT_DROP), min_n), "drop": HAIRCUT_DROP, "drop_at_plus_1c": HAIRCUT_DROP_PLUS1C},
           "book_replay_line": cfg.get("book_replay") or "NOT PROVIDED: no book replay for this card; the haircut line above stands in and a live view needs the 6 second book line",
           "price_source": cfg.get("price_source", "NOT STATED: say which book, tape or cleared source the price came from"), "freshness": cfg.get("freshness", "NOT STATED"),
           "bar": "z bar %.2f at N about %d, cash PF %.1f in each of three windows; under %d trades 'no evidence'" % (zbar, N_SHARED, pfbar, min_n)}
    if cfg.get("price_source", "").lower().startswith("market list") or "list quote" in cfg.get("price_source", "").lower():
        out["warning"] = "a market-list quote is a copy up to about 11 seconds old; no price may be taken from it"
    return out


# ---------- GUARD ----------
class Cutoff:
    """A held-out cutoff as a date constant plus a committed read-once marker line. Usage: Cutoff(CUTOFF_TS, 'REGISTRATION.md', 'READ-ONCE MARKER').
    check(trades, now): refuses to score before `not_before` (a date constant), refuses a trade at or after the cutoff in a development read, and refuses if the marker already says READ ON.
    mark_read(date, commit): returns the replacement marker line for the human to commit; it does not write."""
    def __init__(self, cutoff_ts, marker_file, marker_prefix="READ-ONCE MARKER", not_before=None, held_out=False):
        self.cutoff, self.file, self.prefix, self.not_before, self.held_out = cutoff_ts, marker_file, marker_prefix, not_before, held_out

    def marker_line(self):
        for ln in open(self.file):
            if ln.startswith(self.prefix):
                return ln.strip()
        raise RuntimeError("no marker line starting %r in %s: the read-once marker must be a committed line" % (self.prefix, self.file))

    def check(self, trades, now=None):
        now = time.time() if now is None else now
        if self.not_before is not None and now < self.not_before:
            raise RuntimeError("refused: before the registered read date")
        if re.search(r"READ ON \d{4}-\d{2}-\d{2}", self.marker_line()):          # a filled-in marker, not the template text "READ ON <date>"
            raise RuntimeError("refused: the marker says this was already read once: " + self.marker_line())
        for t in trades:
            late = t["ts"] >= self.cutoff
            if late and not self.held_out:
                raise RuntimeError("refused: a trade at or after the cutoff (held-out data) in a development read: " + t.get("event", "?"))
            if not late and self.held_out:
                raise RuntimeError("refused: a development trade in the held-out read: " + t.get("event", "?"))
        return True

    def mark_read(self, date, commit):
        return "%s: READ ON %s, commit %s" % (self.prefix, date, commit)
