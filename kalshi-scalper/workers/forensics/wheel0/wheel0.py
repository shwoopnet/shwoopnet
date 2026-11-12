#!/usr/bin/env python3
"""WHEEL0: does a hot block of 60 predict the next 60? The premise test of the rotation lane (owner's order, Head of R&D's design, 2026-11-12).
Registration: WHEEL0_REGISTRATION.md (same folder). 1 try. Research only: reads files, sends nothing, no account data.

Every design constant below is the Head of R&D's (messages of 19:53Z, 19:57Z and the rulings of 20:02Z recorded in the registration). This desk chose none of the templates.
A BLOCK (ruling 1, the lane's own rule): at least 60 filled signals in time order, running on until it holds at least 10 of the rarer outcome (wins for a cheap-side
template, losses for a favourite-side template). HOT = cash PF 1.3 or better on the block and 1.0 or better in each half (first floor(n/2), then the rest). The next block
starts at the next signal and is built the same way. Favourites at 88c to 97c: the same with at least 150 signals; reported apart.
Two price sources, never mixed in one figure:
  candle : the 1 minute candle ending exactly at close minus L; the order is kept or dropped at random at the template's measured fill share (WHEEL0_DROP_TABLE.json,
           measured on books with no outcome); price paid = the ask seen. Labelled a candle read.
  book   : recorder R6 order books (gold, XRP, Dogecoin only): the look poll, then the first poll within 4 s must still offer 10 contracts at or under ask + 1c, walking levels.
Commands:
  selftest
  count  --lists <run...> --candles <run...>                      signals, blocks and pairs per template; NO result is read
  run    --lists <run...> --candles <run...> [--books <r6 root>] --out <json> --go <the Head's go line>      the one read
"""
import sys, os, json, gzip, math, hashlib, calendar, time, random, collections, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOOKS = (600, 360, 180)
BANDS = {"cheap": (("05-20", 0.05, 0.20, "[)"), ("20-35", 0.20, 0.35, "[)"), ("35-50", 0.35, 0.50, "[]")),
         "fav": (("50-65", 0.50, 0.65, "(]"), ("65-80", 0.65, 0.80, "(]"), ("80-88", 0.80, 0.88, "()"))}
FAV_HI = ("88-97", 0.88, 0.97, "[]")                       # third line, reported apart, never pooled
SPREAD_MAX, SLIP, SIZE, FILL_WITHIN_MS, LOOK_TOL_MS = 0.04, 0.01, 10, 4000, 10000
BLOCK, HALF, HOT_PF, HALF_PF, RARER_MIN, CONFIRM = 60, 30, 1.3, 1.0, 10, 30
FAV_BLOCK_MIN, FAV_LOSSES = 150, 10
VERDICT_PF, VERDICT_P, VERDICT_MIN_HOT = 1.15, 0.05, 30
BOOT_N, SEED = 10000, 20261112
EPS = 1e-9
def _ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
FROM, BEFORE = _ts("2026-09-12T00:00:00Z"), _ts("2026-11-13T00:00:00Z")
SERIES = ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M")
# Standing rule (h): a series another card holds out on recorded dates is used for closes BEFORE this instant only, from candles only, and no book row of it is kept.
RULE_H_BEFORE = {"KXBTC15M": _ts("2026-10-29T00:00:00Z"), "KXETH15M": _ts("2026-10-29T00:00:00Z")}
BOOK_SERIES = ("KXGOLD15M", "KXXRP15M", "KXDOGE15M")       # no book row is kept for a series in RULE_H_BEFORE (asserted below)
VERDICT_NEEDS_BOTH_P = True                                # Amendment 1, the Head's ruling 2 (20:21Z): SUPPORTED needs the bootstrap p AND the null-calibrated p at or under 0.05
# Amendment 1, the Head's ruling 1 (20:21Z): DEPTH1 holds the gold R6 windows of Oct 30 to Nov 13 and reads them once from 2026-11-14T00:00Z. WHEEL0 joins gold outcomes
# on those windows, so the WHEEL0 read is refused before that instant AND until the marker file carries the line that DEPTH1's read has been made.
NOT_BEFORE = _ts("2026-11-14T00:00:00Z")
MARKER_FILE = os.path.join(HERE, "WHEEL0_PRECONDITION.md")
MARKER_RE = r"(?m)^DEPTH1 READ MADE: \S.*$"
NULL_REPS = 500
# HOT by luck, per band, on made-up fair bets under the growing-block rule (wheel0_null_sim.py, committed with its output WHEEL0_NULL_SIM.json); fixed before any outcome
LUCK = json.load(open(os.path.join(HERE, "WHEEL0_NULL_SIM.json")))["hot_share_by_luck"]
DROP_GROUP = {"KXGOLD15M": "gold_xrp_doge", "KXXRP15M": "gold_xrp_doge", "KXDOGE15M": "gold_xrp_doge", "KXBTC15M": "xrp_doge", "KXETH15M": "xrp_doge"}   # ruling 4
DROP_FILE = os.path.join(HERE, "WHEEL0_DROP_TABLE.json")


# ---------------------------------------------------------------- guards and readers
def refuse_heldout(path):
    parts = os.path.realpath(path).split(os.sep) + os.path.abspath(path).split(os.sep)
    if any(p.upper().startswith("HELDOUT_") for p in parts):
        raise SystemExit("refused: %s is a HELDOUT_ folder (standing rule (h))" % path)


def _answers(folder):
    refuse_heldout(folder)
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") == 200 and row.get("file") and not row.get("truncated"):
            yield json.load(gzip.open(os.path.join(folder, row["file"])))


def _iso(s):
    try: return _ts(s[:19] + "Z")
    except Exception: return None


def read_markets(folders, with_result):
    """{ticker: dict(series, close, result)} for the five series. Rule (h) and the date bounds are applied HERE, on the close time, before anything else sees a market.
    with_result=False (the count command) never touches the result field."""
    out, cnt = {}, collections.Counter()
    for f in folders:
        for body in _answers(f):
            for m in body.get("markets", []) if isinstance(body, dict) else []:
                if not isinstance(m, dict) or not m.get("ticker") or "candlesticks" in m: continue
                s = str(m["ticker"]).split("-")[0]
                if s not in SERIES: cnt["other_series"] += 1; continue
                c = _iso(m.get("close_time") or "")
                if c is None: cnt["no_close_time"] += 1; continue
                if not (FROM <= c < BEFORE): cnt["outside_dates"] += 1; continue
                if s in RULE_H_BEFORE and c >= RULE_H_BEFORE[s]: cnt["rule_h_dropped_%s" % s] += 1; continue
                out[m["ticker"]] = {"series": s, "close": c, "result": ((m.get("result") or "").lower() if with_result else None)}
    return out, dict(cnt)


