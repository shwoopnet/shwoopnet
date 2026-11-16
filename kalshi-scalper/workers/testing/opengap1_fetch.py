#!/usr/bin/env python3
"""OPENGAP1 Databento fetch (Testing Desk, Nov 16, 2026). THREE requests, GET-style reads of historical data through the session's authenticated proxy (no key in this file),
written to a scratch directory that must NOT be inside a git repository; nothing is printed except sizes. The cost of each request is asked first (metadata.get_cost, free)
and the run stops if the total exceeds LIMIT dollars.
Usage: opengap1_fetch.py <scratch dir> [--cost-only]
Head's written go (2026-11-16 13:27Z): "GO on the cost: about $0.0003, the narrow windows only; never pull EQUS.SUMMARY statistics."
"""
import os, ssl, subprocess, sys, urllib.parse, urllib.request

HOST = "https://hist.databento.com/v0/"
START, END = "2026-11-05", "2026-11-14"          # UTC days: trading days Nov 5, 6, 9, 10, 11, 12, 13 (Nov 5 only for the previous close of Nov 6)
LIMIT = 0.01                                      # dollars: far above the estimate (about 0.0003), far below the owner's allowance
REQUESTS = [("xnas_stat.csv", "XNAS.ITCH", "statistics", "QQQ,NVDA,AAPL"), ("arcx_stat.csv", "ARCX.PILLAR", "statistics", "SPY"), ("equs_1d.csv", "EQUS.SUMMARY", "ohlcv-1d", "SPY,QQQ,NVDA,AAPL")]


def params(dataset, schema, symbols):
    return {"dataset": dataset, "schema": schema, "symbols": symbols, "start": START, "end": END, "stype_in": "raw_symbol"}


def get(path, p):
    ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE") or None)
    with urllib.request.urlopen(HOST + path + "?" + urllib.parse.urlencode(p), timeout=120, context=ctx) as r: return r.read()


def main(outdir, cost_only=False):
    near = os.path.abspath(outdir)
    while not os.path.isdir(near): near = os.path.dirname(near)          # the directory may not exist yet: ask git about its nearest existing parent
    top = subprocess.run(["git", "-C", near, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode == 0: raise SystemExit("REFUSED: the output directory is inside a git repository: %s" % top.stdout.strip())
    os.makedirs(outdir, exist_ok=True)
    total = 0.0
    for name, ds, schema, syms in REQUESTS:
        if ds == "EQUS.SUMMARY" and schema != "ohlcv-1d": raise SystemExit("REFUSED: only EQUS.SUMMARY ohlcv-1d is allowed")
        total += float(get("metadata.get_cost", params(ds, schema, syms)))
    print("estimated total cost $%.6f (limit $%.2f)" % (total, LIMIT))
    if total > LIMIT: raise SystemExit("REFUSED: over the limit")
    if cost_only: return
    for name, ds, schema, syms in REQUESTS:
        p = params(ds, schema, syms); p.update({"encoding": "csv", "pretty_px": "true", "pretty_ts": "true", "map_symbols": "true"})
        data = get("timeseries.get_range", p)
        with open(os.path.join(outdir, name), "wb") as fh: fh.write(data)
        print(name, len(data), "bytes")


if __name__ == "__main__":
    main(sys.argv[1], "--cost-only" in sys.argv[2:])
