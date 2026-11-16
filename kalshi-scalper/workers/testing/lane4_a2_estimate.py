#!/usr/bin/env python3
"""PERPSLANE4 A2 Databento ESTIMATE (Testing Desk, Nov 16, 2026): asks metadata.get_cost (free) for EQUS.SUMMARY ohlcv-1d only, never get_range; prints the dollars. No data is fetched and nothing licensed is written.
Group 1: GLD, SPY, QQQ for 2026-09-09 to before 2026-11-14 (EQUS.SUMMARY ends at 2026-11-14T00:00Z; gold, US 500, US Tech 100 development). Group 2: the stock underlyings of the pool for 2026-11-04 to before 2026-11-14 (the Nov 16 session is not in the dataset yet: it comes with the weekly forward pull).
Usage: lane4_a2_estimate.py"""
import os, ssl, urllib.parse, urllib.request
import lane4_load as L
HOST = "https://hist.databento.com/v0/"
EXCEPT = {"BRKB": "BRK.B"}          # a perp name that is not simply the ticker
NO_UNDERLYING = ("SPCX",)          # not listed: no gap rule for it (counted)
def symbols():
    out, skipped = [], []
    for n in L.STOCKS:
        t = n[2:-4]
        if t in NO_UNDERLYING: skipped.append(n); continue
        out.append(EXCEPT.get(t, t))
    return sorted(set(out)), skipped
def cost(symbols, start, end):
    p = {"dataset": "EQUS.SUMMARY", "schema": "ohlcv-1d", "symbols": ",".join(symbols), "start": start, "end": end, "stype_in": "raw_symbol"}
    ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE") or None)
    with urllib.request.urlopen(HOST + "metadata.get_cost?" + urllib.parse.urlencode(p), timeout=120, context=ctx) as r: return float(r.read())
if __name__ == "__main__":
    syms, skipped = symbols(); c1 = cost(["GLD", "SPY", "QQQ"], "2026-09-09", "2026-11-14"); c2 = cost(syms, "2026-11-04", "2026-11-14")
    print("group 1 (GLD, SPY, QQQ) estimated cost $%.6f" % c1); print("group 2 (%d stock underlyings, %d perps without one) estimated cost $%.6f" % (len(syms), len(skipped), c2)); print("total estimated $%.6f (nothing was requested; get_cost is free)" % (c1 + c2))
