"""Reproduction check for gen4_rescore.py: V2's GEN4 code on ALL quote-recorder windows with the recorder's own results (as the ledger ran),
to confirm the old ledger figures are reproduced before they are compared with the book lines. Same test, nothing new scored.
usage: python3 -I gen4_rescore_check.py <v2_kalshi_scalper_dir> <quotes_root> <results_root> <out_json>
"""
import sys, os, glob, json, gzip, csv, re
from collections import defaultdict
from datetime import datetime, timezone
import numpy as np
V2, QROOT, RROOT, OUT = sys.argv[1:5]
sys.path.insert(0, os.path.join(V2, "src"))
from scalper import gen4 as G
T_FROM = datetime(2026, 10, 30, tzinfo=timezone.utc).timestamp()
T_TO = datetime(2026, 11, 4, 19, 36, tzinfo=timezone.utc).timestamp()


def rows_gz(f):
    with gzip.open(f, "rt") as fh:
        return list(csv.DictReader(fh))


W, X = {}, {}
for f in sorted(glob.glob(os.path.join(QROOT, "quotes", "*", "*", "quotes.csv.gz"))):
    folder = os.path.dirname(f); rel = os.path.relpath(folder, QROOT)
    rf = os.path.join(RROOT, rel, "results.csv.gz")
    if not os.path.exists(rf):
        continue
    resd = {}
    for r in rows_gz(rf):
        if r["ticker"].startswith("KXBTC15M-") and r["result"] in ("yes", "no") and r["ticker"] not in W:
            C = datetime.strptime(r["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            if T_FROM <= C <= T_TO:
                resd[r["ticker"]] = (C, r["result"])
    if not resd:
        continue
    sp = os.path.join(folder, "spot.csv.gz")
    if os.path.exists(sp):
        X.update(G.proxy(rows_gz(sp)))
    polls = defaultdict(list)
    for r in rows_gz(f):
        if r["ticker"] in resd:
            polls[r["ticker"]].append(r)
    for tk, (C, result) in resd.items():
        ps = sorted(polls[tk], key=lambda p: int(p["t_recv_ms"]))
        if not ps:
            continue
        arr = []
        for p in ps:
            ok = p["status"] == "active" and p["yes_bid"] not in ("", None) and p["yes_ask"] not in ("", None)
            arr.append((int(p["t_recv_ms"]) / 1000.0, float(p["yes_bid"]) if ok else np.nan, float(p["yes_ask"]) if ok else np.nan, float(p["bid_size"] or 0), float(p["ask_size"] or 0)))
        a = np.array(arr, dtype=float)
        W[tk] = {"C": C, "K": float(ps[0]["strike"]), "result": result, "date": datetime.fromtimestamp(C, timezone.utc).strftime("%Y-%m-%d"),
                 "t": a[:, 0], "yb": a[:, 1], "ya": a[:, 2], "bs": a[:, 3], "as": a[:, 4]}
A, keys, dates = G.build("bitcoin", W, X)
old = {}
for line in open(os.path.join(V2, "workers", "FORWARD_LEDGER.md")):
    m = re.match(r"\| (GEN4_\w+) \| KXBTC15M \| \w+ \| [\d-]+ \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| ([\d.]+) \| ([\d.]+) \|", line)
    if m:
        old[m.group(1)] = (int(m.group(3)), float(m.group(6)), float(m.group(7)))
out = {"windows": len(W), "rows": {}}
dn, dp = [], []
for f in sorted(glob.glob(os.path.join(V2, "workers", "candidates", "GEN4_*.json"))):
    c = json.load(open(f)); idx = G.entries(A, c["params"]); s = G.stats(A, dates, idx, c["params"])
    o = old.get(c["id"])
    out["rows"][c["id"]] = {"ledger_n_pf1_pf10": o, "rerun_n_pf1_pf10": [s["n"], round(s["pf1_1.0"], 2), round(s["pf10_1.0"], 2)]}
    if o:
        dn.append(s["n"] - o[0]); dp.append(s["pf1_1.0"] - o[1])
out["n_diff_min_max"] = [int(min(dn)), int(max(dn))]; out["pf1_diff_min_max"] = [round(float(min(dp)), 3), round(float(max(dp)), 3)]
out["rows_matching_n_exactly"] = int(sum(1 for d in dn if d == 0)); out["rows_pf1_within_0.02"] = int(sum(1 for d in dp if abs(d) <= 0.02))
json.dump(out, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "rows"})); print({k: out["rows"][k] for k in ("GEN4_B42", "GEN4_B06", "GEN4_B11", "GEN4_REF_FAV150")})
