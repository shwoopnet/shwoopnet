"""Reads the Kalshi page's "Download book snapshots" CSV (the Firestore recorder, about every 10 s, three levels a side) and runs the same descriptive and P2 code on it as on the
local recorder's database. Information only: the P2 verdict rules (300 signals, 5 days) are the ones in `bookmaker.py` and are applied unchanged.

The file is data from outside this repository: it is only parsed with csv, never executed, and every number goes through float().

Usage: python -m scalper.bookfile PATH_TO_CSV_OR_CSV_GZ
"""
from __future__ import annotations

import csv
import gzip
import sqlite3
import sys
from collections import defaultdict

from . import bookmaker as BM
from . import obstats as OS
from .paths import DB


def _f(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def read(path: str) -> list[dict]:
    op = gzip.open if str(path).endswith(".gz") else open
    out = []
    with op(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            t = _f(r.get("t"))
            if t is None or not r.get("ticker"):
                continue
            out.append({"ts": t / 1000.0, "ticker": r["ticker"], "series": r.get("series"), "yes_bid": _f(r.get("yesBid")), "yes_ask": _f(r.get("yesAsk")),
                        "no_bid": _f(r.get("noBid")), "no_ask": _f(r.get("noAsk")), "yes_top_q": _f(r.get("y1q")), "no_top_q": _f(r.get("n1q"))})
    return out


def settled(db_path=DB) -> dict:
    return {t: (c, r) for t, c, r in sqlite3.connect(db_path).execute("SELECT ticker, close_ts, result FROM market") if r in ("yes", "no")}


def by_ticker(rows: list[dict]) -> dict:
    d: dict = defaultdict(list)
    for r in rows:
        d[r["ticker"]].append(r)
    return d


def p2_signals(rows: list[dict], results: dict, start: float = BM.START) -> list[dict]:
    sigs = []
    for ticker, snaps in by_ticker(rows).items():
        if ticker not in results or results[ticker][0] <= start:
            continue
        o = BM.simulate(snaps, results[ticker][0], results[ticker][1])
        if o:
            sigs.append(o)
    return sigs


def window_rows(rows: list[dict], results: dict) -> list[tuple]:
    """Snapshots 330 to 400 s before the close where a side's ask is in L1's band: (ts, ticker+side, close, ask, bid, size at the touch)."""
    out = []
    for r in rows:
        if r["ticker"] not in results:
            continue
        c = results[r["ticker"]][0]
        if not (c - 400 <= r["ts"] <= c - 330):
            continue
        for side, ask, bid, q in (("Y", r["yes_ask"], r["yes_bid"], r["no_top_q"]), ("N", r["no_ask"], r["no_bid"], r["yes_top_q"])):
            if ask is not None and 0.88 <= ask <= 0.97:
                out.append((r["ts"], r["ticker"] + side, c, ask, bid, q))
    return out


def main(path: str) -> None:
    rows = read(path)
    res = settled()
    mk = by_ticker(rows)
    print(f"{len(rows)} snapshots, {len(mk)} markets, {sum(1 for t in mk if t in res)} of them settled in the database\n")
    sigs = p2_signals(rows, res)
    v, i = BM.verdict(sigs)
    print(f"P2 on markets closing after {BM.START}: {i['n']} signals on {i['days']} day(s): {v}")
    if i["n"]:
        c = lambda x: "n/a" if x is None else f"{x * 100:+.2f}c"
        print(f"  fill rate {i['fill_rate'] * 100:.0f}% (touch counted: {i['fill_rate_at'] * 100:.0f}%), filled {i['filled_n']}; filled: maker {c(i['filled_maker'])} vs taken {c(i['filled_taker'])}; missed, taken: {c(i['missed_taker'])}")
        print(f"  per signal (unfilled = 0): maker {c(i['maker_per_signal'])}, taker {c(i['taker_all'])}; lower maker fees, information only: " + ", ".join(f"{k} {c(i[f'maker_per_signal_fee{k}'])}" for k in BM.INFO_COEFFS))
        for lo, hi in ((0.90, 0.92), (0.92, 0.95), (0.95, 0.9701)):
            b = [o for o in sigs if lo <= o["ask"] < hi]
            if b:
                print(f"  ask {lo:.2f} to {min(hi, 0.97):.2f}: {len(b)} signals, filled {sum(1 for o in b if o['filled'])}, taken {sum(BM.taker(o) for o in b) / len(b) * 100:+.2f}c")
    st = OS.stats(window_rows(rows, res))
    print(f"\nAsk persistence in the L1 window: {st['pairs']} consecutive pairs ({st['gaps']} skipped for a gap over 20 s)")
    if st["pairs"]:
        print(f"  next snapshot's ask: up {st['up'] * 100:.1f}%, same {st['same'] * 100:.1f}%, down {st['down'] * 100:.1f}%; median spread {st['median_spread']}; median size at the touch {st['median_touch_size']}")


if __name__ == "__main__":
    main(sys.argv[1])
