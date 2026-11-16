#!/usr/bin/env python3
"""SOCDRIFT driver, BUILD 2: runs the 600 cells and prints one deterministic line per cell. Header (m_carried, m_new, m_total) first, then the counts block, then the table. Pure."""
import socdrift_second as m
from nbaladder_driver_second import fmt

def run(rungs, candles, carried=6290660, m_new=m.N_CELLS, days_window=m.DAYS_WINDOW):
    cells, cnt, surv = m.search(rungs, candles, carried, m_new, days_window)
    lines = ["header m_carried %d m_new %d m_total %d days_window %s" % (carried, m_new, m.m_total(carried, m_new), fmt(days_window)), "counts " + repr(sorted(cnt.items())), "cells %d survivors %d" % (len(cells), len(surv))]
    for k in sorted(cells, key=lambda c: (c[0], c[1], c[2], c[3], c[4])):
        s = cells[k]
        lines.append("D%dh|%s|band%.2f|%s|%s | n %d games %d days %d | pf1 %s h1 %s h2 %s pf2 %s | net1 %s weekly5 %s | z %s p %s | marked_n %d marked_pf %s | pass %s" % (
            k[0], k[1], k[2], k[3], k[4], s["n"], s["games"], s["days"], fmt(s["pf1"]), fmt(s["h1"]), fmt(s["h2"]), fmt(s["pf2"]), fmt(s["net1"]), fmt(s["weekly5"]), fmt(s["z"]), fmt(s["p"]), s["marked_n"], fmt(s["marked_pf"]), k in surv))
    return lines
