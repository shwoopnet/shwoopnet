"""Replay CFRTI development signal rows on the R6 books (FILLHAIRCUT1 convention). No outcome is loaded.

usage: python3 -I cfrti_dev_replay_grid.py <data_root> <signals_csv> <out_csv>
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import r6load as R

ROOT, SIG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CUT = pd.Timestamp("2026-11-05T00:00:00Z")
EPS = 1e-9
S = pd.read_csv(SIG)
S["t0_ms"] = R.to_ms(S["t0_utc"])
assert (pd.to_datetime(S["t0_utc"], utc=True) < CUT - pd.Timedelta(seconds=120)).all(), "a row at or after the held-out cut"
tick = set(S["ticker"])
parts = []
for d in R.run_dirs(ROOT):
    f = os.path.join(d, "book.csv.gz")
    if os.path.exists(f) and os.path.basename(os.path.dirname(d)) < "2026-11-06":
        b = pd.read_csv(f, usecols=["t_recv_ms", "ticker"] + R.PX + R.SZ)
        parts.append(b[b["ticker"].isin(tick)])
B = pd.concat(parts, ignore_index=True).drop_duplicates(subset=["ticker", "t_recv_ms"]).sort_values(["ticker", "t_recv_ms"])
by = {tk: g for tk, g in B.groupby("ticker", sort=False)}
rows = []
for r in S.itertuples(index=False):
    o = {"form": r.form, "t0_utc": r.t0_utc, "ticker": r.ticker, "side": r.side, "ask_seen": r.ask_seen}
    g = by.get(r.ticker)
    if g is None:
        o["status"] = "no_book"; rows.append(o); continue
    t = g["t_recv_ms"].to_numpy()
    yb = g[R.PX[:5]].to_numpy(float); nb = g[R.PX[5:]].to_numpy(float)
    ybs = np.nan_to_num(g[R.SZ[:5]].to_numpy(float)); nbs = np.nan_to_num(g[R.SZ[5:]].to_numpy(float))
    usable = (yb[:, 0] == yb[:, 0]) & (nb[:, 0] == nb[:, 0]) & (yb[:, 0] < 1 - nb[:, 0] - EPS)
    apx, asz = (1 - nb, nbs) if r.side == "yes" else (1 - yb, ybs)
    uidx = np.flatnonzero(usable); ut = t[uidx]
    k0 = np.searchsorted(ut, r.t0_ms, side="right") - 1
    if k0 >= 0 and r.t0_ms - ut[k0] <= 6000:
        o["r6_ask_at_t0"] = round(float(apx[uidx[k0], 0]), 4); o["r6_t0_age_s"] = round((r.t0_ms - ut[k0]) / 1000.0, 2)
    any_poll = False
    for d in (2, 6, 10):
        k = np.searchsorted(ut, r.t0_ms + d * 1000, side="left")
        if k >= len(uidx) or ut[k] > r.t0_ms + (d + 4) * 1000:
            continue
        any_poll = True
        j = uidx[k]
        o["lag_%ds" % d] = round((t[j] - r.t0_ms) / 1000.0, 2)
        o["ask_%ds" % d] = round(float(apx[j, 0]), 4)
        for L, slip in ((0, 0.0), (1, 0.01), (2, 0.02)):
            ok = apx[j] <= r.ask_seen + slip + EPS
            for Q in (1, 10):
                got = cost = 0.0
                for p, s in zip(apx[j][ok], asz[j][ok]):
                    q = min(Q - got, s)
                    if q <= 0:
                        break
                    got += q; cost += q * p
                o["fill%d_L%d_%ds" % (Q, L, d)] = int(got >= Q - 1e-6)
                o["px%d_L%d_%ds" % (Q, L, d)] = round(cost / got, 4) if got > 0 else ""
    o["status"] = "replayed" if any_poll else "no_poll_in_window"
    rows.append(o)
O = pd.DataFrame(rows)
O.to_csv(OUT, index=False)
print(O["status"].value_counts().to_dict())
Rp = O[O["status"] == "replayed"]
for form, g in Rp.groupby("form"):
    for L in (0, 1, 2):
        line = {"form": form, "limit": "+%dc" % L}
        for d in (2, 6, 10):
            f = pd.to_numeric(g["fill1_L%d_%ds" % (L, d)], errors="coerce"); f10 = pd.to_numeric(g["fill10_L%d_%ds" % (L, d)], errors="coerce")
            px = pd.to_numeric(g["px1_L%d_%ds" % (L, d)], errors="coerce"); m = f == 1
            line["%ds" % d] = "%d of %d (10 lots: %d), paid %+.1fc" % (int(f.sum()), int(f.notna().sum()), int(f10.sum()), 100 * float((px[m] - g["ask_seen"][m]).mean()) if m.any() else float("nan"))
        print(line)
