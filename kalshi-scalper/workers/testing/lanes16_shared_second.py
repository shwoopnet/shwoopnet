#!/usr/bin/env python3
"""Runs the lanes 1 and 6 second build on Desk A's shared compare fixtures. python3 -B lanes16_shared_second.py <fixture json> 1|2 -> tab separated lines.
Fixture 1 (one page-max table): signal kt ks T column n signals filled pf_lo pf_hi net_bp pct_margin_50 trades_without_page_max gate candidate_blocked.
Fixture 2 (two tables): table first, then the same fields, with maker_only before candidate_blocked and bh_survivor last (TT only, '-' else).
Definitions (my readings, flagged): n = booked trades of the column at h 0.0002; signals = events of the rule; filled = trades entered (booked or not) at h 0.0002; pf_lo, pf_hi = PF of the booked nets at h 0.0002 and 0.0005; net_bp = mean booked net at h 0.0002 in bp of price; pct_margin_50 = mean percent of margin at 50 percent of the page max over trades with page max for every leg."""
import json, math, sys
import lanes16_driver_second as D

def f(x):
    if x is None: return "None"
    if isinstance(x, bool): return str(x)
    if isinstance(x, float): return "inf" if math.isinf(x) else "%.12g" % x
    return str(x)

def one(fx, table):
    data = {n: {int(t): tuple(c) for t, c in s.items()} for n, s in fx["candles"].items()}; fund = {n: {int(t): r for t, r in s.items()} for n, s in fx["funding"].items()}
    lines = D.run(data, fund, table, fx["m_carried"], {"b": tuple(fx["names"])}); rules = [json.loads(l) for l in lines[1:-1]]; return rules, json.loads(lines[0])

def main(path, kind):
    fx = json.load(open(path)); tables = {"": fx["page_max"]} if kind == "1" else fx["page_max_tables"]
    for tn, table in tables.items():
        rules, head = one(fx, table)
        for r in sorted(rules, key=lambda x: 0):   # driver order is alphabetical by rule key; print in signal, kt, ks, T order instead
            pass
        order = []
        for L in (30, 60):
            for c in (1, 2):
                for mode in ("follow", "revert"): order.append("rs_L%d_c%d_%s" % (L, c, mode))
        for W in (120, 240):
            for z in (2, 3): order.append("pair_W%d_z%d" % (W, z))
        key = {(r["signal"], r["kt"], r["ks"], r["T"]): r for r in rules}
        for s in order:
            for ex in D.m.EXITS:
                r = key[(s,) + tuple(ex)]
                for col in [k for k, _n in D.COLS if k in r["cols"]]:
                    c = r["cols"][col]; pct = c["margin"].get("50%", {}).get("mean_pct_of_margin") if c["margin"] else None
                    nopm = c["margin"]["50%"]["trades_without_page_max_not_shown"] if c["margin"] else 0
                    row = ([tn] if kind == "2" else []) + [s, ex[0], ex[1], ex[2], col, c["n"], r["events"], c["trades"], c["pf_lo"], c["pf_hi"], c["mean_bps"], pct if pct is not None else "no page max, not shown", nopm, c["gate"]]
                    if kind == "2": row += [r["maker_only"]]
                    row += [c["candidate_blocked"]]
                    if kind == "2": row += [r["bh_survivor"] if col == "TT" else "-"]
                    print("\t".join(f(x) for x in row))

if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
