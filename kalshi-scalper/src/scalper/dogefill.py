"""DOGEFILL: Dogecoin fill rate before and after the 3 to 5 contract deploy (owner, via the main session, 2026-10-29). Information only.
Usage: python -m scalper.dogefill run   (nightly from `drift run`; aggregates to workers/DOGEFILL.md; raw rows stay in the scratchpad)
Depth at the touch is not in the report endpoint's rows; when recorder R6's files exist on quote-data (book15r6/), the visible
size at the price a 5 contract order would hit is read from the book row nearest each attempt.
"""
from __future__ import annotations

import csv
import gzip
import io
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .drift import live_report
from .paths import DATA_DIR

DEPLOY = datetime(2026, 10, 29, 21, 5, tzinfo=timezone.utc).timestamp()   # main session: Dogecoin 3 to 5 at about 21:05 UTC
OUT = DATA_DIR.parent / "workers" / "DOGEFILL.md"
CT = ZoneInfo("America/Chicago")
FLAG_RATE, FLAG_N = 0.60, 20


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def r6_depth(attempts):
    """For each attempt, the visible size at the side's touch in the R6 book row nearest before the send time (None if no file)."""
    root = DATA_DIR.parent
    try:
        subprocess.run(["git", "fetch", "-q", "origin", "quote-data"], cwd=root, check=True, capture_output=True)
        files = [p for p in subprocess.run(["git", "ls-tree", "-r", "--full-tree", "--name-only", "origin/quote-data"], cwd=root, check=True,
                                           capture_output=True).stdout.decode().split() if p.startswith("book15r6/") and "book" in p.split("/")[-1]]
    except Exception:
        return {}
    rows = []
    for f in files:
        raw = subprocess.run(["git", "show", f"origin/quote-data:{f}"], cwd=root, capture_output=True).stdout
        try:
            text = gzip.decompress(raw).decode()
        except Exception:
            continue
        for r in csv.DictReader(io.StringIO(text)):
            if r.get("ticker", "").startswith("KXDOGE15M-"):
                rows.append(r)
    if not rows:
        return {}
    by_tk = defaultdict(list)
    for r in rows:
        t = r.get("t_send_ms") or r.get("t_recv_ms")
        if t:
            by_tk[r["ticker"]].append((int(t) / 1000, r))
    out = {}
    for a in attempts:
        cand = [x for x in by_tk.get(a["ticker"], []) if x[0] <= a["t"]]
        if not cand:
            continue
        _, r = max(cand, key=lambda x: x[0])
        # a YES buy lifts the NO bids (YES ask = 1 - best NO bid); a NO buy lifts the YES bids
        lvl = "no_bid_1" if a["side"] == "yes" else "yes_bid_1"
        size = r.get(lvl + "_size") or r.get(lvl.replace("_1", "1") + "_size")
        out[a["key"]] = float(size) if size not in (None, "") else None
    return out


def run():
    d = live_report()
    att = []
    for x in d.get("orders", []):
        if not x.get("ticker", "").startswith("KXDOGE15M-"):
            continue
        t = ts(x["ts"])
        att.append(dict(key=x["ts"] + x["ticker"], t=t, ticker=x["ticker"], side=x.get("side"), lead=x.get("entryLead") or "untagged",
                        filled=(x.get("count") or 0) > 0, count=x.get("count") or 0, after=t >= DEPLOY))
    depth = r6_depth([a for a in att if a["after"]])
    lines = [f"## {datetime.now(CT):%Y-%m-%d %H:%M} CT (deploy marker 2026-10-29 21:05 UTC, Dogecoin 3 to 5 contracts)", ""]
    flags = []
    for label, grp in (("before", [a for a in att if not a["after"]]), ("after", [a for a in att if a["after"]])):
        n = len(grp); nf = sum(1 for a in grp if not a["filled"])
        sizes = defaultdict(int)
        for a in grp:
            if a["filled"]:
                sizes[a["count"]] += 1
        streak = cur = 0
        for a in sorted(grp, key=lambda a: a["t"]):
            cur = cur + 1 if not a["filled"] else 0; streak = max(streak, cur)
        by_lead = defaultdict(lambda: [0, 0])
        for a in grp:
            by_lead[a["lead"]][0] += 1; by_lead[a["lead"]][1] += not a["filled"]
        lines.append(f"- {label}: attempts {n}, no fill {nf} ({100 * nf / max(1, n):.0f}%), longest no-fill streak {streak}, filled sizes {dict(sorted(sizes.items()))}, by lead "
                     + ", ".join(f"{k} {v[1]}/{v[0]} no fill" for k, v in sorted(by_lead.items())))
        if label == "after" and n >= FLAG_N and nf / n >= FLAG_RATE:
            flags.append(f"Dogecoin no-fill rate after the deploy {100 * nf / n:.0f}% over {n} attempts (flag at {100 * FLAG_RATE:.0f}% over {FLAG_N}+)")
    if depth:
        vals = [v for v in depth.values() if v is not None]
        under = sum(1 for v in vals if v < 5)
        lines.append(f"- touch depth from recorder R6 for after-deploy attempts: {len(vals)} matched, size at the touch under 5 contracts in {under} ({100 * under / max(1, len(vals)):.0f}%), median {sorted(vals)[len(vals) // 2] if vals else 0}")
    else:
        lines.append("- touch depth: no R6 book rows for these attempts yet (R6 started 2026-10-29 22:03 UTC; the report carries no depth fields)")
    lines.append(f"- **Flags:** {'; '.join(flags) if flags else 'none'}")
    lines.append("")
    old = OUT.read_text() if OUT.exists() else "# DOGEFILL: Dogecoin fill rate around the 3 to 5 contract deploy (newest first; aggregates only; information)\n\n"
    head, _, rest = old.partition("\n\n")
    OUT.write_text(head + "\n\n" + "\n".join(lines) + "\n" + rest)
    print("\n".join(lines))
    return flags


if __name__ == "__main__":
    {"run": run}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
