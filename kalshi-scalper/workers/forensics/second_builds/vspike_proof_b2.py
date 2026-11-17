#!/usr/bin/env python3
"""V3 VSPIKE PICKS PROOF JOB (Forensics desk, Nov 17, 2026; the Head's order, for Auditor B). Runs the three V3 vspike picks SH3_08 (KXETH15M 540 band 14 favourite vspike:mid H), SH3_11 (same, exit T) and SH3_17 (KXHYPE15M 420 band 1 cheap vspike:low M60) on the ARCHIVE extract only, SEARCH and VALIDATE halves (the per-series LAST_SEARCH constants), with Desk A's committed cuts file SHADOW_VSPIKE_CUTS_V1_SHAPE.json (sha256 bac4e22e...) instead of my own terciles; never the held-out window; the batch B search print was not looked at. Also prints whether my own SEARCH terciles equal their cuts for the two (series, bucket) pairs. Per pick and phase: n scored at 1c and PF at 1c (and 2c).
usage: python3 -I vspike_proof_b2.py <archive.sqlite> <cuts shape json>"""
import sys, os, json, hashlib, calendar, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_rank_b2 as P
import engb4xbtc_b2 as E
import engb_b2_blind as G
import heldout_bc_b2 as H
PICKS = {"SH3_08": ("KXETH15M", 540, 14, "favourite", "mid", "H"), "SH3_11": ("KXETH15M", 540, 14, "favourite", "mid", "T"), "SH3_17": ("KXHYPE15M", 420, 1, "cheap", "low", "M60")}
def run(m_list, rule, cu):
    ser, B, band, sr, cls, ex = rule; x1, x2 = [], []
    for m in m_list:
        en = E.entries(m, B, sr)
        if en is None: continue
        side, ca = en; e = m.close - B; v = G.vspike(m, e)
        if v is None or cu is None: continue
        if ca // 5 != band or G.tclass(v, cu) != cls: continue
        a = H.nets_for(m, B, side, 0.01, ex); b = H.nets_for(m, B, side, 0.02, ex)
        if a is not None: x1.append(a)
        if b is not None: x2.append(b)
    return len(x1), (E.pfv(x1) if x1 else None), (E.pfv(x2) if x2 else None)
def main(a):
    sha = hashlib.sha256(open(a[1], "rb").read()).hexdigest(); print("cuts file sha256", sha); cuts = json.load(open(a[1]))
    by = H.load_markets(a[0]); ls = {s: calendar.timegm(tuple(int(x) for x in P.LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in by if s in P.LAST_SEARCH}; mine = H.Cuts(by, ls)
    for pid, rule in PICKS.items():
        ser, B = rule[0], rule[1]; theirs = cuts[ser][str(B)]; my = mine.get("vspike", ser, B)
        same = my is not None and theirs[0] is not None and abs(my[0] - theirs[0]) < 1e-9 and abs(my[1] - theirs[1]) < 1e-9
        for ph in ("SEARCH", "VALIDATE"):
            ml = [m for m in by[ser] if (m.close < ls[ser]) == (ph == "SEARCH")]; n, p1, p2 = run(ml, rule, theirs)
            print("%s %s %s phase %s | their cuts %s: n %d PF1c %s PF2c %s | my SEARCH terciles equal their cuts: %s" % (pid, ser, rule[1:], ph, theirs, n, "%.12f" % p1 if p1 is not None else "-", "%.12f" % p2 if p2 is not None else "-", same))
if __name__ == "__main__": main(sys.argv[1:])
