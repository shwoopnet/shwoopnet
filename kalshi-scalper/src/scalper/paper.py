"""Paper engine: replay recorded books and price fills honestly.

Rules enforced here because backtests in this project have been flattered
before by exactly these shortcuts:
- A signal on snapshot i fills on snapshot i+1 or later, never on i.
- Buys fill at the ASK and exits at the BID. Never the mid.
- Size is capped by the displayed size at the touch.
- Fees are charged on both legs, and results are also shown with fees 20%
  higher, because the fee rate is not yet verified.
- Every run increments a variants counter. Best-of-N crosses any bar by luck,
  so the number of things tried is part of the result.

A strategy is fn(history) -> None | (side, my_prob), where history is the list
of snapshots for one market so far (oldest first) and side is "yes" or "no".
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .fees import taker_fee
from .recorder import DB

COUNTER = Path(DB).parent / "variants_tried.json"
Snap = tuple  # (ts, yes_bid, yes_bid_sz, yes_ask, yes_ask_sz)


@dataclass
class Trade:
    ticker: str
    side: str
    contracts: int
    entry: float
    exit: float
    gross: float
    fees: float

    @property
    def net(self) -> float:
        return self.gross - self.fees


def _px(snap: Snap, side: str, buying: bool) -> float:
    ts, bid, bsz, ask, asz = snap
    if side == "yes":
        return ask if buying else bid
    return (1 - bid) if buying else (1 - ask)   # a NO buy lifts the YES bid


def _size(snap: Snap, side: str) -> float:
    ts, bid, bsz, ask, asz = snap
    return asz if side == "yes" else bsz


def run(history_by_ticker: dict, strategy, hold_s: float, contracts: int = 10,
        fee_mult: float = 1.0) -> list[Trade]:
    trades = []
    for ticker, snaps in history_by_ticker.items():
        i = 0
        while i < len(snaps) - 1:
            sig = strategy(snaps[: i + 1])
            if not sig:
                i += 1
                continue
            side, _ = sig
            fill = snaps[i + 1]                     # strictly later bar
            entry = _px(fill, side, True)
            n = min(contracts, int(_size(fill, side) or 0))
            if n <= 0 or not 0 < entry < 1:
                i += 1
                continue
            j = next((k for k in range(i + 2, len(snaps)) if snaps[k][0] - fill[0] >= hold_s), None)
            if j is None:
                break                                # unresolved: do not count it
            exit_ = _px(snaps[j], side, False)
            fees = (taker_fee(entry, n, fee_mult) + taker_fee(exit_, n, fee_mult)) if exit_ > 0 else 0.0
            trades.append(Trade(ticker, side, n, entry, exit_, (exit_ - entry) * n, fees))
            i = j                                    # one position at a time per market
        # positions are never carried past the last snapshot
    return trades


def load() -> dict:
    db = sqlite3.connect(DB)
    out: dict = {}
    for t, ts, b, bs, a, as_ in db.execute(
            "SELECT ticker,ts,yes_bid,yes_bid_sz,yes_ask,yes_ask_sz FROM snap "
            "WHERE yes_bid IS NOT NULL AND yes_ask IS NOT NULL ORDER BY ticker,ts"):
        out.setdefault(t, []).append((ts, b, bs, a, as_))
    return out


def report(trades: list[Trade], hold_s: float, name: str) -> dict:
    tried = json.loads(COUNTER.read_text()) if COUNTER.exists() else {"n": 0, "names": []}
    tried["n"] += 1
    tried["names"].append(f"{name}@{hold_s}s")
    COUNTER.write_text(json.dumps(tried))
    n = len(trades)
    net = sum(t.net for t in trades)
    stress = sum(t.gross - t.fees * 1.2 for t in trades)
    print(f"{name} hold={hold_s}s trades={n} net=${net:.2f} "
          f"net/trade=${net / n if n else 0:.4f} stressed(fees x1.2)=${stress:.2f} "
          f"| variants tried so far: {tried['n']}")
    return {"n": n, "net": net, "stress": stress, "variants": tried["n"]}
