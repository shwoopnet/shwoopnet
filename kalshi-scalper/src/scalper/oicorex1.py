"""OICOREX1 (workers/OICOREX1_REGISTRATION.md): the Bitcoin open interest core (REF_GEN6_OICORE) on the other 15 minute markets.
Research only; nothing here places an order, reads a key or decides anything live.
    python -m scalper.oicorex1 inventory            (per series: candles, usable open interest, spread; writes nothing but prints)
    python -m scalper.oicorex1 thresholds           (each market's discovery threshold; reads NO outcome)
    python -m scalper.oicorex1 score                (once: discovery and validation per market; refuses a second run)
    python -m scalper.oicorex1 coloss               (after score: co-loss with Bitcoin)
Fill, fee and feature code is gen6.window_rows / gen6.nets (not re-implemented).
forward_eval(window, params) is the forward-ledger evaluator for any market (params: series, threshold).
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from . import gen6
from .paths import DATA_DIR

# Priority order for a ticker that sits in two files: first file wins (as gen6.load_windows does).
ALT_FILES = ("e3b", "alts2", "alts3", "alts4", "rep", "fresh")
BTC_FILES = ("l1b", "book", "fresh", "five")
DISC = gen6.DISC                      # 2026-08-06 to 2026-09-21 (close time, UTC)
VAL = gen6.VAL["KXBTC15M"]            # 2026-09-21 to 2026-10-28
FWD_FROM = VAL[1]                     # holdout: closes on or after 2026-10-28 00:00 UTC, to the end of the data on file
DISC_PCT = 90
BTC_THRESH = 86299.56000000001


def _ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


def _files(series):
    return BTC_FILES if series in ("KXBTC15M", "KXETH15M", "KXGOLD15M") else ALT_FILES


def load_series(series, lo, hi, files=None):
    """{ticker: (close_ts, result, candles)} candles as gen6 builds them (end_ts -> (bid_c, ask_c, volume, oi)); oi None kept as None here."""
    out = {}
    for name in files or _files(series):
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        try:
            mk = db.execute("select ticker, close_ts, result from market where series=? and close_ts>=? and close_ts<?", (series, lo, hi)).fetchall()
        except sqlite3.Error:
            continue
        for tk, ct, res in mk:
            if tk in out:
                continue
            cs = {r[0]: (r[1], r[2], r[3] or 0.0, r[4]) for r in db.execute(
                "select end_ts, bid_c, ask_c, volume, oi from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if cs:
                out[tk] = (ct, res, cs, name)
    return out


def oi_pair(cs, ct):
    """(oi at the -360 candle, oi at the -180 candle) or None if either candle or its oi is missing."""
    a, b = cs.get(ct - 360), cs.get(ct - 180)
    if a is None or b is None or a[3] is None or b[3] is None:
        return None
    return a[3], b[3]


def gen6_cs(cs):
    """The candle dict in gen6's own format (oi None -> 0.0 is NOT used by us: windows without a usable pair are dropped before this)."""
    return {k: (v[0], v[1], v[2], v[3] or 0.0) for k, v in cs.items()}


def window_list(series, lo, hi):
    """Settled windows with a usable open interest pair at -360 and -180, in close order: (ticker, close, result, gen6-format candles)."""
    M = load_series(series, lo, hi)
    out = []
    for tk, (ct, res, cs, f) in sorted(M.items(), key=lambda x: x[1][0]):
        if res not in ("yes", "no"):
            continue
        if oi_pair(cs, ct) is None:
            continue
        out.append((tk, ct, res, gen6_cs(cs)))
    return out


def rows180(series, ct, cs):
    """gen6.window_rows (series key only picks peer names; no peers are used) restricted to the 180 s look. Same fills and features."""
    rows, gaps = gen6.window_rows("KXBTC15M", ct, cs, {})
    return rows, gaps


def _all_rows_doi(series, lo, hi):
    vals, nwin, nrows = [], 0, 0
    for tk, ct, res, cs in window_list(series, lo, hi):
        rows, _ = gen6.window_rows("KXBTC15M", ct, cs, {})
        nwin += 1
        for r in rows:
            nrows += 1
            v = r["feats"][gen6.FEATS.index("doi")]
            if not np.isnan(v):
                vals.append(v)
    return vals, nwin, nrows


