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


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "inventory":
        for r in inventory():
            print(json.dumps(r))
    elif cmd == "inventory_md":
        print(inventory_md())
    elif cmd == "thresholds":
        print(json.dumps(freeze_thresholds(), indent=1))
