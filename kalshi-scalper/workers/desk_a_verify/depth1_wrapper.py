"""DEPTH1 wrapper under AMENDMENT 1 (Idea Desk A, Nov 12 2026, on the Head of R&D's word; V2's depth1.py and its frozen hash are NOT touched).
  THE READ:  python3 -I depth1_wrapper.py <path to the kalshi-scalper dir of V2's branch>        (refuses before 2026-11-14 00:00 UTC and on a second run, through V2's run())
Amendment 1 (written before any R6 outcome was read; text in DEPTH1_AMENDMENT_1_DESK_A.md):
 (a) usable() may drop a window only for reasons known at or before the decision; a missing or non yes/no result is NOT a reason. (installed: usable is called with the result field set to "yes" so every other test is V2's own)
 (b) a window where a feature FIRES and there is no yes or no result is booked as a FEE-ONLY LOSS (price refunded, fee kept), counted in n, PF and z, the count printed; a true void is booked the same way.
 (c) windows where the rule does not fire are unaffected.
 (d) the two features that sit in the closed taker order-flow family, f6_thin_depletion and f7_sweep_net, are printed as SEPARATE lines under their own header; nothing resting on either alone can become a lead.
 (e) default-closed: V2's run() refuses before the date, on a second run and on a started marker; the wrapper adds nothing that bypasses it.
 (f) printed BEFORE the verdict lines, cannot change them (Head, Nov 12): V2's registered NO-LABEL NOISE DESCRIPTION (share of looks where the five-level imbalance f1 changes sign within 4 s, i.e. between the decision poll and either of the next two 2 s polls, and for each other single-poll size feature f2, f3, f8, f9, f10 the share where its sign differs between the decision poll and the next two polls; f4, f5, f6 need earlier polls and f7 the tape, so they are not in it), per market; the MEDIAN FILL DELAY (fill poll time minus decision poll time) per market; and per market how many otherwise-eligible windows each usable() condition removed (counted from the coverage row for the report only; V2's function decides). Reads no outcome.
 STOP RULE: if fired windows with no yes/no result exceed 1% of fired windows, the wrapper stops BEFORE the verdict line is written and says so (on a 15 minute Bitcoin series that would be a data gap, not voids); the started marker stays, so the run is never quietly repeated; the Head decides."""
import sys, collections
from pathlib import Path
def install(D):
    state = {"removed": collections.Counter(), "noise": collections.defaultdict(lambda: collections.Counter()), "delay": collections.defaultdict(list), "orig_usable": D.usable, "orig_wr": D.window_record, "orig_score": D.score, "nores": collections.Counter(), "scored": None}
    def usable(close, row):                                    # (a)
        r = dict(row); r["result"] = "yes"; ok = state["orig_usable"](close, r)
        if not ok:                                              # counting only: which conditions failed (V2's own function decided)
            u = D.CONFIG["usable"]; polls, okp = int(r.get("polls") or 0), int(r.get("ok_polls") or 0); first, last = int(r.get("first_recv_ms") or 0) / 1000, int(r.get("last_recv_ms") or 0) / 1000; note = r.get("note") or ""
            for name, bad in (("no ticker or no polls", not r.get("ticker") or polls <= 0), ("ok_polls/polls below minimum", polls > 0 and okp / polls < u["min_ok_polls"]), ("max gap too long", int(r.get("max_gap_ms") or 0) > u["max_gap_ms"]),
                              ("tape pages 0", int(r.get("tape_pages") or 0) < 1), ("bad tape note", any(b in note for b in u["bad_notes"])), ("first poll too late", first <= 0 or first > close - u["first_recv_at_or_before_s"]),
                              ("last poll too early", last < close - u["last_recv_at_or_after_s"]), ("window opened at or after the recorder end", close - 900 >= D.END_UTC)):
                if bad: state["removed"][(r.get("series"), name)] += 1
        return ok
    def window_record(polls, trades, close, result):           # (b)
        res = result if result in ("yes", "no") else None
        w = state["orig_wr"](polls, trades, close, result if res else "NO_YES_NO_RESULT")
        if w is not None:                                       # (f) noise description and fill delay: book only, no outcome
            Sd = D.R6.last_at(polls, close - D.CONFIG["decision_s_before_close"], D.CONFIG["decision_poll_max_early_s"])
            if Sd is not None:
                nxt = [p for p in polls if p.t > Sd.t + 1e-9][:2]; ser = w.get("series")
                sg = lambda fn, p: (lambda v: None if v is None or v != v or v == 0 else (v > 0))(fn(D.Ctx(p, None, None, [])))
                w["noise"] = {}
                for fn in D.FEATURES:
                    if fn.__name__ in ("f4_d_imb30", "f5_d_imb60", "f6_thin_depletion", "f7_sweep_net"): continue
                    a = sg(fn, Sd); b = [sg(fn, p) for p in nxt]
                    w["noise"][fn.__name__] = None if a is None or not b else any(x is not None and x != a for x in b)
                F = D.R6.first_at(polls, Sd.t + D.CONFIG["live_delay_s"], D.CONFIG["fill_poll_max_late_s"]); w["fill_delay"] = (F.t - Sd.t) if F is not None else None
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
        import statistics as _st
        pre = ["NO-LABEL NOISE DESCRIPTION (registered by V2; reads no outcome, scores nothing, changes no label): share of looks where a single-poll size feature's sign differs between the decision poll and either of the next two 2 s polls (f1 = the five-level imbalance changing sign within 4 s)"]
        for m in D.UNIVERSE:
            ws = [w for w in scored if w["series"] == m and w.get("noise")]
            parts = []
            for nm in sorted({k for w in ws for k in w["noise"]}):
                v = [w["noise"][nm] for w in ws if w["noise"].get(nm) is not None]
                if v: parts.append(f"{nm} {100 * sum(v) / len(v):.1f}% of {len(v)}")
            dl = [w["fill_delay"] for w in scored if w["series"] == m and w.get("fill_delay") is not None]
            pre.append(f"  {m}: " + "; ".join(parts) + (f" | median fill delay (fill poll minus decision poll) {_st.median(dl):.1f} s over {len(dl)} windows" if dl else ""))
            rem = {k[1]: v for k, v in state["removed"].items() if k[0] == m}
            pre.append(f"  {m}: otherwise-eligible windows removed by each usable() condition (report only): {rem if rem else 'none'}")
        print("\n".join(pre))
        v, lines = state["orig_score"](scored, per)
        lines = pre + [""] + lines
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
