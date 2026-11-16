#!/usr/bin/env python3
"""OPENGAP1 Databento fetch (Testing Desk, Nov 16, 2026). THREE requests, GET-style reads of historical data through the session's authenticated proxy (no key in this file),
written to a scratch directory that must NOT be inside a git repository; nothing is printed except sizes. The cost of each request is asked first (metadata.get_cost, free)
and the run stops if the total exceeds LIMIT dollars.
Usage: opengap1_fetch.py <scratch dir> <start YYYY-MM-DD> <end YYYY-MM-DD (exclusive)> [--cost-only]
Head's written go (2026-11-16 13:27Z): "GO on the cost: about $0.0003, the narrow windows only; never pull EQUS.SUMMARY statistics."
"""
import os, ssl, subprocess, sys, urllib.parse, urllib.request

HOST = "https://hist.databento.com/v0/"
FIRST_START, LAST_END, MAX_DAYS = "2026-11-13", "2027-02-02", 10          # the first run (Nov 5 to 14, development) is done; a forward pull may start no earlier than the Friday before the first forward day (2026-11-13) and spans at most MAX_DAYS UTC days
LIMIT = 0.01                                      # dollars: far above the estimate (about 0.0003), far below the owner's allowance
REQUESTS = [("xnas_stat.csv", "XNAS.ITCH", "statistics", "QQQ,NVDA,AAPL"), ("arcx_stat.csv", "ARCX.PILLAR", "statistics", "SPY"), ("equs_1d.csv", "EQUS.SUMMARY", "ohlcv-1d", "SPY,QQQ,NVDA,AAPL")]


def params(dataset, schema, symbols, start, end):
    return {"dataset": dataset, "schema": schema, "symbols": symbols, "start": start, "end": end, "stype_in": "raw_symbol"}


def check_dates(start, end):
    import datetime
    d0, d1 = datetime.date.fromisoformat(start), datetime.date.fromisoformat(end)
    if not (FIRST_START <= start and end <= LAST_END and 0 < (d1 - d0).days <= MAX_DAYS): raise SystemExit("REFUSED: dates %s to %s outside %s to %s or longer than %d days" % (start, end, FIRST_START, LAST_END, MAX_DAYS))


def get(path, p):
    ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE") or None)
    with urllib.request.urlopen(HOST + path + "?" + urllib.parse.urlencode(p), timeout=120, context=ctx) as r: return r.read()


def main(outdir, start, end, cost_only=False):
    check_dates(start, end)
    near = os.path.abspath(outdir)
    while not os.path.isdir(near): near = os.path.dirname(near)          # the directory may not exist yet: ask git about its nearest existing parent
    top = subprocess.run(["git", "-C", near, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode == 0: raise SystemExit("REFUSED: the output directory is inside a git repository: %s" % top.stdout.strip())
    os.makedirs(outdir, exist_ok=True)
    total = 0.0
    for name, ds, schema, syms in REQUESTS:
        if ds == "EQUS.SUMMARY" and schema != "ohlcv-1d": raise SystemExit("REFUSED: only EQUS.SUMMARY ohlcv-1d is allowed")
        total += float(get("metadata.get_cost", params(ds, schema, syms, start, end)))
    print("estimated total cost $%.6f (limit $%.2f)" % (total, LIMIT))
    if total > LIMIT: raise SystemExit("REFUSED: over the limit")
    if cost_only: return
    for name, ds, schema, syms in REQUESTS:
        p = params(ds, schema, syms, start, end); p.update({"encoding": "csv", "pretty_px": "true", "pretty_ts": "true", "map_symbols": "true"})
        data = get("timeseries.get_range", p)
        with open(os.path.join(outdir, name), "wb") as fh: fh.write(data)
        print(name, len(data), "bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], "--cost-only" in sys.argv[4:])
