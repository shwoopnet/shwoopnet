"""DEPTH1 wrapper under AMENDMENT 1, 3 and 4 (Idea Desk A, Nov 12 and Nov 13 2026, on the Head of R&D's word; V2's depth1.py and its frozen hash are NOT touched).
  THE READ:  python3 -I depth1_wrapper.py <path to the kalshi-scalper dir of V2's branch>        (refuses before 2026-11-14 00:00 UTC and on a second run, through V2's run())
Amendment 1 (written before any R6 outcome was read; text in DEPTH1_AMENDMENT_1_DESK_A.md):
 (a) usable() may drop a window only for reasons known at or before the decision; a missing or non yes/no result is NOT a reason. (installed: usable is called with the result field set to "yes" so every other test is V2's own)
 (b) a window where a feature FIRES and there is no yes or no result is booked as a FEE-ONLY LOSS (price refunded, fee kept), counted in n, PF and z, the count printed; a true void is booked the same way.
 (c) windows where the rule does not fire are unaffected.
 (d) the two features that sit in the closed taker order-flow family, f6_thin_depletion and f7_sweep_net, are printed as SEPARATE lines under their own header; nothing resting on either alone can become a lead.
 (e) default-closed: V2's run() refuses before the date, on a second run and on a started marker; the wrapper adds nothing that bypasses it.
 (f) printed BEFORE the verdict lines, cannot change them (Head, Nov 12): V2's registered NO-LABEL NOISE DESCRIPTION (share of looks where the five-level imbalance f1 changes sign within 4 s, i.e. between the decision poll and either of the next two 2 s polls, and for each other single-poll size feature f2, f3, f8, f9, f10 the share where its sign differs between the decision poll and the next two polls; f4, f5, f6 need earlier polls and f7 the tape, so they are not in it), per market; the MEDIAN FILL DELAY (fill poll time minus decision poll time) per market; and per market how many otherwise-eligible windows each usable() condition removed (counted from the coverage row for the report only; V2's function decides). Reads no outcome.
 AMENDMENT 3 (Nov 13, text in DEPTH1_AMENDMENT_3_DESK_A.md; a fault fix and the stricter z, made after the second build's comparison on invented fixtures and before any outcome was joined; no threshold, feature definition, window or try changed): (g) for ALL ten features a value whose absolute size is at or under 1e-12 is ZERO, no trade (applied once, to the features of every window, so the trade rule, the shuffled-book control and the noise description all see the same zero); (h) the VERDICT reads the cluster-corrected z (variance x D/(D-1), D the number of date clusters in that try) against the 5.27 bar; the uncorrected z is printed beside it as information.
 AMENDMENT 4 (Nov 13, text in DEPTH1_AMENDMENT_4_DESK_A.md; two exact-tie fixes found by the auditor's raw-float scan, after the second build's comparison on invented rows, before any outcome was joined; no threshold, feature definition, window or try changed): (i) every verdict bar in passes() is compared in INTEGERS (trade results in thousandths of a dollar, exact for the whole-cent results and for the 1.2 x fee stress results): profit factor >= 1.5 is 2 x wins >= 3 x losses, each half above 1.0 is wins > losses, net > 0, stress net > 0, stress profit factor > 1.2 is 5 x wins > 6 x losses; (j) f6_thin_depletion: if the two 5-level sizes 60 s ago differ by 1e-9 or less in absolute size they are a TIE, f6 is 0.0, no trade (V2's own test is an exact equality). V2's depth1.py and its frozen hash are untouched.
 STOP RULE: if fired windows with no yes/no result exceed 1% of fired windows, the wrapper stops BEFORE the verdict line is written and says so (on a 15 minute Bitcoin series that would be a data gap, not voids); the started marker stays, so the run is never quietly repeated; the Head decides."""
