#!/usr/bin/env python3
"""Driver for lanes16_second.py: 144 rules x columns (single: TT, ME2, ME5, MM2, MM5; pairs: TT, ME2, ME5). One JSON line per rule with every column, then counts first. Pure: run(data, funding, lmax, m_carried) -> list of lines."""
import json, math
import lanes16_second as m, pool1_second as P, engine1_perps_second as p

COLS = (("TT", 0), ("ME2", 2), ("ME5", 5), ("MM2", 2), ("MM5", 5))
PCOLS = (("TT", 0), ("ME2", 2), ("ME5", 5))


def colstats(lo, hi, nd):
    ok, info = P.gate(lo[0], hi[0], nd); b = P.booked(lo[0]); v = [t["net"] for t in b]
    return ok, {"n": len(b), "trades": len(lo[0]), "win_rate": (sum(1 for x in v if x > 0) / len(v)) if v else None, "pf_lo": info.get("pf_lo"), "pf_hi": info.get("pf_hi"), "mean_bps": (sum(v) / len(v) * 1e4) if v else None, "per_day": info.get("per_day"), "share": info.get("share"), "net_hi": info.get("net_hi"), "counts": lo[1], "unfilled_tt_mean_bps": (sum(lo[2]) / len(lo[2]) * 1e4) if lo[2] else None, "unfilled_tt_n": len(lo[2]), "p": m.day_p(b)}, b


def run(data, funding, lmax, m_carried, baskets=None):
    names = P.pool_names(data, funding); data = {n: data[n] for n in names}; days = set(P.trading_dates(data)); nd = len(days)
    baskets, dropped = m.kept_baskets(data, funding, baskets); ticks = {n: m.tick_of(data[n]) for n in names}; sig = {}
    out = [json.dumps({"kind": "counts", "m_carried": m_carried, "m_new": m.M_NEW, "m_total": m_carried + m.M_NEW, "trading_days": nd, "baskets": {b: list(v) for b, v in baskets.items()}, "dropped_baskets": dropped, "ticks": ticks}, sort_keys=True)]
    rules = []
    for L in (30, 60):
        for c in (1, 2):
            for mode in ("follow", "revert"):
                ev = [e for b in sorted(baskets) for e in m.rs_events(data, baskets[b], L, c, mode, sig, days)]
                rules.append(("rs", "rs_L%d_c%d_%s" % (L, c, mode), ev))
    for W in (120, 240):
        for z in (2, 3):
            ev = [e for b in sorted(baskets) for e in m.pair_events(data, baskets[b], W, z, days)]
            rules.append(("pair", "pair_W%d_z%d" % (W, z), ev))
    res = {}
    for kind, sname, ev in rules:
        for ex in m.EXITS:
            name = "%s_k%d_%d_T%d" % (sname, *ex); line = {"rule": name, "events": len(ev), "cols": {}}; passes = {}
            fn = m.single_trades if kind == "rs" else m.pair_trades
            for col, N in (COLS if kind == "rs" else PCOLS):
                ctype = col[:2]; lo = fn(data, funding, ev, ex, m.HS[0], "TT" if ctype == "TT" else ctype, N, ticks); hi = fn(data, funding, ev, ex, m.HS[1], "TT" if ctype == "TT" else ctype, N, ticks)
                ok, st, b = colstats(lo, hi, nd); st["gate"] = ok; st["candidate_blocked"] = bool(ok and any(n not in lmax for tt in b for (n, _w) in tt["legs"])); st["trades"] = len(lo[0]); st["entered_hi"] = len(hi[0]); st["margin"] = m.margin(b, lmax) if b else {}; st["interest_pct_of_margin"] = m.interest(b); line["cols"][col] = st; passes[col] = ok
            line["tt_pass"] = passes["TT"]; line["kt"], line["ks"], line["T"] = ex; line["signal"] = sname; line["maker_only"] = (not passes["TT"]) and any(v for k, v in passes.items() if k != "TT"); res[name] = line
    pv = {k: v["cols"]["TT"]["p"] for k, v in res.items() if v["tt_pass"]}; surv = p.bh(pv, m_carried + m.M_NEW)
    for k in sorted(res): res[k]["bh_survivor"] = k in surv; out.append(json.dumps(res[k], sort_keys=True, default=str))
    out.append(json.dumps({"kind": "last", "rules": len(res), "tt_passes": sum(1 for v in res.values() if v["tt_pass"]), "maker_only": sum(1 for v in res.values() if v["maker_only"]), "bh_survivors": len(surv)}))
    return out
