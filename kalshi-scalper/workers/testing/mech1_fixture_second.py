#!/usr/bin/env python3
"""Invented MECH1 record file (seeded, no real data): 40 signatures built from the vocabularies, with trades on dates of the two windows; header and trade lines in the section 12.0 layout. python3 mech1_fixture_second.py out.jsonl"""
import json, random, sys
import mech1_second as m
def build(registry_path=None):
    rnd = random.Random(20261117); L = []; seen = set(); pre = []
    if registry_path:
        ents = json.load(open(registry_path))["entries"]; sg = [e for e in ents if e.get("kind") == "signature"][0]; pre.append({f: sg[f] for f in ("market", "signal", "clock", "entry", "exit", "side")})
        for e in [e for e in ents if e.get("kind") == "pattern"][:2]:
            c = {}
            for f, vocab in m.FIELDS:
                v = e[f]; c[f] = vocab[0] if v == "*" else (v[0] if isinstance(v, list) else v)
            pre.append(c)
    sd = ["2026-09-%02d" % d for d in range(2, 31)] + ["2026-10-%02d" % d for d in range(1, 7)]; vd = ["2026-10-%02d" % d for d in range(7, 27)]
    while len(seen) < 40:
        if pre: c = pre.pop(0)
        else: c = {"market": rnd.choice(("15m_noncrypto", "15m_crypto", "index_perp", "metal_perp", "crypto_perp", "stock_perp", "hourly_ladder")), "signal": rnd.choice(m.SIGNAL[:12]), "clock": rnd.choice(m.CLOCK), "entry": rnd.choice(m.ENTRY), "exit": rnd.choice(m.EXIT[:5]), "side": rnd.choice(m.SIDE)}
        k = tuple(c.values())
        if k in seen: continue
        seen.add(k); sid = m.sig_id(c); binary = c["market"].startswith("15m") or c["market"] == "hourly_ladder"
        h = {"sig": c, "settings": 1, "primary": rnd.choice(("1c", "2c")) if binary else "bp", "units": "usd10" if binary else "bp", "tail": "abs", "threshold_value": round(rnd.uniform(0.5, 3), 6), "calendar_days_search": 35, "calendar_days_validate": 20, "search_from": "2026-09-02", "search_to": "2026-10-06", "validate_from": "2026-10-07", "validate_to": "2026-10-26", "half1_to": "2026-09-28", "half2_from": "2026-09-29", "data": "perps_candles" if not binary else "R6"}
        if rnd.random() < 0.1: h["threshold_value"] = None
        L.append(json.dumps(h)); edge = rnd.choice((-0.0004, 0.0, 0.0006, 0.0015)); ntr = rnd.choice((30, 80, 130, 220, 400))
        for i in range(ntr):
            w = "search" if rnd.random() < 0.6 else "validate"; day = rnd.choice(sd if w == "search" else vd)
            if binary:
                n1 = round(rnd.gauss(edge * 400, 3.0), 3); n2 = round(n1 - 0.1, 3); g = round(n1 + 0.3 + rnd.random() * 0.1, 9); net = n1 if h["primary"] == "1c" else n2
                t = {"sig_id": sid, "window": w, "day": day, "entry_end": 1790000000 + i * 61 + rnd.randrange(60), "market_id": "KX%d" % rnd.randrange(5), "traded": rnd.random() < 0.9, "gross": g, "cost": round(g - net, 9), "net": net, "net_1c": n1, "net_2c": n2}
            else:
                net = round(rnd.gauss(edge * 1e4 / 6, 30), 6); g = round(net + 24.0, 9)
                t = {"sig_id": sid, "window": w, "day": day, "entry_end": 1790000000 + i * 61 + rnd.randrange(60), "market_id": rnd.choice(("KXA", "KXB", "KXC")), "traded": rnd.random() < 0.9, "gross": g, "cost": round(g - net, 9), "net": net, "net_1c": None, "net_2c": None}
            L.append(json.dumps(t))
    return L
if __name__ == "__main__": open(sys.argv[1], "w").write("\n".join(build(sys.argv[2] if len(sys.argv) > 2 else None)) + "\n")
