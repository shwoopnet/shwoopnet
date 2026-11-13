"""WHEEL BLOCK READER v2 (Desk A, Nov 13 2026): applies ROTATION_LANE.md section 4 at rnd-queue bd7007cb (items (a) to (o), the Head's rulings of 02:05Z and 02:09Z) to the per-signal records of ONE place. Generic for any wheel place. A separate file from the frozen NC15 scorer (nc15_wheel_replay.py v2, 8d1055df); it reads records only (no book, no result of its own).
  python3 -I wheel_block_reader.py <records.csv> --now=<ISO> [--band=11,91] [--fav] [--start=<ISO>] [--place=SERIES]     (made-up folders only unless WHEEL_BLOCK_READ=1; HELDOUT_ paths refused)
Records (canonical CSV): ticker,series,signal_t,limit,status,result,win,cash  (signal_t = the signal poll's estimated exchange time, epoch seconds; limit in dollars; status 'fillable' = a counted candidate, anything else is not a signal, (m); result scored | void | pending; win 1/0; cash dollars = 10 x (win - price) - fee). Forensics' CSV (signal_exchange, status 'fillable, scored|void|open') is read too.
THE RULE AS BUILT. (l) a signal counts only if signal_t >= the place's start time (--start). (i) CLASS from the registered band, read as limits in whole cents (NC15 depth cell: 11 to 91): wholly at or under 50 needs 10 wins, wholly above 50 needs 10 losses, a band crossing 50 needs both; a signal whose limit is 88c or above is a favourite: with --fav (registered in the favourites class) blocks are at least 150 signals, otherwise such a signal is SKIPPED, (m). (g) money in whole cents: each signal's cash is rounded to the nearest whole cent, floor(100 x cash + 0.5 + 1e-9) (the fill price is a size-weighted average, so the gross can sit between cents: on the invented fixtures it does, e.g. 6.754; the number rounded is printed; --strict-cents refuses instead); W = gross wins, L = gross losses (a void's fee is in L); 1.3 or better is 10W >= 13L, 1.0 or better is W >= L, L = 0 with W > 0 passes, W = 0 fails; no float tolerance. (h) a day (US Central, America/Chicago, from signal_t) fails the block if 100 x day net > 30 x block net; a day with a negative net never does. (n) n counts every signal; the rarer-outcome count uses wins (scored, win 1) and losses (scored, win 0); a void is neither. A block grows signal by signal and is READ ONCE at the first signal where n >= 60 (150 fav), >= 7 different days and the rarer outcome hold, and every result in the block is final (a pending result WAITS: nothing after it is read). (k) EXPIRED by the clock: a block not complete by first signal's time + 21 x 24 h is EXPIRED and unread, decided when a later signal falls past that time or when --now passes it; the next block starts at the first counted signal after the expiry time. (j) CONFIRMATION: the next 30 counted signals after the cleared block's last signal, no minimum days or outcome count; it must be complete within 21 x 24 h of that last signal's time, else EXPIRED (unread) and a new block starts after the expiry time; W >= L = QUALIFIED (reading stops), else FAILED; its signals never count toward any block; the next block starts at the first counted signal after it. (e) halves: the first floor(n/2) signals, then the rest."""
import sys, os, csv, collections, time, calendar, re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
CT = ZoneInfo("America/Chicago"); SPAN_S = 21 * 86400; CONF_N = 30; EPS = 1e-9; STRICT_CENTS = False; ROUNDED = []
def day_of(t): return datetime.fromtimestamp(t, timezone.utc).astimezone(CT).date().isoformat()
def cents(x): return int((x * 100 + 0.5 + 1e-9) // 1)
def ge_pf(W, L, num, den):
    if W == 0: return False
    if L == 0: return True
    return den * W >= num * L
def limit_c(x): return int(round(x * 100))
def load(path):
    out = []
    for r in csv.DictReader(open(path, newline="")):
        st = r.get("status", "")
        if not st.startswith("fillable"): continue
        res = r.get("result") or ""
        if "," in st: res = {"fillable, scored": "scored", "fillable, void": "void", "fillable, open": "pending"}.get(st, res)
        t = r.get("signal_t") or r.get("signal_exchange")
        if res == "scored" and r.get("win") in ("", None): raise SystemExit("REFUSED: a scored record (%s) has no win field" % r["ticker"])                      # Auditor B item 7: a blank win never reads as a loss
        c = None
        if r.get("cash") not in ("", None):
            x = float(r["cash"]) * 100
            if abs(x - round(x)) > 1e-6 and STRICT_CENTS: raise SystemExit("REFUSED (--strict-cents): cash %s of %s is not whole cents" % (r["cash"], r["ticker"]))
            if abs(x - round(x)) > 1e-6: ROUNDED.append(r["ticker"])
            c = cents(float(r["cash"]))
        out.append(dict(ticker=r["ticker"], series=r.get("series", ""), t=float(t), limit=limit_c(float(r["limit"])) if r.get("limit") not in ("", None) else None, result=res, win=int(float(r["win"])) if r.get("win") not in ("", None) else 0, cents=c))
    return out
def need_outcomes(band, fav):
    lo, hi = band
    return ("wins", "losses") if lo <= 50 < hi else (("wins",) if hi <= 50 else ("losses",))
def read_place(sigs, band=(11, 91), fav=False, start_t=None, now=None):
    need_n = 150 if fav else 60; needs = need_outcomes(band, fav); blocks = []; cur = []; conf = None
    counted = []
    for s in sorted(sigs, key=lambda s: (s["t"], s["ticker"])):
        if start_t is not None and s["t"] < start_t - EPS: continue                                  # (l)
        if s["limit"] is not None and s["limit"] >= 88 and not fav: continue                         # (i), (m): a favourite signal of a rule not registered as one is skipped
        counted.append(s)
    def outcomes(b): return sum(1 for x in b if x["result"] == "scored" and x["win"] == 1), sum(1 for x in b if x["result"] == "scored" and x["win"] != 1)   # (n): a void is neither
    def complete(b):
        w, l = outcomes(b); ok = len(b) >= need_n and len({day_of(x["t"]) for x in b}) >= 7
        return ok and ("wins" not in needs or w >= 10) and ("losses" not in needs or l >= 10)
    def read(b):
        c = [x["cents"] for x in b]; n = len(c); h = n // 2; W = sum(v for v in c if v > 0); L = -sum(v for v in c if v < 0); net = sum(c); byday = collections.defaultdict(int)
        for x, v in zip(b, c): byday[day_of(x["t"])] += v
        fails = []
        if not ge_pf(W, L, 13, 10): fails.append("profit factor under 1.3")
        hw = lambda part: (sum(v for v in part if v > 0), -sum(v for v in part if v < 0))
        (W1, L1), (W2, L2) = hw(c[:h]), hw(c[h:])
        if not (W1 > 0 and (L1 == 0 or W1 >= L1)) or not (W2 > 0 and (L2 == 0 or W2 >= L2)): fails.append("a half under 1.0")
        bad = [d for d, v in byday.items() if net > 0 and v > 0 and 100 * v > 30 * net]                          # (h): only a block with a positive net can fail on one day (a block that fails (g) is not read further)
        if bad: fails.append("one day holds %.0f%% of the net, over 30%%" % (100 * max(byday[d] for d in bad) / net))
        w, l = outcomes(b)
        return dict(status="FAILED" if fails else "CLEARED", n=n, wins=w, losses=l, voids=sum(1 for x in b if x["result"] == "void"), net_cents=net, W=W, L=L, pf=(W / L if L else float("inf")), halves=((W1 / L1) if L1 else float("inf"), (W2 / L2) if L2 else float("inf")), days=len(byday), span_days=(b[-1]["t"] - b[0]["t"]) / 86400, top_day_pct=(100 * max(byday.values()) / net if net > 0 else None), fails=fails, first=b[0]["ticker"], last=b[-1]["ticker"])
    i = 0; N = len(counted); exp_after = None                                                        # exp_after: a signal must be strictly later than this time to start the next block
    def expired_by_now(t0): return now is not None and now - t0 > SPAN_S + EPS
    while i < N:
        s = counted[i]
        if exp_after is not None and s["t"] <= exp_after + EPS: i += 1; continue                    # (k): the next block starts at the first counted signal after the expiry time
        exp_after = None
        if cur and s["t"] - cur[0]["t"] > SPAN_S + EPS:                                              # (k) a later signal fell past the 21 days: EXPIRED, unread
            blocks.append(dict(status="EXPIRED", n=len(cur), first=cur[0]["ticker"], last=cur[-1]["ticker"], span_days=(cur[-1]["t"] - cur[0]["t"]) / 86400)); exp_after = cur[0]["t"] + SPAN_S; cur = []; continue
        cur.append(s); i += 1
        if any(x["result"] == "pending" for x in cur):
            if expired_by_now(cur[0]["t"]):
                blocks.append(dict(status="EXPIRED", n=len(cur), first=cur[0]["ticker"], last=cur[-1]["ticker"], span_days=(cur[-1]["t"] - cur[0]["t"]) / 86400)); return blocks, dict(waiting=False, expired_by_clock=True)
            return blocks, dict(waiting=True, why="a signal in the block has no final result yet", block_n=len(cur))
        if complete(cur):
            b = read(cur); blocks.append(b); last_t = cur[-1]["t"]; cur = []
            if b["status"] == "CLEARED":
                cs = []
                while i < N and len(cs) < CONF_N and counted[i]["t"] - last_t <= SPAN_S + EPS: cs.append(counted[i]); i += 1
                if len(cs) < CONF_N:
                    if (i < N) or expired_by_now(last_t):                                           # a later signal is past the 21 days, or the clock is: the confirmation is EXPIRED, unread
                        b["confirmation"] = "CONFIRMATION EXPIRED (unread)"; exp_after = last_t + SPAN_S; continue
                    return blocks, dict(waiting=False, confirmation_in_progress=len(cs), of=CONF_N)
                if any(x["result"] == "pending" for x in cs): return blocks, dict(waiting=True, why="a confirmation signal has no final result yet", confirmation_n=len(cs))
                cw = sum(max(x["cents"], 0) for x in cs); cl = -sum(min(x["cents"], 0) for x in cs); ok = cw > 0 and (cl == 0 or cw >= cl)
                b["confirmation"] = "QUALIFIED" if ok else "CONFIRMATION FAILED"; b["confirmation_pf"] = (cw / cl) if cl else float("inf")
                if ok: return blocks, dict(waiting=False, qualified=True)
    if cur and expired_by_now(cur[0]["t"]):
        blocks.append(dict(status="EXPIRED", n=len(cur), first=cur[0]["ticker"], last=cur[-1]["ticker"], span_days=(cur[-1]["t"] - cur[0]["t"]) / 86400)); return blocks, dict(waiting=False, expired_by_clock=True)
    w, l = outcomes(cur)
    return blocks, dict(waiting=False, block_in_progress=len(cur), days=len({day_of(x["t"]) for x in cur}), wins=w, losses=l)
def lines(place, blocks, state):
    out = []
    for k, b in enumerate(blocks, 1):
        if b["status"] == "EXPIRED": out.append("%s BLOCK %d: EXPIRED (unread; too slow for the wheel) | n %d span %.1f days | %s to %s" % (place, k, b["n"], b["span_days"], b["first"], b["last"])); continue
        out.append("%s BLOCK %d: %s | n %d (%s to %s) wins %d losses %d voids %d | net %.2f PF %.2f halves %.2f / %.2f | days %d span %.1f top day %s%s%s" % (place, k, b["status"], b["n"], b["first"], b["last"], b["wins"], b["losses"], b["voids"], b["net_cents"] / 100, b["pf"], b["halves"][0], b["halves"][1], b["days"], b["span_days"], ("%.0f%%" % b["top_day_pct"]) if b["top_day_pct"] is not None else "n/a", (" | fails: " + "; ".join(b["fails"])) if b["fails"] else "", (" | confirmation: %s%s" % (b["confirmation"], (" (PF %.2f)" % b["confirmation_pf"]) if "confirmation_pf" in b else "")) if b.get("confirmation") else ""))
    out.append("%s STATE: %s" % (place, state)); return out
def _iso(s): return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import heldout_guard; heldout_guard.refuse_heldout(os.path.abspath(a[0]), "wheel block reader")
    opt = {x.split("=", 1)[0]: (x.split("=", 1)[1] if "=" in x else True) for x in sys.argv[1:] if x.startswith("--")}
    if "--now" not in opt: sys.exit("REFUSED: a stated --now=<ISO> is required (EXPIRED is decided by the clock, (k))")
    band = tuple(int(v) for v in opt.get("--band", "11,91").split(","))
    if "--strict-cents" in opt: STRICT_CENTS = True
    sigs = load(a[0]); places = sorted({s["series"] for s in sigs})
    for p in places:
        if opt.get("--place") and p != opt["--place"]: continue
        b, st = read_place([s for s in sigs if s["series"] == p], band, "--fav" in opt, _iso(opt["--start"]) if "--start" in opt else None, _iso(opt["--now"])); print("\n".join(lines(p, b, st)))
    if ROUNDED: print("NOTE: %d signals had cash that was not whole cents (the fill price is a size-weighted average) and were rounded to the nearest cent, item (g); --strict-cents refuses instead" % len(ROUNDED))
