#!/usr/bin/env python3
"""ETHLATE1 adapter (Desk B, Nov 16 2026). NO new scoring code: it calls Desk A's cleared engine files for ONLY the 96 cell keys of specs/ETHLATE1.spec.json.
REFUSES unless every engine file's sha256 equals the pin below (the files Auditor B cleared). C8 gate: PF 1.3 at 2c (primary), both halves of the 2c PF at 1.0 or more, n >= 100, >= 10 trade days, >= 3 signals a day in SEARCH;
the driver's own 1c gate is NOT used. BH over m_total with the 2c day-clustered p. Expected figures: EXPECTED_ethlate1_run_nov16.md.
Usage: python3 ethlate1_run.py <quote-data checkout> <ETHD_RESULTS run folder>  (the loader refuses unless Main's allow line names it; the engine needs a dated split constant for ETHD from Desk A)."""
import os, sys, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(HERE, "..", "desk_a_verify")
PINS = {"engine1_enum": "e42ee1a45f67b76e8560cd9cbefac352fce9a765c8300bc04d5ce05a27e4d5a7", "engine1_driver": "1281ce0a1dc0bce7875bbafc4774358f557e45d0897b8099f5615c33cf12640b",
        "engine1_split": "00a94c6ef569261ec4f649f596075d85e2b407c43a2bbe9b0a593f75743e07fd", "engine1_core": "53317e4b56a8328fb616d460d5cb4597af13a2b9020d73aefaa37717439694bf"}
M_TOTAL = 6290756                      # 6,290,660 carried + 96 (the Head's ruling of Nov 16, 18:35Z; Auditor B)
BUCKET, BANDS, SIDE = 120, tuple(range(1, 13)), "cheap"
FILTERS = (None, ("spread", "low"), ("spread", "mid"), ("spread", "high")); EXITS = ("H", "M60")
CELLS = frozenset((BUCKET, b, SIDE, f, x) for b in BANDS for f in FILTERS for x in EXITS)
MIN_N, PF_PRIMARY, HALF_MIN, MIN_DAYS, MIN_SPD, ALPHA, MIN_EVENTS = 100, 1.3, 1.0, 10, 3.0, 0.05, 40
def import_engine(engine_dir):
    mods = {}
    for name, want in PINS.items():
        got = hashlib.sha256(open(os.path.join(engine_dir, name + ".py"), "rb").read()).hexdigest()
        if got != want: raise SystemExit("REFUSED: %s.py has sha256 %s, not the pinned %s" % (name, got, want))
    sys.path.insert(0, os.path.abspath(engine_dir))
    import engine1_core as K, engine1_enum as N, engine1_split as S, engine1_driver as D
    return K, N, S, D
def events_of(items): return len({m["close"] for m, _ in items})          # distinct hourly events (UTC close times): the strikes of one event are correlated (Auditor B, Nov 16)
def c8_pass(a, events): return a["n"] >= MIN_N and a["pf"] >= PF_PRIMARY and a["half1"] >= HALF_MIN and a["half2"] >= HALF_MIN and a["trade_days"] >= MIN_DAYS and events >= MIN_EVENTS
def run(markets, m_total=M_TOTAL, engine_dir=ENGINE_DIR):
    assert len(CELLS) == 96, "the spec has 96 cells"
    K, N, S, D = import_engine(engine_dir)
    rep = {"m_total": m_total, "cells_selected": len(CELLS), "primary_haircut": "2c (C8)"}
    mk = markets["KXETHD"]; series = D.short("KXETHD")
    if series not in S.LAST_SEARCH: raise SystemExit("REFUSED: engine1_split has no dated constant for %s (Desk A adds it before any read)" % series)
    sm = [m for m in mk if S.phase(series, m["close"]) == "search"]; vm = [m for m in mk if S.phase(series, m["close"]) == "validate"]
    cuts = {}
    for b in N.BUCKETS:
        sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
        cuts[b] = N.spread_cuts(sp) if sp else None
    sg, vg = D.groups(sm, cuts, None), D.groups(vm, cuts, None)
    sdays = D.search_days([m["close"] for m in sm]); rep["search_markets"] = len(sm); rep["validate_markets"] = len(vm)
    scored, s_pass = 0, {}
    for (b, band, rs, filt), items in sg.items():
        if (b, band, rs, filt, "H") not in CELLS and (b, band, rs, filt, "M60") not in CELLS: continue
        if len(items) < MIN_N: continue
        for x in EXITS:
            if (b, band, rs, filt, x) not in CELLS: continue
            agg, _ = D.score_group(items, x); scored += 1
            a1, a2 = agg[0.01], agg[0.02]
            rep.setdefault("cells", {})[(b, band, rs, filt, x)] = {"n": a2["n"], "pf_1c": a1["pf"], "pf_2c": a2["pf"]}
            if c8_pass(a2, events_of(items)) and sdays and a2["n"] / sdays >= MIN_SPD: s_pass[(b, band, rs, filt, x)] = a2
    rep["search_cells_scored"] = scored; rep["search_passes"] = len(s_pass)
    v_res, v_p, v_ev = {}, {}, {}
    for k in s_pass:
        items = vg.get(k[:4], [])
        if len(items) < MIN_N: continue
        agg, _ = D.score_group(items, k[4])
        if c8_pass(agg[0.02], events_of(items)): v_res[k] = agg[0.02]; v_p[k] = D.pval(agg[0.02]["day_z"]); v_ev[k] = events_of(items)
    keep = D.bh(v_p, m_total, ALPHA)
    rep["validate_bar_passes"] = len(v_res); rep["survivors"] = [{"cell": k, "pf_2c": v_res[k]["pf"], "n": v_res[k]["n"], "days": v_res[k]["trade_days"], "events": v_ev[k]} for k in sorted(keep, key=str)]
    return rep
def header(rep): return "m_total %d | cells selected %d | primary haircut %s | upper bound, not fill-checked" % (rep["m_total"], rep["cells_selected"], rep["primary_haircut"])
def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    import ethlate1_load as L
    data, cnt = L.load(a[0], a[1])
    rep = run(data)
    print(header(rep)); print("loader counts:", dict(cnt))
    for k in ("search_markets", "validate_markets", "search_cells_scored", "search_passes", "validate_bar_passes"): print(k, rep[k])
    print("survivors:", rep["survivors"] or "none")
if __name__ == "__main__": main()
