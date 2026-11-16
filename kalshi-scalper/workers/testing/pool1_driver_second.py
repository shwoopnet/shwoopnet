#!/usr/bin/env python3
"""POOL1 driver, BUILD 2: runs the 122 rules on in-memory data and prints one deterministic summary line per rule (for the 1e-9 compare with Desk A's build). Pure; the fixture loader is separate."""
import math
import pool1_second as m, engine1_perps_second as p


def fmt(x):
    if x is None: return "None"
    if isinstance(x, float) and math.isinf(x): return "inf"
    if isinstance(x, float) and math.isnan(x): return "nan"
    return "%.12g" % x if isinstance(x, float) else str(x)


def signals(data, funding, names):
    out = []
    for c in m.GAP_CLASSES:
        for mode in ("follow", "fade"): out.append(("gap%d_%s" % (c, mode), m.gap_entries(data, c, mode, names)[0]))
    for kind in ("level", "change"):
        for mode in ("fade", "follow"): out.append(("fund%s_%s" % (kind, mode), m.rank_entries(data, funding, names, kind, mode)[0]))
    return out


def run(data, funding):
    names = m.pool_names(data, funding); data = {n: data[n] for n in names}; nd = len(m.trading_dates(data)); lines = ["pool %s trading_days %d" % (",".join(names), nd), "m 122 + carried 102184 = 102306"]
    for sname, entries in signals(data, funding, names):
        for ex in m.EXITS:
            lo = m.rule_trades(data, funding, entries, ex, m.HS[0]); hi = m.rule_trades(data, funding, entries, ex, m.HS[1]); ok, info = m.gate(lo[0], hi[0], nd)
            lines.append(fmt_rule("%s_k%d_%d_T%d" % (sname, *ex), lo, hi, ok, info))
    for share in ("A", "B"):
        lo = m.carry_trades(data, funding, names, share, m.HS[0]); hi = m.carry_trades(data, funding, names, share, m.HS[1]); ok, info = m.gate(lo[0], hi[0], nd)
        lines.append(fmt_rule("carry%s" % share, lo, hi, ok, info))
    return lines


def fmt_rule(name, lo, hi, ok, info):
    tl = m.booked(lo[0]); th = m.booked(hi[0])
    return "%s | trades_lo %d booked_lo %d | trades_hi %d booked_hi %d | net_lo %s net_hi %s | pf_lo %s pf_hi %s | gate %s | counts %s" % (
        name, len(lo[0]), len(tl), len(hi[0]), len(th), fmt(sum(t["net"] for t in tl)), fmt(sum(t["net"] for t in th)), fmt(info.get("pf_lo")), fmt(info.get("pf_hi")), ok, ",".join("%s=%d" % kv for kv in sorted(lo[1].items())))


if __name__ == "__main__":
    print("library module; see the test")
