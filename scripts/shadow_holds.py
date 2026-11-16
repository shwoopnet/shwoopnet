#!/usr/bin/env python3
"""The held-out guard for the forward shadow runner (Nov 16, 2026). PURE: no network, no file read except the one table it is given, no clock.
Reads Auditor B's HOLDS table (kalshi-scalper/workers/HOLDS.json) and says whether one cell, a ticker at a time, may be read.
Rule (the table's own text): a cell is REFUSED if its time is in [from, to) of any row with status OPEN or FROZEN and its ticker matches the row. A cell in NO row is NOT cleared: any time at or after
`forward_default_deny_from` is refused unless a signed clause (a row in `clauses`, added only on Auditor B's word after the Head's approval) clears that ticker and window for that spec id. A row with a `scope` applies only to that kind of data;
the forward markets read here are not archive data, so an `archive_binary` row does not apply to them. Count-only logging (rows whose note says so) is not outcome reading and is not handled here: this guard is asked only about reads that use a result."""
import json


def load(path):
    with open(path, encoding="utf-8") as f:
        t = json.load(f)
    if not isinstance(t, dict) or not isinstance(t.get("rows"), list) or not isinstance(t.get("forward_default_deny_from"), int):
        raise SystemExit("REFUSED: the holds table has the wrong shape")
    return t


def matches(pattern, ticker):
    if pattern == "*":
        return True
    if pattern.endswith("*"):
        return ticker.startswith(pattern[:-1])
    return ticker == pattern


def clause_clears(clauses, spec_id, ticker, t):
    for c in clauses or []:
        if spec_id in (c.get("spec_ids") or []) and any(matches(p, ticker) for p in c.get("tickers", [])) and c.get("from") <= t and (c.get("to") is None or t < c["to"]):
            return True
    return False


def decide(table, spec_id, ticker, t, kind="forward"):
    """-> (allowed, reason). `t` is the market close time (epoch seconds). `kind` is 'forward' for the markets this runner reads."""
    if not isinstance(t, int) or isinstance(t, bool):
        return False, "no integer time"
    clauses = table.get("clauses") or []
    cleared = clause_clears(clauses, spec_id, ticker, t)
    for r in table["rows"]:
        if r.get("status") not in ("OPEN", "FROZEN"):
            continue
        if r.get("scope") and r["scope"] != "archive_binary":
            continue
        if r.get("scope") == "archive_binary" and kind != "archive":
            continue
        if not any(matches(p, ticker) for p in r.get("tickers", [])):
            continue
        if r["from"] <= t and (r.get("to") is None or t < r["to"]):
            if cleared:
                continue
            return False, "inside hold %s (%s)" % (r.get("id"), r.get("card"))
    if t >= table["forward_default_deny_from"] and not cleared:
        return False, "at or after the default deny line and no signed clause clears it"
    return True, "clear"
