"""E5B (README, Pre-registration: E5B and E3C): L1 unchanged on crude oil (WTI) in E5's holdout window, which E5's design left unread. Research only: nothing here places an order.

Reads `data/alts3.sqlite` (E5's download). Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade. Usage (ONCE): python -m scalper.e5b
"""
from __future__ import annotations

from . import altseries as A
from . import e5
from . import lstrats as L

SERIES = "KXWTI15M"


def holdout(entries: list[dict]) -> list[dict]:
    """Only WTI entries on markets that closed strictly before E5's split."""
    return [e for e in entries if e["series"] == SERIES and e["close_ts"] < e5.SPLIT_TS]


def run() -> None:
    markets, vol = A.load_alts()
    es = holdout(L.hold_rule(markets, **L.L1))
    print(f"{len(markets)} markets in alts3.sqlite; {len(es)} WTI holdout entries. Signal counts first.")
    v, _ = e5.bar(es)
    A._row("KXWTI15M holdout (L1 unchanged)", es, [x for x in (vol.get((e["ticker"], e["close_ts"] - L.L1["left_s"])) for e in es) if x is not None])
    print(f"    -> {v}")


if __name__ == "__main__":
    run()
