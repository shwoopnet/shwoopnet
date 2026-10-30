"""OIFILL: visible size behind the Bitcoin open interest signals, from recorder R6 (research only, information).
Nightly inside `drift run` (same try/except as dogefill and goldslip). Usage: python -m scalper.oifill run

For every forward signal of REF_GEN6_OICORE and REF_GEN6_OIDRIFT (re-run with the ledger's own loader and evaluators on windows that
closed after each freeze), the R6 book row (`origin/quote-data`, book15r6/) NEAREST AFTER the signal candle's end (close - 180 s, R6's
corrected exchange time, at most MAX_LAG_S later) gives: the size at the bought side's best ask, and the contracts offered at most 2c
above that ask (the 5 recorded levels only, so it is a lower bound). Aggregates only go to workers/OIFILL.md, newest first.
It reads public files, places nothing, and changes no rule. With 0 signals it writes a line saying so.
"""
from __future__ import annotations

import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .paths import DATA_DIR

IDS = ("REF_GEN6_OICORE", "REF_GEN6_OIDRIFT")
SERIES = "KXBTC15M"
LOOK = 180
MAX_LAG_S = 10.0
UP_C = 0.02
SIZE_MARK = 10
OUT = DATA_DIR.parent / "workers" / "OIFILL.md"
CT = ZoneInfo("America/Chicago")
EPS = 1e-6


def ask_levels(poll, side):
    """[(ask price, size)] best first for buying `side`: YES lifts the NO bids (ask 1 - p), NO lifts the YES bids."""
    if side == "yes":
        return [(round(1 - p, 6), s) for p, s in zip(poll.nb, poll.nbs)]
    return [(round(1 - p, 6), s) for p, s in zip(poll.yb, poll.ybs)]


def depth(poll, side, up=UP_C):
    """(best ask, size at it, contracts at most `up` above it) or None when that side is empty."""
    lv = ask_levels(poll, side)
    if not lv:
        return None
    best = lv[0][0]
    return best, lv[0][1], sum(s for p, s in lv if p <= best + up + EPS)


def nearest_after(polls, t, max_lag=MAX_LAG_S):
    """First poll at or after t (polls sorted by t), if within max_lag seconds."""
    for p in polls:
        if p.t >= t - EPS:
            return p if p.t - t <= max_lag + EPS else None
    return None


def signals():
    """{candidate id: [trade rows]} for the two candidates, forward windows only, through the ledger's own code."""
    from . import fwdledger as F
    cands = [c for c in F.read_candidates(F.CAND_DIR) if c["id"] in IDS and not c.get("_error")]
    if not cands:
        return {i: [] for i in IDS}
    wins = sorted(F.load_candles({SERIES}, min(c["_freeze"] for c in cands)), key=lambda w: (w["close_ts"], w["ticker"]))
    out = {i: [] for i in IDS}
    for c in cands:
        out[c["id"]] = F.evaluate(c, wins)["trades"]
    return out


def r6_polls(tickers):
    """{ticker: sorted [Poll]} for the wanted tickers from R6's book files (only the runs whose coverage lists them)."""
    from . import r6tests as r6
    want = set(tickers)
    if not want:
        return {}
    r6._git("fetch", "-q", "origin", "quote-data")
    runs = sorted({r for (_, se), (r, row) in r6.windows().items() if se == SERIES and row.get("ticker") in want})
    out = defaultdict(list)
    for r in runs:
        book = r6._csv(f"{r}/book.csv.gz")
        off = r6._offset(book)
        if off is None:
            continue
        for x in book:
            if x.get("ticker") in want:
                out[x["ticker"]].append(r6._poll(x, off))
        del book
    return {k: sorted(v, key=lambda p: p.t) for k, v in out.items()}


def measure(trades, polls):
    rows = []
    for tr in trades:
        ps = polls.get(tr["ticker"])
        t0 = tr["close_ts"] - LOOK
        p = nearest_after(ps, t0) if ps else None
        d = depth(p, tr["side"]) if p is not None else None
        rows.append({"has_r6": ps is not None, "row": p is not None, "lag": None if p is None else p.t - t0,
                     "ask": None if d is None else d[0], "at": None if d is None else d[1], "up2": None if d is None else d[2],
                     "entry": tr["entry"]})
    return rows


def _q(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def summary_line(cid, rows):
    n = len(rows)
    if n == 0:
        return f"| {cid} | 0 | | | | | | | | |"
    m = [r for r in rows if r["ask"] is not None]
    nor6 = sum(1 for r in rows if not r["has_r6"])
    if not m:
        return f"| {cid} | {n} | 0 | {nor6} | | | | | | |"
    at, up = [r["at"] for r in m], [r["up2"] for r in m]
    dc = [100 * (r["ask"] - r["entry"]) for r in m]
    return (f"| {cid} | {n} | {len(m)} | {nor6} | {st.median(r['lag'] for r in m):.1f}s | {st.median(at):.0f} (p10 {_q(at, 0.1):.0f}, min {min(at):.0f}) | "
            f"{st.median(up):.0f} (p10 {_q(up, 0.1):.0f}) | {sum(1 for x in at if x >= SIZE_MARK)} / {sum(1 for x in up if x >= SIZE_MARK)} | "
            f"{st.median(dc):+.1f}c | {', '.join(f'{x:.0f}' for x in sorted(at)[:5])} |")


def run(out=OUT, sigs=None, polls=None):
    sigs = signals() if sigs is None else sigs
    if polls is None:
        polls = r6_polls({t["ticker"] for v in sigs.values() for t in v})
    lines = [f"## {datetime.now(CT):%Y-%m-%d %H:%M} CT (forward signals of the Bitcoin open interest core; R6 book row nearest after close - 180 s, "
             f"at most {MAX_LAG_S:.0f} s later; 5 recorded levels)", ""]
    total = sum(len(v) for v in sigs.values())
    if total == 0:
        lines.append("- 0 forward signals so far for " + " and ".join(IDS) + "; nothing to measure.")
    else:
        lines += ["| candidate | signals | with an R6 row | window not in R6 | median lag | size at the ask (median) | contracts within +2c (median) | "
                  f"{SIZE_MARK}+ at ask / {SIZE_MARK}+ within +2c | book ask minus candle fill (median) | smallest sizes at the ask |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for cid in IDS:
            lines.append(summary_line(cid, measure(sigs.get(cid, []), polls)))
    lines.append("")
    old = out.read_text() if out.exists() else ("# OIFILL: visible size behind the Bitcoin open interest signals (newest first; aggregates only; "
                                                "information)\n\n")
    head, _, rest = old.partition("\n\n")
    out.write_text(head + "\n\n" + "\n".join(lines) + "\n" + rest)
    print("\n".join(lines))
    return []


if __name__ == "__main__":
    {"run": run}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
