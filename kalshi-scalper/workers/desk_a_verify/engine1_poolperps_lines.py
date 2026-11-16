"""ENGPERPS_POOL1 real-data text lines for the second build's compare (Desk A, Nov 16 2026): the SAME format as engine1_poolperps_fixture.py (header with m, trading_days, then one line per rule: signal|exit|t1|b1|t2|b2|net1|net2|pf1|pf2|skips1, full precision), from the audited loader (allow line required). Prints only the lines to the output path.
  python3 -I engine1_poolperps_lines.py <dir holding the two stock perp extracts> <out.txt>"""
import sys, os, json, math, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_poolperps as W, engine1_poolperps_load as L
def main(base, out):
    cand, fund, counts, dropped = L.load(base); days = W.trading_days(cand); nd = len(days); ev = W.events(cand, fund); memo = {}
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
    open(out, "w").write("\n".join(lines) + "\n"); print("wrote", out, hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest())
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