def threshold_for(series):
    vals, nwin, nrows = _all_rows_doi(series, *DISC)
    return float(np.nanpercentile(vals, DISC_PCT)) if vals else None, nwin, nrows, len(vals)


# ------------------------------------------------------------------ inventory

def inventory():
    series_all = set()
    for name in ALT_FILES + BTC_FILES:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        try:
            for (s,) in sqlite3.connect(p).execute("select distinct series from market"):
                if s and s.endswith("15M"):
                    series_all.add(s)
        except sqlite3.Error:
            pass
    rows = []
    for s in sorted(series_all):
        M = load_series(s, 0, 2 ** 40, files=ALT_FILES + BTC_FILES)
        n_set = sum(1 for v in M.values() if v[1] in ("yes", "no"))
        ncandle = sum(len(v[2]) for v in M.values())
        pair = both = nonconst = 0
        cand = 0
        spreads = []
        nonconst_win = 0
        by_file = defaultdict(int)
        for tk, (ct, res, cs, f) in M.items():
            if res not in ("yes", "no"):
                continue
            by_file[f] += 1
            q = cs.get(ct - 180)
            if q is not None:
                spreads.append(q[1] - q[0])
                if any(0.05 - 1e-9 <= gen6._sq((q[0], q[1], 0, 0), y)[1] <= 0.5 + 1e-9 for y in (1, 0)):
                    cand += 1
            p = oi_pair(cs, ct)
            if p is not None:
                pair += 1
                if p[0] != p[1]:
                    nonconst += 1
            ois = [v[3] for v in cs.values() if v[3] is not None]
            if len(set(ois)) > 1:
                nonconst_win += 1
        rows.append({"series": s, "settled": n_set, "candles": ncandle, "oi_pair": pair, "oi_pair_share": pair / n_set if n_set else 0,
                     "oi_moves_share": nonconst / n_set if n_set else 0, "oi_varies_in_window": nonconst_win / n_set if n_set else 0,
                     "cand180": cand, "median_spread": statistics.median(spreads) if spreads else None, "files": dict(by_file)})
    return rows



CAND = ["KXDOGE15M", "KXXRP15M", "KXSOL15M", "KXBNB15M", "KXHYPE15M", "KXZEC15M", "KXNEAR15M", "KXSILVER15M", "KXWTI15M", "KXCOPPER15M", "KXNATGAS15M"]


def info_counts(series):
    """Outcome-free counts: windows with a usable oi pair, with a 5c to 50c side at 180 s, and (given a threshold) firing windows per stage."""
    out = {}
    for name, (lo, hi) in (("disc", DISC), ("val", VAL), ("hold", (FWD_FROM, 2 ** 40))):
        W = window_list(series, lo, hi)
        rows = []
        for tk, ct, res, cs in W:
            r, _ = gen6.window_rows("KXBTC15M", ct, cs, {})
            r = [x for x in r if x["L"] == 180]
            rows.append(r[0] if r else None)
        out[name] = {"windows": len(W), "cand": sum(1 for r in rows if r is not None)}
    return out