def _px(side):
    if not isinstance(side, dict): return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""): continue
        try: v = float(v)
        except (TypeError, ValueError): continue
        return v / 100.0 if (k == "close" and v > 1.0) else v
    return None


def read_candles(folders, wanted):
    """{ticker: {end_ts: (yes_bid, yes_ask)}} for the wanted tickers only (a ticker dropped by rule (h) is never loaded)."""
    out = {}
    for f in folders:
        for body in _answers(f):
            nodes = body.get("markets") if isinstance(body, dict) and isinstance(body.get("markets"), list) else [body]
            for n in nodes:
                if not isinstance(n, dict) or not isinstance(n.get("candlesticks"), list): continue
                t = n.get("market_ticker") or n.get("ticker")
                if t not in wanted: continue
                d = out.setdefault(t, {})
                for c in n["candlesticks"]:
                    try: d[int(c["end_period_ts"])] = (_px(c.get("yes_bid")), _px(c.get("yes_ask")))
                    except (KeyError, TypeError, ValueError): pass
    return out


def load_drop_table(path=DROP_FILE):
    raw = open(path, "rb").read(); j = json.loads(raw)
    return {(g, r["L"], r["side"], r["band"]): r["fill_share"] for g in ("gold_xrp_doge", "xrp_doge") for r in j[g]}, hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------- the order
def in_band(a, b):
    lo, hi, kind = b[1], b[2], b[3]
    return (a >= lo - EPS if kind[0] == "[" else a > lo + EPS) and (a <= hi + EPS if kind[1] == "]" else a < hi - EPS)


def template_of(yes_bid, yes_ask):
    """From one two-sided YES quote: {'cheap': (side, ask, band), 'fav': (side, ask, band)}; band None when the ask is outside every band. {} when there is no signal at all."""
    if yes_bid is None or yes_ask is None or not (0 < yes_bid < yes_ask < 1): return {}
    if yes_ask - yes_bid > SPREAD_MAX + EPS: return {}
    no_ask = 1.0 - yes_bid
    if abs(yes_ask - no_ask) < EPS: return {}
    out = {}
    for kind, (side, ask) in (("cheap", ("yes", yes_ask) if yes_ask < no_ask else ("no", no_ask)), ("fav", ("yes", yes_ask) if yes_ask > no_ask else ("no", no_ask))):
        band = next((b[0] for b in BANDS[kind] if in_band(ask, b)), None)
        if band is None and kind == "fav" and in_band(ask, FAV_HI): band = FAV_HI[0]
        out[kind] = (side, round(ask, 4), band)
    return out


def fee10(p):
    """Taker fee for one order of 10 contracts at price p, rounded UP to the cent (dollars)."""
    return math.ceil(0.07 * p * (1.0 - p) * SIZE * 100 - 1e-9) / 100.0


def cash(p, side, result):
    """Cash result of one order of 10 held to settlement (dollars). No yes/no result = a void: price refunded, fee kept (the Head's standing void rule)."""
    f = fee10(p)
    if result not in ("yes", "no"): return -f, None
    win = result == side
    return (SIZE * (1.0 - p) - f) if win else (-SIZE * p - f), win


def keep_draw(ticker, L, side):
    """A fixed uniform number in [0,1) for one signal: a hash of the seed, the ticker, the look and the side. It cannot depend on the outcome."""
    h = hashlib.sha256(("%d|%s|%d|%s" % (SEED, ticker, L, side)).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2.0 ** 64


def orders_from_candles(markets, candles, drop, apply_drop=True):
    """One paper order per (market, look, side kind) that signals and survives the random drop. Reads ONLY the candle ending exactly at close - L."""
    out, cnt = [], collections.Counter()
    for t, m in markets.items():
        cs = candles.get(t)
        if cs is None: cnt["no_candles_for_market"] += 1; continue
        for L in LOOKS:
            q = cs.get(m["close"] - L)
            if q is None: cnt["no_candle_at_look"] += 1; continue
            tp = template_of(q[0], q[1])
            if not tp: cnt["no_signal_quote"] += 1; continue
            for kind, (side, ask, band) in tp.items():
                if band is None: cnt["out_of_band"] += 1; continue
                share = drop.get((DROP_GROUP[m["series"]], L, kind, band))
                if share is None: cnt["no_drop_rate"] += 1; continue
                if apply_drop and keep_draw(t, L, side) >= share: cnt["dropped_at_random"] += 1; continue
                c, win = cash(ask, side, m["result"]) if m["result"] is not None else (None, None)
                out.append({"series": m["series"], "tpl": (L, kind, band), "ticker": t, "close": m["close"], "day": time.strftime("%Y-%m-%d", time.gmtime(m["close"])), "side": side, "price": ask, "cash": c, "win": win})
    return out, dict(cnt)


def fair_yes(markets, candles):
    """{ticker: YES mid at the market's LATEST look that has a two-sided quote}: the chance used to draw made-up results in the null calibration. No result is read."""
    out = {}
    for t, m in markets.items():
        cs = candles.get(t) or {}
        for L in sorted(LOOKS):
            q = cs.get(m["close"] - L)
            if q and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1: out[t] = (q[0] + q[1]) / 2.0; break
    return out


def orders_from_books(markets, root):
    """Book mode (gold, XRP, Dogecoin): the look poll within 10 s of close - L, then the FIRST later poll within 4 s must still offer 10 at or under ask + 1c."""
    refuse_heldout(root)
    assert not set(BOOK_SERIES) & set(RULE_H_BEFORE), "a series held out under rule (h) is in the book list"
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import r6load as R
    mk = {t: m for t, m in markets.items() if m["series"] in BOOK_SERIES}
    close_ms = {t: m["close"] * 1000 for t, m in mk.items()}
    b = R.load_books(root, mk.keys(), min_left_s=min(LOOKS) - 16, max_left_s=max(LOOKS) + 1, close_ms=close_ms)
    tk = b["ticker"].to_numpy(); px = b[R.PX].to_numpy(float); sz = b[R.SZ].to_numpy(float); tt = b["t_recv_ms"].to_numpy("int64")
    if len(tk) == 0: return [], {"no_book_rows": len(mk)}
    cut = np.r_[0, np.flatnonzero(tk[1:] != tk[:-1]) + 1, len(tk)]
    out, cnt = [], collections.Counter()
    for a, e in zip(cut[:-1], cut[1:]):
        t = tk[a]; m = mk[t]; T = close_ms[t]; ts_ = tt[a:e]
        for L in LOOKS:
            k = int(np.searchsorted(ts_, T - L * 1000, side="left"))
            if k >= len(ts_) or ts_[k] > T - L * 1000 + LOOK_TOL_MS: cnt["no_look"] += 1; continue
            r = a + k; yb, nb = px[r, 0], px[r, 5]
            if not (yb == yb and nb == nb): cnt["one_sided"] += 1; continue
            tp = template_of(float(yb), float(1.0 - nb))
            if not tp: cnt["no_signal_quote"] += 1; continue
            j = k + 1; fr = a + j if (j < len(ts_) and ts_[j] - ts_[k] <= FILL_WITHIN_MS) else None
            for kind, (side, ask, band) in tp.items():
                if band is None: cnt["out_of_band"] += 1; continue
                if fr is None: cnt["no_fill_poll"] += 1; continue
                cols = slice(5, 10) if side == "yes" else slice(0, 5); need, cost = float(SIZE), 0.0
                for p_, s_ in zip(px[fr, cols], sz[fr, cols]):
                    if not (p_ == p_) or not (s_ == s_) or s_ <= 0: continue
                    ak = 1.0 - p_
                    if ak > ask + SLIP + EPS: break
                    take = min(need, s_); cost += take * ak; need -= take
                    if need <= EPS: break
                if need > EPS: cnt["missed"] += 1; continue
                p = round(cost / SIZE, 4); c, win = cash(p, side, m["result"]) if m["result"] is not None else (None, None)
                out.append({"series": m["series"], "tpl": (L, kind, band), "ticker": t, "close": m["close"], "day": time.strftime("%Y-%m-%d", time.gmtime(m["close"])), "side": side, "price": p, "cash": c, "win": win})
    return out, dict(cnt)


# ---------------------------------------------------------------- blocks and the numbers
def pf(x):
    w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0)
    return float("inf") if (l == 0 and w > 0) else (None if l == 0 else w / l)


