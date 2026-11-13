"""CFRTI1-BTC read, with the HELD-OUT path (Idea Desk A, Nov 12 2026). Three-venue (as registered) and Kraken-only figures in ONE sitting,
on the same run folders. Bitcoin only, receive-time stamps for every venue. CFRTI-K (perp index) is added in this same sitting when PERPBTC1M lands
(see workers/CFRTI_K_REGISTRATION.md); it is NOT in this file yet.
  python3 -I cfrti_heldout.py dev <folder holding quotes/>       development: run folders before HELDOUT_FIRST_DAY (reproduces n 36 / n 32)
  python3 -I cfrti_heldout.py heldout <folder holding quotes/>   ONE read, run folders from 2026-11-09 (Nov 5 to 8 printed separately as NOT BLIND), on or after 2026-11-20, at 50 three-venue edge rows; refuses a second run
  python3 -I cfrti_heldout.py selftest <folder holding quotes/>  runs the held-out code path on DEVELOPMENT days (2026-10-28 to 2026-11-04) with the gates off; writes nothing
After a held-out read, commit the marker line it prints into workers/CFRTI1_BTC_HELDOUT_MARKER.md (the script refuses if that file holds a READ ON line)."""
import gzip, csv, glob, math, os, sys, bisect, collections, datetime
from statistics import NormalDist
Phi = NormalDist().cdf
MODE, Q = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import heldout_guard_v2 as heldout_guard; heldout_guard.refuse_heldout(Q, "cfrti_heldout")      # standing rule (h)
DEV_END = "2026-11-05"                      # development = run folders before this day (unchanged: reproduces n 36 / n 32)
NOTBLIND = ("2026-11-05", "2026-11-09")      # Nov 5 to Nov 8: a baseline for this side and band was printed by Forensics on Nov 12 (Head's ruling, option b): NOT blind, printed SEPARATELY, never in the verdict lines
HELDOUT_FIRST_DAY = "2026-11-09"             # the held-out window starts here (Head, Nov 12, after Forensics' disclosure); set by this constant, before any held-out row was opened by Desk A
READ_NOT_BEFORE = datetime.datetime(2026, 11, 20, tzinfo=datetime.timezone.utc)
NEEDED = 50
SELFTEST_FROM = "2026-10-28"
HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = os.path.join(HERE, "..", "CFRTI1_BTC_HELDOUT_MARKER.md")
LOCAL = os.path.join(HERE, ".cfrti_heldout_done")
def rd(p):
    with gzip.open(p, "rt") as f: return list(csv.DictReader(f))
