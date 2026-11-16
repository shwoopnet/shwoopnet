#!/usr/bin/env python3
"""The held-out guard for the forward shadow runner (Nov 16, 2026). PURE: no network, no file read except the one table it is given, no clock.
Reads Auditor B's HOLDS table (kalshi-scalper/workers/HOLDS.json) and says whether one cell, a ticker at a time, may be read.
Rule (the table's own text): a cell is REFUSED if its time is in [from, to) of any row with status OPEN or FROZEN and its ticker matches the row. A cell in NO row is NOT cleared: any time at or after
`forward_default_deny_from` is refused unless a signed clause (the S1 row of the table, Auditor B's clause approved by the Head on Nov 16, 2026) clears that ticker and window for a shadow-list spec named by its sha256. A row with a `scope` applies only to that kind of data;
the forward markets read here are not archive data, so an `archive_binary` row does not apply to them. Count-only logging (rows whose note says so) is not outcome reading and is not handled here: this guard is asked only about reads that use a result."""
import json, re


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


def s1_overrides(table):
    """-> (ids of the rows the S1 clearance overrides, whether it also clears the default deny). S1 is Auditor B's clause for the shadow runner (the Head approved it Nov 16, 2026); it is read from the table, never assumed."""
    for r in table["rows"]:
        if r.get("id") == "S1" and r.get("status") == "APPROVED" and r.get("kind") == "clearance":
            text = " ".join(r.get("overrides") or [])
            return set(re.findall(r"H\d\d", text)), "forward_default_deny" in text
    return set(), False


def s1_applies(spec, ticker, t):
    """The S1 terms: only a shadow-list spec (named by its sha256 in the list) may read, only its own series, only from that list version's start_utc."""
    if not spec or not isinstance(spec.get("sha256"), str) or len(spec["sha256"]) != 64:
        return False
    series = ticker.split("-")[0]
    return series in (spec.get("series") or []) and isinstance(spec.get("start_utc"), int) and t >= spec["start_utc"]


def decide(table, spec, ticker, t, kind="forward"):
    """-> (allowed, reason). `spec` is {sha256, series: [..], start_utc: epoch} of the shadow-list spec reading the cell (or None for any other reader). `t` is the market close time (epoch seconds)."""
    if not isinstance(t, int) or isinstance(t, bool):
        return False, "no integer time"
    over, over_default = s1_overrides(table)
    s1 = s1_applies(spec, ticker, t)
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
            if s1 and r.get("id") in over:
                continue
            return False, "inside hold %s (%s)" % (r.get("id"), r.get("card"))
    if t >= table["forward_default_deny_from"] and not (s1 and over_default):
        return False, "at or after the default deny line and no signed clause clears it"
    return True, "clear"
