"""DEPTH1 wrapper under AMENDMENT 1 (Idea Desk A, Nov 12 2026, on the Head of R&D's word; V2's depth1.py and its frozen hash are NOT touched).
  THE READ:  python3 -I depth1_wrapper.py <path to the kalshi-scalper dir of V2's branch>        (refuses before 2026-11-14 00:00 UTC and on a second run, through V2's run())
Amendment 1 (written before any R6 outcome was read; text in DEPTH1_AMENDMENT_1_DESK_A.md):
 (a) usable() may drop a window only for reasons known at or before the decision; a missing or non yes/no result is NOT a reason. (installed: usable is called with the result field set to "yes" so every other test is V2's own)
 (b) a window where a feature FIRES and there is no yes or no result is booked as a FEE-ONLY LOSS (price refunded, fee kept), counted in n, PF and z, the count printed; a true void is booked the same way.
 (c) windows where the rule does not fire are unaffected.
 (d) the two features that sit in the closed taker order-flow family, f6_thin_depletion and f7_sweep_net, are printed as SEPARATE lines under their own header; nothing resting on either alone can become a lead.
 (e) default-closed: V2's run() refuses before the date, on a second run and on a started marker; the wrapper adds nothing that bypasses it.
 STOP RULE: if fired windows with no yes/no result exceed 1% of fired windows, the wrapper stops BEFORE the verdict line is written and says so (on a 15 minute Bitcoin series that would be a data gap, not voids); the started marker stays, so the run is never quietly repeated; the Head decides."""
import sys, collections
from pathlib import Path
def install(D):
    state = {"orig_usable": D.usable, "orig_wr": D.window_record, "orig_score": D.score, "nores": collections.Counter(), "scored": None}
    def usable(close, row):                                    # (a)
        r = dict(row); r["result"] = "yes"; return state["orig_usable"](close, r)
    def window_record(polls, trades, close, result):           # (b)
        res = result if result in ("yes", "no") else None
        w = state["orig_wr"](polls, trades, close, result if res else "NO_YES_NO_RESULT")
        if w is None or res: return w
        for side, f in w["fill"].items():
            if f:                                              # V2 booked win 0: pnl = -px - fee. Price refunded, fee kept: pnl = -fee.
                f["pnl"] += f["px"]; f["pnl_stress"] += f["px"]; f["win"] = 0.0
        w["nores"] = True; w["result_raw"] = result if result else "(empty)"
        return w
    def score(scored, per):
        fired = [w for w in scored if any(D.trade_of(w, n) for n in D.NAMES)]
        nr = [w for w in fired if w.get("nores")]
        state["scored"] = scored; frac = len(nr) / len(fired) if fired else 0.0
        line = f"AMENDMENT 1 COUNT: windows where a feature fires {len(fired)}; of them with no yes/no result (booked fee-only, counted) {len(nr)} ({100 * frac:.2f}%); raw results {dict(collections.Counter(w['result_raw'] for w in nr))}"
        print(line)
        if frac > 0.01:
            raise SystemExit("STOP (Amendment 1): " + line + " -- above 1%: a data gap, not voids. No verdict written. Tell the Head. The started marker stays.")
        v, lines = state["orig_score"](scored, per)
        lines.insert(0, line)
        sep = ["", "CLOSED-FAMILY FEATURES, REPORTED SEPARATELY (Head's ruling): nothing that rests on either alone can become a lead; the headline above is judged on the registered whole (20 tries, the registered bar)"]
        for m in D.UNIVERSE:
            ws = [w for w in scored if w["series"] == m]
            for nm in ("f6_thin_depletion", "f7_sweep_net"):
                s = D.try_stats(ws, nm)
                sep.append(f"  {m} {nm}: n {s['n']} PF {s['pf']:.2f} net {s['net_c']:+.2f}c stress PF {s['pf_stress']:.2f} blocks {' / '.join(f'{p:.2f} (n {k})' for k, p in s['blocks'])} halves {s['halves'][0]:.2f} / {s['halves'][1]:.2f} z {s['z']:+.2f}")
        return v, lines + sep
    D.usable, D.window_record, D.score = usable, window_record, score
    return state
def main(root):
    sys.path.insert(0, str(Path(root).resolve() / "src")); from scalper import depth1 as D
    install(D); return D.run()
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
