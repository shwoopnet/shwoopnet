#!/usr/bin/env python3
"""PERPSLANE4 A2 Databento fetch (Testing Desk, Nov 16, 2026). EXACTLY the two requests the Head approved (GO of 21:02Z): EQUS.SUMMARY ohlcv-1d, group 1 (GLD, SPY, QQQ, 2026-09-09 to before 2026-11-14) and group 2 (the stock underlyings, 2026-11-04 to before 2026-11-14), estimated $0.001389 in all.
Refuses a scratch directory inside a git repository, any other dataset or schema, and a total estimate above $0.01. Raw bars stay in scratch; only the unit-free ratio table (u_open / u_prev per perp name and ET date) is derived and shared.
Usage: lane4_a2_fetch.py <scratch dir>"""
import csv, datetime, io, json, os, subprocess, sys
import lane4_a2_estimate as E
import lane4_load as L
INDEX = {"GLD": "KXGOLDPERP", "SPY": "KXUS500PERP", "QQQ": "KXUSTECH100PERP"}
LIMIT = 0.01


def get(path, p):
    import ssl, urllib.parse, urllib.request
    ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE") or None)
    with urllib.request.urlopen(E.HOST + path + "?" + urllib.parse.urlencode(p), timeout=120, context=ctx) as r: return r.read()


def main(outdir):
    near = os.path.abspath(outdir)
    while not os.path.isdir(near): near = os.path.dirname(near)
    if subprocess.run(["git", "-C", near, "rev-parse", "--show-toplevel"], capture_output=True, text=True).returncode == 0: raise SystemExit("REFUSED: the scratch directory is inside a git repository")
    os.makedirs(outdir, exist_ok=True); syms, skipped = E.symbols()
    reqs = [("group1.csv", ["GLD", "SPY", "QQQ"], "2026-09-09", "2026-11-14"), ("group2.csv", syms, "2026-11-04", "2026-11-14")]; total = 0.0
    for name, s, a, b in reqs: total += E.cost(s, a, b)
    print("estimated total $%.6f" % total)
    if total > LIMIT: raise SystemExit("REFUSED: over the limit")
    for name, s, a, b in reqs:
        p = {"dataset": "EQUS.SUMMARY", "schema": "ohlcv-1d", "symbols": ",".join(s), "start": a, "end": b, "stype_in": "raw_symbol", "encoding": "csv", "pretty_px": "true", "pretty_ts": "true", "map_symbols": "true"}
        data = get("timeseries.get_range", p); open(os.path.join(outdir, name), "wb").write(data); print(name, len(data), "bytes")
    return total


def ratios(outdir):
    """-> {perp name: {ET date (local day number): u_open / u_prev}}: the bar's open over the previous trading day's close, per symbol; raw prices are not kept"""
    import engine1_perps_second as p
    rows = {}
    for f in ("group1.csv", "group2.csv"):
        for r in csv.DictReader(open(os.path.join(outdir, f))):
            sym = r.get("symbol") or r.get("raw_symbol"); d = r["ts_event"][:10]; rows.setdefault(sym, {})[d] = (float(r["open"]), float(r["close"]))
    out = {}
    for sym, days in rows.items():
        names = [n for n in (INDEX.get(sym), "KX%sPERP" % sym.replace(".", "")) if n and (n in L.INDEX3 or n in L.STOCKS)]          # SPY and QQQ serve the index perps and the stock perps of the same underlying
        ds = sorted(days)
        for name in names:
            for a, b in zip(ds, ds[1:]):
                y, m, dd = (int(x) for x in b.split("-")); Ldaynum = datetime.date(y, m, dd).toordinal() - datetime.date(1970, 1, 1).toordinal()
                out.setdefault(name, {})[Ldaynum] = days[b][0] / days[a][1]
    return out


if __name__ == "__main__":
    t = main(sys.argv[1]); r = ratios(sys.argv[1]); json.dump({n: {str(k): v for k, v in d.items()} for n, d in r.items()}, open(os.path.join(sys.argv[1], "under_ratio.json"), "w"), sort_keys=True)
    print("names with ratios %d, ratios %d" % (len(r), sum(len(v) for v in r.values()))); print("estimated cost logged: $%.6f" % t)