import sys, math, collections
from pathlib import Path
ZERO_TOL = 1e-12
def install(D):
    state = {"removed": collections.Counter(), "noise": collections.defaultdict(lambda: collections.Counter()), "delay": collections.defaultdict(list), "orig_usable": D.usable, "orig_wr": D.window_record, "orig_score": D.score, "nores": collections.Counter(), "scored": None, "orig_cz": D.clustered_z, "orig_ts": D.try_stats, "orig_passes": D.passes, "last_unc": 0.0}
    def clustered_z(vals, keys):                                # Amendment 3 (h): the corrected z decides; the uncorrected one is kept for printing
        n = len(vals); state["last_unc"] = state["orig_cz"](vals, keys)
        if n < 2: return 0.0
        mu = sum(vals) / n; by = collections.defaultdict(float)
        for v, k in zip(vals, keys): by[k] += v - mu
        d = len(by)
        if d < 2: return 0.0
        var = sum(x * x for x in by.values()) * d / (d - 1) / (n * n)
        return mu / math.sqrt(var) if var > 0 else 0.0
    def try_stats(ws, name):
        state["last_unc"] = 0.0; st = state["orig_ts"](ws, name); st["z_unc"] = state["last_unc"]
        tr = sorted(((w["close"], w["date"], *D.trade_of(w, name)) for w in ws if D.trade_of(w, name)), key=lambda x: x[0])   # same selection and order as V2's try_stats
        pn = [round(t[3]["pnl"] * 1000) for t in tr]; ps = [round(t[3]["pnl_stress"] * 1000) for t in tr]; n = len(pn)
        wl = lambda x: (sum(v for v in x if v > 0), -sum(v for v in x if v < 0))
        st["int"] = dict(n=n, blocks=[(len(b), wl(b)) for b in ([[pn[j] for j, t in enumerate(tr) if D.block_of(t[1]) == i] for i in range(3)])], pooled=wl(pn), halves=[wl(pn[:n // 2]), wl(pn[n // 2:])], net=sum(pn), net_stress=sum(ps), stress=wl(ps))
        return st
    def ge(w_l, num, den):                                      # profit factor >= num/den in integers, V2's pf(): no losses with wins is infinite, nothing at all is 0
        w, l = w_l; return (w > 0) if l == 0 else den * w >= num * l
    def gt(w_l, num, den):
        w, l = w_l; return (w > 0) if l == 0 else den * w > num * l
    def passes(st, ctrl_ok, zb):                                # Amendment 4 (i): the registered bar, compared in integers
        b = D.CONFIG["bar"]; I = st["int"]
        assert b["pf_each_block"] == 1.5 and b["pf_pooled"] == 1.5 and b["halves_pf_above"] == 1.0 and b["stress_pf_above"] == 1.2 and b["n_trades"] == 300
        return (st["n"] >= 300 and all(k > 0 and ge(wl_, 3, 2) for k, wl_ in I["blocks"]) and ge(I["pooled"], 3, 2) and all(gt(h, 1, 1) for h in I["halves"])
                and I["net"] > 0 and I["net_stress"] > 0 and gt(I["stress"], 6, 5) and st["z"] >= zb and ctrl_ok)
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
        if w is not None:                                       # Amendment 3 (g): |v| <= 1e-12 is exactly zero for all ten features
            w["resid"] = [k for k, v in w["feat"].items() if v is not None and v != 0 and abs(v) <= ZERO_TOL]
            for k, v in list(w["feat"].items()):
                if v is not None and abs(v) <= ZERO_TOL: w["feat"][k] = 0.0
            Sx = D.R6.last_at(polls, close - D.CONFIG["decision_s_before_close"], D.CONFIG["decision_poll_max_early_s"])   # Amendment 4 (j): f6 tie at 1e-9, V2's own test is exact equality
            P60 = D.R6.last_at(polls, Sx.t - 60, D.CONFIG["lookback_poll_max_early_s"]) if Sx is not None else None
            if P60 is not None and w["feat"].get("f6_thin_depletion") is not None:
                y0, n0 = D._sums(P60)
                if abs(y0 - n0) <= 1e-9: w["feat"]["f6_thin_depletion"] = 0.0
        if w is not None:                                       # (f) noise description and fill delay: book only, no outcome
            Sd = D.R6.last_at(polls, close - D.CONFIG["decision_s_before_close"], D.CONFIG["decision_poll_max_early_s"])
            if Sd is not None:
                nxt = [p for p in polls if p.t > Sd.t + 1e-9][:2]; ser = w.get("series")
                sg = lambda fn, p: (lambda v: None if v is None or v != v or abs(v) <= ZERO_TOL else (v > 0))(fn(D.Ctx(p, None, None, [])))
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
        sep += ["", "Z BESIDE (information; the verdict above reads the corrected z, variance x D/(D-1), against 5.27): per try corrected z / uncorrected z"]
        for m in D.UNIVERSE:
            ws = [w for w in scored if w["series"] == m]
            sep.append("  " + m + ": " + "; ".join("%s %+.2f / %+.2f" % (nm.split("_")[0], D.try_stats(ws, nm)["z"], D.try_stats(ws, nm)["z_unc"]) for nm in D.NAMES))
        sep += ["", "ZERO RULE (information): scored windows per try whose raw feature was within 1e-12 of zero but not exactly zero (set to zero, no trade; before this rule each could have traded on floating point residue)"]
        for m in D.UNIVERSE:
            ws = [w for w in scored if w["series"] == m]
            sep.append("  " + m + ": " + "; ".join("%s %d" % (nm.split("_")[0], sum(1 for w in ws if nm in w.get("resid", []))) for nm in D.NAMES))
        return v, lines + sep
    D.usable, D.window_record, D.score, D.clustered_z, D.try_stats, D.passes = usable, window_record, score, clustered_z, try_stats, passes
    return state
def main(root):
    sys.path.insert(0, str(Path(root).resolve() / "src")); from scalper import depth1 as D
    install(D); return D.run()
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