def fee(p): return 0.07 * p * (1 - p)
skipped3 = []
def build(venues, keep_day, need3=False):
    rows = []; lost = collections.Counter(); folders = 0
    for d in sorted(glob.glob(Q + "/quotes/*/*")):
        day = d.split("/")[-2]
        if not keep_day(day): continue                 # folders outside the chosen block are never opened
        try: res = {r["ticker"]: r for r in rd(d + "/results.csv.gz")}
        except Exception: continue
        try: spot = rd(d + "/spot.csv.gz"); qs = rd(d + "/quotes.csv.gz")
        except Exception: continue
        folders += 1
        ser = collections.defaultdict(list)
        for r in spot:
            if r["asset"] != "BTC" or (venues and r["exchange"] not in venues): continue
            try: ser[r["exchange"]].append((int(r["t_recv_ms"]), float(r["price"])))
            except Exception: pass
        for v in ser: ser[v].sort()
        if need3 and any(not ser.get(v) for v in ("coinbase", "kraken", "bitstamp")):
            skipped3.append(d); continue    # three-venue line only: this folder lacks a venue (the Kraken-only line keeps it)
        qb = collections.defaultdict(list)
        for r in qs:
            try: qb[r["ticker"]].append((int(r["t_send_ms"]), r))
            except Exception: pass
        def idx(t):
            ps = []
            for v, L in ser.items():
                i = bisect.bisect_right(L, (t, 1e18)) - 1
                if i >= 0 and t - L[i][0] <= 10000: ps.append(L[i][1])
            return sum(ps) / len(ps) if ps else None
        for tk, r in res.items():
            if tk.split("-")[0] != "KXBTC15M" or r["result"] not in ("yes", "no") or tk not in qb: continue
            ct = int(datetime.datetime.strptime(r["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
            t0 = ct - 120000
            L = qb[tk]; i = max([j for j, x in enumerate(L) if x[0] <= t0] or [-1])
            if i < 0 or t0 - L[i][0] > 3000: continue
            q = L[i][1]
            try: yb, ya, k = float(q["yes_bid"]), float(q["yes_ask"]), float(q["strike"])
            except Exception: continue
            if ya <= yb or ya - yb > 0.03 or q["status"] != "active": continue
            cheap = (0.03 <= ya <= 0.30) or (0.03 <= 1 - yb <= 0.30)
            p0 = idx(t0)
            if not p0:
                lost["no trade in 10 s" + ("" if cheap else " (not a cheap row)")] += 1; continue
            xs = [idx(t0 - 10000 * j) for j in range(0, 61)]
            lr = [math.log(xs[j] / xs[j + 1]) for j in range(60) if xs[j] and xs[j + 1]]
            if len(lr) < 30:
                lost["under 30 changes" + ("" if cheap else " (not a cheap row)")] += 1; continue
            m = sum(lr) / len(lr); sd = math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1)) * math.sqrt(8)
            if sd <= 0: continue
            py = Phi(math.log(p0 / k) / sd); yes_win = r["result"] == "yes"
            if 0.03 <= ya <= 0.30: rows.append((day, tk, "yes", ya, py, yes_win, d, t0, None, None, L[i][0]))
            elif 0.03 <= 1 - yb <= 0.30: rows.append((day, tk, "no", 1 - yb, 1 - py, not yes_win, d, t0, None, None, L[i][0]))
    return rows, lost, folders

def rep(name, rs):
    if not rs: print("%-34s n 0" % name); return
    pnl = [((1 if r[5] else 0) - r[3] - fee(r[3])) for r in rs]
    gw = sum(x for x in pnl if x > 0); gl = -sum(x for x in pnl if x < 0)
    days = sorted({r[0] for r in rs}); h = len(rs) // 2
    def pf(v):
        a = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return a / b if b else float("inf")
    print("%-34s n %4d days %2d | cash PF %.2f | mean %+.2fc | win %.1f%% | mean ask %.3f | halves PF %.2f / %.2f | wins %d" % (name, len(rs), len(days), gw / gl if gl else 9, 100 * sum(pnl) / len(pnl), 100 * sum(1 for r in rs if r[5]) / len(rs), sum(r[3] for r in rs) / len(rs), pf(pnl[:h]), pf(pnl[h:]), sum(1 for r in rs if r[5])))
def rep_replay(name, rs, k):
    got = [r for r in rs if r[k] is not None]
    if not got: print("%-34s n 0 of %d" % (name, len(rs))); return
    pnl = [((1 if r[5] else 0) - r[k] - fee(r[k])) for r in got]
    gw = sum(x for x in pnl if x > 0); gl = -sum(x for x in pnl if x < 0)
    print("%-34s filled %d of %d | cash PF %.2f | mean %+.2fc | wins %d" % (name, len(got), len(rs), gw / gl if gl else 9, 100 * sum(pnl) / len(pnl), sum(1 for r in got if r[5])))


def r6_replay(rows, R6, freeze=None):
    """TRUE book replay with the fixed convention (cfrti_b.fill_ioc): an immediate-or-cancel buy of 1 contract walking the book's levels at or below the limit (the ask seen), the first poll within 4 s after
    t0 + delay only. Rows with no R6 book at the decision are counted as 'no book' and never scored. The quote recorder's list rows are NOT used (QUOTEVSBOOK1). Returns {delay: [(row, avg price or None)]}, n_nobook."""
    sys.path.insert(0, HERE); import cfrti_b
    cfrti_b.load_book(R6); book = cfrti_b.book
    out = {2: [], 6: []}; nobook = 0
    for r in rows:
        tk, side, ask, t0 = r[1], r[2], r[3], r[7] / 1000
        B = book.get(tk); times = [p[0] for p in B] if B else []
        i = bisect.bisect_right(times, t0 - 0.25) - 1
        if not B or i < 0 or t0 - 0.25 - times[i] > 4: nobook += 1; continue        # an R6 poll must exist just before the decision
        for d in (2, 6): out[d].append((r, cfrti_b.fill_ioc(B, side, ask, t0, d)))
    return out, nobook
def rep_r6(name, rs, rep6):
    res, nobook = rep6
    for d, lab in ((2, "+2 s"), (6, "+6 s (judges live use)")):
        got = [(r, f) for r, f in res[d] if f is not None]; n = len(res[d])
        pnl = [(1 if r[5] else 0) - f - fee(f) for r, f in got]
        gw = sum(x for x in pnl if x > 0); gl = -sum(x for x in pnl if x < 0)
        print("BOOK-REPLAY (R6) %-6s %-22s rows with a book %d, no book %d (not scored) | filled %d | cash PF %s | mean %s | wins %d | no evidence at n = %d" % (lab, name, n, nobook, len(got), ("%.2f" % (gw / gl if gl else 9)) if got else "n/a", ("%+.2fc" % (100 * sum(pnl) / len(pnl))) if got else "n/a", sum(1 for r, f in got if r[5]), len(got)))

def r6_stale(rows, root, freeze=("2026-11-09", "2026-11-13")):
    """Rows with an R6 book at the decision, and of those how many show a book ask more than 1c above the ask the rule saw
    ('ask not on the book'). The book poll must be at least 0.25 s before t0 and within 4 s (two different machines' clocks).
    Rows whose close is inside the DEPTH1 freeze (closes 2026-11-09 to 2026-11-13) are not opened and are counted separately."""
    folders = sorted(glob.glob(root + "/book15r6/*/*"))
    starts = [(datetime.datetime.strptime(f.split("/")[-2] + f.split("/")[-1], "%Y-%m-%d%H%M").replace(tzinfo=datetime.timezone.utc).timestamp() * 1000, f) for f in folders]
    cache, tot, have, stale, frozen = {}, 0, 0, 0, 0
    for r in rows:
        tot += 1
        t0, tk, side, seen = r[7], r[1], r[2], r[3]
        cl = datetime.datetime.strptime(tk.split("-")[1], "%y%b%d%H%M").replace(tzinfo=datetime.timezone.utc) if False else None
        day = datetime.datetime.fromtimestamp((t0 + 120000) / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")
        if freeze[0] <= day <= freeze[1]: frozen += 1; continue
        cand = [f for st, f in starts if st <= t0][-2:]
        best = None
        for f in cand:
            if f not in cache:
                try:
                    with gzip.open(f + "/book.csv.gz", "rt") as fh:
                        rd_ = [x for x in csv.DictReader(fh) if x["series"] == "KXBTC15M"]
                except Exception: rd_ = []
                offs = []
                for x in rd_:
                    h = x.get("server_date_header")
                    if h:
                        try: offs.append(__import__("email.utils").utils.parsedate_to_datetime(h).timestamp() + 0.5 - int(x["t_recv_ms"]) / 1000)
                        except Exception: pass
                off = sorted(offs)[len(offs) // 2] if offs else None
                cache[f] = (off, collections.defaultdict(list))
                if off is not None:
                    for x in rd_: cache[f][1][x["ticker"]].append((int(x["t_recv_ms"]) / 1000 + off, x))
            off, by = cache[f]
            for tt, x in by.get(tk, []):
                if t0 / 1000 - 4 <= tt <= t0 / 1000 - 0.25 and (best is None or tt > best[0]): best = (tt, x)
        if best is None: continue
        x = best[1]
        try: ask = (1 - float(x["no_bid_px_1"])) if side == "yes" else (1 - float(x["yes_bid_px_1"]))
        except Exception: continue
        have += 1
        if ask > seen + 0.01 + 1e-9: stale += 1
    return tot, have, stale, frozen

if MODE == "replaytest":      # synthetic book: IOC walk of up to 5 levels, first poll within 4 s only, no-book rows counted
    sys.path.insert(0, HERE); import cfrti_b
    t0 = 1_000_000.0
    L = lambda yb, nb: (tuple(yb), tuple(nb))
    # polls: (t, yb1, ybs1, nb1, nbs1, yes_bid_levels, no_bid_levels); a YES buy meets NO bids: ask = 1 - NO bid price
    polls = [(t0 - 1.0, 0.18, 5.0, 0.76, 5.0, ((0.18, 5.0),), ((0.76, 5.0),)),
             (t0 + 2.1, 0.19, 5.0, 0.78, 0.4, ((0.19, 5.0),), ((0.78, 0.4), (0.77, 5.0))),      # best ask 0.22 shows 0.4, next 0.23: walks to 0.4 @ 0.22 + 0.6 @ 0.23 = 0.228
             (t0 + 6.1, 0.18, 5.0, 0.70, 0.5, ((0.18, 5.0),), ((0.70, 0.5), (0.69, 0.4))),     # 0.30 and 0.31 asks, only 0.9 contracts in all, and above the 0.24 limit anyway
             (t0 + 11.0, 0.18, 5.0, 0.76, 5.0, ((0.18, 5.0),), ((0.76, 5.0),))]
    cfrti_b.load_book = lambda root: (cfrti_b.book.clear(), cfrti_b.book.update({"KXBTC15M-T": polls}))
    row = lambda tk, ask: (None, tk, "yes", ask, 0, True, None, t0 * 1000, None, None, None)
    res, nb = r6_replay([row("KXBTC15M-T", 0.24), row("KXBTC15M-NOBOOK", 0.24)], "x")
    assert nb == 1 and len(res[2]) == 1, (nb, res)
    assert abs(res[2][0][1] - (0.4 * 0.22 + 0.6 * 0.23)) < 1e-9, res[2]     # walks two levels
    assert res[6][0][1] is None, res[6]                                       # the poll at +6.1 s has asks above the limit
    assert cfrti_b.fill_ioc(polls, "yes", 0.24, t0, 6.5) is None             # first poll after t0 + 6.5 s is at +11 s: 4.5 s late, so no trade
    print("REPLAYTEST OK (IOC walk across levels, 4 s poll rule, no-book rows counted)"); sys.exit(0)
def print_notblind():
        print("\n### NOT BLIND (a baseline for this side and band was printed by Forensics on Nov 12): closes %s to %s, printed SEPARATELY, NOT in the verdict lines above, never pooled" % (NOTBLIND[0], NOTBLIND[1]))
        nb = lambda d: NOTBLIND[0] <= d < NOTBLIND[1]
        nrows3, nlost3, nf3 = build(None, nb, need3=True); nsel3 = [r for r in nrows3 if r[4] - r[3] >= 0.05]
        nrowsK, nlostK, nfK = build({"kraken"}, nb); nselK = [r for r in nrowsK if r[4] - r[3] >= 0.05]
        print("== not blind, three venues | folders %d | cheap rows with a model %d" % (nf3, len(nrows3))); rep("  baseline cheap side (not blind)", nrows3); rep("  model edge >= 0.05 (not blind)", nsel3)
        print("== not blind, kraken only | folders %d | cheap rows with a model %d" % (nfK, len(nrowsK))); rep("  baseline cheap side (not blind)", nrowsK); rep("  model edge >= 0.05 (not blind)", nselK)

if MODE == "notblind_selftest":                                     # tests the NOT BLIND block on a folder whose path contains SYNTHETIC; refuses any other folder (so it cannot open Nov 5 to 8 outcomes)
    sig = os.path.join(os.path.realpath(Q), "SYNTHETIC_FIXTURE_SIGNATURE.txt")      # a signature file written only by the fixture generator (fixed content), checked on the REAL path: a symlink to the real quotes folder has none
    if not os.path.isfile(sig) or open(sig).read().strip() != "CFRTI SYNTHETIC FIXTURE v1 (made-up data, no recorded row)": sys.exit("Refusing: notblind_selftest runs only on a folder holding the fixture signature file written by the synthetic generator")
    print_notblind(); sys.exit(0)
if MODE not in ("dev", "heldout", "selftest", "export", "exportall"): sys.exit(__doc__)
keep = {"dev": lambda d: d < DEV_END, "export": lambda d: d < DEV_END, "exportall": lambda d: d < DEV_END,
        "heldout": lambda d: d >= HELDOUT_FIRST_DAY,
        "selftest": lambda d: SELFTEST_FROM <= d < DEV_END}[MODE]
if MODE == "heldout":
    now = datetime.datetime.now(datetime.timezone.utc)
    if now < READ_NOT_BEFORE: sys.exit("Refusing: first allowed %s" % READ_NOT_BEFORE.date())
    if os.path.exists(LOCAL) or (os.path.exists(MARKER) and "READ ON" in open(MARKER).read()):
        sys.exit("Refusing: the held-out read is already marked done.")
rows3, lost3, f3 = build(None, keep, need3=(MODE != "dev"))
sel3 = [r for r in rows3 if r[4] - r[3] >= 0.05]
DUE = "--due" in sys.argv    # the Head of R&D says the read is due even though three-venue rows are under 50
if MODE == "heldout" and len(sel3) < NEEDED and not DUE:
    sys.exit("Refusing: %d three-venue Bitcoin edge rows on %d folders with all three venues, %d needed (nothing scored). Use --due only when told the read is due." % (len(sel3), f3, NEEDED))
if MODE == "heldout":                                                  # the done marker is written BEFORE anything is printed (as DEPTH1 does), so a crash after the held-out folders were opened still leaves a record; the final line below overwrites it
    open(LOCAL, "w").write("STARTED %s (a crashed run is never quietly repeated; the Head decides)\n" % datetime.datetime.now(datetime.timezone.utc).isoformat())
rowsK, lostK, fK = build({"kraken"}, keep)
selK = [r for r in rowsK if r[4] - r[3] >= 0.05]
tag = {"dev": "DEVELOPMENT", "export": "DEVELOPMENT EXPORT", "exportall": "DEVELOPMENT EXPORT ALL", "heldout": "HELD-OUT (read once)", "selftest": "SELFTEST on development days, not a result"}[MODE]
print("###", tag, "| three-venue line: %d run folders with all three venues (%d folders skipped for a missing venue) | kraken-only line: %d run folders" % (f3, len(skipped3), fK))
if MODE != "dev" and len(sel3) < NEEDED: print("THREE-VENUE LINE: no evidence at n = %d (under %d rows)" % (len(sel3), NEEDED))
print("== three venues (as registered) | cheap rows with a model", len(rows3), "| lost:", dict(lost3)); rep("  baseline cheap side", rows3); rep("  model edge >= 0.05", sel3)
print("== kraken only | cheap rows with a model", len(rowsK), "| lost:", dict(lostK)); rep("  baseline cheap side", rowsK); rep("  model edge >= 0.05", selK)
A = {(r[6], r[1]): r for r in sel3}; K = {(r[6], r[1]): r for r in selK}
print("three-venue trades", len(A), "| kraken-only trades", len(K), "| in both", len(set(A) & set(K)), "| three-venue only", len(set(A) - set(K)), "| kraken-only extra", len(set(K) - set(A)))
rep("  kept (in both), kraken stats", [K[k] for k in sorted(set(A) & set(K))])
if "--r6" in sys.argv:
    R6ROOT = sys.argv[sys.argv.index("--r6") + 1]
    for nm, rs in (("three venues", sel3), ("kraken only", selK)):
        rep_r6(nm, rs, r6_replay(rs, R6ROOT))
else:
    print("BOOK-REPLAY (R6): not computed (no --r6 <root holding book15r6/>); the quote recorder's own later rows are NOT a book replay and are not printed.")
if MODE == "exportall":
    out = ["form,t0_utc,ticker,side,ask_seen,quote_t_send_ms,edge"]
    for nm, rs in (("three", rows3), ("kraken", rowsK)):
        for r in sorted(rs, key=lambda r: (r[7], r[1])):
            out.append("%s,%s,%s,%s,%.4f,%d,%d" % (nm, datetime.datetime.fromtimestamp(r[7] / 1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), r[1], r[2], r[3], r[10], 1 if r[4] - r[3] >= 0.05 else 0))
    open(sys.argv[3], "w").write("\n".join(out) + "\n"); print("wrote", len(out) - 1, "rows (all cheap rows with a model, no outcome column)")
if MODE == "export":
    import io
    out = ["form,t0_utc,ticker,side,ask_seen"]
    for nm, rs in (("three", sel3), ("kraken", selK)):
        for r in sorted(rs, key=lambda r: (r[7], r[1])):
            out.append("%s,%s,%s,%s,%.4f" % (nm, datetime.datetime.fromtimestamp(r[7] / 1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), r[1], r[2], r[3]))
    open(sys.argv[3], "w").write("\n".join(out) + "\n"); print("wrote", len(out) - 1, "rows (no outcome column)")
if "--r6" in sys.argv:
    R6 = sys.argv[sys.argv.index("--r6") + 1]
    for nm, rs in (("three venues", sel3), ("kraken only", selK)):
        tot, have, stale, frozen = r6_stale(rs, R6, freeze=(("9999", "9999") if MODE == "heldout" else ("2026-11-09", "2026-11-13")))
        print("STALE-ASK COUNT, %s: %d signal rows | %d with an R6 book at the decision | %d of those show a book ask more than 1c above the ask seen (\"ask not on the book\") | %d rows not opened (DEPTH1 freeze, closes Nov 9 to 13)" % (nm, tot, have, stale, frozen))
else:
    print("STALE-ASK COUNT: not computed (no --r6 <root holding book15r6/>).")
if "--r6" in sys.argv:
    sys.path.insert(0, HERE); import cfrti_b
    HELD_LO = datetime.datetime(2026, 11, 9, tzinfo=datetime.timezone.utc).timestamp()
    lo, hi = (HELD_LO, 1e12) if MODE == "heldout" else (cfrti_b.FIRST_CLOSE, cfrti_b.CUTOFF)
    kd = (lambda d: d >= HELDOUT_FIRST_DAY) if MODE == "heldout" else (lambda d: d < DEV_END)
    print("\n### CFRTI-B (workers/CFRTI_B_REGISTRATION.md): signal and price from the R6 book; the registered lines above are PRICED AT A STALE COPY, NOT TRADABLE")
    print("\n".join(cfrti_b.lines(Q, sys.argv[sys.argv.index("--r6") + 1], kd, lo, hi, final=(MODE == "heldout"))))
if MODE == "heldout": print_notblind()
print("CFRTI-K line: not computed here (perp candles not supplied).")
if MODE == "heldout":
    line = "READ ON %s, three-venue n %d, kraken-only n %d" % (datetime.date.today(), len(sel3), len(selK))
    open(LOCAL, "w").write(line + "\n")
    print("\nCOMMIT THIS MARKER LINE into workers/CFRTI1_BTC_HELDOUT_MARKER.md:\n" + line)
