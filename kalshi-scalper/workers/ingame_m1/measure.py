#!/usr/bin/env python3
"""In-game lag card, step 1: the MEASUREMENT (zero tries). Committed Nov 12, 2026, BEFORE the
pull INGAMELAG_M1 was dispatched. Card: workers/IDEA_DESK_B_INGAME_CARD.md.

It measures ONE thing: after a moneyline jump, how much of the spread market's move over the
next ten minutes is already in its price at the end of the first full minute after the signal
minute. No entry, no exit, no fee, no profit, no settlement result.

Kill rule for the card (as written in the card): if the spread has made 75% or more of its
ten minute move by the end of the first full minute on 80% or more of trigger events, the lag
is shorter than a one-minute bot's clock and the card is CLOSED. Fewer than 40 trigger events
with a clean move: NOT_ENOUGH_DATA.

Usage: python3 measure.py <folder of one pull run (manifest.json, 0001.json.gz ...)> <games.json>
"""
import glob
import gzip
import json
import os
import sys

# ---- pinned constants (the card carries the same values) ----
JUMP = 0.08          # moneyline mid move against three minutes earlier
LOOKBACK_MIN = 3
BAND = (0.10, 0.90)  # the moneyline mid three minutes earlier must be inside
GAP_MIN = 10         # at most one event per game per ten minutes
HORIZON_MIN = 10     # the spread's "full" move is measured to here
CLEAN_MOVE = 0.03    # the spread must have moved at least this far, the expected way, by the horizon
LAGS = (1, 2, 3, 5)
SHARE_BAR = 0.75     # share of the move already in at lag 1 ...
EVENTS_BAR = 0.80    # ... on this share of events closes the card
MIN_EVENTS = 40


def price(side):
    """A quote's closing value in dollars from a candle's yes_bid or yes_ask object."""
    if not isinstance(side, dict):
        return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""):
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        return v / 100.0 if v > 1.0 else v
    return None


def walk(node, found, hint=None):
    """Collect {ticker: [candles]} from an answer of unknown shape."""
    if isinstance(node, dict):
        tk = node.get("market_ticker") or node.get("ticker") or hint
        c = node.get("candlesticks")
        if isinstance(c, list) and c and isinstance(c[0], dict) and "end_period_ts" in c[0]:
            if tk:
                found.setdefault(tk, []).extend(c)
        for v in node.values():
            walk(v, found, tk)
    elif isinstance(node, list):
        for v in node:
            walk(v, found, hint)


def minute_mids(candles):
    out = {}
    for c in candles:
        b, a = price(c.get("yes_bid")), price(c.get("yes_ask"))
        if b is not None and a is not None and b > 0 and 0 < a <= 1 and a >= b:
            out[int(c["end_period_ts"]) // 60] = (a + b) / 2.0
    return out


def team(ticker):
    return ticker.rsplit("-", 1)[1]


def main():
    run, games = sys.argv[1], json.load(open(sys.argv[2]))
    cand = {}
    for f in sorted(glob.glob(os.path.join(run, "[0-9]*.json.gz"))):
        try:
            walk(json.load(gzip.open(f, "rt")), cand)
        except (ValueError, OSError):
            continue
    events, no_clean, games_used, games_missing = [], 0, 0, 0
    for g in games:
        a, b = g["ml"]                                    # the two moneyline tickers
        ml = minute_mids(cand.get(a, []))
        spreads = {t: minute_mids(cand.get(t, [])) for t in g["spread"]}
        if len(ml) < 30 or not any(len(v) >= 30 for v in spreads.values()):
            games_missing += 1
            continue
        games_used += 1
        last = None
        for t in sorted(ml):
            if t - LOOKBACK_MIN not in ml or (last is not None and t - last < GAP_MIN):
                continue
            before, move = ml[t - LOOKBACK_MIN], ml[t] - ml[t - LOOKBACK_MIN]
            if abs(move) < JUMP or not (BAND[0] <= before <= BAND[1]):
                continue
            last = t
            mover = team(a) if move > 0 else team(b)      # the team whose moneyline rose
            best = None
            for tk, s in spreads.items():
                need = [t - LOOKBACK_MIN, t + HORIZON_MIN] + [t + k for k in LAGS]
                if any(m not in s for m in need):
                    continue
                sign = 1.0 if team(tk).startswith(mover) else -1.0
                full = sign * (s[t + HORIZON_MIN] - s[t - LOOKBACK_MIN])
                if full < CLEAN_MOVE:
                    continue
                shares = {k: sign * (s[t + k] - s[t - LOOKBACK_MIN]) / full for k in LAGS}
                if best is None or full > best[0]:
                    best = (full, shares)                # one spread market per event: the one that moved most
            if best is None:
                no_clean += 1
                continue
            events.append({"sport": g["sport"], "game": g["game"], "minute": t, "ml_move": move, "spread_move": best[0], "shares": best[1]})
    n = len(events)
    print(f"games in the list {len(games)} | with candles {games_used} | without {games_missing}")
    print(f"trigger events with a clean spread move {n} | trigger events where the spread did not move {CLEAN_MOVE:.2f} the expected way {no_clean}")
    if n:
        for k in LAGS:
            v = sorted(e["shares"][k] for e in events)
            print(f"  share of the ten minute move already in after {k} min: median {v[n // 2]:.2f} | quartiles {v[n // 4]:.2f} to {v[(3 * n) // 4]:.2f} | events at {SHARE_BAR:.0%} or more: {sum(1 for x in v if x >= SHARE_BAR)} of {n}")
        for sp in ("NBA", "NHL", "NFL"):
            sub = [e["shares"][1] for e in events if e["sport"] == sp]
            if sub:
                print(f"  {sp}: events {len(sub)} | at {SHARE_BAR:.0%} or more after 1 min: {sum(1 for x in sub if x >= SHARE_BAR)}")
    if n < MIN_EVENTS:
        print(f"VERDICT: NOT_ENOUGH_DATA ({n} events, need {MIN_EVENTS})")
        return
    hit = sum(1 for e in events if e["shares"][1] >= SHARE_BAR) / n
    print("VERDICT: " + (f"CARD CLOSED (the lag is under a minute on {hit:.0%} of events)" if hit >= EVENTS_BAR else f"SURVIVES step 1 ({hit:.0%} of events had {SHARE_BAR:.0%} of the move in after one minute; the bar to close was {EVENTS_BAR:.0%})"))


if __name__ == "__main__":
    main()
