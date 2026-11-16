#!/usr/bin/env python3
"""PERPSCALP2 real run, second build. python3 -B perpscalp2_second_run.py <perp-data checkout root> <m_carried> [allow file]. stdout = the print (its sha256 goes to stderr; commit it BEFORE reading the print)."""
import json, sys
import perpscalp2_second as m, perpscalp2_second_load as LD

def main(root, m_carried, allow=None):
    data, funding, counts = LD.load(root, allow); out = []
    valid = {n: sum(1 for t, c in s.items() if m.usable(c) and m.is_regular(t)) for n, s in data.items()}
    keep = sorted(n for n in data if valid[n] >= 600)
    out.append(json.dumps({"kind": "counts", "load": counts, "valid_regular_candles": valid, "left_out_under_600": sorted(set(data) - set(keep)), "m_carried": m_carried, "m_new": m.N_CELLS, "m_total": m_carried + m.N_CELLS}, sort_keys=True))
    data = {n: data[n] for n in keep}; funding = {n: funding[n] for n in keep}
    ticks = {n: m.tick_of(data[n]) for n in keep}; out.append(json.dumps({"kind": "ticks", "ticks": ticks}, sort_keys=True)); lm = {n: m.LMAX[n] for n in keep}
    pv = {}; rows = []
    for cell in m.cells():
        key = "%s|%s|%s|%s" % (cell[0][0], cell[1], cell[2], cell[3]); line = {"cell": key}; trs = {}
        for col in m.COLUMNS:
            tr, cnt = m.run_cell(data, funding, ticks, cell, col); trs[col] = tr; line[col] = {**m.stats(tr), **cnt}
        st = line["TT"]; line["pass"] = bool(m.meets(st) and m.num(line["TS"]["pf"]) >= 1.0)
        if st["n"] >= 48: pv[key] = m.p_upper(st["z"])
        line["margin"] = m.margin(trs["TT"], lm); line["adverse"] = {str(N): m.adverse(data, funding, ticks, cell, N) for N in (2, 5)}; rows.append(line)
    surv = m.bh(pv, m_carried + m.N_CELLS)
    for line in rows: line["bh_survivor"] = line["cell"] in surv; out.append(json.dumps(line, sort_keys=True, default=str))
    out.append(json.dumps({"kind": "last", "cells": len(rows), "passes": sum(1 for l in rows if l["pass"]), "bh_survivors": len(surv)}))
    return out

if __name__ == "__main__":
    import hashlib
    a = sys.argv[1:]; text = "\n".join(main(a[0], int(a[1]), a[2] if len(a) > 2 else None)) + "\n"; sys.stdout.write(text); sys.stderr.write("print sha256 %s\n" % hashlib.sha256(text.encode()).hexdigest())
