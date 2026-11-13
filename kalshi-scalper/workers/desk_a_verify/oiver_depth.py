"""OIVER-DEPTH scorer, BUILD 1 (Desk A, Nov 13 2026; the Head's queue item 3, 21:05Z), built to DESK_A_OICORE_VERSIONS_NOV13.md card 3 on the OIVER-SPREAD convention (oiver_spread.py, sha256 30d45c00..., imported unchanged) with an R6 book replay. History screen only, NOT a takeover. Offline, sends nothing. Hand case first; NO real run (queued).
  python3 -I oiver_depth.py dev <lists dir> <candles dir> <R6 root>
<R6 root>: a folder of run folders <date>/<HHMM>/book.csv.gz (the R6 recorder's shape, as nc15depth1.py reads it: t_recv_ms, server_date_header, ticker, close_time, yes_bid_px_1..5, yes_bid_sz_1..5, no_bid_px_1..5, no_bid_sz_1..5); exchange time = the rolling median of the last 120 readable Date headers + 0.5 s - t_recv (nc15depth1.Run, imported unchanged). Refused by heldout_guard_v2 if it is a HELDOUT_ folder or a listed pull run.
THE PARENT is the OIVER-SPREAD parent on the candles (decision at the candle ending close - 180 s; the ask seen, no slip or fill check; OI rise at least 86,300 inclusive; 0.08 to 0.50; C = 20 for the fee rounding; held; halves by count, first floor(n/2)). THE REPLAY SET = the parent trades that also have an R6 DECISION POLL: the last R6 poll with exchange time in [close - 190 s, close - 180 s] (a window without one is counted and left out of the set, never guessed).
THE VERSION (OIVER-DEPTH): a replay-set trade ONLY IF the displayed size at the touch the order would meet is at least DEPTH_MIN = 2 x 20 = 40 contracts, read at that decision poll: buying YES meets the NO bids (size at the best NO bid, no_bid_sz_1, the YES ask level), buying NO meets the YES bids (yes_bid_sz_1, the level whose price is 1 - the YES bid); a blank or unreadable size removes the trade and is counted. Every version trade is a replay-set trade, which is a parent trade.
OUTPUT: the parent (all candle trades), the replay set and the version; the share removed from the replay set; the paired comparison on the replay-set windows (PF difference, net per contract-week, second-half PF) and the four 7g bar parts as a HISTORY SCREEN, NOT A TAKEOVER; 'no evidence at n = x' under 100. Development only: closes before 2026-12-01T00:00:00Z. R6 GUARD (the Head, 21:08Z): R6 closes on or after 2026-11-09T00:00:00Z are held out by unread cards, so the replay set is parent trades closing 2026-10-29 to before 2026-11-09 ONLY; a later parent trade is counted and never looked up, and no R6 folder dated 2026-11-09 or later is opened; the replay set's first and last close are printed. R6 starts 2026-10-29, so the replay set is small by construction."""
import sys, os, glob, math, collections, calendar, time
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oiver_spread as O
import nc15depth1 as N
DEPTH_MIN = 2 * 20.0
R6_HELDOUT_FROM = calendar.timegm(time.strptime("2026-11-09", "%Y-%m-%d"))      # R6 closes on or after this are held out by unread cards (DEPTH1, CFRTI1-BTC, CFRTI-B, CFRTI-K, W-SPOTLEAD1; the Head, 21:08Z): never looked up, and no R6 folder dated on or after it is opened
def load_r6(root):
    import heldout_guard_v2 as G; G.refuse_heldout(str(root), "oiver_depth")
    cut_day = time.strftime("%Y-%m-%d", time.gmtime(R6_HELDOUT_FROM))
    runs = sorted(os.path.dirname(f) for f in glob.glob(os.path.join(root, "*", "*", "book.csv.gz")) if os.path.basename(os.path.dirname(os.path.dirname(f))) < cut_day); R = {p: N.Run(p) for p in runs}; by = collections.defaultdict(list)      # a folder dated on or after 2026-11-09 is never opened
    for p, run in R.items():
        for tk, lst in run.by.items():
            for t, i in lst: by[tk].append((t, p, i))
    return R, by
