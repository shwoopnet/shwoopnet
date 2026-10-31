"""Candle quote extraction that works on both Kalshi candle shapes (CPIMENT-RERUN, 2026-10-31).
Live candles name a price field `close_dollars`; historical candles (/historical/markets/{ticker}/candlesticks)
name it `close` (and the volume `volume`, live: `volume_fp`). Run 1 of CPI1 and MENT1 read only `close_dollars`
and so saw no quote on any historical market."""
from . import api


def quote_close(side):
    """Dollar close of a candle's yes_bid / yes_ask object, from either naming; None if absent."""
    side = side or {}
    v = side.get("close_dollars")
    return api.f(v if v is not None else side.get("close"))


def candle_volume(c):
    v = c.get("volume_fp")
    return api.f(v if v is not None else c.get("volume"))
