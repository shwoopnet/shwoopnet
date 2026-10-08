"""The forward check of L1 and the four overnight survivors (rules fixed in the README, "Pre-registration: the forward check", before this
file existed or any rule was run on the new data).

Only markets that closed AFTER OLD_END (the last close in the database before the 2026-10-08 download) are used. No function here takes a
performance parameter, and the verdict is NOT_ENOUGH_DATA until a rule has both MIN_N entries and MIN_DAYS separate UTC days; a rule below
that is printed as information only. Verdict words are FALSIFIED, NOT_YET_FALSIFIED and NOT_ENOUGH_DATA. Nothing here means "trade".

Usage: python -m scalper.forward
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import lstrats as L
from . import search as S
from .scalps import MIN_N, STRESS, Z_BAR, judge, load as load_markets

OLD_END = 1791397800        # 2026-10-07 18:30:00 UTC, the last close in the database before the forward window
W3_START = 1791212400       # the first close after the first search's data (2026-10-05 15:00 UTC); W3 is (W3_START, OLD_END]
MIN_DAYS = 5

F1 = {"left": 2, "lo": 0.03, "hi": 0.20, "side": "either", "filters": [("series", "KXBTC15M"), ("spread", 0.01)]}
F2 = {"left": 2, "lo": 0.03, "hi": 0.97, "side": "no", "filters": [("move", "away", 0.02, 5), ("series", "KXBTC15M"), ("spread", 0.04)]}
F3 = {"left": 8, "lo": 0.80, "hi": 0.97, "side": "yes", "filters": []}
F4 = {"left": 8, "lo": 0.80, "hi": 0.97, "side": "yes", "filters": [("spread", 0.02)]}
SEARCH_RULES = {"F1": F1, "F2": F2, "F3": F3, "F4": F4}


def settle(side: str, price: float, yes_won: bool, mult: float) -> float:
    return L.net(side, price, yes_won, mult)


def rule_entries(ms: list[dict], rule: dict) -> list[dict]:
    """Entries of a search-grammar rule: the price comes from S.entry (prices only), the result is read only to settle the trade."""
    out = []
    for m in ms:
        e = S.entry(m, rule)
        if e is None:
            continue
        day, side, price, _ = e
        yes = m["res"] == "yes"
        out.append({"ticker": m["ticker"], "series": m["series"], "day": day, "close_ts": m["close"], "side": side, "price": price,
                    "net": settle(side, price, yes, 1.0), "stress": settle(side, price, yes, STRESS), "gross": settle(side, price, yes, 0.0)})
    return sorted(out, key=lambda o: o["close_ts"])


def forward_only(markets: list[tuple]) -> list[tuple]:
    """Markets that closed strictly after OLD_END. The tuples are scalps.load()'s (ticker, series, candles, close_ts, result)."""
    return [m for m in markets if m[3] > OLD_END]


def verdict(entries: list[dict]) -> tuple[str, dict | None]:
    """NOT_ENOUGH_DATA below MIN_N entries or MIN_DAYS days; otherwise the common bar via scalps.judge."""
    days = {e["day"] for e in entries}
    if len(entries) < MIN_N or len(days) < MIN_DAYS:
        return "NOT_ENOUGH_DATA", None
    return L.verdict(entries)


def stats(entries: list[dict]) -> dict | None:
    """The numbers printed with every rule, whether or not a verdict is allowed. Same judge, same halves."""
    if len(entries) < 2:
        return None
    mid = sorted(e["close_ts"] for e in entries)[len(entries) // 2]
    _, summ = judge({"x": [(e["day"], e["close_ts"], e["net"], e["stress"]) for e in entries]}, mid)
    s = summ[0]
    s["gross"] = sum(e["gross"] for e in entries) / len(entries)
    s["days"] = len({e["day"] for e in entries})
    s["win"] = sum(1 for e in entries if e["gross"] + e["price"] > 0.5) / len(entries)   # gross is won - price, so gross + price is 1 on a win and 0 on a loss
    s["price"] = sum(e["price"] for e in entries) / len(entries)
    return s


def all_rules(markets: list[tuple]) -> dict[str, list[dict]]:
    ms = S.prep(markets)
    out = {"F0 L1": L.hold_rule(markets, **L.L1)}
    for name, rule in SEARCH_RULES.items():
        out[name] = rule_entries(ms, rule)
    return out


def line(name: str, entries: list[dict]) -> str:
    v, _ = verdict(entries)
    s = stats(entries)
    if not s:
        return f"{name}: n={len(entries)}  (too few to compute)  VERDICT: {v}"
    z = f"{s['z']:+.2f}" if s["days"] >= 2 else "n/a (one day)"       # one cluster has no spread to measure; the raw ratio is rounding noise
    return (f"{name}: n={s['n']} on {s['days']} day(s)  gross {s['gross']*100:+.2f}c  net {s['mean']*100:+.2f}c  z {z}  "
            f"1st half {s['h1']*100:+.2f}c  2nd half {s['h2']*100:+.2f}c  fees x{STRESS} {s['stress']*100:+.2f}c  "
            f"win {s['win']*100:.1f}% at mean price {s['price']*100:.1f}c\n   VERDICT (n>={MIN_N}, days>={MIN_DAYS}, z>={Z_BAR}, both halves, fees x{STRESS}): {v}"
            + ("" if v != "NOT_ENOUGH_DATA" else "   (numbers above are information only)"))


def main() -> None:
    markets, _ = load_markets()
    fwd = forward_only(markets)
    w3 = [m for m in markets if W3_START < m[3] <= OLD_END]
    overlap = {m[0] for m in fwd} & {m[0] for m in w3}
    days = sorted({datetime.fromtimestamp(m[3], timezone.utc).strftime("%Y-%m-%d") for m in fwd})
    print(f"forward window: {len(fwd)} markets closing after {OLD_END} ({', '.join(days)}); W3 has {len(w3)} markets; markets in both: {len(overlap)}\n")
    for name, ents in all_rules(fwd).items():
        print(line(name, ents))
        print()
    print("Information only, decides nothing:")
    for name, ents in all_rules(fwd).items():
        for series in sorted({e["series"] for e in ents}):
            sub = [e for e in ents if e["series"] == series]
            print(f"  {name} {series}: n={len(sub)} mean net {sum(e['net'] for e in sub) / len(sub) * 100:+.2f}c")
    ms = S.prep(fwd)
    for left in (1, 3):
        ents = rule_entries(ms, dict(F1, left=left))
        print(f"  F1 at {left} minute(s) left: n={len(ents)}" + (f" mean net {sum(e['net'] for e in ents) / len(ents) * 100:+.2f}c" if ents else ""))
    print("\nNo verdict here means trade. NOT_YET_FALSIFIED is permission to keep testing forward and nothing more.")


if __name__ == "__main__":
    main()
