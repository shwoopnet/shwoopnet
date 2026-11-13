#!/usr/bin/env python3
"""WHEEL0: the unrounded companion to the frozen scorer (Forensics desk, Nov 13, 2026; the Head of R&D's ruling of 15:36Z, standing rule 16b: a bar is decided on UNROUNDED figures).
`wheel0.py` (sha256 10a7b363...) is frozen and prints PF to 3 decimals and D and both p to 4. This file imports it, changes nothing in it, and recomputes the three verdict figures
(profit factor after HOT, D, the bootstrap p, the null-calibrated p) from the SAME orders with the SAME functions and seeds, unrounded, printing them beside the rounded ones, with a flag when a figure lies
within 0.001 of its bar (the same window for every bar figure: PF against 1.0 and 1.15, D against 0, each p against 0.05; AUDIT_PREP step 8) and the verdict taken on the UNROUNDED figures. Where a figure is flagged, 'exact' means exact to the frozen scorer's own 1e-9 EPS (wheel0.py line 30): both builds decide that bar in exact arithmetic with that tolerance. It reads no result before the same
precondition as the scorer's own run (not before 2026-11-14T00:00Z and the DEPTH1 marker line), refuses any run listed in HELDOUT_PULL_RUNS.md (listed_runs_guard) and prints its own and the scorer's sha256.
usage: python3 -I wheel0_unrounded.py run --lists <run...> --candles <run...> --out <new json file> --go <the Head's go line>       (same inputs and the same go line as the scorer's run; not run before the Head's go)
       python3 -I wheel0_unrounded.py selftest                                                           (made-up data only: the unrounded figures must round to the scorer's own printed figures)"""
import sys, os, json, hashlib, collections, random, time, math, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = "10a7b3630be5807a"
sys.path.insert(0, os.path.join(HERE, ".."))


def load_scorer():
    p = os.path.join(HERE, "wheel0.py"); h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if not h.startswith(FROZEN): raise SystemExit("refused: wheel0.py is not the frozen scorer (%s)" % h[:16])
    sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location("wheel0", p); m = importlib.util.module_from_spec(spec); sys.modules["wheel0"] = m; spec.loader.exec_module(m); return m, h


def unrounded_pooled(W, orders, fair):
    """The pooled primary read of `report` (wheel0.py 417 to 435) with every verdict figure kept unrounded. Returns a dict."""
    kept = [o for o in orders if o["ticker"] in fair]; orders = [dict(o) for o in kept]
    for o in orders:
        if o["win"] is None: o["win"] = False
    g = W.grid(orders); rows, ah, an, hot_pairs = [], [], [], 0
    for (s, tpl), gg in g.items():                                             # wheel0.py 297 to 305
        if tpl[2] == W.FAV_HI[0]: continue
        bl = gg["blocks"]; flags = [W.is_hot(b) for b in bl]
        for i in range(1, len(bl)):
            hot_pairs += flags[i - 1]; (ah if flags[i - 1] else an).extend(o["cash"] for o in bl[i]); rows.extend((o["day"], o["cash"], flags[i - 1]) for o in bl[i])
    d0, p_boot, ci = W.boot_p(rows)
    return {"orders": len(orders), "hot_pairs": hot_pairs, "pf_after_hot": W.pf(ah), "D": d0, "p_boot": p_boot, "interval": ci, "_orders": orders}


def null_unrounded(W, orders, fair, d_rounded, d_unrounded, reps=None):
    """wheel0.null_calibration (326 to 346), copied line for line, but it keeps the list of null D values so the p can be taken against the observed D as the scorer does (rounded to 4 decimals)
    and against the unrounded observed D. p stays unrounded."""
    reps = W.NULL_REPS if reps is None else reps
    by = collections.defaultdict(list)
    for o in sorted(orders, key=lambda o: (o["close"], o["ticker"])):
        if o["ticker"] not in fair: continue
        p = o["price"]; f = W.fee10(p)
        by[(o["series"], o["tpl"])].append((o["ticker"], o["side"] == "yes", W.SIZE * (1.0 - p) - f, -W.SIZE * p - f))
    tickers = sorted({x[0] for v in by.values() for x in v}); rng = random.Random(W.SEED + 1); ds = []
    for _ in range(reps):
        res = {t: rng.random() < fair[t] for t in tickers}
        groups = {k: [((cw, True) if res[t] == is_yes else (cl, False)) for t, is_yes, cw, cl in v] for k, v in by.items()}
        ah, an = W._split(groups)
        if ah and an: ds.append(sum(ah) / len(ah) - sum(an) / len(an))
    if not ds or d_unrounded is None: return None, None, len(ds)
    pr = (1 + sum(1 for v in ds if v >= d_rounded - W.EPS)) / (len(ds) + 1); pu = (1 + sum(1 for v in ds if v >= d_unrounded - W.EPS)) / (len(ds) + 1)
    return pr, pu, len(ds)


