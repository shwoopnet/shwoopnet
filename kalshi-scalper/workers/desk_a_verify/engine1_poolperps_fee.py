"""ENGPERPS_POOL1 FEE SENSITIVITY (Desk A, Nov 16 2026), the Head's request: from the SAME rules and the SAME trades as the pooled run (no new rule, no new m), re-state each rule's net per trade and PF at taker fees of 4, 8 and 12 bp a side (plus the 0.02% / 0.05% haircut already in the fills), and the break-even fee per rule. Label: sensitivity, NOT a pass. Net at fee f = (gross + funding) - 2 f; the trades do not depend on the fee.
  python3 -I engine1_poolperps_fee.py <dir holding the two stock perp extracts> <out.json>"""
import sys, os, json, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_poolperps as W, engine1_poolperps_load as L
FEES = (0.0004, 0.0008, 0.0012)
def main(base, out):
    cand, fund, counts, dropped = L.load(base); nd = len(W.trading_days(cand)); ev = W.events(cand, fund); memo = {}
    def sc(nm, e):
        k = (nm, e)
        if k not in memo:
            sg = W.sigma(cand[nm], e); memo[k] = None if sg is None else sg * math.sqrt(30)
        return memo[k]
    rows_out = []
    for sid in W.ALL_SIGNALS:
        for x in ([None] if sid.startswith("carry") else W.EXITS):
            rec = {"signal": sid, "exit": (None if x is None else {"kt": x[0], "ks": x[1], "T": x[2]})}
            for tag, h in (("h0.0002", W.H_PRIMARY), ("h0.0005", W.H_SECOND)):
                rs, _ = W.run_rule(cand, fund, ev.get(sid, []), x, h, sc); rs = [r for r in rs if not r[6]]
                gross_funding = [r[2] + 2 * W.TAKER for r in rs]; n = len(rs)
                rec["n_" + tag] = n; rec["break_even_fee_bp_per_side_" + tag] = (sum(gross_funding) / n / 2 * 1e4 if n else None)
                for f in FEES:
                    xs = [g - 2 * f for g in gross_funding]
                    rec["net_bp_" + tag + "_fee%d" % round(f * 1e4)] = (sum(xs) / n * 1e4 if n else None); rec["pf_" + tag + "_fee%d" % round(f * 1e4)] = W.pf(xs)
            rec["trades_per_day"] = rec["n_h0.0002"] / nd; rows_out.append(rec)
    fam = collections.defaultdict(list)
    for r in rows_out: fam[r["signal"].split(":")[0]].append(r)
    best = {}
    for k, v in fam.items():
        best[k] = {}
        for f in FEES:
            key = "net_bp_h0.0002_fee%d" % round(f * 1e4); b = max((r for r in v if r["n_h0.0002"]), key=lambda r: r[key])
            best[k]["fee%d" % round(f * 1e4)] = {"signal": b["signal"], "exit": b["exit"], "n": b["n_h0.0002"], "trades_per_day": b["trades_per_day"], "net_bp_h0.0002": b[key], "pf_h0.0002": b["pf_h0.0002_fee%d" % round(f * 1e4)], "pf_h0.0005": b["pf_h0.0005_fee%d" % round(f * 1e4)], "net_bp_h0.0005": b["net_bp_h0.0005_fee%d" % round(f * 1e4)], "break_even_fee_bp_per_side": b["break_even_fee_bp_per_side_h0.0002"]}
    json.dump({"label": "FEE SENSITIVITY, not a pass; development, 6 trading days in one regime, no evidence at n < 100; same rules and trades as the pooled run, m unchanged", "best_by_family": best, "rules": rows_out}, open(out, "w"), indent=1, default=str); print("wrote", out)
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