def _ge(v, bar): return v is not None and v >= bar - EPS


def is_hot(block):
    """PF 1.3 or better on the block, 1.0 or better in each half (first floor(n/2), then the rest). The count of the rarer outcome is guaranteed by how a block is built."""
    c = [o["cash"] for o in block]; half = len(block) // 2
    return _ge(pf(c), HOT_PF) and _ge(pf(c[:half]), HALF_PF) and _ge(pf(c[half:]), HALF_PF)


def build_blocks(v, kind, min_len):
    """v: one template's orders in time order. -> [(start, end)] inclusive indices. A block is at least min_len orders and runs on until it holds RARER_MIN of the rarer
    outcome (wins for 'cheap', losses for 'fav'); the next block starts at the next order. A tail that never completes is not a block."""
    out, i = [], 0
    while i < len(v):
        rare, e = 0, None
        for j in range(i, len(v)):
            rare += (1 if v[j]["win"] else 0) if kind == "cheap" else (0 if v[j]["win"] else 1)
            if j - i + 1 >= min_len and rare >= RARER_MIN: e = j; break
        if e is None: break
        out.append((i, e)); i = e + 1
    return out


def grid(orders):
    """{(series, tpl): dict(orders=[...in time order], spans=[(start, end)], blocks=[[orders]])}"""
    by = collections.defaultdict(list)
    for o in orders: by[(o["series"], o["tpl"])].append(o)
    out = {}
    for k, v in by.items():
        v.sort(key=lambda o: (o["close"], o["ticker"]))
        sp = build_blocks(v, k[1][1], FAV_BLOCK_MIN if k[1][2] == FAV_HI[0] else BLOCK)
        out[k] = {"orders": v, "spans": sp, "blocks": [v[a:e + 1] for a, e in sp]}
    return out


def boot_p(rows):
    """rows: (day, cash, after_hot). One-sided p for D = mean after HOT minus mean after not-HOT being at or below zero, resampling UTC days. -> (D, p, [2.5%, 97.5%])"""
    hs = collections.defaultdict(lambda: [0.0, 0, 0.0, 0])
    for d, c, h in rows:
        a = hs[d]
        if h: a[0] += c; a[1] += 1
        else: a[2] += c; a[3] += 1
    days = sorted(hs); H = [hs[d] for d in days]
    def D(idx):
        sh = sum(H[i][0] for i in idx); nh = sum(H[i][1] for i in idx); sn = sum(H[i][2] for i in idx); nn = sum(H[i][3] for i in idx)
        return None if nh == 0 or nn == 0 else sh / nh - sn / nn
    d0 = D(range(len(days)))
    if d0 is None: return None, None, [None, None]
    rng = random.Random(SEED); ds = []
    for _ in range(BOOT_N):
        v = D([rng.randrange(len(days)) for _ in days])
        if v is not None: ds.append(v)
    ds.sort()
    return d0, sum(1 for v in ds if v <= 0) / len(ds), [ds[int(0.025 * len(ds))], ds[int(0.975 * len(ds)) - 1]]


