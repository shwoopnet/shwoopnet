"""Re-score of V2's GEN4 forward ledger rows on R6 order books. Method: RESCORE_GEN4_RECORD1_NOTE.md (committed before this ran).

The same test: V2's own module (scalper.gen4: proxy, build, entries, stats, side_q, pnl_trade) is imported unmodified from a checkout of
claude/epic-ptolemy-0amjd9; only the rows fed to it change. No rule changed, no new try. No network, no account data.

usage: python3 -I gen4_rescore.py <v2_kalshi_scalper_dir> <r6_root> <quotes_root> <out_csv> <out_json>
"""
import sys, os, glob, json, gzip, csv, re
from collections import defaultdict
from datetime import datetime, timezone
import numpy as np
import pandas as pd

V2, R6, QROOT, OUT_CSV, OUT_JSON = sys.argv[1:6]
sys.path.insert(0, os.path.join(V2, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scalper import gen4 as G          # V2's evaluator, unmodified
import r6load as R

PRE = "KXBTC15M-"
T_FROM = datetime(2026, 10, 30, tzinfo=timezone.utc).timestamp()
T_TO = datetime(2026, 11, 4, 19, 30, tzinfo=timezone.utc).timestamp()        # the ledger's last scoring; inclusive
assert T_TO < datetime(2026, 11, 5, tzinfo=timezone.utc).timestamp()
SPAN_S = 152.0
EPS = 1e-9


def rows_gz(f):
    with gzip.open(f, "rt") as fh:
        return list(csv.DictReader(fh))


# R6 coverage: close time and Kalshi's result
parts = []
for d in R.run_dirs(R6):
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f):
        c = pd.read_csv(f, dtype={"ticker": str, "result": str})
        parts.append(c[c["ticker"].notna() & (c["series"] == "KXBTC15M")])
cov = pd.concat(parts, ignore_index=True)
cov = cov[cov["result"].isin(["yes", "no"])].drop_duplicates("ticker").set_index("ticker")
cov["C"] = (pd.to_datetime(cov["close_time"], utc=True) - R.EPOCH) / pd.Timedelta(seconds=1)
cov = cov[(cov["C"] >= T_FROM) & (cov["C"] <= T_TO)]
RES = {tk: (float(r.C), r.result) for tk, r in cov.iterrows()}

# quote recorder windows, parsed as V2's load_windows does (first folder holding a window wins); spot proxy through V2's proxy()
Wq, X = {}, {}
for f in sorted(glob.glob(os.path.join(QROOT, "quotes", "*", "*", "quotes.csv.gz"))):
    folder = os.path.dirname(f)
    sp = os.path.join(folder, "spot.csv.gz")
    if os.path.exists(sp):
        X.update(G.proxy(rows_gz(sp)))
    polls = defaultdict(list)
    for r in rows_gz(f):
        if r["ticker"] in RES and r["ticker"] not in Wq:
            polls[r["ticker"]].append(r)
    for tk, ps in polls.items():
        C, result = RES[tk]
        ps = sorted(ps, key=lambda p: int(p["t_recv_ms"]))
        arr = []
        for p in ps:
            ok = p["status"] == "active" and p["yes_bid"] not in ("", None) and p["yes_ask"] not in ("", None)
            yb = float(p["yes_bid"]) if ok else np.nan
            ya = float(p["yes_ask"]) if ok else np.nan
            arr.append((int(p["t_recv_ms"]) / 1000.0, yb, ya, float(p["bid_size"] or 0), float(p["ask_size"] or 0)))
        a = np.array(arr, dtype=float)
        Wq[tk] = {"C": C, "K": float(ps[0]["strike"]), "result": result, "date": datetime.fromtimestamp(C, timezone.utc).strftime("%Y-%m-%d"),
                  "t": a[:, 0], "yb": a[:, 1], "ya": a[:, 2], "bs": a[:, 3], "as": a[:, 4]}

# R6 book windows in the same shape
bparts = []
for d in R.run_dirs(R6):
    f = os.path.join(d, "book.csv.gz")
    if os.path.exists(f):
        b = pd.read_csv(f, usecols=["t_recv_ms", "ticker", "yes_bid_px_1", "no_bid_px_1", "yes_bid_sz_1", "no_bid_sz_1"])
        b = b[b["ticker"].isin(Wq)]
        if len(b):
            C = b["ticker"].map(lambda k: RES[k][0])
            left = C - b["t_recv_ms"] / 1000.0
            bparts.append(b[(left <= SPAN_S) & (left > 0)])
B = pd.concat(bparts, ignore_index=True).drop_duplicates(["ticker", "t_recv_ms"]).sort_values(["ticker", "t_recv_ms"])
Wb = {}
for tk, g in B.groupby("ticker", sort=False):
    yb = g["yes_bid_px_1"].to_numpy(float); nb = g["no_bid_px_1"].to_numpy(float)
    bs = np.nan_to_num(g["yes_bid_sz_1"].to_numpy(float)); as_ = np.nan_to_num(g["no_bid_sz_1"].to_numpy(float))
    yb = np.where(yb == yb, yb, 0.0); ya = np.where(nb == nb, 1 - nb, 1.0)
    q = Wq[tk]
    Wb[tk] = {"C": q["C"], "K": q["K"], "result": q["result"], "date": q["date"], "t": g["t_recv_ms"].to_numpy(float) / 1000.0, "yb": yb, "ya": ya, "bs": bs, "as": as_}
common = sorted(set(Wq) & set(Wb))
Wq = {k: Wq[k] for k in common}; Wb = {k: Wb[k] for k in common}
Aq, keys_q, dates_q = G.build("bitcoin", Wq, X)
Ab, keys_b, dates_b = G.build("bitcoin", Wb, X)


def summ(v1, v10, ndates=None):
    def pf(v):
        v = v[~np.isnan(v)]
        g, l = v[v > 0].sum(), -v[v < 0].sum()
        return round(float(g / l), 3) if l > 0 else (999.0 if g > 0 else 0.0)
    v = v1[~np.isnan(v1)]
    o = {"n": int(len(v)), "wins": int((v > 0).sum()), "pf1": pf(v1), "pf10": pf(v10), "mean1_c": round(float(v.mean() * 100), 2) if len(v) else None,
         "z": round(float(v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))), 2) if len(v) > 1 and v.std(ddof=1) > 0 else None}
    if ndates is not None:
        o["dates"] = ndates
    return o


