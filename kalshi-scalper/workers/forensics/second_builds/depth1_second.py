#!/usr/bin/env python3
"""DEPTH1, an INDEPENDENT SECOND BUILD of the scorer (Forensics desk, 2026-11-13, on the Head of R&D's order under rule 16b).
Written from the registration text (V2's workers/DEPTH1_REGISTRATION.md and the frozen settings in DEPTH1_FROZEN.md) and Desk A's DEPTH1_AMENDMENT_1_DESK_A.md ALONE.
Not read: V2's depth1.py, its tests, Desk A's depth1_wrapper.py, depth1_dryrun.py and depth1_precheck.py. The recorder's column names come from scripts/record_15m_book.py on main.
Disclosure: for WHEEL0's books-only count on Nov 12 this desk read R6 gold, XRP and Dogecoin books (no result joined). No R6 file was opened for this build.

DEFAULT-CLOSED. `read` refuses before 2026-11-14T00:00:00Z, refuses a second run (a result file) and refuses after a started marker; any path in or resolving into a
HELDOUT_ folder is refused. Before the read time the scorer runs only from Python on a folder that carries the marker file MADE_UP_DATA (measure(root, made_up=True)).

usage (after the read time, on the Head's word only): python3 -I depth1_second.py read <R6 root: folders <date>/<HHMM>/{book,trades,coverage}.csv.gz> <out dir>

Places where the text leaves a choice (AMBIGUITIES, printed with the output):
 1. Poll time: t_recv_ms plus the run's clock offset (median over the run's book rows of Date header + 0.5 s minus t_recv_ms). The close T is the coverage row's close_time.
 2. Coverage times (first_recv_ms, last_recv_ms) are compared with T after adding the same run offset.
 3. A ticker with coverage rows in two runs: the usable row with the most ok_polls is the window; its book rows are that run's only. One window counts once.
 4. The decision poll: the last poll with time at or before T-480 s and no earlier than T-490 s. A window with such a poll is a scored window even if that poll's book is one-sided or empty (aligned to the first build on Nov 13; every imbalance feature is then undefined, but f7 can still fire from the tape).
 5. The 30 s and 60 s lookbacks are measured from the DECISION POLL's own time: the last poll at or before (decision poll time minus 30 s or 60 s) and no more than 6 s before that.
 6. f7's tape window: trades with created_time in [decision poll time minus 60 s, decision poll time). A sweep: same taker side, same whole second (of created_time), two or more distinct prices.
 7. The fill poll: the first poll at or after (decision poll time + 1.0 s) and no later than 20 s after that instant. The other reading (from T-480 s itself) is not built.
 8. f3: weighted YES bid = sum(px x sz)/sum(sz) over the YES levels; weighted YES ask = 1 minus the same over the NO levels; plain mid = (YES bid 1 + (1 - NO bid 1))/2.
 9. f6: thin side = the smaller 5 level size 60 s ago; value = (then - now)/then for that side, positive when the thin side is NO, negated when it is YES; equal sizes then = 0; thin size then of 0 = undefined.
10. f8: gap = level 1 price minus level 2 price; a missing level 2 gives a gap of the whole level 1 price. f9 needs two levels a side; slope = (level 1 price - last level price)/sum of sizes.
11. f10: levels whose price is within 0.03 of the side's level 1 price (inclusive, tolerance 1e-9).
12. A feature whose absolute value is at or under 1e-12 is zero (no trade): the registered sign rule says "0 or undefined: no trade", and a zero computed in floating point can come out as a residue near 1e-17. The first build trades on any non-zero float; setting ZERO_TOL to 0.0 reproduces it.
13. Halves: the try's trades in close-time order, first floor(n/2) and the rest. Blocks by US Central close date.
14. Date-clustered z, as the first build prints it (aligned Nov 13): sum of nets over sqrt(sum over US Central close dates of (date sum - date n x mean)^2), with NO small-sample factor. The same with the usual D/(D-1) factor on the variance is printed beside it; it is smaller by sqrt((D-1)/D), 3.4% at 15 dates. Direction accuracy is wins over ALL trades (a fee-only no-result trade counts as a miss); wins over settled trades is printed beside it.
15. Shuffled-book control: one permutation of the windows a market and round; a window's whole vector of 10 feature values moves together; the window keeps its own fill quotes and result. random.Random(20261114), markets in the order gold, Bitcoin, 1,000 rounds. A try with under 30 trades in a round is not counted in that round's best. An independent build cannot reproduce another build's random draws: the 99th percentile is compared approximately.
16. Overlap: gold "held" = exactly one side's ask 0.88 to 0.97 at the last poll at or before T-360 s (within 10 s). Bitcoin needs candles this build does not read: every Bitcoin window is "unknown".
17. The history check (candles, weaker evidence, not part of the verdict) is not built here.
18. Stop rule (Amendment 1, point 6): fired windows with no yes or no result over 1% of fired windows, counted per try and on distinct windows; the stop uses distinct fired windows over both markets.
"""
import sys, os, csv, gzip, glob, json, math, random, statistics, collections, time, email.utils
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

