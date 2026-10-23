"""Refreshes data/fresh.sqlite (1 minute candles of the 18 pooled series) from Kalshi's public API, resumable.
Usage: python -m scalper.fresh_update      (run before `python -m scalper.fwd_reads look` or `read`; public data, no key)
"""
from __future__ import annotations

from pathlib import Path

from . import backfill as b
from .fwd_reads import POOL18


def main() -> None:
    b.DB = Path("data/fresh.sqlite")
    b.SERIES = tuple(POOL18)
    b.BATCH = 25
    b.PAUSE_S = 0.4
    b.run_range(10, 0)


if __name__ == "__main__":
    main()
