"""TAPEFLOW1 simulation (workers/TAPEFLOW1_PROTOCOL.md). Reads extracted quote-data files on disk (arg 1 = dir holding book/ and book15r6/); no network.
usage: python3 -I tapeflow1.py DATADIR [dev|heldout]   (heldout only after the development gate is met)"""
import sys, glob, os, math, json, collections, datetime as dt
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
ROOT = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else "dev"
CUT = "2026-11-07T12:15:00Z"
MIN = 60000; STEP = 30000
def ms(s): return int(pd.Timestamp(s).timestamp() * 1000)
def day(tms): return dt.datetime.fromtimestamp(tms / 1000, ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")
def iter_events():
    """yield (family, ticker, T_ms, book_df, trade_df) for every ticker of every file dir"""
    for fam, pat, tcol, tbt in (("15m", "book15r6/*/*/book.csv.gz", "t_recv_ms", None), ("hourly", "book/*/*/book.csv.gz", "poll_ts_local_ms", None)):
        for bf in sorted(glob.glob(os.path.join(ROOT, pat))):
            tf = bf.replace("book.csv.gz", "trades.csv.gz")
            if not os.path.exists(tf): continue
            b = pd.read_csv(bf); t = pd.read_csv(tf)
            if len(b) == 0 or len(t) == 0: continue
            b["tb"] = b[tcol]
            t["tc"] = pd.to_datetime(t["created_time"], utc=True, format="ISO8601").astype("int64") // 10**6 if True else 0
            t["tc"] = pd.to_datetime(t["created_time"], utc=True, format="ISO8601").map(lambda x: int(x.timestamp() * 1000))
            if "trade_id" in t.columns:
                t = t.drop_duplicates("trade_id")
                t["avail"] = np.maximum(t["tc"], t["poll_ts_local_ms"])    # known only when the poll saw it
            else:
                t["avail"] = t["tc"]
            tg = {k: v for k, v in t.groupby("ticker")}
            for tk, bb in b.groupby("ticker"):
                if tk not in tg: continue
                T = ms(bb["close_time"].iloc[0])
                yield fam, tk, T, bb.sort_values("tb").reset_index(drop=True), tg[tk].sort_values("tc").reset_index(drop=True)
def series_of(tk): return tk.split("-")[0]
def grid_cells(bb, tr, T):
    """grid times, Vyes, Vno (trailing 5 min, by availability), bucket"""
    t0 = int(bb["tb"].iloc[0]) + 5 * MIN; t1 = T - 4 * MIN
    if t1 < t0: return None
    g = np.arange(t0, t1 + 1, STEP)
    av = tr["avail"].values; tc = tr["tc"].values; c = tr["count_fp"].values; sy = (tr["taker_outcome_side"].values == "yes")
    o = np.argsort(av, kind="stable"); av = av[o]; tc = tc[o]; c = c[o]; sy = sy[o]
    cy = np.concatenate([[0], np.cumsum(c * sy)]); cn = np.concatenate([[0], np.cumsum(c * ~sy)])
    # trades with created in (t-5min, t] and available by t: use availability for the upper cut and created for the lower
    hi = np.searchsorted(av, g, side="right")
    # lower cut by created time: subtract trades created <= t-5min (all of those are also available by t)
    o2 = np.argsort(tc, kind="stable"); tcs = tc[o2]; cy2 = np.concatenate([[0], np.cumsum((c * sy)[o2])]); cn2 = np.concatenate([[0], np.cumsum((c * ~sy)[o2])])
    lo = np.searchsorted(tcs, g - 5 * MIN, side="right")
    vy = cy[hi] - cy2[lo]; vn = cn[hi] - cn2[lo]
    return g, np.maximum(vy, 0), np.maximum(vn, 0), ((T - g) // (5 * MIN)).astype(int)
def book_at(bb, x, maxage=30000):
    i = np.searchsorted(bb["tb"].values, x, side="right") - 1
    if i < 0 or x - bb["tb"].values[i] > maxage: return None
    return bb.iloc[i]
def bestbid(row, X):
    v = row["yes_bid_px_1" if X == "yes" else "no_bid_px_1"]; return 0.0 if pd.isna(v) else float(v)
def exit_sim(bb, tr, T, X, tf, p, ahead_row, base_time_for_book):
    """from a fill at tf at own-price p; returns (exit_price, kind, exit_time, maker_exit)"""
    D = min(tf + 10 * MIN, T - 3 * MIN)
    s = round(p + 0.02, 2)
    bt = bb["tb"].values
    best = None   # (time, price, kind, maker)
    if s <= 0.99:
        # queue ahead for own ask at s: opposite side's bid at 1-s
        row = ahead_row; o = "no" if X == "yes" else "yes"; lvl = round(1 - s, 2); ahead = None
        if row is not None:
            px1 = row[o + "_bid_px_1"]
            if pd.isna(px1) or lvl > px1 + 1e-9: ahead = 0.0
            else:
                for k in range(1, 6):
                    pk = row["%s_bid_px_%d" % (o, k)]
                    if not pd.isna(pk) and abs(pk - lvl) < 1e-6: ahead = float(row["%s_bid_sz_%d" % (o, k)]); break
        if ahead is not None:
            yp = s if X == "yes" else round(1 - s, 2)
            m = tr[(tr["tc"] > tf) & (tr["tc"] <= D) & (tr["taker_outcome_side"] == X) & ((tr["yes_price_dollars"] - yp).abs() < 1e-6)]
            if len(m):
                cum = m["count_fp"].cumsum().values
                j = np.searchsorted(cum, ahead + 1 - 1e-9, side="left")
                if j < len(cum): best = (int(m["tc"].values[j]), s, "target_queue", True)
        # taker cross of the target by the book
        i0 = np.searchsorted(bt, tf, side="right"); i1 = np.searchsorted(bt, D, side="right")
        if i1 > i0:
            col = bb["yes_bid_px_1" if X == "yes" else "no_bid_px_1"].values[i0:i1]
            hit = np.where(col >= s - 1e-9)[0]
            if len(hit):
                tt = int(bt[i0 + hit[0]])
                if best is None or tt < best[0]: best = (tt, float(col[hit[0]]), "target_cross", False)
    if best: return best
    i = np.searchsorted(bt, D, side="right") - 1
    bid = 0.0 if i < 0 else bestbid(bb.iloc[i], X)
    return (D, bid, "time" if D == tf + 10 * MIN else "forced", False)
def pnl(p, ex, maker_exit, mc):
    f = mc * p * (1 - p) + (mc * ex * (1 - ex) if maker_exit else 0.07 * ex * (1 - ex))
    return ex - p - f
def process(bb, tr, T, base, fam, ser, sigs):
    cells = grid_cells(bb, tr, T)
    if cells is None: return
    g, vy, vn, bk = cells; busy = 0
    for k in range(len(g)):
        t = int(g[k])
        if t < busy: continue
        mb = base.get((ser, int(bk[k])))
        if mb is None or mb <= 0 and False: continue
        thr = 3 * (mb or 0)
        ry = vy[k] / max(thr, 1e-9); rn = vn[k] / max(thr, 1e-9)
        if max(vy[k], vn[k]) < 50: continue
        if vy[k] >= thr and vy[k] > vn[k] and ry >= rn: flow = "yes"
        elif vn[k] >= thr and vn[k] > vy[k]: flow = "no"
        else: continue
        X = "no" if flow == "yes" else "yes"
        row = book_at(bb, t)
        if row is None: continue
        p = bestbid(row, X); sz = row[X + "_bid_sz_1"]
        if p <= 0 or pd.isna(sz): continue
        cancel = min(t + 5 * MIN, T - 4 * MIN)
        yp = p if X == "yes" else round(1 - p, 2); other = "no" if X == "yes" else "yes"
        m = tr[(tr["tc"] >= t) & (tr["tc"] <= cancel) & (tr["taker_outcome_side"] == other) & ((tr["yes_price_dollars"] - yp).abs() < 1e-6)]
        filled = False; tf = None
        if len(m):
            cum = m["count_fp"].cumsum().values; j = np.searchsorted(cum, float(sz) + 1 - 1e-9, side="left")
            if j < len(cum): filled = True; tf = int(m["tc"].values[j])
        rec = dict(fam=fam, ser=ser, tk=bb["ticker"].iloc[0], T=T, t=t, flow=flow, X=X, p=p, filled=filled, day=day(t), vy=float(vy[k]), vn=float(vn[k]))
        # counterfactual (instant fill at signal) for every signal; actual for filled
        for tag, tstart in (("cf", t), ("fill", tf)):
            if tag == "fill" and not filled: continue
            r2 = book_at(bb, tstart, 60000)
            te, ex, kind, mk = exit_sim(bb, tr, T, X, tstart, p, r2, None)
            rec[tag] = {str(mc): pnl(p, ex, mk, mc) for mc in (0.0, 0.0175)}; rec[tag + "_kind"] = kind; rec[tag + "_hold"] = (te - tstart) / 1000.0
        sigs.append(rec)
        busy = (tf if filled else cancel) + 1
        if filled: busy = max(busy, int(rec["fill_hold"] * 1000 + tf) + 1)
def pf(x):
    x = np.array(x); w = x[x > 0].sum(); l = -x[x < 0].sum(); return float(w / l) if l > 0 else float("inf")
def stats(x, days):
    x = np.array(x, float); n = len(x)
    if n < 2: return dict(n=n)
    z = x.mean() / (x.std(ddof=1) / math.sqrt(n))
    d = collections.defaultdict(float)
    for v, dy in zip(x, days): d[dy] += v
    dv = np.array(list(d.values())); zc = dv.mean() / (dv.std(ddof=1) / math.sqrt(len(dv))) if len(dv) > 2 and dv.std(ddof=1) > 0 else float("nan")
    return dict(n=n, days=len(d), pf=round(pf(x), 3), mean_c=round(100 * x.mean(), 3), z=round(z, 2), z_day=round(zc, 2), net_dollars=round(x.sum(), 2))
if __name__ == "__main__":
    # pass 1: development baseline
    cells = collections.defaultdict(list)
    for fam, tk, T, bb, tr in iter_events():
        if T >= ms(CUT): continue
        c = grid_cells(bb, tr, T)
        if c is None: continue
        g, vy, vn, bk = c
        for b_ in np.unique(bk):
            msk = bk == b_; cells[(series_of(tk), int(b_))] += list(vy[msk]) + list(vn[msk])
    base = {k: float(np.median(v)) for k, v in cells.items()}
    print("baseline cells", len(base), "sample", sorted(base.items())[:6])
    sigs = []
    for fam, tk, T, bb, tr in iter_events():
        if (MODE == "dev") != (T < ms(CUT)): continue
        process(bb, tr, T, base, fam, series_of(tk), sigs)
    json.dump(sigs, open(os.path.join(ROOT, "tapeflow1_%s_signals.json" % MODE), "w"))
    print("MODE", MODE, "signals", len(sigs))
    for name, sel in (("pooled", lambda r: True), ("15m", lambda r: r["fam"] == "15m"), ("hourly", lambda r: r["fam"] == "hourly")):
        S = [r for r in sigs if sel(r)]; F = [r for r in S if r["filled"]]
        print("==", name, "signals", len(S), "filled", len(F), "fill rate %.3f" % (len(F) / max(1, len(S))), "signal days", len({r["day"] for r in S}), "fill days", len({r["day"] for r in F}))
        for mc in ("0.0", "0.0175"):
            print("  maker coef", mc, "FILLED", stats([r["fill"][mc] for r in F], [r["day"] for r in F]))
            U = [r for r in S if not r["filled"]]
            print("  maker coef", mc, "UNFILLED-would-have-been", stats([r["cf"][mc] for r in U], [r["day"] for r in U]))
        print("  exit kinds filled", dict(collections.Counter(r["fill_kind"] for r in F)), "mean hold s %.0f" % (np.mean([r["fill_hold"] for r in F]) if F else 0))
        by = collections.defaultdict(list)
        for r in F: by[r["ser"]].append(r["fill"]["0.0175"])
        print("  by series (filled, bound)", {k: (len(v), round(pf(v), 2), round(100 * np.mean(v), 2)) for k, v in by.items()})
