#!/usr/bin/env python3
"""MADE-UP edge games for endnet.py (see EXPECTED_DECISIONS_edge.md, committed before this file). Usage: edge_set_MADE_UP_DATA.py <out json>"""
import json
import sys
from datetime import datetime, timezone

D0 = int(datetime(2026, 11, 20, 2, 0, tzinfo=timezone.utc).timestamp())


def m(end, period, left, h, a):
    return {"end_ts": end, "period": period, "secs_left": left, "home": h, "away": a}


def cd(end, bid, ask):
    return {"end_ts": end, "bid": bid, "ask": ask}


def g(k, name, mins, strikes):
    close = D0 + k * 86400
    return {"game": name, "close_ts": close, "minutes": mins, "strikes": strikes}


def build():
    out = []
    def one(k, name, floor, bid, ask, res, left=170, h=3, a=2, period=3, candle_shift=0):
        close = D0 + k * 86400
        e = close - 600
        mins = [m(e - 60, 3, 240, h, a), m(e, period, left, h, a)]
        out.append(g(k, name, mins, [{"ticker": name + "-T", "floor_strike": floor, "result": res, "candles": [cd(e + candle_shift, bid, ask)]}]))
    one(1, "e01_exactly_180s", 5.5, 28, 30, "yes", left=180)
    one(2, "e02_181s", 5.5, 28, 30, "yes", left=181)
    one(3, "e03_line_one_above", 6.0, 28, 30, "yes")
    one(4, "e04_line_just_inside", 5.9, 28, 30, "yes")
    one(5, "e05_line_below_total", 4.5, 28, 30, "yes")
    close = D0 + 6 * 86400; e = close - 600
    out.append(g(6, "e06_two_strikes", [m(e - 60, 3, 240, 3, 2), m(e, 3, 170, 3, 2)],
                 [{"ticker": "e06-A", "floor_strike": 6.5, "result": "no", "candles": [cd(e, 8, 10)]},
                  {"ticker": "e06-B", "floor_strike": 5.5, "result": "yes", "candles": [cd(e, 28, 30)]}]))
    one(7, "e07_ask_14", 5.5, 12, 14, "yes")
    one(8, "e08_ask_15_spread_4", 5.5, 11, 15, "no")
    one(9, "e09_ask_46", 5.5, 43, 46, "yes")
    one(10, "e10_spread_5", 5.5, 10, 15, "yes")
    one(11, "e11_void", 5.5, 28, 30, "void")
    one(12, "e12_result_null", 5.5, 28, 30, None)
    one(13, "e13_candle_one_minute_early", 5.5, 28, 30, "yes", candle_shift=-60)
    close = D0 + 14 * 86400; e = close - 600
    out.append(g(14, "e14_one_look", [m(e - 60, 3, 240, 3, 2), m(e, 3, 170, 3, 2), m(e + 60, 3, 110, 3, 2)],
                 [{"ticker": "e14-T", "floor_strike": 5.5, "result": "yes", "candles": [cd(e + 60, 28, 30)]}]))
    close = D0 + 15 * 86400; e = close - 600
    out.append(g(15, "e15_tie_then_one_goal", [m(e - 60, 3, 240, 2, 2), m(e, 3, 170, 3, 3), m(e + 60, 3, 120, 3, 2)],
                 [{"ticker": "e15-T", "floor_strike": 5.5, "result": "no", "candles": [cd(e + 60, 28, 30)]}]))
    one(16, "e16_overtime", 5.5, 28, 30, "yes", left=100, period=4)
    one(17, "e17_away_leads", 5.5, 28, 30, "yes", h=2, a=3)
    one(18, "e18_spread_4_mid", 5.5, 36, 40, "no")
    return out


if __name__ == "__main__":
    json.dump(build(), open(sys.argv[1], "w"))