def book_fill(tk, t_sig, s, limit, delay, e, win):
    """Fill on the R6 book at the first poll at least `delay` s after t_sig (delay 0: at or after), 1 and 10 contracts; limit None = pay whatever is there."""
    w = Wb[tk]; t = w["t"]; C = w["C"]
    j = int(np.searchsorted(t, t_sig + delay, side="left"))
    if j >= len(t) or t[j] >= C or t[j] - (t_sig + delay) > 10:
        return np.nan, np.nan
    fp, fsz, _, _ = G.side_q(w, j, s)
    if not (fp == fp and 0 < fp < 1 and fsz >= 1) or (limit is not None and fp > limit + EPS):
        return np.nan, np.nan
    eb = ebs = None
    if e:
        k = int(np.searchsorted(t, C - e, side="left"))
        if k < len(t) and t[k] <= C - e + 5 and t[k] > t[j]:
            _, _, eb, ebs = G.side_q(w, k, s)
    out = []
    for c in (1, 10):
        out.append(G.pnl_trade(win, fp, fsz, eb if (eb is not None and ebs >= 1) else None, ebs or 0, c, 1.0))
    return out[0], out[1]


# the ledger's old figures
old = {}
for line in open(os.path.join(V2, "workers", "FORWARD_LEDGER.md")):
    m = re.match(r"\| (GEN4_\w+) \| KXBTC15M \| \w+ \| [\d-]+ \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| ([\d.]+) \| ([\d.]+) \|", line)
    if m:
        old[m.group(1)] = {"days": int(m.group(2)), "n": int(m.group(3)), "wins": int(m.group(4)), "pf1": float(m.group(6)), "pf10": float(m.group(7))}

