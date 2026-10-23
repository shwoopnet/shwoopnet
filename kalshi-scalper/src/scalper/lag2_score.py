"""LAG2-F scoring (README, Pre-registration: LAG2): scores the build session's log-only rows (studies/LAG2_LOGONLY_REQUEST_2026-10-23.md) at the quote level. Research only.
A row is a JSON object per line: {"ticker", "left" (120, 90 or 60), "ts" (epoch seconds), "signal" ("yes", "no" or null), "yesBid", "yesAsk"}.
The first row with a signal per market is the trade, bought at the logged ask of its side (yes at yesAsk, no at 1 - yesBid), held to settlement; the result is read from
`results` ({ticker: "yes" or "no"}). Same claim, bars and verdict words as LAG2 (imported from scalper.lag2).
Usage: python -m scalper.lag2_score ROWS.jsonl RESULTS.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from . import lag2 as T
from . import lstrats as L


def trades(rows: list[dict], results: dict[str, str]) -> list[dict]:
    first: dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: (r["ts"], -r["left"])):
        if r.get("signal") in ("yes", "no") and r["ticker"] not in first and results.get(r["ticker"]) in ("yes", "no"):
            first[r["ticker"]] = r
    out = []
    for tk, r in first.items():
        side = r["signal"]
        price = r["yesAsk"] if side == "yes" else round(1 - r["yesBid"], 4)
        yes = results[tk] == "yes"
        out.append({"day": datetime.fromtimestamp(r["ts"], timezone.utc).strftime("%Y-%m-%d"), "close_ts": r["ts"], "net": L.net(side, price, yes), "stress": L.net(side, price, yes, L.STRESS)})
    return out


def main(argv: list[str]) -> None:
    if len(argv) < 3:
        print(__doc__)
        return
    rows = [json.loads(x) for x in open(argv[1]) if x.strip()]
    results = json.load(open(argv[2]))
    t = trades(rows, results)
    j = T.judge(t)
    print(f"LAG2-F: {j['verdict']}; rows {len(rows)}, trades {len(t)} on {j.get('days', 0)} days" + (f"; mean {100 * j['mean']:+.2f}c z {j['z']:+.2f} PF {j['pf']:.2f}" if "mean" in j else ""))


if __name__ == "__main__":
    main(sys.argv)