MARKETS = ("KXGOLD15M", "KXBTC15M")
CT = ZoneInfo("America/Chicago")
FIRST_DATE, LAST_DATE = "2026-10-30", "2026-11-13"
BLOCKS = (("A", "2026-10-30", "2026-11-03"), ("B", "2026-11-04", "2026-11-08"), ("C", "2026-11-09", "2026-11-13"))
LOOK_S, DEC_EARLY_S, LOOKBACK_EARLY_S, LIVE_S, FILL_LATE_S, TAPE_S = 480, 10, 6, 1.0, 20, 60
BAND, MIN_SIZE = (0.10, 0.90), 1.0
USABLE = {"min_ok": 0.80, "max_gap_ms": 20000, "first_s": 545, "last_s": 470, "bad": ("tape incomplete", "tape page cap", "tape out of time")}
BAR = {"n": 300, "pf": 1.5, "halves": 1.0, "stress_pf": 1.2, "z": 5.27, "z_shared": 5.46}
NEED_WINDOWS, SHUFFLES, SEED, CONTROL_P, MIN_SHUFFLE_TRADES = 300, 1000, 20261114, 0.01, 30
READ_NOT_BEFORE = 1794614400            # 2026-11-14T00:00:00Z
RECORDER_END_MS = (READ_NOT_BEFORE - 60) * 1000      # CONFIG recorder_end_utc 2026-11-13T23:59:00Z; the first build drops a window that opened (close minus 900 s) at or after it (Desk A, Nov 13)
COVERAGE_OFFSET = 0                     # the first build compares the coverage row's raw receive times with T (no clock offset); 1 would add the run's offset
ZERO_TOL = 1e-12                        # a feature this close to zero is "zero: no trade" (AMBIGUITY 12); 0.0 reproduces a build that trades on any non-zero float
EPS = 1e-9
FEATURES = ("f1_imb5", "f2_imb1", "f3_dwmid_minus_mid", "f4_d_imb30", "f5_d_imb60", "f6_thin_depletion", "f7_sweep_net", "f8_hole_asymmetry", "f9_book_slope", "f10_imb_3c")
CLOSED_FAMILY = ("f6_thin_depletion", "f7_sweep_net")
FRESH = "blind as to its own features; not blind as to cheap-side and favourite-side baselines on the same windows"
AMBIGUITIES = [l.strip() for l in __doc__.split("AMBIGUITIES, printed with the output):")[1].strip().split("\n")]
assert READ_NOT_BEFORE == int(datetime(2026, 11, 14, tzinfo=timezone.utc).timestamp())


def refuse_heldout(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % path)


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError): return None


def iso_ms(s):
    try: return int(round(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp() * 1000))
    except Exception: return None


def rows(path):
    with gzip.open(path, "rt", newline="") as f: yield from csv.DictReader(f)


# ---------------------------------------------------------------- the book of one poll, and the 10 features
def book(r):
    y = [(num(r.get("yes_bid_px_%d" % i)), num(r.get("yes_bid_sz_%d" % i))) for i in range(1, 6)]
    n = [(num(r.get("no_bid_px_%d" % i)), num(r.get("no_bid_sz_%d" % i))) for i in range(1, 6)]
    keep = lambda lv: [(p, s) for p, s in lv if p is not None and s is not None and s > 0]
    return {"y": keep(y), "n": keep(n)}


