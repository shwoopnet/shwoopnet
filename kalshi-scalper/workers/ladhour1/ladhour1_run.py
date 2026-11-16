#!/usr/bin/env python3
"""LADHOUR1 adapter (Desk B, Nov 16 2026; DRAFT, unrun, unsigned). NO new scoring code: it calls Desk A's cleared engine files for the 96 cell keys of each of KXINXU, KXNASDAQ100U, KXWTIH, KXGOLDH (specs/LADHOUR1.spec.json).
REFUSES unless every engine file's sha256 equals the pin below, and unless engine1_split has a dated constant for each series that has data. C8 gate as in ETHLATE1 (PF 1.3 at 2c primary, both 2c halves 1.0 or more, n >= 100, >= 10 trade days,
>= 3 signals a day in SEARCH, >= 40 events = distinct closes of SCORED trades). BH PER SERIES (each series is read once on its own date) over the one m_total (m_carried + 384) with the 2c day-clustered p. Expected figures: EXPECTED_ladhour1_nov16.md.
Usage: python3 ladhour1_run.py <quote-data checkout> KXINXU=<run folder> KXNASDAQ100U=<run folder> KXWTIH=<run folder> KXGOLDH=<run folder>"""
import os, sys, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(HERE, "..", "desk_a_verify")
PINS = {"engine1_enum": "e42ee1a45f67b76e8560cd9cbefac352fce9a765c8300bc04d5ce05a27e4d5a7", "engine1_driver": "1281ce0a1dc0bce7875bbafc4774358f557e45d0897b8099f5615c33cf12640b",
        "engine1_split": "00a94c6ef569261ec4f649f596075d85e2b407c43a2bbe9b0a593f75743e07fd", "engine1_core": "53317e4b56a8328fb616d460d5cb4597af13a2b9020d73aefaa37717439694bf"}
M_TOTAL = None                        # m_carried + 384, written when the spec is frozen (the Head and Auditor B fix m_carried that day); run() refuses while None
SERIES = ("KXINXU", "KXNASDAQ100U", "KXWTIH", "KXGOLDH")
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
def events_of(items, exit_, K, D):
    """Distinct hourly events (UTC close times) of the cell's SCORED trades only (Auditor B, Nov 16): an entry the engine drops for 'no mark' or 'too late' is in neither n nor events. Uses the pinned engine's own score() on the same core entries score_group builds; the drop reasons do not depend on the haircut, so 0.02 is used."""
    return len({m["close"] for m, ent in items if K.score(D.to_core(m, ent), exit_, 0.02, D.CONTRACTS)[0] is not None})
def c8_pass(a, events): return a["n"] >= MIN_N and a["pf"] >= PF_PRIMARY and a["half1"] >= HALF_MIN and a["half2"] >= HALF_MIN and a["trade_days"] >= MIN_DAYS and events >= MIN_EVENTS
def run(markets_by_series, m_total=None, engine_dir=ENGINE_DIR):
    m_total = M_TOTAL if m_total is None else m_total
    if m_total is None: raise SystemExit("REFUSED: m_total is not set (m_carried + 384, fixed by the Head and Auditor B)")
    assert len(CELLS) == 96, "the spec has 96 cells per series"
    K, N, S, D = import_engine(engine_dir)
    rep = {"m_total": m_total, "cells_selected": len(CELLS) * len(SERIES), "primary_haircut": "2c (C8)", "series": {}}
    s_pass, v_res, v_p, v_ev, scored = {}, {}, {}, {}, 0
    for ser in SERIES:
        mk = markets_by_series.get(ser) or []
        if not mk: rep["series"][ser] = {"markets": 0}; continue
        series = D.short(ser)
        if series not in S.LAST_SEARCH: raise SystemExit("REFUSED: engine1_split has no dated constant for %s (Desk A adds it before any read)" % series)
        sm = [m for m in mk if S.phase(series, m["close"]) == "search"]; vm = [m for m in mk if S.phase(series, m["close"]) == "validate"]
        cuts = {}
        for b in N.BUCKETS:
            sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
            cuts[b] = N.spread_cuts(sp) if sp else None
        sg, vg = D.groups(sm, cuts, None), D.groups(vm, cuts, None)
        sdays = D.search_days([m["close"] for m in sm]); rep["series"][ser] = {"markets": len(mk), "search_markets": len(sm), "validate_markets": len(vm)}
        for (b, band, rs, filt), items in sg.items():
            if len(items) < MIN_N: continue
            for x in EXITS:
                if (b, band, rs, filt, x) not in CELLS: continue
                agg, _ = D.score_group(items, x); scored += 1
                a2 = agg[0.02]
                if c8_pass(a2, events_of(items, x, K, D)) and sdays and a2["n"] / sdays >= MIN_SPD: s_pass[(ser, b, band, rs, filt, x)] = a2
        for k in [k for k in s_pass if k[0] == ser]:
            items = vg.get(k[1:5], [])
            if len(items) < MIN_N: continue
            agg, _ = D.score_group(items, k[5]); ev = events_of(items, k[5], K, D)
            if c8_pass(agg[0.02], ev): v_res[k] = agg[0.02]; v_p[k] = D.pval(agg[0.02]["day_z"]); v_ev[k] = ev
    keep = set()
    for ser in SERIES: keep |= D.bh({k: p for k, p in v_p.items() if k[0] == ser}, m_total, ALPHA)      # each series is read on its own date (spec release rule), so BH runs per series over the one m_total
    rep["search_cells_scored"] = scored; rep["search_passes"] = len(s_pass); rep["validate_bar_passes"] = len(v_res)
    rep["survivors"] = [{"series": k[0], "cell": k[1:], "pf_2c": v_res[k]["pf"], "n": v_res[k]["n"], "days": v_res[k]["trade_days"], "events": v_ev[k]} for k in sorted(keep, key=str)]
    return rep
def header(rep): return "m_total %d | cells selected %d | primary haircut %s | upper bound, not fill-checked" % (rep["m_total"], rep["cells_selected"], rep["primary_haircut"])
def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    import ladhour1_load as L
    data, cnt = L.load(a[0], dict(x.split("=", 1) for x in a[1:]))
    rep = run(data)
    print(header(rep)); print("loader counts:", dict(cnt))
    for ser, v in rep["series"].items(): print(ser, v)
    for k in ("search_cells_scored", "search_passes", "validate_bar_passes"): print(k, rep[k])
    print("survivors:", rep["survivors"] or "none")
if __name__ == "__main__": main()
