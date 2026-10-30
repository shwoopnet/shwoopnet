"""OIDRIFT: the Bitcoin open interest core with a drifting threshold, as a forward ledger evaluator (research only).
Definition: workers/OIDRIFT_REGISTRATION.md. Nothing here places an order, reads a key or decides anything live.

    PYTHONPATH=src python -m scalper.oidrift parity    (history Sep 21 to Oct 27 against fals4's check 5; no forward window)

Rule: KXBTC15M, doi = oi at the candle ending 180 s before the close minus oi at the one ending 360 s before; trade when doi is above
the 90th percentile of doi over settled KXBTC15M windows closing in the 30 UTC days before the scored window's day (20+ days with a
value, else NoData); cheap side at the signal candle (ask 5c to 50c, YES first); fill at that side's ask on the candle ending 120 s
before the close; held to settlement.
"""
from __future__ import annotations

import sqlite3
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone

from .fwdeval import NoData
from .paths import DATA_DIR

SERIES = "KXBTC15M"
FILES = ["l1b.sqlite", "book.sqlite", "fresh.sqlite"]      # first file holding a ticker wins (as fals4)
LOOK, BACK, FILL = 180, 360, 120
LO, HI = 0.05, 0.50
SPAN_DAYS, MIN_DAYS, Q = 30, 20, 0.9
_CACHE: dict = {}


def _day0(ts: int) -> int:
    return int(ts) - int(ts) % 86400


def doi_by_day(files=None, data_dir=None) -> dict:
    """{UTC day start: [doi, ...]} over settled KXBTC15M windows, raw candle oi (null excluded)."""
    files = FILES if files is None else files
    data_dir = DATA_DIR if data_dir is None else data_dir
    seen, out = set(), defaultdict(list)
    for f in files:
        p = data_dir / f
        if not p.exists():
            continue
        con = sqlite3.connect(p)
        mk = con.execute("select ticker, close_ts from market where series=? and result in ('yes','no')", (SERIES,)).fetchall()
        mine = {t: c for t, c in mk if t not in seen}
        seen.update(mine)
        oi = defaultdict(dict)
        for t, e, o in con.execute("select ticker, end_ts, oi from candle where series=?", (SERIES,)):
            c = mine.get(t)
            if c is not None and e - c in (-LOOK, -BACK):
                oi[t][e - c] = o
        for t, c in mine.items():
            a, b = oi[t].get(-LOOK), oi[t].get(-BACK)
            if a is not None and b is not None:
                out[_day0(c)].append(a - b)
        con.close()
    return dict(out)


def threshold(close_ts: int, by_day: dict):
    """p90 of doi over the 30 UTC days before close_ts's day; None with fewer than MIN_DAYS days holding a value."""
    d0 = _day0(close_ts)
    days = [d for d in by_day if d0 - SPAN_DAYS * 86400 <= d < d0 and by_day[d]]
    if len(days) < MIN_DAYS:
        return None
    v = sorted(x for d in days for x in by_day[d])
    return v[int(Q * (len(v) - 1))]


def _by_day():
    if "by_day" not in _CACHE:
        _CACHE["by_day"] = doi_by_day()
        _CACHE["thr"] = {}
    return _CACHE["by_day"]


def _thr(close_ts: int):
    bd = _by_day()
    d0 = _day0(close_ts)
    if d0 not in _CACHE["thr"]:
        _CACHE["thr"][d0] = threshold(close_ts, bd)
    return _CACHE["thr"][d0]


def side_ask(q, side):
    return q[1] if side == "yes" else round(1 - q[0], 6)


def decide(window: dict, thr):
    """The rule on one window given its threshold (thr None means the threshold is unavailable)."""
    if window.get("series") != SERIES:
        return None
    cs, close = window["candles"], window["close_ts"]
    s, p = cs.get(close - LOOK), cs.get(close - BACK)
    if s is None or p is None or not s[3] or not p[3]:
        raise NoData("signal or back candle (or its open interest) missing")
    if thr is None:
        raise NoData(f"fewer than {MIN_DAYS} earlier days for the threshold")
    doi = s[3] - p[3]
    if not doi > thr:
        return None
    side = next((sd for sd in ("yes", "no") if s[0] is not None and s[1] is not None and LO <= side_ask(s, sd) <= HI), None)
    if side is None:
        return None
    f = cs.get(close - FILL)
    if f is None or f[0] is None or f[1] is None:
        raise NoData("fill candle missing")
    fill = side_ask(f, side)
    if not 0 < fill < 1:
        return None
    return {"side": side, "entry": float(fill), "exit": None, "t": close - FILL, "zero_volume": (s[2] or 0) <= 0 or (f[2] or 0) <= 0,
            "note": f"doi {doi:.0f} > p90 {thr:.0f}, signal ask {side_ask(s, side):.2f}"}


