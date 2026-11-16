#!/usr/bin/env python3
"""OPENGAP2 (Testing Desk, Nov 16, 2026): the OPENGAP1 rule on KXUS500PERP and KXUSTECH100PERP against SPY and QQQ official opens. Research only: scratch files in, aggregates out.
Registration: OPENGAP2_REGISTRATION.md. No trade logic of its own: it imports opengap1f.py (checked, da2346e5) and sets its name map and window.
Usage: opengap2.py <perp dir with kalshi1m <date>.csv.gz files> <underlying.csv from opengap1_convert.py (SPY and QQQ rows)> [--fee X]
"""
import csv, hashlib, os, sys, tempfile
import opengap1f as f

UNDER = {"KXSPYPERP": "KXUS500PERP", "KXQQQPERP": "KXUSTECH100PERP"}          # the converter's SPY and QQQ rows become the two index perps
NAMES = {"KXUS500PERP": "US500", "KXUSTECH100PERP": "UST100"}
WINDOW = ("2026-11-06", "2026-11-13")
F_SHA = "da2346e5dac2fae42f1c060e8edc2e5eeae2035a6e6baa7f37d9c89e9932728d"


def remap(src, dst):
    n = 0
    with open(src, newline="") as fh, open(dst, "w", newline="") as out:
        rd = csv.DictReader(fh); w = csv.DictWriter(out, fieldnames=rd.fieldnames); w.writeheader()
        for r in rd:
            if r["perp"] in UNDER: r = dict(r, perp=UNDER[r["perp"]]); w.writerow(r); n += 1          # any other row (NVDA, AAPL) is dropped
    return n


def events(perp_dir, ucsv):
    saved = (f.PERPS, f.FWD_FROM, f.FWD_TO)
    f.PERPS, (f.FWD_FROM, f.FWD_TO) = NAMES, WINDOW
    try:
        tmp = os.path.join(tempfile.mkdtemp(), "u.csv"); remap(ucsv, tmp); return f.load(perp_dir, tmp)
    finally: f.PERPS, f.FWD_FROM, f.FWD_TO = saved


def main(perp_dir, ucsv, fees):
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "opengap1f.py")
    if hashlib.sha256(open(here, "rb").read()).hexdigest() != F_SHA: raise SystemExit("REFUSED: opengap1f.py is not the checked build")
    evs = events(perp_dir, ucsv); saved = f.PERPS; f.PERPS = NAMES
    try:
        n, per = f.triggered(evs)
        print("OPENGAP2 events", len(evs), "triggered events pooled", n, "per name", {NAMES[k]: v for k, v in sorted(per.items())})
        for fee in fees:
            for label, sel in [("pooled", evs)] + [(NAMES[k], [e for e in evs if e["name"] == k]) for k in NAMES]:
                sk = {}
                for e in sel: st = f.score_event(e, "abs", 0.0, fee)[0]; sk[st] = sk.get(st, 0) + 1
                print(f"{label} fee/side {fee}: events {len(sel)} outcomes {dict(sorted(sk.items()))}")
                lines = [(("rel", r), "(primary)") for r in f.REL] + [(("rel", r), "(stress, information only)") for r in f.STRESS] + [(("abs", h), "(information only)") for h in f.ABS]
                for (mode, x), tag in lines:
                    b = f.block(f.run(sel, mode, x, fee))
                    print(f"  haircut {mode} {x} {tag}: n {b['n']} wins {b['wins']} PF {b['pf']:.4f} half1 {b['h1']:.4f} half2 {b['h2']:.4f} dayz {b['z'] if b['z'] is None else round(b['z'], 4)}" + ("  no evidence at n = %d (under 100)" % b["n"] if b["n"] < 100 else ""))
    finally: f.PERPS = saved
    print("development read of Nov 6 to 13 only; the same SPY and QQQ prints as OPENGAP1, so the US 500 and SPY signals (and US Tech 100 and QQQ) are not independent; nothing can pass; upper bound, not fill-checked; one try")


if __name__ == "__main__":
    a = sys.argv[1:]; fees = list(f.FEES)
    while "--fee" in a: i = a.index("--fee"); fees.append(float(a[i + 1])); del a[i:i + 2]
    main(a[0], a[1], fees)