NEAR = 0.001                                                                  # one window for every bar figure (AUDIT_PREP step 8; the Head, Nov 13)


def near(v, bar, tol): return v is not None and abs(v - bar) <= tol


def unrounded_report(W, orders, fair, reps=None):
    u = unrounded_pooled(W, orders, fair)
    d_r = None if u["D"] is None else round(u["D"], 4)
    p_null_as_scorer, p_null_unr, nrep = null_unrounded(W, u["_orders"], fair, d_r, u["D"], reps)
    pv = {"hot_pairs": u["hot_pairs"], "pf_after_hot": u["pf_after_hot"], "D_dollars_per_order_of_10": u["D"], "D_one_sided_p_day_bootstrap": u["p_boot"]}
    verdict_unrounded = W.verdict(pv, p_null_unr)
    printed = {"pf_after_hot": None if u["pf_after_hot"] is None else (u["pf_after_hot"] if u["pf_after_hot"] == float("inf") else round(u["pf_after_hot"], 3)), "D": d_r,
               "p_boot": None if u["p_boot"] is None else round(u["p_boot"], 4), "p_null": None if p_null_as_scorer is None else round(p_null_as_scorer, 4)}
    pvp = {"hot_pairs": u["hot_pairs"], "pf_after_hot": printed["pf_after_hot"], "D_dollars_per_order_of_10": printed["D"], "D_one_sided_p_day_bootstrap": printed["p_boot"]}
    verdict_printed = W.verdict(pvp, printed["p_null"])
    flags = []
    if near(u["pf_after_hot"], 1.0, NEAR) or near(u["pf_after_hot"], W.VERDICT_PF, NEAR): flags.append("pf_after_hot within 0.001 of 1.0 or 1.15")
    if near(u["D"], 0.0, NEAR): flags.append("D within 0.001 of 0")
    for nm, v in (("p_boot", u["p_boot"]), ("p_null", p_null_unr)):
        if near(v, W.VERDICT_P, NEAR): flags.append("%s within 0.001 of 0.05" % nm)
    return {"hot_pairs": u["hot_pairs"], "orders": u["orders"],
            "pf_after_hot": {"unrounded": u["pf_after_hot"], "printed_by_scorer": printed["pf_after_hot"]}, "D": {"unrounded": u["D"], "printed_by_scorer": printed["D"]},
            "p_bootstrap": {"unrounded": u["p_boot"], "printed_by_scorer": printed["p_boot"]},
            "p_null": {"unrounded_against_unrounded_D": p_null_unr, "against_the_rounded_D_as_the_scorer_does_unrounded": p_null_as_scorer, "printed_by_scorer": printed["p_null"], "reps": nrep},
            "interval_95_unrounded": u["interval"], "near_a_bar": flags, "verdict_on_unrounded_figures": verdict_unrounded, "verdict_the_scorer_prints": verdict_printed,
            "verdicts_agree": verdict_unrounded == verdict_printed,
            "near_a_bar_window": NEAR, "note": "Standing rule 16b: the recorded verdict is the one on the unrounded figures. If a figure is within 0.001 of a bar the flag says so and both builds decide that bar in exact arithmetic, where exact means exact to the frozen scorer's 1e-9 EPS."}