def forward_eval(window: dict, params: dict):
    if window.get("series") != params.get("series", SERIES):
        return None
    return decide(window, _thr(window["close_ts"]))


# ---------------------------------------------------------------- parity (history only)

def _ledger_windows(lo: int, hi: int) -> list:
    """History windows built as fwdledger.load_candles builds them (bid/ask not null, volume and oi `or 0`), lo <= close < hi."""
    seen, out = set(), []
    for f in FILES:
        con = sqlite3.connect(DATA_DIR / f)
        mk = [(t, c, r) for t, c, r in con.execute("select ticker, close_ts, result from market where series=? and close_ts>=? and close_ts<? "
                                                   "and result in ('yes','no')", (SERIES, lo, hi)) if t not in seen]
        seen.update(t for t, _, _ in mk)
        want = {t for t, _, _ in mk}
        cs = defaultdict(dict)
        for t, e, b, a, v, oi in con.execute("select ticker, end_ts, bid_c, ask_c, volume, oi from candle where series=? and bid_c is not null "
                                             "and ask_c is not null", (SERIES,)):
            if t in want:
                cs[t][e] = (b, a, v or 0.0, oi or 0.0)
        for t, c, r in mk:
            if cs.get(t):
                out.append({"source": "candles", "ticker": t, "series": SERIES, "close_ts": c, "result": r, "candles": cs[t]})
        con.close()
    return sorted(out, key=lambda w: w["close_ts"])


def parity():
    from . import fals4
    from .fwdledger import net_per_contract, pf
    val0, fwd = fals4.DISC_END, fals4.FORWARD_TS
    bd = {d: v for d, v in _by_day().items() if d < fwd}      # history only: nothing closing on or after 2026-10-28
    mine, nodata = {}, 0
    for w in _ledger_windows(val0, fwd):
        try:
            tr = decide(w, threshold(w["close_ts"], bd))
        except NoData:
            nodata += 1
            continue
        if tr:
            mine[w["ticker"]] = (tr, net_per_contract(tr, w["result"], 10), w["result"])
    # fals4's own check 5
    win = fals4.load()
    dd = defaultdict(list)
    for w in win.values():
        sg = fals4.signal(w)
        if sg:
            dd[fals4.day(w["close"])].append(sg["doi"])
    days = sorted(dd)

    def thr_fn(w):
        d0 = datetime.strptime(fals4.day(w["close"]), "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
        prev = [x for x in days if d0 - 30 * 86400 <= datetime.strptime(x, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() < d0]
        if len(prev) < 10:
            return None
        v = sorted(sum((dd[x] for x in prev), []))
        return v[int(0.9 * (len(v) - 1))]
    ref = {t["t"]: t for t in fals4.trades(win, thr_fn=thr_fn) if t["stage"] == "val"}
    only_m = sorted(set(mine) - set(ref)); only_r = sorted(set(ref) - set(mine))
    diff = [t for t in set(mine) & set(ref) if mine[t][0]["side"] != ref[t]["side"] or abs(mine[t][0]["entry"] - ref[t]["fill"]) > 1e-9]
    mine_pf = pf([x[1] for x in mine.values()])
    ref_pf = fals4.pf([t["net"] for t in ref.values()])
    line = (f"OIDRIFT parity (validation Sep 21 to Oct 27): evaluator n {len(mine)} PF10 {mine_pf:.2f}; fals4 check 5 n {len(ref)} PF10 {ref_pf:.2f}; "
            f"only evaluator {len(only_m)}, only fals4 {len(only_r)}, side or fill differs {len(diff)}; NoData windows {nodata}")
    print(line)
    for t in only_m[:10] + only_r[:10] + diff[:10]:
        print("  mismatch", t)
    return {"n": len(mine), "pf": mine_pf, "ref_n": len(ref), "ref_pf": ref_pf, "only_m": only_m, "only_r": only_r, "diff": diff, "nodata": nodata}


if __name__ == "__main__":
    {"parity": parity}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
