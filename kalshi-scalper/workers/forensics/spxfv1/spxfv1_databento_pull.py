#!/usr/bin/env python3
"""SPXFV1 build 2: the Databento pull for the futures file (Forensics desk, Nov 13, 2026; the Head of R&D's order of 16:57Z). Research only.
The SAME query the Testing Desk used: dataset GLBX.MDP3, symbol ES.c.0 (continuous), schema ohlcv-1m, 14:30Z to 21:00Z on Nov 5, 6, 9, 10, 11 and 12, 2026 (start inclusive, end exclusive).
Order of events, and nothing else: (1) get_cost for every day (a metadata call that costs nothing), the SUM printed; (2) if the sum is over the cap (default 0.25 US dollars) the run STOPS before any data is requested;
(3) otherwise one get_range per day, appended to ONE csv in a scratch path outside the git working tree; (4) the spend (the get_cost sum, as the vendor quotes it) is printed for the report to Main.
No API key is handled here: hist.databento.com is reached through the environment's proxy, which supplies the credential; this file sends no Authorization header and reads no secret.
Databento data is never committed: the output path must lie outside the git working tree, and the file is read only by spxfv1_rows_builder.py futures.
usage: python3 -I spxfv1_databento_pull.py cost                              (step 1 only: prints the per-day costs and their sum; spends nothing)
       python3 -I spxfv1_databento_pull.py pull --out <scratch csv> [--cap 0.25]"""
import sys, os, json, urllib.request, urllib.parse

HOST = "https://hist.databento.com/v0"
DATASET, SYMBOL, SCHEMA, STYPE = "GLBX.MDP3", "ES.c.0", "ohlcv-1m", "continuous"
DAYS = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12"]
START_T, END_T = "14:30:00", "21:00:00"
CAP = 0.25
REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))


class Stop(Exception):
    pass


def params(day):
    return {"dataset": DATASET, "symbols": SYMBOL, "schema": SCHEMA, "stype_in": STYPE, "start": "%sT%sZ" % (day, START_T), "end": "%sT%sZ" % (day, END_T)}


def http(method, path, q):
    """One request to the vendor host through the environment's proxy; no Authorization header (the proxy supplies the credential)."""
    if method == "GET": req = urllib.request.Request(HOST + path + "?" + urllib.parse.urlencode(q), method="GET", headers={"User-Agent": "research-client"})
    else: req = urllib.request.Request(HOST + path, data=urllib.parse.urlencode(q).encode(), method="POST", headers={"User-Agent": "research-client"})
    with urllib.request.urlopen(req, timeout=120) as r: return r.read()


def costs(fetch=http):
    out = []
    for d in DAYS:
        body = fetch("GET", "/metadata.get_cost", params(d))
        try: out.append((d, float(json.loads(body))))
        except Exception: raise Stop("get_cost for %s returned an answer that is not a number: %r" % (d, body[:80]))
    return out


def refuse_in_repo(path):
    r = os.path.realpath(path)
    if r == REPO or r.startswith(REPO + os.sep): raise Stop("REFUSED: %s is inside the git working tree (scratch only)" % path)


def pull(out, cap=CAP, fetch=http):
    refuse_in_repo(out)
    if os.path.exists(out): raise Stop("%s exists" % out)
    cs = costs(fetch); total = sum(c for _, c in cs)
    print("get_cost per day: %s | sum %.6f USD | cap %.2f USD" % (", ".join("%s %.6f" % x for x in cs), total, cap))
    if total > cap + 1e-12: raise Stop("ABORTED before any data request: the quoted cost %.6f is over the %.2f cap" % (total, cap))
    first = True
    with open(out, "wb") as f:
        for d in DAYS:
            q = dict(params(d), encoding="csv", pretty_px="true", pretty_ts="false", map_symbols="true", stype_out="instrument_id")
            body = fetch("POST", "/timeseries.get_range", q)
            lines = body.split(b"\n")
            if not first and lines: lines = lines[1:]                          # one header only
            first = False
            f.write(b"\n".join(l for l in lines if l.strip()) + b"\n")
    print("pulled %d day(s) to %s; spend as quoted by the vendor: %.6f USD (report to Main)" % (len(DAYS), out, total)); return total


def main(argv):
    if not argv or argv[0] not in ("cost", "pull"): print(__doc__); return 2
    try:
        if argv[0] == "cost":
            cs = costs(); print("get_cost per day: %s | sum %.6f USD" % (", ".join("%s %.6f" % x for x in cs), sum(c for _, c in cs))); return 0
        if "--out" not in argv: raise Stop("needs --out <scratch csv>")
        cap = float(argv[argv.index("--cap") + 1]) if "--cap" in argv else CAP
        pull(argv[argv.index("--out") + 1], cap)
    except Stop as e:
        print(str(e)); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
