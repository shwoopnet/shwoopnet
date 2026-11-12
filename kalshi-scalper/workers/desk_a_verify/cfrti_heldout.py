"""CFRTI1-BTC read, with the HELD-OUT path (Idea Desk A, Nov 12 2026). Three-venue (as registered) and Kraken-only figures in ONE sitting,
on the same run folders. Bitcoin only, receive-time stamps for every venue. CFRTI-K (perp index) is added in this same sitting when PERPBTC1M lands
(see workers/CFRTI_K_REGISTRATION.md); it is NOT in this file yet.
  python3 -I cfrti_heldout.py dev <folder holding quotes/>       development: run folders before HELDOUT_FIRST_DAY (reproduces n 36 / n 32)
  python3 -I cfrti_heldout.py heldout <folder holding quotes/>   ONE read, on or after 2026-11-20, at 50 three-venue edge rows; refuses a second run
  python3 -I cfrti_heldout.py selftest <folder holding quotes/>  runs the held-out code path on DEVELOPMENT days (2026-10-28 to 2026-11-04) with the gates off; writes nothing
After a held-out read, commit the marker line it prints into workers/CFRTI1_BTC_HELDOUT_MARKER.md (the script refuses if that file holds a READ ON line)."""
import gzip, csv, glob, math, os, sys, bisect, collections, datetime
from statistics import NormalDist
Phi = NormalDist().cdf
MODE, Q = sys.argv[1], sys.argv[2]
HELDOUT_FIRST_DAY = "2026-11-05"
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
            def replay(side, limit, delay):
                # first recorded quote at least `delay` ms after the decision (within 30 s), status active; limit = the ask seen, no slip
                for tt, x in L:
                    if tt >= t0 + delay:
                        if tt - t0 - delay > 30000 or x["status"] != "active": return None
                        try: a = float(x["yes_ask"]) if side == "yes" else 1 - float(x["yes_bid"])
                        except Exception: return None
                        return a if a <= limit + 1e-9 else None
                return None
            if 0.03 <= ya <= 0.30: rows.append((day, tk, "yes", ya, py, yes_win, d, t0, replay("yes", ya, 2000), replay("yes", ya, 6000)))
            elif 0.03 <= 1 - yb <= 0.30: rows.append((day, tk, "no", 1 - yb, 1 - py, not yes_win, d, t0, replay("no", 1 - yb, 2000), replay("no", 1 - yb, 6000)))
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
if MODE not in ("dev", "heldout", "selftest", "export", "exportall"): sys.exit(__doc__)
keep = {"dev": lambda d: d < HELDOUT_FIRST_DAY, "export": lambda d: d < HELDOUT_FIRST_DAY, "exportall": lambda d: d < HELDOUT_FIRST_DAY,
        "heldout": lambda d: d >= HELDOUT_FIRST_DAY,
        "selftest": lambda d: SELFTEST_FROM <= d < HELDOUT_FIRST_DAY}[MODE]
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
for nm, rs in (("three venues", sel3), ("kraken only", selK)):
    rep_replay("BOOK-REPLAY +2 s, " + nm, rs, 8); rep_replay("BOOK-REPLAY +6 s, " + nm + " (judges live use)", rs, 9)
if MODE == "exportall":
    out = ["form,t0_utc,ticker,side,ask_seen,model_edge_flag"]
    for nm, rs in (("three", rows3), ("kraken", rowsK)):
        for r in sorted(rs, key=lambda r: (r[7], r[1])):
            out.append("%s,%s,%s,%s,%.4f,%d" % (nm, datetime.datetime.fromtimestamp(r[7] / 1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), r[1], r[2], r[3], 1 if r[4] - r[3] >= 0.05 else 0))
    open(sys.argv[3], "w").write("\n".join(out) + "\n"); print("wrote", len(out) - 1, "rows (all cheap rows with a model, no outcome column)")
if MODE == "export":
    import io
    out = ["form,t0_utc,ticker,side,ask_seen"]
    for nm, rs in (("three", sel3), ("kraken", selK)):
        for r in sorted(rs, key=lambda r: (r[7], r[1])):
            out.append("%s,%s,%s,%s,%.4f" % (nm, datetime.datetime.fromtimestamp(r[7] / 1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), r[1], r[2], r[3]))
    open(sys.argv[3], "w").write("\n".join(out) + "\n"); print("wrote", len(out) - 1, "rows (no outcome column)")
print("CFRTI-K line: not computed here (perp candles not supplied).")
if MODE == "heldout":
    line = "READ ON %s, three-venue n %d, kraken-only n %d" % (datetime.date.today(), len(sel3), len(selK))
    open(LOCAL, "w").write(line + "\n")
    print("\nCOMMIT THIS MARKER LINE into workers/CFRTI1_BTC_HELDOUT_MARKER.md:\n" + line)
