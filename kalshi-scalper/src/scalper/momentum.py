"""M1, early window momentum (rules fixed in the README before this file existed).

Signal: YES mid at the close of minute 5 minus YES mid at the close of minute 1. A move of at least THRESH up is UP, at least THRESH down is
DOWN. Entry on the NEXT candle (minute 6) at the ask of the side bought (YES at its ask, NO at 1 minus the YES bid), exit exactly HOLD_MIN minutes
later at that side's bid, a taker fee on both legs. An exit candle with no usable two sided quote DROPS the observation and it is counted.

Judged by the common bar (scalps.judge): n at least 300, day clustered z at least 2.1, positive in both halves, positive with fees x1.2.
Verdicts are only FALSIFIED, NOT_YET_FALSIFIED and NOT_ENOUGH_DATA. Nothing in a signature below reads a result.

Usage: python -m scalper.momentum
"""
from __future__ import annotations

import random
import sqlite3
from datetime import datetime, timezone

from .analyze import valid_quote
from .paths import DB
from .scalps import STRESS, Z_BAR, MIN_N, fee, judge
from .calibration import cluster_mean_z

SIGNAL_MIN = 5       # the candle that closes the 5th minute
BASE_MIN = 1         # the candle that closes the 1st minute
THRESH = 0.05
HOLD_MIN = 3
CUTS_THRESH = (0.03, 0.08)
CUTS_HOLD = (2, 5)
NULL_REPS = 500


def load() -> list[dict]:
    """Every settled market of both series: {ticker, series, open, close, res, book: {end_ts: (bid_c, ask_c)}}."""
    db = sqlite3.connect(DB)
    ms = {t: {"ticker": t, "series": s, "open": o, "close": c, "res": r, "book": {}}
          for t, s, o, c, r in db.execute("SELECT ticker, series, open_ts, close_ts, result FROM market") if r in ("yes", "no")}
    for t, end, bc, ac in db.execute("SELECT ticker, end_ts, bid_c, ask_c FROM candle"):
        if t in ms:
            ms[t]["book"][end] = (bc, ac)
    return sorted(ms.values(), key=lambda m: m["close"])


def day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def yes_mid(q: tuple) -> float:
    return (q[0] + q[1]) / 2


def side_ask(side: str, q: tuple) -> float:
    return q[1] if side == "yes" else round(1 - q[0], 4)


def side_bid(side: str, q: tuple) -> float:
    return q[0] if side == "yes" else round(1 - q[1], 4)


def side_mid(side: str, q: tuple) -> float:
    return yes_mid(q) if side == "yes" else 1 - yes_mid(q)


def signal(book: dict, open_ts: int, thresh: float):
    """'yes' (UP), 'no' (DOWN) or None, plus the reason for None: 'quote' if a signal candle is missing or unusable, else 'flat'."""
    a, b = book.get(open_ts + 60 * BASE_MIN), book.get(open_ts + 60 * SIGNAL_MIN)
    if a is None or b is None or not valid_quote(*a) or not valid_quote(*b):
        return None, "quote"
    d = round(yes_mid(b) - yes_mid(a), 4)
    if d >= thresh - 1e-9:
        return "yes", ""
    if d <= -thresh + 1e-9:
        return "no", ""
    return None, "flat"


def trade(m: dict, thresh: float, hold_min: int | None) -> dict:
    """One market. Returns {'status': ...} where status is no_signal_quote, flat, no_entry_quote, dropped, or traded.
    hold_min None means hold to settlement. The entry candle is strictly after the signal candle."""
    side, why = signal(m["book"], m["open"], thresh)
    if side is None:
        return {"status": "no_signal_quote" if why == "quote" else "flat"}
    entry_end = m["open"] + 60 * (SIGNAL_MIN + 1)
    q = m["book"].get(entry_end)
    if q is None or not valid_quote(*q):
        return {"status": "no_entry_quote"}
    price = side_ask(side, q)
    out = {"ticker": m["ticker"], "series": m["series"], "day": day(m["close"]), "close_ts": m["close"], "side": side,
           "price": price, "mid": side_mid(side, q), "entry_end": entry_end}
    if hold_min is None:
        won = (m["res"] == side)
        for k, mult in (("net", 1.0), ("stress", STRESS), ("gross", 0.0)):
            out[k] = (1.0 if won else 0.0) - price - fee(price, mult)
        out["status"] = "traded"
        return out
    x = m["book"].get(entry_end + 60 * hold_min)
    if x is None or not valid_quote(*x):
        return {"status": "dropped", "side": side, "price": price, "series": m["series"]}
    bid = side_bid(side, x)
    out["exit"] = bid
    out["exit_mid"] = side_mid(side, x)
    out["exit_half_spread"] = bid_half_spread(x)
    for k, mult in (("net", 1.0), ("stress", STRESS), ("gross", 0.0)):
        out[k] = bid - fee(bid, mult) - price - fee(price, mult)
    out["status"] = "traded"
    return out


