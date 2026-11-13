#!/usr/bin/env python3
"""Settlement clauses and how many events each touched, from lists ALREADY landed. No request, no price.
Reads, per series, the rules text of each market and its result field (to tell a set-price settlement from yes or no).
It opens only development-window answers: any manifest row whose id starts with hist_ is skipped, and a run folder
in a HELDOUT_ path is refused.

Usage: python3 -I clause_count.py <lists run folder> [<lists run folder> ...]
"""
import collections
import gzip
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from deskb_guard import refuse_all, refuse_heldout  # noqa: E402

KEY = re.compile(r"fair|\$0\.50|postpon|cancel|forfeit|walkover|withdraw|retire|abandon|does not occur|not started|suspend|disqualif|inactive|never takes|protected|tie|draw", re.I)


def ts(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text or "") if s.strip()]


def generic(s):
    """Replace the match-specific middle of a sentence so the same clause counts once across markets."""
    s = re.sub(r"the [^.]{0,160}? (professional tennis match|CS2 match|Dota 2 match|match|game)\b[^,.]{0,120}", r"the <this \1>", s, count=1)
    s = re.sub(r"\b[A-Z][a-z]{2} \d{1,2}, \d{4}( at \d{1,2}:\d{2} [AP]M [A-Z]{2,4})?", "<date>", s)
    return re.sub(r"\s+", " ", s)


def main():
    refuse_all()
    series = collections.OrderedDict()
    for run in sys.argv[1:]:
        refuse_heldout(run)
        man = json.load(open(os.path.join(run, "manifest.json")))
        for row in man.get("rows", []):
            sid = row.get("params", {}).get("series_ticker")
            if not sid or str(row.get("id", "")).startswith("hist_") or row.get("status") != 200 or "/markets" not in row.get("path", "/markets"):
                continue
            try:
                body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
            except Exception:
                continue
            d = series.setdefault(sid, {"events": {}, "clauses": collections.Counter(), "markets": 0, "runs": set()})
            d["runs"].add(os.path.basename(os.path.dirname(os.path.abspath(run))) + "/" + os.path.basename(os.path.abspath(run)))
            for m in body.get("markets", []) if isinstance(body, dict) else []:
                tk, ev = m.get("ticker", ""), m.get("event_ticker", "")
                if not tk.startswith(sid + "-") or tk in d["events"].get(ev, {}):
                    continue
                d["events"].setdefault(ev, {})[tk] = m
                d["markets"] += 1
                for s in sentences((m.get("rules_primary") or "") + "\n" + (m.get("rules_secondary") or "")):
                    if KEY.search(s) and not s.startswith("Kalshi is not affiliated"):
                        d["clauses"][generic(s)] += 1
    for sid, d in series.items():
        ev = d["events"]
        closes = sorted(ts(m["close_time"]) for ms in ev.values() for m in ms.values() if m.get("close_time"))
        day = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")  # noqa: E731
        allset = [e for e, ms in ev.items() if all((m.get("result") or "").lower() not in ("yes", "no") for m in ms.values())]
        part = [e for e, ms in ev.items() if e not in allset and any((m.get("result") or "").lower() not in ("yes", "no") for m in ms.values())]
        half = other = 0
        for e in allset:
            vals = []
            for m in ev[e].values():
                try:
                    vals.append(float(m.get("settlement_value_dollars")))
                except (TypeError, ValueError):
                    vals.append(None)
            if vals and all(v is not None and abs(v - 0.5) < 1e-9 for v in vals):
                half += 1
            else:
                other += 1
        print("== %s | events %d | markets %d | closes %s to %s | from %s" % (sid, len(ev), d["markets"], day(closes[0]) if closes else "?", day(closes[-1]) if closes else "?", ", ".join(sorted(d["runs"]))))
        print("   events with EVERY contract settled at a set price (not yes or no): %d (%.1f%%) | of those, every side at exactly 0.50: %d, at another price: %d | events with SOME contracts at a set price: %d"
              % (len(allset), 100.0 * len(allset) / len(ev) if ev else 0, half, other, len(part)))
        for s, n in d["clauses"].most_common(12):
            print("   [%d of %d markets] %s" % (n, d["markets"], s[:420]))


if __name__ == "__main__":
    main()
