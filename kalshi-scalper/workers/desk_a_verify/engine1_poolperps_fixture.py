"""ENGPERPS_POOL1 compare vehicle (Desk A, Nov 16 2026): runs engine1_poolperps on an INVENTED fixture json.gz ({"data": {ticker: {end_ts: [bid, ask]}}, "funding": {ticker: {ts: rate}}}) and prints one line per rule for a 1e-9 compare with the Testing Desk's second build: signal, exit, trades and booked trades at h 0.0002 and 0.0005, net total at taker, PF, gate, skips. No real data.
  python3 -I engine1_poolperps_fixture.py <fixture.json.gz>"""
import sys, os, json, gzip, math, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_poolperps as W
def main(path):
    d = json.load(gzip.open(path)); cand = {tk: {int(t): tuple(v) for t, v in by.items()} for tk, by in d["data"].items()}; fund = {tk: {int(t): float(r) for t, r in f.items()} for tk, f in d["funding"].items()}
    days = W.trading_days(cand); nd = len(days); ev = W.events(cand, fund); memo = {}
    def sc(nm, e):
        k = (nm, e)
        if k not in memo:
            sg = W.sigma(cand[nm], e); memo[k] = None if sg is None else sg * math.sqrt(30)
        return memo[k]
    lines = ["header BH m = %d (%d new rules + %d carried)" % (len(W.ALL_SIGNALS[:-2]) * 12 + 2 + W.PRIOR_PERPS_M, len(W.ALL_SIGNALS[:-2]) * 12 + 2, W.PRIOR_PERPS_M), "trading_days %d" % nd]
    for sid in W.ALL_SIGNALS:
        for x in ([None] if sid.startswith("carry") else W.EXITS):
            r1, c1 = W.run_rule(cand, fund, ev.get(sid, []), x, W.H_PRIMARY, sc); r2, c2 = W.run_rule(cand, fund, ev.get(sid, []), x, W.H_SECOND, sc)
            b1 = [r for r in r1 if not r[6]]; b2 = [r for r in r2 if not r[6]]; s1 = W.stats(b1, nd); s2 = W.stats(b2, nd)
            lines.append("%s|%s|t1=%d|b1=%d|t2=%d|b2=%d|net1=%r|net2=%r|pf1=%r|pf2=%r|skips1=%s" % (sid, "carry" if x is None else "%d-%d-%d" % x, len(r1), len(b1), len(r2), len(b2), s1["net_total"], s2["net_total"], s1["pf"], s2["pf"], json.dumps(dict(sorted(c1.items())))))
    print("\n".join(lines)); print("sha256 of the lines:", hashlib.sha256("\n".join(lines).encode()).hexdigest(), file=sys.stderr)
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