def decision_poll(R, by, tk, close):
    D = close - 180; cand = [(t, p, i) for t, p, i in by.get(tk, []) if D - 10 - O.EPS <= t <= D + O.EPS]
    if not cand: return None
    t, p, i = max(cand, key=lambda c: (c[0], c[1])); return R[p].rows[i]
def touch_size(row, side):
    return N._f(row.get("no_bid_sz_1" if side == "yes" else "yes_bid_sz_1"))
def report(windows, cands, R, by):
    parent, why, rset, ver, nopoll, nosize, heldout_skipped = [], collections.Counter(), [], [], 0, 0, 0
    for tk, w in windows.items():
        t, r = O.decide(w, cands.get(tk, {})); why[r] += 1
        if not t: continue
        parent.append(t)
        if w["close"] >= R6_HELDOUT_FROM: heldout_skipped += 1; continue      # an R6-held-out window is never looked up
        row = decision_poll(R, by, tk, w["close"])
        if row is None: nopoll += 1; continue
        rset.append(t); sz = touch_size(row, t["side"])
        if sz is None: nosize += 1; continue
        if sz >= DEPTH_MIN - O.EPS: ver.append(t)
    for l in (parent, rset, ver): l.sort(key=lambda t: t["close"])
    L = ["OIVER-DEPTH HISTORY SCREEN (development, closes before 2026-12-01; NOT A TAKEOVER) | windows %d | decisions: %s" % (len(windows), dict(why)), O.line("parent OICORE (all candle trades)", parent),
         "parent trades closing on or after 2026-11-09 (held out for R6, never looked up): %d" % heldout_skipped, "parent trades with no R6 decision poll (left out of the replay set): %d" % nopoll, O.line("replay set (parent trades with an R6 decision poll)", rset), "replay-set trades with no readable touch size (removed from the version): %d" % nosize, O.line("version touch size >= %d" % DEPTH_MIN, ver)]
    if rset: L.append("replay set date span: first close %s, last close %s (R6 folders opened: dated before 2026-11-09 only)" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(min(t["close"] for t in rset))), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(max(t["close"] for t in rset)))))
    if not rset or not ver: return L
    L.append("share of the replay set removed by the depth condition: %.1f%%" % (100 * (1 - len(ver) / len(rset))))
    wk = O.weeks(rset); pp, pv = O.pf([t["cash"] for t in rset]), O.pf([t["cash"] for t in ver]); inf = lambda x: x is not None and math.isinf(x)
    nets = (sum(t["cash"] for t in rset) / wk, sum(t["cash"] for t in ver) / wk)
    p1, p2 = O.halves(rset); v1, v2 = O.halves(ver); pp2, pv2 = O.pf([t["cash"] for t in p2]), O.pf([t["cash"] for t in v2])
    L.append("paired, same replay-set windows: PF difference (version - replay set) %s | net per contract-week replay set %+.3f version %+.3f | second-half PF replay set %s version %s" % (
        "n/a" if pp is None or pv is None or inf(pp) or inf(pv) else "%+.2f" % (pv - pp), nets[0], nets[1], "n/a" if pp2 is None else "%.2f" % pp2, "n/a" if pv2 is None else "%.2f" % pv2))
    parts = {"n >= 60 version signals": len(ver) >= 60,
             "PF difference >= 0.10": pp is not None and pv is not None and (pv - pp >= 0.10 - 1e-12 if not (inf(pp) or inf(pv)) else (pv > pp)),
             "net per contract-week not lower": nets[1] >= nets[0] - 1e-12,
             "second-half PF not worse than the replay set's": pv2 is not None and pp2 is not None and pv2 >= pp2 - 1e-12}
    L.append("7g bar parts (a history screen only; the takeover is a forward read beside the parent): " + "; ".join("%s: %s" % (k, "yes" if v else "NO") for k, v in parts.items()))
    if len(ver) < 100: L.append("no evidence at n = %d version trades" % len(ver))
    return L
def main(lists, cands, root):
    import heldout_guard_v2 as G; print(G.list_line())
    windows, bad = O.load_windows(lists); R, by = load_r6(root); print("\n".join(report(windows, O.load_candles(cands), R, by))); print("windows dropped for a result that is not yes or no: %d" % bad)
if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "dev": sys.exit(__doc__)
    main(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4]))
