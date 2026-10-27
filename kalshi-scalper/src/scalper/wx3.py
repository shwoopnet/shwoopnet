"""WX3 (README, Pre-registration: WX3): are the daily-high-temperature ladders internally consistent? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.wx3 run   (once; a second run is refused)
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict

from . import api
from .paths import DATA_DIR

SERIES = ["KXHIGHNY", "KXHIGHMIA", "KXHIGHAUS", "KXHIGHDEN", "KXHIGHLAX", "KXHIGHPHIL", "KXHIGHHOU", "KXHIGHTDC", "KXHIGHTSEA", "KXHIGHTATL"]
DAYS, MIN_GAP, MIN_HITS, MIN_EVENTS_HIT, MIN_EVENTS = 30, 0.010, 30, 10, 30
RESULT = DATA_DIR / "wx3_result.txt"


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def gaps(asks: list[float], bids: list[float]) -> tuple[float, float]:
    """(buy-all gap, sell-all gap): profit per full set of buckets after fees; positive is a lock."""
    return 1.0 - (sum(asks) + sum(fee(a) for a in asks)), (sum(bids) - sum(fee(b) for b in bids)) - 1.0


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    now = int(time.time()); lo = now - DAYS * 86400
    events = defaultdict(list)
    for s in SERIES:
        n = 0
        for m in api.settled_markets(s, lo, now):
            events[m["event_ticker"]].append(m); n += 1
        print(s, n, "markets", flush=True)
    scanned = hits_b = hits_s = 0
    hit_events, gaps_b, gaps_s, hours_all = set(), [], [], 0
    for ev, ms in events.items():
        if len(ms) < 3:
            continue
        close_ts = max(int(time.mktime(time.strptime(m["close_time"][:19], "%Y-%m-%dT%H:%M:%S"))) - time.timezone for m in ms)
        tks = [m["ticker"] for m in ms]
        try:
            d = api._get("/markets/candlesticks", {"market_tickers": ",".join(tks), "start_ts": close_ts - 48 * 3600, "end_ts": close_ts, "period_interval": 60})
        except Exception as e:
            print("skip", ev, e, flush=True); continue
        per = {m["market_ticker"]: {c["end_period_ts"]: c for c in m.get("candlesticks", [])} for m in d.get("markets", [])}
        if len(per) < len(tks):
            continue
        scanned += 1
        stamps = set.intersection(*[set(v) for v in per.values()]) if per else set()
        for t in sorted(stamps):
            asks, bids, traded = [], [], True
            for tk in tks:
                c = per[tk][t]
                a, b = api.f((c.get("yes_ask") or {}).get("close_dollars")), api.f((c.get("yes_bid") or {}).get("close_dollars"))
                if a is None or b is None or a <= 0:
                    traded = False; break
                if not api.f(c.get("volume_fp")):
                    traded = False
                asks.append(a); bids.append(b)
            if len(asks) != len(tks):
                continue
            if traded:
                hours_all += 1
                gb, gs = gaps(asks, bids)
                if gb >= MIN_GAP: hits_b += 1; hit_events.add(ev); gaps_b.append(gb)
                if gs >= MIN_GAP: hits_s += 1; hit_events.add(ev); gaps_s.append(gs)
        time.sleep(0.15)
    hits = hits_b + hits_s
    avg = (sum(gaps_b + gaps_s) / hits) if hits else 0.0
    if scanned < MIN_EVENTS:
        v = "NOT_ENOUGH_DATA"
    elif hits >= MIN_HITS and len(hit_events) >= MIN_EVENTS_HIT and avg >= MIN_GAP:
        v = "NOT_YET_FALSIFIED"
    else:
        v = "FALSIFIED"
    out = (f"WX3 {v}: {scanned} events scanned, {hours_all} hours with every bucket traded, BUY_ALL hits {hits_b}, SELL_ALL hits {hits_s}, "
           f"events with a hit {len(hit_events)}, average locked gap {100 * avg:.2f}c")
    RESULT.write_text(out + "\n"); print(out)


if __name__ == "__main__":
    main(sys.argv)