def bid_half_spread(q: tuple) -> float:
    return (q[1] - q[0]) / 2


def run(markets: list[dict], thresh: float = THRESH, hold_min: int | None = HOLD_MIN) -> dict:
    trades, counts = [], {"no_signal_quote": 0, "flat": 0, "no_entry_quote": 0, "dropped": 0}
    dropped = []
    for m in markets:
        t = trade(m, thresh, hold_min)
        if t["status"] == "traded":
            trades.append(t)
        else:
            counts[t["status"]] += 1
            if t["status"] == "dropped":
                dropped.append(t)
    return {"trades": sorted(trades, key=lambda t: t["close_ts"]), "counts": counts, "dropped": dropped}


def verdict(trades: list[dict]) -> tuple[str, dict | None]:
    if len(trades) < MIN_N:
        return "NOT_ENOUGH_DATA", None
    mid = sorted(t["close_ts"] for t in trades)[len(trades) // 2]
    v, summ = judge({"x": [(t["day"], t["close_ts"], t["net"], t["stress"]) for t in trades]}, mid)
    return v, summ[0]


def null_settle(trades: list[dict], seed: int) -> float:
    """Hold to settlement on a fair market: each entry wins with probability equal to the side's mid at its own entry candle."""
    rng = random.Random(seed)
    return sum((1.0 if rng.random() < t["mid"] else 0.0) - t["price"] - fee(t["price"]) for t in trades) / len(trades)


def null_roundtrip(trades: list[dict], seed: int) -> float:
    """Round trip with the direction removed: the realised change in the side's mid keeps its size and loses its sign at random; the exit
    bid is that mid less the real exit half spread. Real spreads, real volatility, real fees, no continuation by construction."""
    rng = random.Random(seed)
    tot = 0.0
    for t in trades:
        delta = t["exit_mid"] - t["mid"]
        if rng.random() < 0.5:
            delta = -delta
        bid = min(max(t["mid"] + delta - t["exit_half_spread"], 0.001), 0.999)
        tot += bid - fee(bid) - t["price"] - fee(t["price"])
    return tot / len(trades)


def null_summary(trades: list[dict], real_mean: float, fn, reps: int = NULL_REPS) -> dict:
    xs = sorted(fn(trades, 1000 + i) for i in range(reps))
    mean = sum(xs) / reps
    sd = (sum((x - mean) ** 2 for x in xs) / reps) ** 0.5
    return {"mean": mean, "sd": sd, "lo": xs[int(reps * 0.025)], "hi": xs[int(reps * 0.975)],
            "p_ge_real": sum(1 for x in xs if x >= real_mean) / reps}


def line(name: str, r: dict) -> str:
    v, s = verdict(r["trades"])
    n = len(r["trades"])
    gross = sum(t["gross"] for t in r["trades"]) / n if n else 0.0
    head = f"{name}: n={n}  gross {gross*100:+.2f}c"
    if s:
        head += f"  net {s['mean']*100:+.2f}c  z {s['z']:+.2f}  1st {s['h1']*100:+.2f}c  2nd {s['h2']*100:+.2f}c  fees x{STRESS} {s['stress']*100:+.2f}c  [{v}]"
    else:
        head += f"  [{v}]"
    return head


def main() -> None:
    ms = load()
    if not ms:
        print("No data. Run: python -m scalper.backfill")
        return
    base = run(ms)
    tr = base["trades"]
    days = {t["day"] for t in tr}
    print(f"{len(ms)} markets with a result. M1: threshold {THRESH*100:.0f}c, hold {HOLD_MIN} min, both series pooled.\n")
    print("Funnel:", base["counts"], f"traded {len(tr)} on {len(days)} days")
    print(line("PRIMARY", base))
    v, s = verdict(tr)
    if s:
        print(f"   se {s['se']*100:.2f}c, detectable (2.8 se) {s['detectable']*100:.2f}c")
    for series in sorted({t["series"] for t in tr}):
        sub = [t for t in tr if t["series"] == series]
        print(f"   {series}: n={len(sub)} net {sum(t['net'] for t in sub)/len(sub)*100:+.2f}c (information only)")
    for side in ("yes", "no"):
        sub = [t for t in tr if t["side"] == side]
        if sub:
            print(f"   {'UP' if side == 'yes' else 'DOWN'}: n={len(sub)} gross {sum(t['gross'] for t in sub)/len(sub)*100:+.2f}c net {sum(t['net'] for t in sub)/len(sub)*100:+.2f}c")
    if tr:
        cont = sum(t["exit_mid"] - t["mid"] for t in tr) / len(tr)
        sp = sum(t["price"] - t["mid"] + t["exit_half_spread"] for t in tr) / len(tr)
        fees = sum(fee(t["price"]) + fee(t["exit"]) for t in tr) / len(tr)
        print(f"   decomposition per trade: mid continuation {cont*100:+.2f}c, spread crossed {sp*100:.2f}c, fees {fees*100:.2f}c")
    d = base["dropped"]
    if d:
        print(f"   DROPPED (exit candle unusable): {len(d)} ({len(d)/(len(d)+len(tr))*100:.1f}% of entries); UP {sum(1 for x in d if x['side']=='yes')}, DOWN {sum(1 for x in d if x['side']=='no')}; "
              f"mean entry price {sum(x['price'] for x in d)/len(d)*100:.1f}c vs traded {sum(t['price'] for t in tr)/len(tr)*100:.1f}c")
        lo = sum(1 for x in d if x["price"] >= 0.5)
        print(f"   dropped with entry price at or above 50c: {lo}")
    if tr:
        print(f"\nFAIR-MARKET NULL ({NULL_REPS} repeats, same entries, zero edge at each entry's own price):")
        sett = run(ms, THRESH, None)["trades"]
        real_s = sum(t["net"] for t in sett) / len(sett)
        ns = null_summary(sett, real_s, null_settle)
        print(f"   hold to settlement: real {real_s*100:+.2f}c (n={len(sett)}), null mean {ns['mean']*100:+.2f}c sd {ns['sd']*100:.2f}c 95% [{ns['lo']*100:+.2f}, {ns['hi']*100:+.2f}]c, P(null >= real) {ns['p_ge_real']:.3f}")
        real_r = sum(t["net"] for t in tr) / len(tr)
        nr = null_summary(tr, real_r, null_roundtrip)
        print(f"   round trip, direction removed: real {real_r*100:+.2f}c, null mean {nr['mean']*100:+.2f}c sd {nr['sd']*100:.2f}c 95% [{nr['lo']*100:+.2f}, {nr['hi']*100:+.2f}]c, P(null >= real) {nr['p_ge_real']:.3f}")
    print(f"\nVERDICT (pre-registered, bar z>={Z_BAR}, n>={MIN_N}, both halves, fees x{STRESS}): {v}")
    print("\nINFORMATION ONLY, decides nothing (5 cuts; counted against the bar):")
    for th in CUTS_THRESH:
        print("  threshold %dc, hold %d: " % (round(th * 100), HOLD_MIN) + line("", run(ms, th, HOLD_MIN)).lstrip(": "))
    for h in CUTS_HOLD:
        print("  threshold 5c, hold %d: " % h + line("", run(ms, THRESH, h)).lstrip(": "))
    print("  threshold 5c, hold to settlement: " + line("", run(ms, THRESH, None)).lstrip(": "))


if __name__ == "__main__":
    main()
