#!/usr/bin/env python3
"""LADHOUR1 driver, BUILD 2: runs the 96 rules per series (384 in all) and prints one deterministic line per rule, prefixed by the series. BH is per series over m_carried + 384. Pure."""
import ladhour1_second as m, ethlate1_driver_second as d

def run(markets, candles, m_carried):
    mt = m.m_total(m_carried); out = ["header m_carried %d m_new %d m_total %d" % (m_carried, m.M_NEW, mt)]
    for s, (mk, cd) in m.split_by_series(markets, candles).items():
        for i, l in enumerate(d.run(mk, cd, mt)): out.append("%s %s" % (s, l))
    return out
