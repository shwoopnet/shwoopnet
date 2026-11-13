#!/usr/bin/env python3
"""Sums the per_window counts of a kxinx15m_quote_profile.py JSON over tickers dated in [from, to) (Eastern date in the ticker). Counts only; no run file is opened, the audited profile script is untouched.
usage: python3 -I quote_profile_range.py <profile.json> 2026-11-05 2026-11-13   (prints the range line; the full-run totals are printed too)"""
import sys, json, re
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
CATS = ("candles", "two_sided", "spread_1c", "spread_2c", "spread_3c", "spread_over3c", "cheap_20_30", "not_two_sided", "missing_quote", "off_cent")
def tdate(t):
    m = re.match(r"^[A-Z0-9]+-(\d{2})([A-Z]{3})(\d{2})", t); return (2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)))
def main(a):
    if len(a) != 3: print(__doc__); return 2
    j = json.load(open(a[0])); lo = tuple(map(int, a[1].split("-"))); hi = tuple(map(int, a[2].split("-")))
    pw = [p for p in j["per_window"] if lo <= tdate(p["ticker"]) < hi]; out = [p for p in j["per_window"] if not (lo <= tdate(p["ticker"]) < hi)]
    tot = {k: sum(p[k] for p in pw) for k in CATS}
    print("full run: windows %d, %s" % (j["windows"], ", ".join("%s %d" % (k, j["totals"][k]) for k in CATS)))
    print("range [%s, %s): windows %d (outside the range: %d), no candles %d, with a two-sided minute %d, with a cheap 20-30c minute %d" % (a[1], a[2], len(pw), len(out), sum(1 for p in pw if p["candles"] == 0), sum(1 for p in pw if p["two_sided"]), sum(1 for p in pw if p["cheap_20_30"])))
    print("range minutes: " + ", ".join("%s %d" % (k, tot[k]) for k in CATS)); return 0
if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
