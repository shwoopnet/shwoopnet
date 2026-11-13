"""HOURLYTEMP second reader, built from HOURLYTEMP_MEASUREMENT_NOTE.md (f5cf6af9, pins 1 to 12 + Amendment 2) only.
Usage: python3 -I hourlytemp_second.py <case folder holding lists/ and optionally candles/>
Measurement, not a rule. Zero tries. No result field is read. All arithmetic is exact (Decimal); lines carry 1e-9 where a float would."""
import sys, os, gzip, json, calendar
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING
from datetime import datetime, timezone

SERIES = ["KXTEMPNYCHS", "KXTEMPMIAH", "KXTEMPLAXHS", "KXTEMPCHIHS"]
LOOKS = (55, 30, 10)
LO, HI = "2026-11-05T00:00:00Z", "2026-11-11T23:59:59Z"
CAP = 140
TOL = D("1e-9")

class Refuse(Exception): pass

def F(t): return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H")

def ep(s):
    return calendar.timegm(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timetuple())

def inside(run, name):
    if "HELDOUT_" in os.path.realpath(os.path.join(run, name)) or "HELDOUT_" in name:
        raise Refuse("held-out guard: " + name)
    p = os.path.join(run, name)
    rr = os.path.realpath(run)
    if os.path.realpath(p) != os.path.join(rr, name) and not os.path.realpath(p).startswith(rr + os.sep):
        raise Refuse("file leads outside its run folder: " + name)
    if ".." in name.split("/") or os.path.islink(p):
        raise Refuse("link or .. refused: " + name)
    return p

def manifest(run):
    if "HELDOUT_" in os.path.realpath(run): raise Refuse("held-out guard on run folder")
    return json.load(open(inside(run, "manifest.json")))

def answer(run, fn):
    return json.load(gzip.open(inside(run, fn), "rt"))

def rnd(x, places):   # half up
    return D(x).quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)

def med(v):
    v = sorted(v); n = len(v)
    if n == 0: return None
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2

def fee(p):  # 0.07 p (1-p) rounded UP to the next cent, as dollars
    return (D("0.07") * p * (1 - p) * 100).to_integral_value(rounding=ROUND_CEILING) / 100

# ---------- step: sample from the lists run
def load_lists(lists):
    m = manifest(lists)
    rows = m.get("rows", [])
    markets = {}; problems = []
    for S in SERIES:
        rs = [r for r in rows if r.get("id") == "settled_" + S]
        if not rs: problems.append("settled list of %s missing" % S); continue
        bad = [r for r in rs if r.get("status") != 200 or r.get("truncated") or not r.get("file")]
        if bad: problems.append("settled list of %s refused or cut short" % S); continue
        rs.sort(key=lambda r: r["page"])
        last = answer(lists, rs[-1]["file"])
        if last.get("cursor"): problems.append("settled list of %s ends on a page that still carries a cursor" % S); continue
        for r in rs:
            for mk in answer(lists, r["file"]).get("markets", []):
                markets[mk["ticker"]] = mk
    return m, rows, markets, problems

def sample(lists):
    m, rows, markets, problems = load_lists(lists)
    if problems: raise Refuse("; ".join(problems))
    out = []
    types = {}
    for t, mk in sorted(markets.items()):
        for f in ("ticker", "event_ticker", "floor_strike", "open_time", "close_time"):
            if mk.get(f) in (None, ""): raise Refuse("market %s lacks %s" % (t, f))
        if not (LO <= mk["close_time"] <= HI): raise Refuse("market %s closes outside the sample dates: %s" % (t, mk["close_time"]))
        life = ep(mk["close_time"]) - ep(mk["open_time"])
        if life > 3600: raise Refuse("market %s lives longer than 3600 s (%d)" % (t, life))
        if life <= 0: raise Refuse("market %s opens at or after its close" % t)
        if ep(mk["close_time"]) % 3600 != 0: raise Refuse("market %s closes off the clock hour: %s" % (t, mk["close_time"]))
        types[mk.get("strike_type")] = types.get(mk.get("strike_type"), 0) + 1
        out.append(dict(ticker=t, event=mk["event_ticker"], series=t.split("-")[0], strike=D(str(mk["floor_strike"])),
                        open=ep(mk["open_time"]), close=ep(mk["close_time"]), life=life))
    if len(types) > 1 or any(x not in ("greater", "greater_or_equal") for x in types):
        raise Refuse("strike types are not one ladder of above thresholds: %s" % types)
    return out, markets