def inventory_md():
    inv = inventory()
    lines = ["| series | settled windows | candles | first / last close (UTC) | windows with oi at -360 and -180 | oi at -180 differs from oi at -360 | median spread at -180 | windows with a 5c to 50c side at 180 s | usable? |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in inv:
        M = load_series(r["series"], 0, 2 ** 40, files=ALT_FILES + BTC_FILES)
        cts = sorted(v[0] for v in M.values())
        first = datetime.fromtimestamp(cts[0], timezone.utc).strftime("%m-%d") if cts else "-"
        last = datetime.fromtimestamp(cts[-1], timezone.utc).strftime("%m-%d") if cts else "-"
        ms = r["median_spread"]
        lines.append(f"| {r['series']} | {r['settled']} | {r['candles']} | {first} / {last} | {r['oi_pair_share']:.1%} | {r['oi_moves_share']:.1%} | "
                     f"{'-' if ms is None else format(ms, '.3f')} | {r['cand180']} | {{U_{r['series']}}} |")
    return "\n".join(lines)


def freeze_thresholds():
    res = {}
    for s in ["KXBTC15M"] + CAND:
        th, nwin, nrows, nval = threshold_for(s)
        res[s] = {"threshold": th, "disc_windows_with_oi": nwin, "disc_rows": nrows, "disc_rows_valid_doi": nval, **info_counts(s)}
    return res



SCORED = ["KXDOGE15M", "KXXRP15M", "KXNEAR15M", "KXZEC15M", "KXBNB15M", "KXHYPE15M", "KXSILVER15M", "KXWTI15M"]
FLOOR = {"disc": 100, "val": 50}
Z_BAR = 5.27
OUT = DATA_DIR / "oicorex1_score.json"


def strat(th):
    return {"L_hi": 180, "L_lo": 180, "side": "both", "conds": [("doi", "gt", th)], "e": 0}


def pack(W):
    """The same packing as gen6.build, from a window list (gen6.build itself needs peers that only BTC and gold have)."""
    X, meta, EB, EZ = [], [], [], []
    for wid, (tk, ct, res, cs) in enumerate(W):
        rows, _ = gen6.window_rows("KXBTC15M", ct, cs, {})
        day = datetime.fromtimestamp(ct, timezone.utc).strftime("%Y-%m-%d")
        for r in rows:
            win = 1.0 if (res == "yes") == bool(r["yes"]) else 0.0
            X.append(r["feats"]); meta.append((wid, day, r["L"], r["yes"], r["fill"], r["sig_ask"], r["zv_entry"], win, ct))
            EB.append([np.nan if b is None else b for b, z, k in r["exits"]]); EZ.append([z for b, z, k in r["exits"]])
    days = sorted({m[1] for m in meta})
    D = {"X": np.array(X).reshape(-1, len(gen6.FEATS)), "wid": np.array([m[0] for m in meta], dtype=int),
         "day": np.array([days.index(m[1]) for m in meta], dtype=int), "L": np.array([m[2] for m in meta]),
         "yes": np.array([m[3] for m in meta]), "fill": np.array([m[4] for m in meta]), "sig": np.array([m[5] for m in meta]),
         "zve": np.array([m[6] for m in meta], dtype=bool), "win": np.array([m[7] for m in meta]), "close": np.array([m[8] for m in meta]),
         "EB": np.array(EB), "EZ": np.array(EZ, dtype=bool), "days": days, "nwin": len(W), "tickers": [w[0] for w in W]}
    return gen6._order(D)


def stage_score(series, th, lo, hi):
    D = pack(window_list(series, lo, hi))
    if not len(D["wid"]):
        return {"n": 0}, []
    s = strat(th)
    idx = gen6.trades(D, s)
    sc = gen6.score(D, idx, 0)
    v = gen6.nets(D, idx, 0)
    tr = [{"t": D["tickers"][int(D["wid"][i])], "close": int(D["close"][i]), "net10": float(x * 10), "win": float(D["win"][i]), "fill": float(D["fill"][i])}
          for i, x in zip(idx, v)]
    sc["windows"] = D["nwin"]
    return sc, tr


def verdict(d, v, h=None):
    if d["n"] < FLOOR["disc"] or v["n"] < FLOOR["val"]:
        return "NOT_ENOUGH_DATA"
    if d["pf"] < 1.5 or v["pf"] < 1.5 or d["pfs"] <= 1.0 or v["pfs"] <= 1.0:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def score():
    if OUT.exists():
        print("Refusing to run again: validation already read"); return
    fz = json.loads((ROOT_W / "OICOREX1_thresholds.json").read_text())
    res = {}
    for s in ["KXBTC15M"] + SCORED:
        th = threshold_for(s)[0]
        assert abs(th - fz[s]["threshold"]) < 1e-6, (s, th, fz[s]["threshold"])
        d, dt = stage_score(s, th, *DISC)
        v, vt = stage_score(s, th, *VAL)
        r = {"threshold": th, "disc": d, "val": v, "disc_trades": dt, "val_trades": vt}
        if s != "KXBTC15M":
            r["verdict"] = verdict(d, v)
            if r["verdict"] == "NOT_YET_FALSIFIED":
                h, ht = stage_score(s, th, FWD_FROM, 2 ** 40)
                r["hold"] = h; r["hold_trades"] = ht
        res[s] = r
        print(s, "disc", d.get("n"), round(d.get("pf", 0), 2), "val", v.get("n"), round(v.get("pf", 0), 2), r.get("verdict", "(reference)"), flush=True)
    OUT.write_text(json.dumps(res))


def coloss():
    res = json.loads(OUT.read_text())
    out = {}
    for stage in ("disc", "val"):
        btc = {t["close"]: t for t in res["KXBTC15M"][stage + "_trades"]}
        rows = {}
        multi = defaultdict(list)
        for s in SCORED:
            for t in res[s][stage + "_trades"]:
                multi[t["close"]].append((s, t))
        for s in SCORED:
            mt = {t["close"]: t for t in res[s][stage + "_trades"]}
            both = [c for c in btc if c in mt]
            n = len(both)
            if not n:
                rows[s] = {"n": 0}; continue
            bl = [btc[c]["net10"] < 0 for c in both]; ml = [mt[c]["net10"] < 0 for c in both]
            pb, pm = sum(bl) / n, sum(ml) / n
            rows[s] = {"n": n, "both_lost": sum(a and b for a, b in zip(bl, ml)), "only_btc_lost": sum(a and not b for a, b in zip(bl, ml)),
                       "only_m_lost": sum(b and not a for a, b in zip(bl, ml)), "both_won": sum((not a) and (not b) for a, b in zip(bl, ml)),
                       "expected_both_lost": n * pb * pm, "net_btc": sum(btc[c]["net10"] for c in both), "net_m": sum(mt[c]["net10"] for c in both),
                       "btc_loss_rate": pb, "m_loss_rate": pm}
        two = [c for c in set(btc) | set(multi) if (c in btc) + len(multi.get(c, [])) >= 2]
        tot = sum((btc[c]["net10"] if c in btc else 0) + sum(t["net10"] for _, t in multi.get(c, [])) for c in two)
        legs = sum((c in btc) + len(multi.get(c, [])) for c in two)
        rows["_two_or_more"] = {"windows": len(two), "legs": legs, "net": tot}
        out[stage] = rows
    (DATA_DIR / "oicorex1_coloss.json").write_text(json.dumps(out))
    print(json.dumps(out, indent=1))


def forward_eval(window, params):
    """Forward-ledger evaluator of the core on market params["series"] with params["threshold"] (the same rows as gen6.forward_eval)."""
    from .fwdeval import NoData
    series = params["series"]
    if window["series"] != series:
        return None
    th = params["threshold"]
    cs = window["candles"]
    ct = window["close_ts"]
    a, b = cs.get(ct - 360), cs.get(ct - 180)
    if a is None or b is None or a[3] is None or b[3] is None or a[3] == 0 or b[3] == 0:
        raise NoData("open interest candle missing")
    rows, gaps = gen6.window_rows("KXBTC15M", ct, cs, {})
    for r in rows:
        if r["L"] != 180:
            continue
        v = r["feats"][gen6.FEATS.index("doi")]
        if np.isnan(v):
            raise NoData("doi missing")
        if v > th:
            return {"side": "yes" if r["yes"] else "no", "entry": float(r["fill"]), "exit": None, "t": int(r["t"] + 60),
                    "zero_volume": bool(r["zv_entry"]), "note": f"look 180s, signal ask {r['sig_ask']:.2f}, doi {v:.0f}"}
        return None
    if 180 in gaps:
        raise NoData("a candle the rule needs is missing")
    return None


from pathlib import Path
ROOT_W = Path(__file__).resolve().parents[2] / "workers"


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "inventory":
        for r in inventory():
            print(json.dumps(r))
    elif cmd == "inventory_md":
        print(inventory_md())
    elif cmd == "thresholds":
        print(json.dumps(freeze_thresholds(), indent=1))
    elif cmd == "parity":
        th = BTC_THRESH
        for nm, (lo, hi) in (("disc", DISC), ("val", VAL)):
            sc, _ = stage_score("KXBTC15M", th, lo, hi)
            print(nm, sc["n"], round(sc["pf"], 3), round(sc["z"], 2))
    elif cmd == "score":
        score()
    elif cmd == "coloss":
        coloss()