def _imb(a, b): return None if a + b <= 0 else (a - b) / (a + b)
def _tot(lv): return sum(s for _, s in lv)
def f1(b): return None if (not b["y"] or not b["n"]) else _imb(_tot(b["y"]), _tot(b["n"]))      # both sides must be quoted at that poll (aligned to the first build, Nov 13)
def f2(b): return None if not b["y"] or not b["n"] else _imb(b["y"][0][1], b["n"][0][1])
def f3(b):
    if not b["y"] or not b["n"]: return None
    wy = sum(p * s for p, s in b["y"]) / _tot(b["y"]); wn = sum(p * s for p, s in b["n"]) / _tot(b["n"])
    return (wy + (1 - wn)) / 2 - (b["y"][0][0] + (1 - b["n"][0][0])) / 2
def f6(now, then):
    if then is None or not now["y"] or not now["n"] or not then["y"] or not then["n"]: return None      # both sides quoted at both polls (aligned to the first build, Nov 13)
    ty, tn = _tot(then["y"]), _tot(then["n"])
    if abs(ty - tn) < EPS: return 0.0
    if tn < ty: return None if tn <= 0 else (tn - _tot(now["n"])) / tn
    return None if ty <= 0 else -((ty - _tot(now["y"])) / ty)
def f8(b):
    if not b["y"] or not b["n"]: return None
    gap = lambda lv: lv[0][0] - (lv[1][0] if len(lv) > 1 else 0.0)
    return gap(b["n"]) - gap(b["y"])
def f9(b):
    if len(b["y"]) < 2 or len(b["n"]) < 2: return None
    slope = lambda lv: (lv[0][0] - lv[-1][0]) / _tot(lv)
    return slope(b["n"]) - slope(b["y"])
def f10(b):
    if not b["y"] or not b["n"]: return None
    near = lambda lv: sum(s for p, s in lv if lv[0][0] - p <= 0.03 + EPS)
    return _imb(near(b["y"]), near(b["n"]))
