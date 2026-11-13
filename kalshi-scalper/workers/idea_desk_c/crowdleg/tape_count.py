#!/usr/bin/env python3
"""CROWDLEG tape-sizing trial reader (Idea Desk C, Nov 13, 2026). Research only. [research]

Counts, for one landed run folder of the kalshi-pull job CROWDLEG_TAPE_TRIAL (sha256 165d906a...):
the number of answer pages, the number of trade rows, and the number of rows whose ticker starts with
"KXMVE" (combo markets). It reads NOTHING else: for each row it touches only the "ticker" key, never a
price, size, side, time or id. The raw rows are never read for any other purpose, and this file never
writes them anywhere. Hand case first: hand_case/ (committed at 93865e2d, before this file).

Usage: python3 -I tape_count.py <run folder holding 0001.json.gz, 0002.json.gz, ...>
A page that is not valid JSON (for example cut at the 5 MB answer cap) is counted as unreadable, and
the totals are then labelled a lower bound. 50 pages read means the window was truncated (job cap).
"""
import gzip, json, os, re, sys

PAGE = re.compile(r"^\d{4}\.json\.gz$")
MAX_PAGES = 50

def count(folder):
    pages = sorted(f for f in os.listdir(folder) if PAGE.match(f))
    rows = kx = bad = 0
    last_cursor_empty = None
    for f in pages:
        try:
            with gzip.open(os.path.join(folder, f), "rt") as fh:
                ans = json.load(fh)
            trades = ans.get("trades") or []
        except Exception:
            bad += 1
            continue
        for t in trades:
            rows += 1
            tk = t.get("ticker") if isinstance(t, dict) else None
            if isinstance(tk, str) and tk.startswith("KXMVE"):
                kx += 1
        last_cursor_empty = not ans.get("cursor")
    out = {"pages": len(pages), "rows": rows, "kxmve_rows": kx,
           "kxmve_share": round(kx / rows, 4) if rows else None, "unreadable_pages": bad}
    notes = []
    if bad: notes.append("lower bound: %d unreadable page(s)" % bad)
    if len(pages) >= MAX_PAGES and not last_cursor_empty:
        notes.append("truncated: the job's 50 page cap was reached with a cursor still open")
    out["notes"] = notes
    return out

if __name__ == "__main__":
    print(json.dumps(count(sys.argv[1]), indent=1, sort_keys=True))