def primary(g, series=None):
    rows, after_hot, after_not = [], [], []; blocks = hot = pairs = hot_pairs = 0; luck = 0.0
    lens = collections.defaultdict(list)
    for (s, tpl), gg in g.items():
        if tpl[2] == FAV_HI[0] or (series and s != series): continue
        bl = gg["blocks"]
        flags = [is_hot(b) for b in bl]; blocks += len(bl); hot += sum(flags); luck += len(bl) * LUCK[tpl[2]]
        lens[tpl[2]].extend(len(b) for b in bl)
        for i in range(1, len(bl)):
            pairs += 1; hot_pairs += flags[i - 1]
            (after_hot if flags[i - 1] else after_not).extend(o["cash"] for o in bl[i])
            rows.extend((o["day"], o["cash"], flags[i - 1]) for o in bl[i])
    d, p, ci = boot_p(rows)
    r = lambda v, n=4: None if v is None else (v if v == float("inf") else round(v, n))
    return {"blocks": blocks, "hot_blocks": hot, "hot_blocks_expected_by_luck": round(luck, 1), "pairs": pairs, "hot_pairs": hot_pairs,
            "orders_after_hot": len(after_hot), "orders_after_not_hot": len(after_not), "pf_after_hot": r(pf(after_hot), 3), "pf_after_not_hot": r(pf(after_not), 3),
            "mean_cash_per_order_after_hot": r(sum(after_hot) / len(after_hot)) if after_hot else None, "mean_cash_per_order_after_not_hot": r(sum(after_not) / len(after_not)) if after_not else None,
            "D_dollars_per_order_of_10": r(d), "D_one_sided_p_day_bootstrap": r(p), "D_interval_95": [r(ci[0]), r(ci[1])],
            "median_block_length_by_band": {b: sorted(v)[len(v) // 2] for b, v in sorted(lens.items()) if v}, "blocks_by_band": {b: len(v) for b, v in sorted(lens.items())}}


def _split(groups):
    """groups: {(series, tpl): [(cash, win)] in time order}. -> (after HOT cash list, after not-HOT cash list), labelling each block by the block BEFORE it."""
    ah, an = [], []
    for (s, tpl), v in groups.items():
        if tpl[2] == FAV_HI[0]: continue
        ob = [{"cash": c, "win": w} for c, w in v]; sp = build_blocks(ob, tpl[1], BLOCK); fl = [is_hot(ob[a:e + 1]) for a, e in sp]
        for i in range(1, len(sp)):
            (ah if fl[i - 1] else an).extend(c for c, _ in v[sp[i][0]:sp[i][1] + 1])
    return ah, an


def null_calibration(orders, fair, observed_d, reps=None):
    """Auditor B's calibration (Amendment 1). Keep every order exactly as it is (market, look, side, price), redraw every market's result at random with the chance
    'fair' (its YES mid at its latest look), rebuild blocks and labels, and compute D. Repeat. No template has an edge or a streak in these made-up results, so the
    spread of D here is what luck alone gives at the observed signals and prices. -> the rank of the observed D among them."""
    reps = NULL_REPS if reps is None else reps
    by = collections.defaultdict(list)
    for o in sorted(orders, key=lambda o: (o["close"], o["ticker"])):
        if o["ticker"] not in fair: continue
        p = o["price"]; f = fee10(p)
        by[(o["series"], o["tpl"])].append((o["ticker"], o["side"] == "yes", SIZE * (1.0 - p) - f, -SIZE * p - f))
    tickers = sorted({x[0] for v in by.values() for x in v}); rng = random.Random(SEED + 1); ds, pfs = [], []
    for _ in range(reps):
        res = {t: rng.random() < fair[t] for t in tickers}
        groups = {k: [((cw, True) if res[t] == is_yes else (cl, False)) for t, is_yes, cw, cl in v] for k, v in by.items()}
        ah, an = _split(groups)
        if ah and an: ds.append(sum(ah) / len(ah) - sum(an) / len(an)); x = pf(ah); pfs.append(x if x is not None and x != float("inf") else None)
    if not ds or observed_d is None: return {"reps": len(ds), "D_null_calibrated_p": None}
    m = sum(ds) / len(ds); sd = (sum((v - m) ** 2 for v in ds) / max(1, len(ds) - 1)) ** 0.5; pfv = [v for v in pfs if v is not None]
    return {"reps": len(ds), "D_null_calibrated_p": round((1 + sum(1 for v in ds if v >= observed_d - EPS)) / (len(ds) + 1), 4), "null_D_mean": round(m, 4), "null_D_sd": round(sd, 4),
            "null_pf_after_hot_mean": round(sum(pfv) / len(pfv), 3) if pfv else None,
            "what": "made-up results drawn at each market's own YES mid, the real orders and prices kept; the share of such runs whose D is at least the observed D"}


def verdict(pr, null_p=None):
    n = pr["hot_pairs"]; pfh, d, p = pr["pf_after_hot"], pr["D_dollars_per_order_of_10"], pr["D_one_sided_p_day_bootstrap"]
    if n >= VERDICT_MIN_HOT and pfh is not None and d is not None:
        p_ok = p is not None and p <= VERDICT_P + EPS
        if VERDICT_NEEDS_BOTH_P: p_ok = p_ok and null_p is not None and null_p <= VERDICT_P + EPS
        if pfh >= VERDICT_PF - EPS and d > 0 and p_ok: return "PREMISE SUPPORTED"
        if pfh < 1.0 or d <= 0: return "PREMISE NOT SUPPORTED"
    return "no evidence at n = %d HOT pairs" % n


def sisters(g):
    """When a block is HOT, how often is the block of a sister template in the SAME market, covering the same moment, HOT too? Against that market's plain HOT share."""
    out = {}
    for series in sorted({s for s, _ in g}):
        tp = {tpl: gg["blocks"] for (s, tpl), gg in g.items() if s == series and tpl[2] != FAV_HI[0]}
        span = {tpl: [(b[0]["close"], b[-1]["close"], is_hot(b)) for b in bl] for tpl, bl in tp.items()}
        n_blocks = sum(len(v) for v in span.values()); base = sum(h for v in span.values() for _, _, h in v) / n_blocks if n_blocks else None
        tally = collections.defaultdict(lambda: [0, 0])
        for a, va in span.items():
            for lo, hi, h in va:
                if not h: continue
                mid = (lo + hi) / 2
                for b, vb in span.items():
                    if b == a: continue
                    hit = next((x for x in vb if x[0] <= mid <= x[1]), None)
                    if hit is None: continue
                    kind = "mirror side, same look" if (b[0] == a[0] and b[1] != a[1]) else ("same side, another look" if b[1] == a[1] and b[0] != a[0] else ("same side and look, another band" if b[1] == a[1] else "other"))
                    for k in (kind, "all sisters"): tally[k][0] += 1; tally[k][1] += hit[2]
        out[series] = {"hot_share_of_all_blocks": None if base is None else round(base, 4), "sister_also_hot": {k: {"pairs_looked_at": v[0], "also_hot": v[1], "share": round(v[1] / v[0], 4) if v[0] else None} for k, v in sorted(tally.items())}}
    return out


def secondary(g):
    """The wheel's real rule: a HOT block, then the next 30 signals at PF 1.0 or better (confirmation), then the 60 after those (the seat)."""
    seat = {"confirmed": [], "not_confirmed": []}; n = collections.Counter()
    for (s, tpl), gg in g.items():
        if tpl[2] == FAV_HI[0]: continue
        v = gg["orders"]
        for (a, e), bl in zip(gg["spans"], gg["blocks"]):
            if not is_hot(bl) or e + CONFIRM + BLOCK >= len(v): continue
            conf = [o["cash"] for o in v[e + 1:e + 1 + CONFIRM]]; nxt = [o["cash"] for o in v[e + 1 + CONFIRM:e + 1 + CONFIRM + BLOCK]]
            k = "confirmed" if _ge(pf(conf), 1.0) else "not_confirmed"; n[k] += 1; seat[k].extend(nxt)
    r = lambda v: None if v is None else (v if v == float("inf") else round(v, 3))
    return {k: {"hot_blocks_with_90_more_signals": n[k], "seat_orders": len(v), "seat_pf": r(pf(v)), "seat_mean_cash_per_order": round(sum(v) / len(v), 4) if v else None} for k, v in seat.items()}


def favourites(g):
    """Third line, apart: favourite ask 88c to 97c. A block is at least 150 signals and runs on to its 10th loss; HOT as elsewhere. Paired with the next such block."""
    res = {"blocks": 0, "hot_blocks": 0, "pairs": 0, "hot_pairs": 0}; ah, an, lens = [], [], []
    for (s, tpl), gg in g.items():
        if tpl[2] != FAV_HI[0]: continue
        bl = gg["blocks"]; fl = [is_hot(b) for b in bl]; res["blocks"] += len(bl); res["hot_blocks"] += sum(fl); lens.extend(len(b) for b in bl)
        for q in range(1, len(bl)):
            res["pairs"] += 1; res["hot_pairs"] += fl[q - 1]; (ah if fl[q - 1] else an).extend(o["cash"] for o in bl[q])
    r = lambda v: None if v is None else (v if v == float("inf") else round(v, 3))
    res.update({"pf_after_hot": r(pf(ah)), "pf_after_not_hot": r(pf(an)), "orders_after_hot": len(ah), "orders_after_not_hot": len(an), "median_block_length": sorted(lens)[len(lens) // 2] if lens else None,
                "label": "favourites 88c to 97c, reported apart and never pooled; %s" % ("no evidence at n = %d HOT pairs" % res["hot_pairs"] if res["hot_pairs"] < VERDICT_MIN_HOT else "see the figures")})
    return res


def counts(orders):
    """No result is held here, and a block's end depends on outcomes, so only orders are counted; orders // 60 is an upper bound on blocks."""
    by = collections.Counter((o["series"], o["tpl"]) for o in orders if o["tpl"][2] != FAV_HI[0])
    rows = [{"series": s, "L": t[0], "side": t[1], "band": t[2], "orders": n, "blocks_at_most": n // BLOCK} for (s, t), n in sorted(by.items())]
    return {"orders": len(orders), "blocks_at_most": sum(r["blocks_at_most"] for r in rows), "by_series": {s: {"orders": sum(r["orders"] for r in rows if r["series"] == s), "blocks_at_most": sum(r["blocks_at_most"] for r in rows if r["series"] == s)}
            for s in sorted({r["series"] for r in rows})}, "templates": rows}


def report(orders, label, fair=None):
    no_fair = 0
    if fair is not None:
        # Amendment 2, point 13 (the Head's ruling of 20:34Z): the observed D and the no-effect runs must use exactly the same orders, so an order whose market has no
        # chance value is dropped from BOTH, counted and printed. On a candle read the count is zero by construction (an order needs a two-sided candle at its own look).
        kept = [o for o in orders if o["ticker"] in fair]; no_fair = len(orders) - len(kept); orders = kept
    void = sum(1 for o in orders if o["win"] is None)
    for o in orders:
        if o["win"] is None: o["win"] = False                      # a void is a fee-only loss and counts as a loss, never as a win
    g = grid(orders); pooled = primary(g)
    cal = null_calibration(orders, fair, pooled["D_dollars_per_order_of_10"]) if fair is not None else None
    if cal is not None: pooled["null_calibration"] = cal
    npv = None if cal is None else cal.get("D_null_calibrated_p")
    out = {"source": label, "orders_dropped_from_both_reads_for_no_chance_value": no_fair, "caveat_first": "Real misses lean toward winners, so a candle read overstates the LEVEL of every profit factor; the comparison D between HOT and not-HOT carries the verdict.",
           "p_note": "Two p values are printed for D. The day bootstrap was found by Auditor B to be mildly generous on made-up no-effect data (p at or under 0.05 in 7.5 percent of runs). The null-calibrated p is the rank of the observed D among D from made-up no-effect results at the real orders and prices.", "orders": len(orders), "void_orders_booked_as_fee_only_loss": void, "primary_pooled": pooled, "verdict": verdict(pooled, npv), "verdict_rule_needs_both_p": VERDICT_NEEDS_BOTH_P,
           "primary_by_market": {s: dict(primary(g, s), verdict_shaped_label=verdict(primary(g, s)), label_note="per market, descriptive; the verdict is the pooled line") for s in sorted({k[0] for k in g})},
           "sister_templates_hot_together": sisters(g), "secondary_wheel_rule": secondary(g), "third_line_favourites_88_97": favourites(g),
           "all_orders_pf": (lambda v: None if v is None else round(v, 3))(pf([o["cash"] for o in orders if o["tpl"][2] != FAV_HI[0]]))}
    return out


# ---------------------------------------------------------------- commands
def precondition(now, marker_text):
    """None if the read may run, else the reason it is refused. Pure, so the selftest can try every case."""
    import re
    if now < NOT_BEFORE: return "refused: the WHEEL0 read is not allowed before 2026-11-14T00:00Z (DEPTH1 reads the gold windows first)"
    if not re.search(MARKER_RE, marker_text or ""): return "refused: WHEEL0_PRECONDITION.md does not carry the line 'DEPTH1 READ MADE: ...' (committed on the Head of R&D's word)"
    return None


def _args(a):
    out = collections.defaultdict(list); key = None
    for x in a:
        if x.startswith("--"): key = x[2:]; out[key]
        elif key: out[key].append(x)
    return out


def main(argv, _selftest_made_up_data=False):
    """_selftest_made_up_data is set only by selftest() for its made-up files; no command line value can set it."""
    if not argv or argv[0] not in ("selftest", "count", "run"): print(__doc__); return 2
    if argv[0] == "selftest": return selftest()
    a = _args(argv[1:]); drop, sha = load_drop_table()
    if argv[0] == "count":
        mk, c1 = read_markets(a["lists"], with_result=False); cd = read_candles(a["candles"], mk)
        od, c2 = orders_from_candles(mk, cd, drop)
        print(json.dumps({"note": "candle signals after the random drop; NO result read; nothing scored", "markets": len(mk), "market_counts": c1, "signal_counts": c2, "drop_table_sha256": sha, "counts": counts(od)}, indent=1)); return 0
    if not a["go"] or not a["out"]: raise SystemExit("refused: the read needs --go <the Head of R&D's go line> and --out <file>; it is run once")
    if os.path.exists(a["out"][0]): raise SystemExit("refused: %s exists; WHEEL0 is read once" % a["out"][0])
    if not _selftest_made_up_data:
        why = precondition(time.time(), open(MARKER_FILE).read() if os.path.exists(MARKER_FILE) else "")
        if why: raise SystemExit(why)
    mk, c1 = read_markets(a["lists"], with_result=True); cd = read_candles(a["candles"], mk)
    od, c2 = orders_from_candles(mk, cd, drop)
    if a["books"]: refuse_heldout(a["books"][0])
    fair = fair_yes(mk, cd)
    res = {"test": "WHEEL0", "tries": 1, "go": " ".join(a["go"]), "drop_table_sha256": sha, "scorer_sha256": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(),
           "markets": len(mk), "market_counts": c1, "candle_signal_counts": c2,
           "MAIN_candle_read": report(od, "CANDLE READ: 1 minute candles, random drop at the measured fill share, price = the ask seen; candle freshness measured on Bitcoin 15 minute only; real misses lean toward winners, so this read is generous", fair)}
    od0, _ = orders_from_candles(mk, cd, drop, apply_drop=False)
    res["sensitivity_no_drop"] = {k: v for k, v in report(od0, "candle read with NO drop (every signal filled): sensitivity only").items() if k in ("orders", "primary_pooled", "verdict")}
    if a["books"]:
        bm = {t: m for t, m in mk.items() if m["series"] in BOOK_SERIES}
        ob, c3 = orders_from_books(bm, a["books"][0]); win = {o["ticker"] for o in ob}
        lo = min((o["close"] for o in ob), default=None); hi = max((o["close"] for o in ob), default=None)
        same = [o for o in od if o["series"] in BOOK_SERIES and lo is not None and lo <= o["close"] <= hi]
        res["CROSS_CHECK_books"] = {"window": [lo, hi], "book_counts": c3, "book_read": report(ob, "BOOK READ: R6 order books, real fill check (10 contracts, ask + 1c, first poll within 4 s), gold, XRP and Dogecoin"),
                                    "candle_read_same_dates": {k: v for k, v in report(same, "candle read restricted to the book dates").items() if k in ("orders", "primary_pooled", "verdict", "all_orders_pf")}}
    json.dump(res, open(a["out"][0], "w"), indent=1, default=str)
    print(json.dumps({"verdict": res["MAIN_candle_read"]["verdict"], "primary_pooled": res["MAIN_candle_read"]["primary_pooled"]}, indent=1)); return 0


# ---------------------------------------------------------------- selftest (made-up data only)
def _synth(seed, persist, n_days=40, flip=False, after=None):
    """Made-up markets and candles. persist=True plants regimes: for days at a time the cheap side wins far more often than its price says."""
    rng = random.Random(seed); mk, cd = {}, {}
    for s in ("KXXRP15M", "KXDOGE15M"):
        for i in range(n_days * 96):
            c = FROM + 900 * (i + 1); t = "%s-W%05d" % (s, i); regime = persist and ((i // (96 * 20)) % 2 == 0)          # regimes of 20 days: several blocks long
            mid = rng.choice([0.12, 0.28, 0.43, 0.57, 0.72, 0.84]); cheap_yes = mid < 0.5; pc = min(mid, 1 - mid)
            p_cheap = min(0.95, pc * (1.9 if regime else 0.75)) if persist else pc
            cheap_wins = rng.random() < p_cheap; yes = cheap_wins if cheap_yes else (not cheap_wins)
            if flip: yes = not yes
            mk[t] = {"series": s, "close": c, "result": "yes" if yes else "no"}
            q = {c - L: (round(mid - 0.01, 2), round(mid + 0.01, 2)) for L in LOOKS}
            if after is not None:
                for dt in (120, 60, 0): q[c - dt] = (round(after - 0.01, 2), round(after + 0.01, 2))
            cd[t] = q
    return mk, cd


def selftest():
    ok = []
    def chk(name, cond, detail=""):
        ok.append(bool(cond)); print("%-108s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    drop = {(grp, L, k, b[0]): 0.8 for grp in ("gold_xrp_doge", "xrp_doge") for L in LOOKS for k in BANDS for b in BANDS[k]}; drop.update({(grp, L, "fav", FAV_HI[0]): 0.9 for grp in ("gold_xrp_doge", "xrp_doge") for L in LOOKS})
    chk("fee: 10 contracts at 50c cost 18c, at 12c 8c (rounded up)", fee10(0.50) == 0.18 and fee10(0.12) == 0.08)
    chk("cash: a 12c winner pays 8.80 less the fee, a loser costs 1.20 plus the fee, a void costs the fee", cash(0.12, "yes", "yes")[0] == 8.80 - 0.08 and abs(cash(0.12, "yes", "no")[0] + 1.28) < 1e-9 and cash(0.12, "yes", "")[0] == -0.08)
    t = template_of(0.27, 0.29)
    chk("template: YES 27/29 -> cheap side is YES at 29c in 20-35, favourite is NO at 73c in 65-80", t["cheap"] == ("yes", 0.29, "20-35") and t["fav"] == ("no", 0.73, "65-80"))
    chk("template: band edges (20c is in 20-35, 50c cheap is in 35-50, 50c is not a favourite, 88c is in 88-97 not 80-88)", template_of(0.19, 0.20)["cheap"][2] == "20-35" and template_of(0.86, 0.88)["fav"][2] == "88-97"
        and template_of(0.48, 0.50)["cheap"][2] == "35-50" and template_of(0.48, 0.50)["fav"] == ("no", 0.52, "50-65") and template_of(0.78, 0.80)["fav"][2] == "65-80" and template_of(0.79, 0.81)["fav"][2] == "80-88")
    chk("template: a 5c spread, a one-sided quote and equal asks give no signal", template_of(0.25, 0.30) == {} and template_of(0.0, 0.3) == {} and template_of(0.49, 0.51) == {})
    mk, cd = _synth(1, persist=False); od, _ = orders_from_candles(mk, cd, drop)
    sig = lambda o: sorted((x["ticker"], x["tpl"], x["side"], x["price"]) for x in o)
    mk2, cd2 = _synth(1, persist=False, flip=True); od2, _ = orders_from_candles(mk2, cd2, drop)
    chk("every result flipped -> the same orders, sides and prices (no outcome reaches a signal or the drop)", sig(od) == sig(od2), "n %d" % len(od))
    mk3, cd3 = _synth(1, persist=False, after=0.97); od3, _ = orders_from_candles(mk3, cd3, drop)
    chk("candles after the last look changed -> the same orders", sig(od) == sig(od3))
    g = grid(od); pr = primary(g)
    chk("no persistence planted -> not SUPPORTED, and HOT blocks near the luck count", verdict(pr) != "PREMISE SUPPORTED" and abs(pr["hot_blocks"] - pr["hot_blocks_expected_by_luck"]) < 4 * math.sqrt(pr["hot_blocks_expected_by_luck"] + 1),
        "hot %d, luck %.1f, D %s p %s" % (pr["hot_blocks"], pr["hot_blocks_expected_by_luck"], pr["D_dollars_per_order_of_10"], pr["D_one_sided_p_day_bootstrap"]))
    chk("no persistence planted -> PF after HOT is within noise of PF after not-HOT (a block labelled by its OWN flag would split them wide apart)",
        pr["pf_after_hot"] is not None and abs(pr["pf_after_hot"] - pr["pf_after_not_hot"]) < 0.30, "after HOT %s, after not-HOT %s" % (pr["pf_after_hot"], pr["pf_after_not_hot"]))
    ps = [pr["D_one_sided_p_day_bootstrap"]]
    for sd_ in (11, 12):
        mk_, cd_ = _synth(sd_, persist=False); o_, _ = orders_from_candles(mk_, cd_, drop); ps.append(primary(grid(o_))["D_one_sided_p_day_bootstrap"])
    chk("no persistence planted, three seeds -> the bootstrap p is not tiny and differs from seed to seed (a p forced to zero fails here)", min(ps) > 0.02 and len(set(ps)) == 3, str(ps))
    nc = null_calibration(od, fair_yes(mk, cd), pr["D_dollars_per_order_of_10"], reps=60)
    chk("null calibration: on no-effect data the observed D sits inside the made-up null spread (p not small), and the null D is centred near zero", nc["D_null_calibrated_p"] > 0.05 and abs(nc["null_D_mean"]) < 3 * nc["null_D_sd"], json.dumps(nc)[:160])
    mkp, cdp = _synth(2, persist=True, n_days=60); odp, _ = orders_from_candles(mkp, cdp, drop); prp = primary(grid(odp))
    chk("persistence planted (twenty-day regimes) -> D above zero with a small p (the test can see a real effect)", prp["D_dollars_per_order_of_10"] is not None and prp["D_dollars_per_order_of_10"] > 0 and prp["D_one_sided_p_day_bootstrap"] <= 0.05,
        "hot pairs %d, PF after HOT %s, D %s, p %s" % (prp["hot_pairs"], prp["pf_after_hot"], prp["D_dollars_per_order_of_10"], prp["D_one_sided_p_day_bootstrap"]))
    W, Lo = {"cash": 1.0, "win": True}, {"cash": -0.3, "win": False}
    chk("HOT: PF 1.3 on the block and 1.0 in each half (a block whose second half loses is not HOT)", is_hot([W] * 10 + [Lo] * 20 + [W] * 10 + [Lo] * 20) and not is_hot([W] * 20 + [Lo] * 40))
    v = [dict(Lo) for _ in range(200)]
    for i in (3, 9, 15, 21, 27, 33, 39, 45, 51, 70, 71, 72, 190): v[i] = dict(W)
    sp = build_blocks(v, "cheap", BLOCK)
    chk("a cheap block is at least 60 and runs on to its 10th win; the tail that never gets there is not a block", sp == [(0, 70)], str(sp))
    vf = [dict(W) for _ in range(140)]
    for i in list(range(0, 60, 6)) + [61, 62, 100]: vf[i] = dict(Lo)
    chk("a favourite block counts LOSSES as the rarer outcome: 10 losses by signal 55, so it ends at 60; the next never reaches 10", build_blocks(vf, "fav", BLOCK) == [(0, 59)], str(build_blocks(vf, "fav", BLOCK)))
    blocks = grid(od); any_k = next(k for k in blocks if len(blocks[k]["blocks"]) > 2); bb = blocks[any_k]["blocks"]; flat = [o["ticker"] for bl in bb for o in bl]
    chk("blocks do not overlap, are in time order, each at least 60", len(flat) == len(set(flat)) and all(bb[i][-1]["close"] <= bb[i + 1][0]["close"] for i in range(len(bb) - 1)) and min(len(x) for x in bb) >= BLOCK)
    mk4 = {"KXBTC15M-A": {"ticker": "KXBTC15M-A", "close_time": "2026-10-29T00:15:00Z", "result": "yes"}, "KXBTC15M-B": {"ticker": "KXBTC15M-B", "close_time": "2026-10-28T23:45:00Z", "result": "yes"},
           "KXXRP15M-C": {"ticker": "KXXRP15M-C", "close_time": "2026-11-05T00:15:00Z", "result": "no"}}
    d = tempfile.mkdtemp(prefix="w0_"); gzip.open(os.path.join(d, "0001.json.gz"), "wt").write(json.dumps({"markets": list(mk4.values())})); json.dump({"rows": [{"status": 200, "file": "0001.json.gz"}]}, open(os.path.join(d, "manifest.json"), "w"))
    m, c = read_markets([d], with_result=True)
    chk("rule (h): a Bitcoin market closing on or after Oct 29 is dropped at the reader; XRP after it is kept", set(m) == {"KXBTC15M-B", "KXXRP15M-C"} and c.get("rule_h_dropped_KXBTC15M") == 1)
    chk("the count command path never holds a result", all(v["result"] is None for v in read_markets([d], with_result=False)[0].values()))
    h = os.path.join(tempfile.mkdtemp(prefix="w0h_"), "HELDOUT_X"); os.makedirs(h); json.dump({"rows": []}, open(os.path.join(h, "manifest.json"), "w")); link = os.path.join(os.path.dirname(h), "ok"); os.symlink(h, link)
    ref = 0
    for p in (h, link):
        try: read_markets([p], False)
        except SystemExit: ref += 1
    for pth in (h, link):
        try: orders_from_books({}, pth)
        except SystemExit: ref += 1
    chk("a HELDOUT_ folder is refused, typed or through an innocent link, as lists, candles or the books root", ref == 4)
    chk("the random drop is fixed per signal and near its rate", keep_draw("T", 600, "yes") == keep_draw("T", 600, "yes") and 0.77 < sum(keep_draw("T%d" % i, 360, "no") < 0.8 for i in range(20000)) / 20000 < 0.83)
    fo = [{"series": "S", "tpl": (600, "fav", "88-97"), "ticker": "t%04d" % i, "close": i, "day": "d", "cash": (0.9 if i % 16 else -9.3), "win": bool(i % 16)} for i in range(700)]
    fv = favourites(grid(fo))
    chk("favourites line: blocks of at least 150 that run on to the 10th loss", fv["blocks"] == 4 and fv["pairs"] == 3, json.dumps({k: fv[k] for k in ("blocks", "pairs", "median_block_length")}))
    # end to end through the files, as the read will run: made-up lists and candles written as pull run folders
    td = tempfile.mkdtemp(prefix="w0e_"); Lf, Cf = os.path.join(td, "lists"), os.path.join(td, "candles"); os.makedirs(Lf); os.makedirs(Cf)
    iso = lambda t_: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_))
    gzip.open(os.path.join(Lf, "0001.json.gz"), "wt").write(json.dumps({"markets": [{"ticker": t_, "close_time": iso(m_["close"]), "result": m_["result"]} for t_, m_ in mkp.items()]}))
    json.dump({"rows": [{"status": 200, "file": "0001.json.gz"}]}, open(os.path.join(Lf, "manifest.json"), "w"))
    gzip.open(os.path.join(Cf, "0001.json.gz"), "wt").write(json.dumps({"markets": [{"market_ticker": t_, "candlesticks": [{"end_period_ts": e_, "yes_bid": {"close_dollars": "%.4f" % q_[0]}, "yes_ask": {"close_dollars": "%.4f" % q_[1]}} for e_, q_ in c_.items()]} for t_, c_ in cdp.items()]}))
    json.dump({"rows": [{"status": 200, "file": "0001.json.gz"}]}, open(os.path.join(Cf, "manifest.json"), "w"))
    import io, contextlib
    outf = os.path.join(td, "res.json"); buf = io.StringIO()
    with contextlib.redirect_stdout(buf): rc = main(["run", "--lists", Lf, "--candles", Cf, "--out", outf, "--go", "selftest"], _selftest_made_up_data=True)
    res = json.load(open(outf)); mr = res["MAIN_candle_read"]
    chk("the whole read runs from files and returns one of the three registered labels", rc == 0 and (mr["verdict"] in ("PREMISE SUPPORTED", "PREMISE NOT SUPPORTED") or mr["verdict"].startswith("no evidence at n = ")), mr["verdict"])
    chk("the result carries pooled and per-market numbers, sisters, the wheel rule, the favourites line and block lengths", all(k in mr for k in ("primary_pooled", "primary_by_market", "sister_templates_hot_together", "secondary_wheel_rule", "third_line_favourites_88_97"))
        and "median_block_length_by_band" in mr["primary_pooled"] and len(mr["primary_by_market"]) == 2)
    again = 0
    try:
        with contextlib.redirect_stdout(io.StringIO()): main(["run", "--lists", Lf, "--candles", Cf, "--out", outf, "--go", "selftest"], _selftest_made_up_data=True)
    except SystemExit: again = 1
    chk("a second read into the same result file is refused (read once)", again == 1)
    fz = fair_yes(mk, cd); gone = sorted(fz)[:25]
    for t_ in gone: del fz[t_]
    od_c = [dict(o) for o in od]; rp = report(od_c, "selftest", fz); n_gone = sum(1 for o in od if o["ticker"] in set(gone))
    chk("an order whose market has no chance value is dropped from BOTH the observed read and the no-effect runs, and counted", n_gone > 0 and rp["orders_dropped_from_both_reads_for_no_chance_value"] == n_gone and rp["orders"] == len(od) - n_gone,
        "dropped %d of %d" % (n_gone, len(od)))
    good = "x\nDEPTH1 READ MADE: 2026-11-14, recorded by the Head of R&D\n"
    chk("precondition: refused before 2026-11-14T00:00Z even with the marker; refused after it without the marker; allowed only with both",
        precondition(NOT_BEFORE - 1, good) is not None and precondition(NOT_BEFORE + 1, "") is not None and precondition(NOT_BEFORE + 1, "DEPTH1 READ MADE:") is not None and precondition(NOT_BEFORE + 1, good) is None)
    if time.time() < NOT_BEFORE or not os.path.exists(MARKER_FILE):
        blocked = 0
        try:
            with contextlib.redirect_stdout(io.StringIO()): main(["run", "--lists", Lf, "--candles", Cf, "--out", os.path.join(td, "res2.json"), "--go", "x"])
        except SystemExit as e: blocked = 1 if "refused" in str(e) else 0
        chk("the real command line cannot run the read today (no flag reaches the selftest's bypass)", blocked == 1 and not os.path.exists(os.path.join(td, "res2.json")))
    pv = {"hot_pairs": 40, "pf_after_hot": 1.2, "D_dollars_per_order_of_10": 0.3, "D_one_sided_p_day_bootstrap": 0.03}
    chk("verdict: SUPPORTED needs BOTH p values at or under 0.05 (bootstrap 0.03 with a null p of 0.08, or with none, is not SUPPORTED)",
        verdict(pv, 0.04) == "PREMISE SUPPORTED" and verdict(pv, 0.08).startswith("no evidence") and verdict(pv, None).startswith("no evidence") and verdict(dict(pv, D_one_sided_p_day_bootstrap=0.06), 0.01).startswith("no evidence")
        and verdict(dict(pv, pf_after_hot=0.99), 0.01) == "PREMISE NOT SUPPORTED" and verdict(dict(pv, hot_pairs=29), 0.01) == "no evidence at n = 29 HOT pairs")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): main(["count", "--lists", Lf, "--candles", Cf])
    cj = json.loads(buf.getvalue())
    chk("the count command reports orders and no profit, win or verdict field", cj["counts"]["orders"] > 0 and not any(w in buf.getvalue() for w in ("pf", "verdict", "win", "cash")))
    print("\n%d checks, %d FAIL" % (len(ok), sum(1 for x in ok if not x)))
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