def selftest():
    W, h = load_scorer(); ok = []
    def chk(name, cond, detail=""): ok.append(bool(cond)); print("%-110s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    drop = {(grp, L, k, b[0]): 0.8 for grp in ("gold_xrp_doge", "xrp_doge") for L in W.LOOKS for k in W.BANDS for b in W.BANDS[k]}; drop.update({(grp, L, "fav", W.FAV_HI[0]): 0.9 for grp in ("gold_xrp_doge", "xrp_doge") for L in W.LOOKS})
    for tag, seed, persist, nd in (("persistence planted", 2, True, 60), ("no effect", 1, False, 40)):
        mk, cd = W._synth(seed, persist=persist, n_days=nd); od, _ = W.orders_from_candles(mk, cd, drop); fair = W.fair_yes(mk, cd)
        r = unrounded_report(W, od, fair, reps=60)
        rep = W.report([dict(o) for o in od], "selftest", fair)                                              # the scorer's own pooled numbers (null reps differ: the scorer uses 500)
        pp = rep["primary_pooled"]
        chk("%s: unrounded PF, D and bootstrap p round to the scorer's printed figures" % tag, r["pf_after_hot"]["unrounded"] is not None and round(r["pf_after_hot"]["unrounded"], 3) == pp["pf_after_hot"] and round(r["D"]["unrounded"], 4) == pp["D_dollars_per_order_of_10"]
            and round(r["p_bootstrap"]["unrounded"], 4) == pp["D_one_sided_p_day_bootstrap"] and r["hot_pairs"] == pp["hot_pairs"], "PF %r D %r p %r" % (r["pf_after_hot"]["unrounded"], r["D"]["unrounded"], r["p_bootstrap"]["unrounded"]))
        r500 = unrounded_report(W, od, fair)
        chk("%s: at the scorer's 500 repetitions the null p printed by the scorer equals this file's p taken the scorer's way, rounded" % tag, r500["p_null"]["printed_by_scorer"] == pp["null_calibration"]["D_null_calibrated_p"] and round(r500["p_null"]["against_the_rounded_D_as_the_scorer_does_unrounded"], 4) == pp["null_calibration"]["D_null_calibrated_p"],
            "null p %r vs scorer %r" % (r500["p_null"]["printed_by_scorer"], pp["null_calibration"]["D_null_calibrated_p"]))
        chk("%s: the verdict the scorer prints is reproduced from its printed figures, and the unrounded verdict is computed" % tag, r500["verdict_the_scorer_prints"] == rep["verdict"] and isinstance(r500["verdict_on_unrounded_figures"], str), "%s | %s" % (r500["verdict_the_scorer_prints"], r500["verdict_on_unrounded_figures"]))
    # the flag and the decision on a planted near-bar case: a figure that rounds onto the bar but sits just past it
    pv = {"hot_pairs": 40, "pf_after_hot": 1.14996, "D_dollars_per_order_of_10": 0.3, "D_one_sided_p_day_bootstrap": 0.03}
    chk("a PF of 1.14996 prints as 1.150 and passes the 1.15 bar rounded, but fails it unrounded (the case 16b exists for)", round(1.14996, 3) >= 1.15 - W.EPS and W.verdict(pv, 0.04).startswith("no evidence") and W.verdict(dict(pv, pf_after_hot=round(1.14996, 3)), 0.04) == "PREMISE SUPPORTED")
    chk("near-bar flags use one window, 0.001, for PF, D and p: inside it they fire, outside they do not", near(1.1496, 1.15, NEAR) and not near(1.152, 1.15, NEAR) and near(0.0505, 0.05, NEAR) and not near(0.0512, 0.05, NEAR) and near(0.0009, 0.0, NEAR) and not near(0.0011, 0.0, NEAR))
    def _try(argv):
        try: run(argv); return "ran"
        except SystemExit as e: return str(e)
    r1_, r2_ = _try(["--out", "/tmp/_unr_never_written.json"]), _try(["--go", "x"])
    chk("the run is refused without --go and without --out, before anything is read or written", "--go" in r1_ and "--out" in r2_ and not os.path.exists("/tmp/_unr_never_written.json"), (r1_[:50] + " | " + r2_[:50]))
    print("\n%d checks, %d FAIL; wheel0.py sha256 %s" % (len(ok), sum(1 for x in ok if not x), h[:16])); return 0 if all(ok) else 1


def run(argv):
    W, h = load_scorer(); a = W._args(argv)
    if not a["go"] or not a["out"]: raise SystemExit("refused: the run needs --go <the Head of R&D's go line> and --out <new file>; the read is made once")
    if os.path.exists(a["out"][0]): raise SystemExit("refused: %s exists" % a["out"][0])
    why = W.precondition(time.time(), open(W.MARKER_FILE).read() if os.path.exists(W.MARKER_FILE) else "")
    if why: raise SystemExit(why)
    from listed_runs_guard import refuse_listed, listed_source
    for f in a["lists"] + a["candles"]: refuse_listed(f)
    src, lh = listed_source()
    drop, dsha = W.load_drop_table(); mk, c1 = W.read_markets(a["lists"], with_result=True); cd = W.read_candles(a["candles"], mk); od, c2 = W.orders_from_candles(mk, cd, drop); fair = W.fair_yes(mk, cd)
    res = {"companion_of": "wheel0.py", "go": " ".join(a["go"]), "scorer_sha256": h, "this_file_sha256": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(), "drop_table_sha256": dsha, "list_copy": os.path.relpath(src), "list_copy_sha256": lh,
           "markets": len(mk), "market_counts": c1, "candle_signal_counts": c2, "pooled": unrounded_report(W, od, fair)}
    json.dump(res, open(a["out"][0], "w"), indent=1, default=str); print(json.dumps(res["pooled"], indent=1, default=str)); return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit(selftest() if cmd == "selftest" else run(sys.argv[2:]) if cmd == "run" else print(__doc__) or 2)