rows_out, full = [], {}
for f in sorted(glob.glob(os.path.join(V2, "workers", "candidates", "GEN4_*.json"))):
    cand = json.load(open(f)); cid = cand["id"]; sp = cand["params"]; e = sp["exit"]
    rec = {"id": cid, "family": cand.get("family", ""), "side": sp["side"], "exit": e, "conds": "; ".join("%s %s %.4g" % tuple(c) for c in sp["conds"]), "L0": old.get(cid)}
    iq = G.entries(Aq, sp); ib = G.entries(Ab, sp)
    rec["L1_quotes_common"] = summ(Aq["s%d_1_1.0" % e][iq], Aq["s%d_10_1.0" % e][iq], int(len(set(dates_q[Aq["w"][iq].astype(int)]))) if len(iq) else 0)
    rec["L2_book_same_poll"] = summ(Ab["s%d_1_1.0" % e][ib], Ab["s%d_10_1.0" % e][ib], int(len(set(dates_b[Ab["w"][ib].astype(int)]))) if len(ib) else 0)
    rec["L2_signals"] = int(len(ib)); rec["L1_signals"] = int(len(iq))
    for nm, dl in (("L3_book_2s_limit", 2.0), ("L3_book_6s_limit", 6.0)):
        v = [book_fill(keys_b[int(Ab["w"][i])], Ab["t"][i], int(Ab["side"][i]), float(Ab["ask"][i]), dl, e,
                       (Wb[keys_b[int(Ab["w"][i])]]["result"] == "yes") == (Ab["side"][i] == 0)) for i in ib]
        v = np.array(v, dtype=float).reshape(-1, 2)
        rec[nm] = summ(v[:, 0], v[:, 1]); rec[nm]["fill_share"] = round(float((~np.isnan(v[:, 0])).mean()), 3) if len(v) else None
    for nm, lim in (("L4_quote_signal_book_price", False), ("L4_quote_signal_book_price_limit", True)):
        v = [book_fill(keys_q[int(Aq["w"][i])], Aq["t"][i], int(Aq["side"][i]), float(Aq["ask"][i]) if lim else None, 0.0, e,
                       (Wq[keys_q[int(Aq["w"][i])]]["result"] == "yes") == (Aq["side"][i] == 0)) for i in iq]
        v = np.array(v, dtype=float).reshape(-1, 2)
        rec[nm] = summ(v[:, 0], v[:, 1]); rec[nm]["fill_share"] = round(float((~np.isnan(v[:, 0])).mean()), 3) if len(v) else None
    # how far the quote ask at the signal poll sat from the book ask at that instant (negative = the quote showed a cheaper ask)
    gaps = []
    for i in iq:
        tk = keys_q[int(Aq["w"][i])]; w = Wb[tk]; j = int(np.searchsorted(w["t"], Aq["t"][i], side="left"))
        if j < len(w["t"]) and w["t"][j] - Aq["t"][i] <= 10:
            a = G.side_q(w, j, int(Aq["side"][i]))[0]
            if a == a:
                gaps.append(float(Aq["ask"][i]) - a)
    rec["quote_ask_minus_book_ask_c"] = {"n": len(gaps), "mean": round(float(np.mean(gaps)) * 100, 2) if gaps else None,
                                         "share_quote_2c_or_more_below": round(float(np.mean(np.array(gaps) <= -0.02 + EPS)), 3) if gaps else None}
    full[cid] = rec
    flat = {"id": cid, "family": rec["family"], "side": rec["side"], "exit": e, "conds": rec["conds"]}
    for k in ("L0", "L1_quotes_common", "L2_book_same_poll", "L3_book_2s_limit", "L3_book_6s_limit", "L4_quote_signal_book_price", "L4_quote_signal_book_price_limit"):
        d = rec[k] or {}
        for kk in ("n", "wins", "pf1", "pf10", "mean1_c", "z", "fill_share"):
            if kk in d:
                flat[k.split("_")[0] + ("" if k in ("L0",) else "_" + "_".join(k.split("_")[1:])) + "." + kk] = d[kk]
    flat["quote_minus_book_ask_mean_c"] = rec["quote_ask_minus_book_ask_c"]["mean"]
    rows_out.append(flat)

pd.DataFrame(rows_out).to_csv(OUT_CSV, index=False)


def over(k):
    p = np.array([full[c][k]["pf1"] for c in full if full[c][k] and full[c][k]["n"] > 0], float)
    return {"rows": int(len(p)), "rows_pf1_at_or_above_1": int((p >= 1).sum()), "rows_pf1_at_or_above_1.5": int((p >= 1.5).sum()), "median_pf1": round(float(np.median(p)), 3),
            "median_n": float(np.median([full[c][k]["n"] for c in full if full[c][k]]))}


summary = {"test": "GEN4 forward rows re-scored on R6 books (same test, no new try)", "windows_common": len(common),
           "windows_with_quotes_only_dropped": None, "closes_from": "2026-10-30T00:00Z", "closes_to": "2026-11-04T19:30Z",
           "spot_seconds": len(X), "over_all_rows": {k: over(k) for k in ("L0", "L1_quotes_common", "L2_book_same_poll", "L3_book_2s_limit", "L3_book_6s_limit",
                                                                         "L4_quote_signal_book_price", "L4_quote_signal_book_price_limit")}, "rows": full}
json.dump(summary, open(OUT_JSON, "w"), indent=1, default=float)
print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
