#!/usr/bin/env python3
"""MADE-UP games for endnet.py. Nothing here came from Kalshi. Usage: make_fixtures_MADE_UP_DATA.py <out dir>
  hand       12 games, one per rule edge, each hand-checkable (see EXPECTED_hand.md)
  pass       160 entries, a high win rate: survives development
  fail       160 entries, a low win rate: falsified
  outside    one game closing on 2026-12-15: the run must stop
"""
import json
import os
import sys
from datetime import datetime, timezone

D0 = int(datetime(2026, 11, 20, 2, 0, tzinfo=timezone.utc).timestamp())


def game(name, close, mins, strikes):
    return {"game": name, "close_ts": close, "minutes": mins, "strikes": strikes}


def m(end, period, left, home, away):
    return {"end_ts": end, "period": period, "secs_left": left, "home": home, "away": away}


def strike(tk, floor, result, candles):
    return {"ticker": tk, "floor_strike": floor, "result": result, "candles": candles}


def cd(end, bid, ask):
    return {"end_ts": end, "bid": bid, "ask": ask}


def simple(name, close, home, away, floor, bid, ask, result, period=3, left=170, candle_at=0):
    e = close - 600
    return game(name, close, [m(e - 60, 3, 240, home, away), m(e, period, left, home, away)],
                [strike(name + "-T", floor, result, [cd(e + candle_at, bid, ask)])])


def hand():
    g = []
    t = D0
    def nxt():
        nonlocal t
        t += 86400
        return t
    g.append(simple("g01_win", nxt(), 3, 2, 5.5, 28, 30, "yes"))             # pay 31, fee 1.5c, pnl +0.675
    g.append(simple("g02_loss", nxt(), 3, 2, 5.5, 38, 40, "no"))             # pay 41, fee 1.7c, pnl -0.427
    g.append(simple("g03_two_goals", nxt(), 4, 2, 6.5, 28, 30, "yes"))        # diff 2: no state minute
    g.append(simple("g04_ask_50", nxt(), 3, 2, 5.5, 48, 50, "yes"))           # ask out of band
    g.append(simple("g05_spread_6", nxt(), 3, 2, 5.5, 24, 30, "no"))          # spread 6
    g.append(simple("g06_no_candle", nxt(), 3, 2, 5.5, 28, 30, "no", candle_at=60))   # candle not at the entry minute
    g.append(simple("g07_two_away", nxt(), 3, 2, 6.5, 28, 30, "no"))          # strike needs two goals
    g.append(simple("g08_period2", nxt(), 3, 2, 5.5, 28, 30, "no", period=2)) # not the third period
    g.append(simple("g09_tied", nxt(), 2, 2, 4.5, 28, 30, "no"))              # tied
    g.append(simple("g10_int_line_ask15_spread4", nxt(), 2, 1, 3.0, 11, 15, "yes"))   # floor == total: qualifies; ask 15, spread 4: pay 16, fee 1.0c, pnl +0.830
    g.append(simple("g11_ask45", nxt(), 1, 2, 3.5, 41, 45, "no"))             # ask 45: pay 46, fee 1.8c, pnl -0.478
    g.append(simple("g12_late_game_check", nxt(), 3, 4, 7.5, 0, 12, "no"))   # bid 0: not two-sided
    return g


def many(kind):
    g = []
    t = D0
    wins = 0
    for i in range(160):
        t += 12600 + (i % 7) * 60
        win = (i % 3 != 0) if kind == "pass" else (i % 4 == 0)
        g.append(simple("m%03d" % i, t, 3, 2, 5.5, 28, 30, "yes" if win else "no"))
    return g


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    sets = {"hand": hand(), "pass": many("pass"), "fail": many("fail"),
            "outside": [simple("o1", int(datetime(2026, 12, 15, 1, 0, tzinfo=timezone.utc).timestamp()), 3, 2, 5.5, 28, 30, "yes")]}
    for k, v in sets.items():
        json.dump(v, open(os.path.join(out, k + ".json"), "w"))


if __name__ == "__main__":
    main()
