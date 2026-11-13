#!/usr/bin/env python3
"""COMBODONE stage 1, SECOND BUILD (History Miner, Nov 13, 2026), from Idea Desk C's card only (claude/idea-desk-c 593597e6, COMBODONE_CARD.md, Amendments 1 and 2) and Desk B's
INPUT_LAYOUT.md (22c2f47a; layout and output names only). Desk B's combodone.py, outputs and generator are NOT read. Zero tries: a count. Reads files only; sends nothing.
Usage: python3 -I combodone2.py count <combo dir> <legs run dir>"""
import csv, gzip, io, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import combodone2_core as K
from datetime import datetime, timezone


def refuse_heldout(p):
    for q in (os.path.abspath(p), os.path.realpath(p)):
        if any(c.upper().startswith("HELDOUT") for c in q.split(os.sep)):
            raise SystemExit("refused: %s is a held-out path" % p)


def read_csv(path):
    if not os.path.exists(path):
        return None
    with gzip.open(path, "rt", newline="") as f:
        return list(csv.DictReader(f))


def iso(s):
    try:
        return datetime.strptime(s.strip().replace("Z", "")[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_runs(combo):
    """[(day folder, run folder path, coverage rows or None, quotes rows or None, books rows or None)]"""
    refuse_heldout(combo)
    runs = []
    for day in sorted(os.listdir(combo)):
        dp = os.path.join(combo, day)
        if not os.path.isdir(dp):
            continue
        for rn in sorted(os.listdir(dp)):
            rp = os.path.join(dp, rn)
            if os.path.isdir(rp):
                runs.append((day, rp, read_csv(os.path.join(rp, "coverage.csv.gz")), read_csv(os.path.join(rp, "quotes.csv.gz")), read_csv(os.path.join(rp, "books.csv.gz"))))
    return runs


def completed(cov, quotes):
    """Amendment 1 point 1: a coverage row with stopped_early = 0 and a quotes file."""
    return bool(cov) and quotes is not None and any(str(r.get("stopped_early", "")).strip() in ("0", "0.0") for r in cov)


def load_legs(run):
    """Amendment 2 point 16: (whole?, asked tickers, {ticker: (result, settlement_ts)})."""
    refuse_heldout(run)
    m = json.load(open(os.path.join(run, "manifest.json")))
    job = m.get("job") or {}
    asked = set()
    for r in job.get("requests", []):
        asked |= {t for t in str((r.get("params") or {}).get("tickers", "")).split(",") if t}
    whole = m.get("status") == "complete"
    got, info = {}, {}
    for row in m.get("rows", []):
        if row.get("status") == 200 and row.get("file") and not row.get("truncated"):
            body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
            got[(row["id"], row.get("page", 1))] = body
            for mk in body.get("markets") or []:
                t = mk.get("ticker")
                if t:
                    st = mk.get("settlement_ts")
                    info[t] = (mk.get("result") or "", iso(st) if isinstance(st, str) and st else None)
        elif row.get("status") == 200:
            whole = False                                   # a 200 cut short or with no file
    for r in job.get("requests", []):
        pages = sorted(pg for (i, pg) in got if i == r["id"])
        if not pages:
            whole = False; continue
        if (got[(r["id"], pages[-1])] or {}).get("cursor"):
            whole = False                                   # an answer left on a cursor
    return whole, asked, info


def count(combo, legs_run):
    runs = load_runs(combo)
    out = {}
    by_day = {}
    for day, rp, cov, q, b in runs:
        by_day.setdefault(day, 0)
        by_day[day] += completed(cov, q)
    out["completed_runs_per_day"] = dict(sorted(by_day.items()))
    last = max(by_day) if by_day else None
    first = K.pick_week(by_day, last)
    if first is None:
        out["verdict"] = "no full week yet"
        return out
    week = [K.next_day(first, k) for k in range(K.WEEK_DAYS)]
    wk_runs = [(d, rp, cov, q, b) for d, rp, cov, q, b in runs if d in week]
    n_done = sum(completed(cov, q) for d, rp, cov, q, b in wk_runs)
    out["week"] = {"first_day": week[0], "last_day": week[-1], "completed_runs": n_done, "of": K.RUNS_PER_DAY * K.WEEK_DAYS,
                   "pct": round(100.0 * n_done / (K.RUNS_PER_DAY * K.WEEK_DAYS), 2), "run_folders_not_completed": sum(1 for d, rp, cov, q, b in wk_runs if not completed(cov, q)),
                   "completed_with_list_complete": sum(1 for d, rp, cov, q, b in wk_runs if completed(cov, q) and any(str(r.get("list_complete", "")).strip() in ("1", "1.0") for r in cov))}
    # snapshots: every quotes row whose receive time falls on a week day, from any run folder (point 11)
    snaps, unreadable = [], 0
    for d, rp, cov, q, b in runs:
        books = {r.get("ticker"): r for r in (b or [])}
        for r in q or []:
            tm = num(r.get("t_recv_ms"))
            if tm is None or not r.get("ticker"):
                # READING (sent to Desk B): an unreadable row counts toward the week if its receive time falls in the week, or, with no receive time, if its run folder's day does
                unreadable += int((K.day_of(tm / 1000.0) if tm is not None else d) in week)
                continue
            t = tm / 1000.0
            if K.day_of(t) in week:
                snaps.append((t, r, books.get(r["ticker"])))
    whole_legs = [s for s in snaps if K.parse_legs(s[1].get("leg_tickers", "")) is not None]
    empty = sum(1 for s in snaps if not s[1].get("leg_tickers", ""))
    cut = sum(1 for s in snaps if s[1].get("leg_tickers", "").endswith("|..."))
    out["quote_rows"] = {"in_week": len(snaps), "unreadable_left_out": unreadable, "whole_leg_string": len(whole_legs),
                         "whole_share": round(len(whole_legs) / len(snaps), 4) if snaps else None, "empty": empty, "cut": cut}
    named = set()
    for s in whole_legs:
        named |= {tk for tk, _ in K.parse_legs(s[1]["leg_tickers"])}
    whole, asked, info = load_legs(legs_run)
    if not named <= asked:
        out["verdict"] = "refused: the leg run did not ask for every leg the week names (%d missing)" % len(named - asked)
        return out
    reasons = {k: 0 for k in ("leg_unknown", "leg_other_result", "leg_against", "no_leg_for_60s", "all_legs_settled", "combo_closed")}
    elig = []
    for t, r, book in sorted(whole_legs, key=lambda s: s[0]):
        cat, uns = K.classify(t, r["leg_tickers"], r.get("legs"), iso(r.get("close_time") or ""), info)
        if cat == "eligible":
            elig.append((t, r, book, uns))
        else:
            reasons[cat] += 1
    out["not_eligible_by_reason"] = reasons
    with_ask = [e for e in elig if K.resting_ask(e[1].get("yes_ask"), e[1].get("yes_ask_size"))]
    out["eligible_snapshots"] = {"all": len(elig), "with_resting_ask": len(with_ask), "none": len(elig) - len(with_ask)}
    keys, keys_ask, first_ask = {}, set(), {}
    for t, r, book, uns in elig:
        k = (uns, K.day_of(t)); keys.setdefault(k, 0); keys[k] += 1
        if K.resting_ask(r.get("yes_ask"), r.get("yes_ask_size")):
            keys_ask.add(k)
            if k not in first_ask:
                first_ask[k] = float(r["yes_ask"])
    sets_all = {k[0] for k in keys}; sets_ask = {k[0] for k in keys_ask}
    out["independent_combos"] = {"all": len(keys), "with_resting_ask": len(keys_ask), "none": len(keys) - len(keys_ask),
                                 "distinct_sets_week": len(sets_all), "distinct_sets_with_ask": len(sets_ask)}
    out["per_day"] = {d: {"independent": sum(1 for k in keys if k[1] == d), "with_ask": sum(1 for k in keys_ask if k[1] == d)} for d in week}
    out["median_ask_cents"] = round(statistics.median([a * 100 for a in first_ask.values()]), 2) if first_ask else None
    in_book = [e for e in elig if e[2] is not None]
    book_ok = [e for e in in_book if K.book_ask(e[2].get("no_bid_px_1"), e[2].get("no_bid_sz_1"))]
    out["book_figure"] = {"eligible_in_books": len(in_book), "passing_book_test": len(book_ok), "independent_by_book": len({(e[3], K.day_of(e[0])) for e in book_ok})}
    n = len(keys_ask)
    if not whole:
        out["verdict"] = "the leg pull is not whole: not decided"
    elif n < K.KILL_MIN_COMBOS:
        out["verdict"] = "CLOSED: nothing to buy (%d independent combos with a resting ask, fewer than 30)" % n
    else:
        out["verdict"] = "SURVIVES THE COUNT (%d independent combos with a resting ask)" % n
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == "count":
        print(json.dumps(count(a[1], a[2]), indent=1))
    else:
        print(__doc__)
