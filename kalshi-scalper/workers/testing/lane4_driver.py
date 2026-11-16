#!/usr/bin/env python3
"""PERPSLANE4 driver (first build): one deterministic line per rule and fee. Pure."""
import math
import lane4_plugin as m

def fmt(x):
    if x is None: return "None"
    if isinstance(x, float) and math.isinf(x): return "inf"
    if isinstance(x, float) and math.isnan(x): return "nan"
    return "%.12g" % x if isinstance(x, float) else str(x)

def rid(r): return "_".join(str(x) for x in r)

def run(data, funding, under, m_carried=0):
    res, surv, nd = m.run(data, funding, under, m_carried)
    lines = ["header m_carried %d m_new %d m_total %d trading_days %d" % (m_carried, m.M_NEW, m_carried + m.M_NEW, nd)]
    for r in m.rules():
        o = res[r]; c = o["counts"]
        for key in ("net_taker", "net_maker"):
            s = o[key]
            lines.append("%s|%s | n %d days %d per_day %s | pf_lo %s pf_hi %s h1 %s h2 %s | z %s p %s | gate %s survivor %s | blocked %d no_mark %d unbooked %d boundary %d" % (
                rid(r), key, s["n"], s["days"], fmt(s["per_day"]), fmt(s["pf_lo"]), fmt(s["pf_hi"]), fmt(s["h1"]), fmt(s["h2"]), fmt(s["z"]), fmt(s["p"]), s["gate"], r in surv[key], c["blocked"], c["no_mark"], c["funding_not_booked"], c["boundary"]))
    return lines
