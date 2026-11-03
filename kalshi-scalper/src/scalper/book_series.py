"""RECBOOK2 reader: yields book polls and trades for any recorded hourly ladder (Bitcoin from book/, Ethereum and gold from book2/) without touching the registered
makertail1.py. Research only. Rows are yielded in the shape makertail1 builds its Poll objects from, plus the series and strike.

    from scalper.book_series import iter_polls, iter_trades
    for p in iter_polls(series="KXETHD"): ...    # p.series, p.close, p.strike, p.t, p.yes_px, p.yes_sz, p.no_px, p.no_sz

`t` is the EXCHANGE time in seconds (the Date header), as in makertail1. Books in book/ have no series column, so it is read from the ticker.
Pure parsing is in rows_to_polls / rows_to_trades (no git), so tests need no data branch.
"""
from __future__ import annotations

import csv
import gzip
import io
import subprocess
from collections import namedtuple
from datetime import datetime
from email.utils import parsedate_to_datetime

REPO = "/home/user/shwoopnet"
DIRS = ("book/", "book2/")
Poll = namedtuple("Poll", "series close strike t yes_px yes_sz no_px no_sz ticker")
Trade = namedtuple("Trade", "series ticker t yes_price count taker_side trade_id")


def series_of(ticker):
    return (ticker or "").split("-", 1)[0]


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _levels(row, kind):
    pairs = []
    for i in range(1, 6):
        p, s = num(row.get(f"{kind}_px_{i}")), num(row.get(f"{kind}_sz_{i}"))
        if p is not None and s is not None:
            pairs.append((p, s))
    return [p for p, _ in pairs], [s for _, s in pairs]


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def rows_to_polls(rows, series=None, seen=None):
    """rows: dicts of a book.csv. A row with no server date, or already seen (ticker, poll time), is skipped. `series` filters."""
    seen = set() if seen is None else seen
    for r in rows:
        ser = r.get("series") or series_of(r.get("ticker"))
        if series and ser != series:
            continue
        key = (r["ticker"], r["poll_ts_local_ms"])
        if key in seen or not r.get("server_date_header"):
            continue
        seen.add(key)
        try:
            t = parsedate_to_datetime(r["server_date_header"]).timestamp()
        except Exception:
            continue
        yp, ys = _levels(r, "yes_bid")
        np_, ns = _levels(r, "no_bid")
        yield Poll(ser, parse_iso(r["close_time"]), num(r.get("strike")), t, yp, ys, np_, ns, r["ticker"])


def rows_to_trades(rows, series=None, seen=None):
    seen = set() if seen is None else seen
    for r in rows:
        ser = r.get("series") or series_of(r.get("ticker"))
        if series and ser != series:
            continue
        if r["trade_id"] in seen:
            continue
        seen.add(r["trade_id"])
        yield Trade(ser, r["ticker"], parse_iso(r["created_time"]), float(r["yes_price_dollars"]), float(r["count_fp"]), r["taker_outcome_side"], r["trade_id"])


def _git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True).stdout


def book_files(dirs=DIRS):
    """[(commit, path)] for every book file ever added to origin/quote-data (the tip carries only the newest runs)."""
    _git("fetch", "-q", "origin", "quote-data")
    out = _git("log", "origin/quote-data", "--diff-filter=A", "--name-only", "--format=C %H", "--", *dirs).decode().splitlines()
    res, c = [], None
    for ln in out:
        if ln.startswith("C "):
            c = ln[2:]
        elif ln.strip():
            res.append((c, ln.strip()))
    return res


def _csv(commit, path):
    raw = _git("show", f"{commit}:{path}")
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


def iter_polls(series=None, dirs=DIRS):
    seen = set()
    for commit, path in book_files(dirs):
        if path.endswith("/book.csv.gz"):
            yield from rows_to_polls(_csv(commit, path), series, seen)


def iter_trades(series=None, dirs=DIRS):
    seen = set()
    for commit, path in book_files(dirs):
        if path.endswith("/trades.csv.gz"):
            yield from rows_to_trades(_csv(commit, path), series, seen)