def f7(trades, t_ms):
    """trades: [(created_ms, price, taker side)] of the window's ticker. Sweeps in [t - 60 s, t)."""
    groups = collections.defaultdict(set)
    for ms, px, side in trades:
        if t_ms - TAPE_S * 1000 <= ms < t_ms and side in ("yes", "no") and px is not None: groups[(side, ms // 1000)].add(round(px, 6))
    sw = collections.Counter(side for (side, _), pxs in groups.items() if len(pxs) >= 2)
    return float(sw["yes"] - sw["no"])


def fee_up(p): return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100.0


# ---------------------------------------------------------------- reading R6 folders
def load(root):
    """-> windows: {ticker: {...}}, counts. One coverage row a ticker (AMBIGUITY 3)."""
    refuse_heldout(root)
    C = collections.Counter(); cand = collections.defaultdict(list); runs = {}
    for cov in sorted(glob.glob(os.path.join(root, "*", "*", "coverage.csv.gz"))):
        run = os.path.dirname(cov); refuse_heldout(run)
        for r in rows(cov):
            if r.get("series") in MARKETS and r.get("ticker"): cand[r["ticker"]].append((run, r))
            elif r.get("series") in MARKETS: C["coverage rows with no ticker"] += 1
    need_runs = {run for v in cand.values() for run, _ in v}
    polls = collections.defaultdict(lambda: collections.defaultdict(list)); tape = collections.defaultdict(lambda: collections.defaultdict(list))
    for run in sorted(need_runs):
        offs = []
        bp = os.path.join(run, "book.csv.gz")
        if os.path.exists(bp):
            for r in rows(bp):
                tr = num(r.get("t_recv_ms"))
                if tr is None: continue
                d = email.utils.parsedate_to_datetime(r["server_date_header"]) if r.get("server_date_header") else None
                if d is not None: offs.append(d.timestamp() * 1000 + 500 - tr)
                if r.get("series") in MARKETS and r.get("ticker"): polls[run][r["ticker"]].append((tr, book(r)))
        runs[run] = statistics.median(offs) if offs else None
        tp = os.path.join(run, "trades.csv.gz")
        if os.path.exists(tp):
            for r in rows(tp):
                ms = iso_ms(r.get("created_time"))
                if ms is not None and r.get("ticker"): tape[run][r["ticker"]].append((ms, num(r.get("yes_price_dollars")), str(r.get("taker_outcome_side") or "").lower()))
    windows = {}; why = collections.Counter()
    for tk, lst in sorted(cand.items()):
        best = None
        for run, r in lst:
            T = iso_ms(r.get("close_time")); off = runs.get(run)
            if T is None: why["no close time"] += 1; continue
            date = datetime.fromtimestamp(T / 1000, CT).strftime("%Y-%m-%d")
            if date < FIRST_DATE: why["dated before 2026-10-30 (US Central close date), excluded"] += 1; continue
            if date > LAST_DATE: why["dated after 2026-11-13, excluded"] += 1; continue
            if off is None: why["no clock in the run"] += 1; C["windows with no clock"] += 1; continue
            p, ok = num(r.get("polls")), num(r.get("ok_polls")); fails = []
            if not p or ok is None or ok / p < USABLE["min_ok"] - EPS: fails.append("ok polls under 80%")
            if (num(r.get("max_gap_ms")) or 0) > USABLE["max_gap_ms"]: fails.append("largest gap over 20 s")
            if (num(r.get("tape_pages")) or 0) < 1 or any(b in str(r.get("note") or "") for b in USABLE["bad"]): fails.append("tape missing or incomplete")
            fr, lr = num(r.get("first_recv_ms")), num(r.get("last_recv_ms"))
            if fr is None or fr + COVERAGE_OFFSET * off > T - USABLE["first_s"] * 1000: fails.append("first poll after T-545 s")
            if lr is None or lr + COVERAGE_OFFSET * off < T - USABLE["last_s"] * 1000: fails.append("last poll before T-470 s")
            if T - 900 * 1000 >= RECORDER_END_MS: fails.append("window opened at or after the recorder end (2026-11-13T23:59Z)")
            for f_ in fails: why[f_] += 1
            if fails: continue
            if best is None or ok > best["ok"]:
                res = str(r.get("result") or "").strip().lower()
                best = {"ticker": tk, "series": r["series"], "T": T, "date": date, "run": run, "off": off, "ok": ok, "result": res}
        if best is None: C["windows not usable"] += 1; continue
        best["polls"] = sorted(((t + best["off"], b) for t, b in polls[best["run"]].get(tk, [])), key=lambda x: x[0])
        best["tape"] = tape[best["run"]].get(tk, [])
        windows[tk] = best; C["usable windows (Amendment 1: never dropped for a missing result)"] += 1
    return windows, C, why


def last_at_or_before(polls, t, early_ms):
    got = None
    for pt, b in polls:
        if pt > t: break
        if pt >= t - early_ms: got = (pt, b)
    return got


def first_at_or_after(polls, t, late_ms):
    for pt, b in polls:
        if pt >= t: return (pt, b) if pt <= t + late_ms else None
    return None


def prepare(w):
    """features at the decision poll and the fill quotes. No result is touched here."""
    T = w["T"]; dec = last_at_or_before(w["polls"], T - LOOK_S * 1000, DEC_EARLY_S * 1000)
    if dec is None: return "no decision poll"
    t0, b0 = dec
    p30 = last_at_or_before(w["polls"], t0 - 30000, LOOKBACK_EARLY_S * 1000); p60 = last_at_or_before(w["polls"], t0 - 60000, LOOKBACK_EARLY_S * 1000)
    a = f1(b0)
    feats = {"f1_imb5": a, "f2_imb1": f2(b0), "f3_dwmid_minus_mid": f3(b0),
             "f4_d_imb30": None if (p30 is None or a is None or f1(p30[1]) is None) else a - f1(p30[1]),
             "f5_d_imb60": None if (p60 is None or a is None or f1(p60[1]) is None) else a - f1(p60[1]),
             "f6_thin_depletion": f6(b0, p60[1] if p60 else None), "f7_sweep_net": f7(w["tape"], t0),
             "f8_hole_asymmetry": f8(b0), "f9_book_slope": f9(b0), "f10_imb_3c": f10(b0)}
    fill = first_at_or_after(w["polls"], t0 + LIVE_S * 1000, FILL_LATE_S * 1000)
    q = {"yes": None, "no": None}
    if fill is not None:
        bf = fill[1]
        if bf["n"]: q["yes"] = (1 - bf["n"][0][0], bf["n"][0][1])          # buying YES lifts the NO bid
        if bf["y"]: q["no"] = (1 - bf["y"][0][0], bf["y"][0][1])
    held = None
    if w["series"] == "KXGOLD15M":
        l1 = last_at_or_before(w["polls"], T - 360000, DEC_EARLY_S * 1000)
        if l1 is not None and l1[1]["y"] and l1[1]["n"]:
            asks = (1 - l1[1]["n"][0][0], 1 - l1[1]["y"][0][0]); held = sum(1 for x in asks if 0.88 - EPS <= x <= 0.97 + EPS) == 1
    nxt = [b for pt, b in w["polls"] if t0 < pt <= t0 + 4500][:2]            # the next two 2 s polls, for the noise description only
    return {"feats": feats, "q": q, "fill_delay": None if fill is None else (fill[0] - t0) / 1000.0, "held": held, "noise": [{"f1": f1(b), "f2": f2(b), "f3": f3(b), "f8": f8(b), "f9": f9(b), "f10": f10(b)} for b in nxt]}


def trade(value, q, result):
    """-> None (no trade) or a string reason, or (net, stress net, ask, win or None)."""
    if value is None or abs(value) <= ZERO_TOL: return "no signal"
    side = "yes" if value > 0 else "no"; quote = q[side]
    if quote is None: return "no fill poll or no ask"
    ask, size = quote
    if not (BAND[0] - EPS <= ask <= BAND[1] + EPS): return "ask outside 0.10 to 0.90"
    if size < MIN_SIZE - EPS: return "under 1 contract at the ask"
    fee = fee_up(ask)
    if result not in ("yes", "no"): return (-fee, -1.2 * fee, ask, None)      # Amendment 1, point 2: a fired window with no yes or no result is a fee-only loss
    win = result == side
    return ((1 - ask - fee) if win else (-ask - fee), (1 - ask - 1.2 * fee) if win else (-ask - 1.2 * fee), ask, win)


def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return None if l == 0 and w == 0 else (float("inf") if l == 0 else w / l)


def zstats(tr):
    n = len(tr)
    if n < 2: return None, None
    m = sum(t["net"] for t in tr) / n; by = collections.defaultdict(lambda: [0.0, 0])
    for t in tr: by[t["date"]][0] += t["net"]; by[t["date"]][1] += 1
    D = len(by)
    if D < 2: return None, None
    v = sum((s - k * m) ** 2 for s, k in by.values())
    z = None if v <= 0 else m * n / math.sqrt(v)                                    # as the first build prints it: no small-sample factor
    zc = None if z is None else z * math.sqrt((D - 1) / D)                           # with the usual D/(D-1) factor on the variance: smaller by sqrt((D-1)/D), 3.4% at 15 dates
    return z, zc


def score(trs):
    trs = sorted(trs, key=lambda t: (t["T"], t["ticker"])); n = len(trs); nets = [t["net"] for t in trs]; st = [t["stress"] for t in trs]
    blocks = {name: pf([t["net"] for t in trs if lo <= t["date"] <= hi]) for name, lo, hi in BLOCKS}
    h = n // 2; z, tday = zstats(trs); wins = sum(1 for t in trs if t["win"]); settled = sum(1 for t in trs if t["win"] is not None)
    return {"n": n, "wins": wins, "no_result_fee_only": n - settled, "direction_accuracy": (wins / n) if n else None, "direction_accuracy_over_settled_trades_only": (wins / settled) if settled else None, "mean_ask": (sum(t["ask"] for t in trs) / n) if n else None,
            "pf": pf(nets), "pf_blocks": blocks, "block_n": {name: sum(1 for t in trs if lo <= t["date"] <= hi) for name, lo, hi in BLOCKS}, "pf_halves": [pf(nets[:h]), pf(nets[h:])],
            "net_per_trade": (sum(nets) / n) if n else None, "net_per_trade_fee_x1.2": (sum(st) / n) if n else None, "pf_fee_x1.2": pf(st), "z_date_clustered": z, "z_with_the_D_over_D_minus_1_factor": tday}


def meets_bar(s, control_ok):
    g = lambda x, bar: x is not None and x >= bar - EPS
    gt = lambda x, bar: x is not None and x > bar + EPS
    return (s["n"] >= BAR["n"] and g(s["pf"], BAR["pf"]) and all(g(v, BAR["pf"]) for v in s["pf_blocks"].values()) and all(gt(v, BAR["halves"]) for v in s["pf_halves"])
            and gt(s["net_per_trade"], 0) and gt(s["net_per_trade_fee_x1.2"], 0) and gt(s["pf_fee_x1.2"], BAR["stress_pf"]) and g(s["z_date_clustered"], BAR["z"]) and control_ok)


def measure(root, made_up=False, now=None):
    now = time.time() if now is None else now
    if made_up:
        if not os.path.exists(os.path.join(root, "MADE_UP_DATA")): raise SystemExit("REFUSED: made_up=True needs the marker file MADE_UP_DATA in the folder")
    elif now < READ_NOT_BEFORE: raise SystemExit("REFUSED: DEPTH1 is not read before 2026-11-14T00:00:00Z")
    windows, C, why = load(root)
    out = {"build": "Forensics second build of DEPTH1", "label": FRESH, "made_up_data": bool(made_up), "counts": C, "usable_conditions_that_removed_a_coverage_row": dict(why), "ambiguities": AMBIGUITIES}
    prep = {}; per_market = collections.Counter(); skip = collections.Counter()
    for tk, w in windows.items():
        p = prepare(w)
        if isinstance(p, str): skip[w["series"] + ": " + p] += 1; continue
        prep[tk] = p; per_market[w["series"]] += 1
    out["windows_with_a_decision_poll"] = dict(per_market); out["usable_windows_without_one"] = dict(skip)
    clockless = C["windows with no clock"]
    if clockless > 0.2 * (clockless + len(windows)): out["verdict"] = "NOT_RUNNABLE: more than 20% of windows lack a clock"; return out
    if any(per_market[m] < NEED_WINDOWS for m in MARKETS):
        out["verdict"] = "NOT_ENOUGH_DATA: %s windows with a decision poll (need 300 a market); nothing is scored" % ", ".join("%s %d" % (m, per_market[m]) for m in MARKETS); return out
    # ---- printed before the verdict lines, cannot change them (Amendment 1, point 7); no outcome is read here
    desc = {}
    for m in MARKETS:
        ps = [p for tk, p in prep.items() if windows[tk]["series"] == m]; d = {}
        for short, full in (("f1", "f1_imb5"), ("f2", "f2_imb1"), ("f3", "f3_dwmid_minus_mid"), ("f8", "f8_hole_asymmetry"), ("f9", "f9_book_slope"), ("f10", "f10_imb_3c")):
            looks = [p for p in ps if p["feats"][full] is not None and abs(p["feats"][full]) >= 1e-12 and p["noise"]]
            flips = sum(1 for p in looks if any(nx[short] is not None and abs(nx[short]) >= 1e-12 and (nx[short] > 0) != (p["feats"][full] > 0) for nx in p["noise"]))
            d[full] = {"looks": len(looks), "share_sign_changes_within_two_polls": (flips / len(looks)) if looks else None}
        delays = [p["fill_delay"] for p in ps if p["fill_delay"] is not None]
        desc[m] = {"noise": d, "median_fill_delay_s": statistics.median(delays) if delays else None, "windows_with_no_fill_poll": sum(1 for p in ps if p["fill_delay"] is None)}
    out["no_label_description"] = desc
    # ---- the 20 tries
    tries = {}; reasons = collections.Counter(); fired_windows, fired_noresult = set(), set(); raw_noresult = collections.Counter()
    for m in MARKETS:
        for f in FEATURES:
            trs = []
            for tk, p in prep.items():
                w = windows[tk]
                if w["series"] != m: continue
                r = trade(p["feats"][f], p["q"], w["result"])
                if isinstance(r, str): reasons["%s %s: %s" % (m, f, r)] += 1; continue
                trs.append({"ticker": tk, "T": w["T"], "date": w["date"], "net": r[0], "stress": r[1], "ask": r[2], "win": r[3], "held": p["held"]})
                fired_windows.add(tk)
                if r[3] is None and tk not in fired_noresult: fired_noresult.add(tk); raw_noresult[w["result"] or "(empty)"] += 1
            tries[(m, f)] = trs
    out["AMENDMENT 1 COUNT"] = {"fired_windows": len(fired_windows), "fired_windows_with_no_yes_or_no_result": len(fired_noresult), "raw_result_values_of_those_windows": dict(raw_noresult)}
    out["no_trade_reasons"] = dict(reasons)
    if fired_windows and len(fired_noresult) > 0.01 * len(fired_windows):
        out["verdict"] = "STOPPED before any verdict line (Amendment 1, point 6): %d of %d fired windows have no yes or no result, over 1%%; the Head decides" % (len(fired_noresult), len(fired_windows)); return out
    # ---- shuffled-book control
    rng = random.Random(SEED); real_mean = {k: (sum(t["net"] for t in v) / len(v)) if v else None for k, v in tries.items()}
    by_m = {m: [tk for tk in sorted(prep) if windows[tk]["series"] == m] for m in MARKETS}
    best_of_20 = []; ge = collections.Counter(); counted = collections.Counter()
    for _ in range(SHUFFLES):
        best = None
        for m in MARKETS:
            tks = by_m[m]; perm = tks[:]; rng.shuffle(perm)
            for f in FEATURES:
                s = 0.0; k = 0
                for dst, src in zip(tks, perm):
                    r = trade(prep[src]["feats"][f], prep[dst]["q"], windows[dst]["result"])
                    if not isinstance(r, str): s += r[0]; k += 1
                if k < MIN_SHUFFLE_TRADES: continue
                mean = s / k; counted[(m, f)] += 1
                if real_mean[(m, f)] is not None and mean >= real_mean[(m, f)] - EPS: ge[(m, f)] += 1
                if best is None or mean > best: best = mean
        if best is not None: best_of_20.append(best)
    best_of_20.sort(); p99 = best_of_20[min(len(best_of_20) - 1, int(math.ceil(0.99 * len(best_of_20))) - 1)] if best_of_20 else None
    out["shuffled_book_control"] = {"rounds_counted": len(best_of_20), "p99_of_best_of_20_mean_net": p99, "median_of_best_of_20": statistics.median(best_of_20) if best_of_20 else None,
                                    "note": "an independent build cannot reproduce another build's random draws; compare this figure approximately"}
    res = {}; passed = []
    for (m, f), trs in tries.items():
        s = score(trs); ctl = p99 is not None and real_mean[(m, f)] is not None and real_mean[(m, f)] > p99 + EPS
        s["control_passed"] = ctl; s["marginal_p"] = ((1 + ge[(m, f)]) / (1 + counted[(m, f)])) if counted[(m, f)] else None
        s["control_p_best_of_20"] = ((1 + sum(1 for b in best_of_20 if real_mean[(m, f)] is not None and b >= real_mean[(m, f)] - EPS)) / (1 + len(best_of_20))) if (best_of_20 and real_mean[(m, f)] is not None) else None
        s["meets_the_whole_bar"] = meets_bar(s, ctl); s["z_against_5.46"] = s["z_date_clustered"] is not None and s["z_date_clustered"] >= BAR["z_shared"] - EPS
        s["second_look_flag_55pct_at_300"] = s["n"] >= 300 and s["direction_accuracy"] is not None and s["direction_accuracy"] >= 0.55 - EPS
        nh = [t for t in trs if t["held"] is False]
        s["without_held_and_unknown_windows"] = {"n": len(nh), "pf": pf([t["net"] for t in nh])}
        if s["meets_the_whole_bar"]:
            passed.append("%s %s" % (m, f))
            if s["without_held_and_unknown_windows"]["pf"] is None or s["without_held_and_unknown_windows"]["pf"] < BAR["pf"] - EPS: s["paper_only"] = "overlaps L1 or OICORE"
        res["%s %s" % (m, f)] = s
    out["tries"] = {k: v for k, v in res.items() if k.split(" ")[1] not in CLOSED_FAMILY}
    out["CLOSED-FAMILY FEATURES, REPORTED SEPARATELY"] = {k: v for k, v in res.items() if k.split(" ")[1] in CLOSED_FAMILY}
    out["verdict"] = ("NOT_YET_FALSIFIED: %s meet the whole bar (a forward-test registration only; a closed-family feature alone cannot become a lead)" % passed) if passed else "FALSIFIED: none of the 20 tries meets the whole bar"
    return out


def lines(out):
    """the figures as text lines, one a try, in the order Desk A's read prints them (for a line by line comparison)"""
    f = lambda x, d=2: "n/a" if x is None else ("inf" if x == float("inf") else ("%." + str(d) + "f") % x)
    c = out.get("shuffled_book_control") or {}; L = ["verdict: " + str(out.get("verdict"))]
    if "tries" not in out: return L
    L.append("z bar 5.27 (5.46 beside it); shuffled-book control: %s rounds, best-of-20 mean net 99th percentile %sc, median %sc" % (c.get("rounds_counted"), f(100 * c["p99_of_best_of_20_mean_net"]), f(100 * c["median_of_best_of_20"])))
    allt = dict(out["tries"]); allt.update(out["CLOSED-FAMILY FEATURES, REPORTED SEPARATELY"])
    for m in MARKETS:
        L.append("-- %s: %s scored windows" % (m, out["windows_with_a_decision_poll"].get(m)))
        for ft in FEATURES:
            v = allt["%s %s" % (m, ft)]; b = v["pf_blocks"]; bn = v["block_n"]; nh = v["without_held_and_unknown_windows"]
            L.append("%s%s n %d PF %s blocks %s (n %d) / %s (n %d) / %s (n %d) halves %s / %s net %sc stress PF %s acc %s vs mean ask %s z %s control p(best of 20) %s %s; no-result fee-only %d; without windows L1 / OICORE holds: n %d PF %s%s" % (
                "[closed family] " if ft in CLOSED_FAMILY else "", ft, v["n"], f(v["pf"]), f(b["A"]), bn["A"], f(b["B"]), bn["B"], f(b["C"]), bn["C"], f(v["pf_halves"][0]), f(v["pf_halves"][1]),
                f(None if v["net_per_trade"] is None else 100 * v["net_per_trade"]), f(v["pf_fee_x1.2"]), f(v["direction_accuracy"], 3), f(v["mean_ask"], 3), f(v["z_date_clustered"]), f(v["control_p_best_of_20"], 3),
                "PASS" if v["control_passed"] else "fail", v["no_result_fee_only"], nh["n"], f(nh["pf"]), " <- BAR MET" if v["meets_the_whole_bar"] else ""))
    flags = [k for k, v in allt.items() if v["second_look_flag_55pct_at_300"]]
    L.append("second look flags (accuracy >= 55% with n >= 300; not a verdict): " + (", ".join(flags) if flags else "none"))
    return L


def read(root, outdir):
    refuse_heldout(root); refuse_heldout(outdir)
    if time.time() < READ_NOT_BEFORE: raise SystemExit("REFUSED: DEPTH1 is not read before 2026-11-14T00:00:00Z")
    res, mark = os.path.join(outdir, "depth1_second_result.json"), os.path.join(outdir, "depth1_second_started")
    if os.path.exists(res): raise SystemExit("REFUSED: a result file exists; DEPTH1 is read once")
    if os.path.exists(mark): raise SystemExit("REFUSED: a started marker exists without a result; the Head decides")
    open(mark, "w").write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    out = measure(root)
    json.dump(out, open(res, "w"), indent=1, default=str); print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "read": read(sys.argv[2], sys.argv[3])
    else: raise SystemExit(__doc__)
