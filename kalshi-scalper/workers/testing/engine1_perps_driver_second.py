#!/usr/bin/env python3
"""ENGINE1 perps_grid driver, BUILD 2 (Testing Desk, Nov 16, 2026): reads a FAMILY SPEC (ENGINE_FAMILY_SPEC_FORMAT.md, kind perps_grid) and runs SEARCH, VALIDATE and
Benjamini-Hochberg with my own scorer (engine1_perps_second.py). Independent of Desk A's driver: written from the spec format and the amendment text only. Pure functions; the loader is separate.
Hand case: ENGINE1_PERPS_DRIVER_SECOND_HAND_CASE.md (committed first). Test: test_engine1_perps_driver_second.py (invented series only).
"""
import json, math, sys
import engine1_perps_second as p

OPTIONS = {"none": ["none"], "mom1": ["mom1_up", "mom1_down"], "mom3": ["mom3_up", "mom3_down"], "mom5": ["mom5_up", "mom5_down"], "mom15": ["mom15_up", "mom15_down"],
           "spread": ["spread_low", "spread_mid", "spread_high"], "tod": ["tod_pre", "tod_open", "tod_mid", "tod_close", "tod_post"], "orb": ["orb_up", "orb_down"], "sess": ["sess_high", "sess_low"]}


def rules(spec):
    g = spec["grid"]
    return [(f, s, e) for f in [o for k in g["filters"] for o in OPTIONS[k]] for s in g["side_rules"] for e in g["exits"]]


def day_p(trades, key):
    """the one-sided day-clustered p of the mean net of a rule's booked trades: the upper normal tail of the day-clustered z"""
    return p.p_upper(p.stats(trades, key)["z"] if trades else None)


def run_spec(spec, series_by_name, splits, funding_by_name=None, prior_m=0):
    """series_by_name {name: {end_ts: (bid, ask)}}; splits {name: validate_first_ts} (the first VALIDATE candle: SEARCH entries end before it); funding_by_name {name: {utc day: rate}} or None.
    -> dict with m, per-name counts, SEARCH passes, VALIDATE passes, BH survivors (each a dict), stress passes counted apart."""
    hs = spec["costs"]["haircuts_primary"]; hst = spec["costs"].get("haircuts_stress") or []
    gt = spec["gates"]; mn, md = gt["min_n"], gt["min_trade_days"]
    rl = rules(spec); m = prior_m + len(rl) * len(series_by_name)
    out = {"rules_per_name": len(rl), "names": sorted(series_by_name), "m": m, "search_passes": [], "validate_passes": [], "survivors": [], "stress_passes": 0, "search_n": {}}
    pvals = {}
    for name in sorted(series_by_name):
        s = series_by_name[name]; B = splits[name]; fund = None if funding_by_name is None else funding_by_name.get(name)
        cuts = p.spread_cuts(s, -math.inf, B)
        for (f, side, ex) in rl:
            def trades(h, lo, hi, boundary):
                return p.rule_trades(s, cuts, f, side, ex, h, entry_range=(lo, hi), boundary=boundary, funding=fund)[0]
            sa, sb = trades(hs[0], -math.inf, B, B), trades(hs[1], -math.inf, B, B)
            if not p.gate(sa, sb, "net_taker", mn, md): continue
            key = (name, f, side, ex); out["search_passes"].append(key); out["search_n"][key] = p.stats(sa, "net_taker")["n"]
            if len(hst) >= 2 and p.gate(trades(hst[0], -math.inf, B, B), trades(hst[1], -math.inf, B, B), "net_taker", mn, md): out["stress_passes"] += 1          # the stress pair (0.1% and 0.2%) cleared too: counted apart, never gating, never a candidate
            va, vb = trades(hs[0], B, math.inf, None), trades(hs[1], B, math.inf, None)
            if not p.gate(va, vb, "net_taker", mn, md): continue
            out["validate_passes"].append(key); pvals[key] = day_p(va, "net_taker")
            out.setdefault("_v", {})[key] = (p.stats(va, "net_taker"), p.stats(vb, "net_taker"))
    keep = p.bh(pvals, m)
    for key in sorted(keep):
        a, b = out["_v"][key]; out["survivors"].append({"rule": key, "pf_lo": a["pf"], "pf_hi": b["pf"], "n": a["n"], "days": a["trade_days"], "p": pvals[key]})
    out.pop("_v", None)
    return out


def report(out):
    return ["m %d (rules per name %d, names %s)" % (out["m"], out["rules_per_name"], ",".join(out["names"])), "SEARCH passes %d" % len(out["search_passes"]), "VALIDATE passes %d" % len(out["validate_passes"]),
            "BH survivors %d" % len(out["survivors"]), "of the SEARCH passes, also clear at the stress pair (apart, information) %d" % out["stress_passes"]] + [
            "survivor %s PF %.4f / %.4f n %d days %d p %.6f" % (" ".join(s["rule"]), s["pf_lo"], s["pf_hi"], s["n"], s["days"], s["p"]) for s in out["survivors"]]


if __name__ == "__main__":
    print(json.dumps({"note": "library module; see the test"}))