def job_requests(smp):
    """Amendment 3 pin 3 + Amendment 4 (a): full-life markets: one time range a request, <=100 tickers, <=9,800 candles (tickers x minutes of the range, both ends counted); hours in time order; an hour joins the request
    only if it closes <=3,600 s after the request's last close and both limits hold. Late markets (life under 3,600 s): a request starts at the market's own open and ends at its close; late markets share a request only with the
    same open time and the same close time (same limits). Returns the number of requests."""
    full = [x for x in smp if x["life"] == 3600]; late = [x for x in smp if x["life"] < 3600]
    by = {}
    for s_ in full: by.setdefault(s_["close"], []).append(s_["ticker"])
    reqs = []; cur = None   # [first_close, last_close, ntickers]
    def mins(a, b): return (b - a) // 60 + 60 + 1   # from a-60min to b, both ends counted
    for c in sorted(by):
        n = len(by[c])
        if n > 100 or n * mins(c, c) > 9800: raise Refuse("an hour breaks a request limit by itself (%d tickers)" % n)
        if cur and c - cur[1] <= 3600 and cur[2] + n <= 100 and (cur[2] + n) * mins(cur[0], c) <= 9800:
            cur[1] = c; cur[2] += n
        else:
            if cur: reqs.append(cur)
            cur = [c, c, n]
    if cur: reqs.append(cur)
    lg = {}
    for x in late: lg.setdefault((x["open"], x["close"]), []).append(x["ticker"])
    nlate = 0
    for (o, c), tk in lg.items():
        per = max(1, min(100, 9800 // ((c - o) // 60 + 1)))
        if per < 1: raise Refuse("a late market breaks a request limit by itself")
        nlate += -(-len(tk) // per)
    return len(reqs) + nlate

# ---------- candles
def load_candles(candles, smp):
    m = manifest(candles)
    notes = []
    if "job" not in m: raise Refuse("candle run manifest carries no job")
    reqs = m["job"]["requests"]
    asked = set()
    for r in reqs: asked |= set(x for x in r["params"]["market_tickers"].split(",") if x)
    if asked != {s["ticker"] for s in smp}: raise Refuse("job tickers differ from the sample tickers")
    rows = m.get("rows", [])
    whole = 0; cdata = {}; novol = 0
    for r in reqs:
        rs = [x for x in rows if x.get("id") == r["id"]]
        ok = bool(rs) and all(x.get("status") == 200 and not x.get("truncated") and x.get("file") for x in rs)
        whole += ok
        for x in rs:
            if x.get("status") == 200 and x.get("file"):
                for mk in answer(candles, x["file"]).get("markets", []):
                    d = cdata.setdefault(mk["market_ticker"], {})
                    for c in mk.get("candlesticks", []): d[c["end_period_ts"]] = c
    complete = m.get("status") == "complete" and whole == len(reqs)
    for d in cdata.values():
        for c in d.values():
            if c.get("volume_fp") in (None, ""): novol += 1
    return cdata, complete, whole, len(reqs), novol

def px(c, side):
    o = c.get(side)
    if not isinstance(o, dict) or o.get("close_dollars") in (None, ""): return None
    return D(o["close_dollars"])

def found(cd, mk, L, carried):
    c = cd.get(L)
    if c is None and carried:
        ks = [t for t in cd if mk["open"] < t < L]
        c = cd[max(ks)] if ks else None
    return c

def quote(cd, mk, L, carried):
    c = cd.get(L)
    if c is None and carried:
        ks = [t for t in cd if mk["open"] < t < L]
        c = cd[max(ks)] if ks else None
    if c is None: return None
    b, a = px(c, "yes_bid"), px(c, "yes_ask")
    if b is None or a is None or (b == 0 and a == 1): return None
    return b, a

def oneway(b, a):  # cents, exact; only the fee is rounded
    p = min(a + D("0.01"), D("0.99"))
    return (a - b) * 50 + fee(p) * 100

def rtrip(b, a):   # cents
    mid = (a + b) / 2
    return (a - b) * 100 + 2 * D("0.07") * mid * (1 - mid) * 100

def gained_hours(smp):
    """series-hours that gained strikes (Amendment 4 c): (series, close, event) with at least one market of life under 3,600 s -> number of strikes added."""
    g = {}
    for x in smp:
        if x["life"] < 3600: g[(x["series"], x["close"], x["event"])] = g.get((x["series"], x["close"], x["event"]), 0) + 1
    return g

def figure_lines(tag, sub, cdata):
    """Every per-city, per-look, per-reading figure line on the strikes `sub`; returns {reading: {(city, look): median one-way near the money}}."""
    out = {}
    for reading in ("carried", "exact"):
        carried = reading == "carried"
        meds = {}
        for S in SERIES:
            for look in LOOKS:
                strikes = [s for s in sub if s["series"] == S]
                nq = 0; noy = 0; two = []   # (event, strike, bid, ask)
                for s in strikes:
                    L = s["close"] - look * 60
                    if L <= s["open"]: noy += 1; continue        # Amendment 4 (a): not yet open at a look at or before its own open
                    if found(cdata.get(s["ticker"], {}), s, L, carried) is not None: nq += 1   # candle found, empty book included
                    q = quote(cdata.get(s["ticker"], {}), s, L, carried)
                    if q is None: continue
                    b, a = q
                    if 0 < b < a < 1: two.append((s["event"], s["strike"], b, a))
                spreads = [(a - b) * 100 for _, _, b, a in two]
                rts = [rtrip(b, a) for _, _, b, a in two]
                ex = {}
                for e, st, b, a in two: ex.setdefault(e, []).append((st, b, a))
                near_rt, near_ow = [], []; cert = {1: [], 2: [], 3: []}
                for e, v in ex.items():
                    v.sort(key=lambda x: x[0])
                    i0 = min(range(len(v)), key=lambda i: (abs((v[i][1] + v[i][2]) / 2 - D("0.5")), v[i][0]))
                    for i, (st, b, a) in enumerate(v):
                        r = abs(i - i0)
                        if r <= 2: near_rt.append(rtrip(b, a)); near_ow.append(oneway(b, a))
                        if r >= 1:
                            na = a if i < i0 else 1 - b
                            cert[min(r, 3)].append(na * 100)
                ext = sum(1 for _, _, b, a in two if (b + a) / 2 >= D("0.95") - TOL or (b + a) / 2 <= D("0.05") + TOL)
                mo = med(near_ow); meds[(S, look)] = mo
                f = lambda x, n=2: "n/a" if x is None else str(rnd(x, n))
                share = lambda a_, b_: "n/a" if b_ == 0 else str(rnd(D(a_) * 100 / b_, 1)) + "%"
                print("[%s|%s] %s %dmin: strikes=%d not_yet_open=%d candle_found=%d twosided=%d (%s of candle-found strikes) median_spread=%s median_rt=%s | near: n=%d median_rt=%s median_oneway=%s | extreme95/5=%s of twosided | nearer-certain ask median r1=%s r2=%s r3+=%s [cents] (n %d/%d/%d)  measurement, not a rule" % (
                    reading, tag, S, look, len(strikes), noy, nq, len(two), share(len(two), nq), f(med(spreads)), f(med(rts)),
                    len(near_ow), f(med(near_rt)), f(mo), share(ext, len(two)), f(med(cert[1])), f(med(cert[2])), f(med(cert[3])),
                    len(cert[1]), len(cert[2]), len(cert[3])))
        out[reading] = meds
    return out

def measure(smp, cdata, complete, whole, nreq, novol, markets, lists):
    print("measurement, not a rule")
    print("STEP ONE, settlement source as listed:")
    for S in SERIES:
        mk = next(markets[s["ticker"]] for s in smp if s["series"] == S) if any(s["series"] == S for s in smp) else None
        print("  %s rules_primary=%r rules_secondary=%r" % (S, mk and mk.get("rules_primary"), mk and mk.get("rules_secondary")))
    print("sample: %d markets, %d events, series counts %s" % (len(smp), len({s["event"] for s in smp}),
          {S: sum(1 for s in smp if s["series"] == S) for S in SERIES}))
    lives = {}
    for x in smp: lives[(x["series"], x["life"])] = lives.get((x["series"], x["life"]), 0) + 1
    print("table of lives (series, seconds, markets): %s" % sorted(lives.items()))
    g = gained_hours(smp)
    print("series-hours that gained strikes: %d: %s" % (len(g), [(sr, F(c), n) for (sr, c, ev), n in sorted(g.items())]))
    exp = list(range(ep(LO), ep("2026-11-12T00:00:00Z"), 3600))          # the 168 clock hours of the fixed seven days (Amendment 4 (d), clarified): a series-hour is one event, a series and a close hour
    for S in SERIES:
        have_h = {x["close"] for x in smp if x["series"] == S}
        miss = [F(h) for h in exp if h not in have_h]
        print("missing clock hours %s against the %d expected (printed as they are, not filled): %d %s" % (S, len(exp), len(miss), miss))
    print("candle requests answered whole: %d of %d asked; candles with no volume field: %d (each a minute with no trade)" % (whole, nreq, novol))
    excl = [x for x in smp if (x["series"], x["close"], x["event"]) not in g]
    allm = figure_lines("ALL", smp, cdata)
    print("(information only) the same figures without the series-hours that gained strikes:")
    figure_lines("EXCL", excl, cdata)
    verdicts = {}
    for reading in ("carried", "exact"):
        vals = list(allm[reading].values())
        if any(v is not None and v <= 4 + TOL for v in vals): v = "not closed"
        elif all(v is not None for v in vals): v = "closed"
        else: v = "cannot say"
        verdicts[reading] = v
        print("[%s|ALL] twelve medians: %s -> %s" % (reading, ["n/a" if x is None else str(rnd(x, 2)) for x in vals], v))
    print("per city, share of market-minutes with a trade (volume>0 over each market's own minutes of life):")
    for tag, sub in (("ALL", smp), ("EXCL", excl)):
        for S in SERIES:
            strikes = [s for s in sub if s["series"] == S]
            tr = sum(1 for s in strikes for c in cdata.get(s["ticker"], {}).values() if c.get("volume_fp") not in (None, "") and D(c["volume_fp"]) > 0)
            den = sum(s["life"] // 60 for s in strikes)
            print("  [%s] %s %s%% (%d of %d)  measurement, not a rule" % (tag, S, rnd(D(tr) * 100 / den, 1) if den else "n/a", tr, den))
    # size at touch from open_ answers
    m = manifest(lists)
    for S in SERIES:
        bids, asks = [], []
        for r in m.get("rows", []):
            if r.get("id") == "open_" + S and r.get("status") == 200 and r.get("file"):
                for mk in answer(lists, r["file"]).get("markets", []):
                    for key, dst in (("yes_bid_size_fp", bids), ("yes_ask_size_fp", asks)):
                        if mk.get(key) not in (None, "") and D(mk[key]) > 0: dst.append(D(mk[key]))
        g = lambda v: "n/a" if not v else str(rnd(med(v), 2))
        print("  size at touch %s: median YES bid size %s (n %d), median YES ask size %s (n %d), pooled %s  measurement, not a rule" % (S, g(bids), len(bids), g(asks), len(asks), g(bids + asks)))
    if not complete: final = "the candle pull is not whole: not decided"
    elif verdicts["carried"] == verdicts["exact"] == "closed": final = "CLOSED as too costly"
    elif verdicts["carried"] == verdicts["exact"] == "not closed": final = "NOT CLOSED"
    else: final = "depends on the reading of a missing minute: not decided"
    print("VERDICT: %s (carried: %s; exact: %s)" % (final, verdicts["carried"], verdicts["exact"]))

if __name__ == "__main__":
    case = sys.argv[1]
    try:
        lists = os.path.join(case, "lists"); candles = os.path.join(case, "candles")
        smp, markets = sample(lists)
        n = job_requests(smp)
        print("SAMPLE OK: %d markets; candle job would need %d requests (cap %d) -> %s" % (len(smp), n, CAP, "job written" if n <= CAP else "no job, over cap"))
        if os.path.isdir(candles):
            cdata, complete, whole, nreq, novol = load_candles(candles, smp)
            measure(smp, cdata, complete, whole, nreq, novol, markets, lists)
    except Refuse as e:
        print("REFUSED: %s" % e)
