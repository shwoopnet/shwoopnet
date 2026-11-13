"""OIVER-CAP30 scorer, BUILD 1 (Desk A, Nov 13 2026; the Head's queue item 2, 21:05Z), built to DESK_A_OICORE_VERSIONS_NOV13.md card 2 on the OIVER-SPREAD convention (oiver_spread.py, sha256 938b360b... (the version with the rule 18 two-sided book check)), which it imports unchanged for the loaders, the parent rule and the report parts. History screen only, NOT a takeover. Offline, sends nothing. Hand case first; NO real run (queued).
  python3 -I oiver_cap30.py dev <lists dir> <candles dir>
THE PARENT is exactly the OIVER-SPREAD parent (decision at the candle ending close - 180 s; price = the ask seen on the cheaper side, ties to YES, no slip, no fill check; OI rise to the candle ending close - 360 s at least 86,300 inclusive; 0.08 <= price <= 0.50; C = 20 contracts for the fee rounding; held to settlement; halves by count, first floor(n/2)).
THE VERSION (OIVER-CAP30): the parent's trade ONLY IF the price paid (the cheaper side's ask at the decision candle) is at most 0.30 (1e-9 slack); the 8c floor stays. Every version trade is a parent trade (a subset on the same windows).
OUTPUT: as OIVER-SPREAD: parent and version n, win rate, cash PF, mean; the share removed; the paired comparison (PF difference, net per contract-week, second-half PF) and the four 7g bar parts as a HISTORY SCREEN, NOT A TAKEOVER; 'no evidence at n = x' under 100. Development only: closes from 2026-09-12T00:00:00Z (inclusive) to before 2026-11-09T00:00:00Z (exclusive) (the Head, 21:12Z)."""
import sys, os, math, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oiver_spread as O
CAP = 0.30
def report(windows, cands):
    parent, why = [], collections.Counter()
    for tk, w in windows.items():
        t, r = O.decide(w, cands.get(tk, {})); why[r] += 1
        if t: parent.append(t)
    parent.sort(key=lambda t: t["close"]); ver = [t for t in parent if t["p"] <= CAP + O.EPS]
    L = ["OIVER-CAP30 HISTORY SCREEN (development, closes 2026-09-12 to before 2026-11-09; NOT A TAKEOVER) | windows %d | decisions: %s" % (len(windows), dict(why)), O.line("parent OICORE", parent), O.line("version price <= 0.30", ver)]
    if not parent: return L
    removed = 1 - len(ver) / len(parent); L.append("share of parent signals removed by the 0.30 ceiling: %.1f%%" % (100 * removed))
    if not ver: return L
    wk = O.weeks(parent); pp, pv = O.pf([t["cash"] for t in parent]), O.pf([t["cash"] for t in ver])
    nets = (sum(t["cash"] for t in parent) / wk, sum(t["cash"] for t in ver) / wk)
    p1, p2 = O.halves(parent); v1, v2 = O.halves(ver); pp2, pv2 = O.pf([t["cash"] for t in p2]), O.pf([t["cash"] for t in v2])
    inf = lambda x: x is not None and math.isinf(x)
    L.append("paired, same windows: PF difference (version - parent) %s | net per contract-week parent %+.3f version %+.3f | second-half PF parent %s version %s" % (
        "n/a" if pp is None or pv is None or inf(pp) or inf(pv) else "%+.2f" % (pv - pp), nets[0], nets[1], "n/a" if pp2 is None else "%.2f" % pp2, "n/a" if pv2 is None else "%.2f" % pv2))
    parts = {"n >= 60 version signals": len(ver) >= 60,
             "PF difference >= 0.10": pp is not None and pv is not None and (pv - pp >= 0.10 - 1e-12 if not (inf(pp) or inf(pv)) else (pv > pp)),
             "net per contract-week not lower": nets[1] >= nets[0] - 1e-12,
             "second-half PF not worse than the parent's": pv2 is not None and pp2 is not None and pv2 >= pp2 - 1e-12}
    L.append("7g bar parts (a history screen only; the takeover is a forward read beside the parent): " + "; ".join("%s: %s" % (k, "yes" if v else "NO") for k, v in parts.items()))
    if len(ver) < 100: L.append("no evidence at n = %d version trades" % len(ver))
    return L
def main(lists, cands):
    import heldout_guard_v2 as G; print(G.list_line())
    windows, bad = O.load_windows(lists); print("\n".join(report(windows, O.load_candles(cands)))); print("windows dropped for a result that is not yes or no: %d" % bad)
if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "dev": sys.exit(__doc__)
    main(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]))
