"""OW1, the opening window test (rules fixed in the README, "Pre-registration: OW1, the opening window, two lanes", before this file existed and
before any rule was run on a market that closed after OW1_START).

  F  the early favourite: the side whose ask is 0.82 to 0.87 on the minute candle that ends 600 s before the close, bought at the ask, held to settlement.
  U  the early underdog (the "flip"): the same, with the side whose ask is 0.20 to 0.30.

One market never gets both lanes: the two sides of a market sum to about a dollar, so buying both is a guaranteed small loss and not a flip. F takes the market.
These are the bands and the window the paper recorder in functions/kalshiOpeningLib.js uses (a test reads that file and fails if the two drift apart).

Only markets that closed AFTER OW1_START are judged. Anything earlier was looked at before the rules were fixed (the README discloses it) and is printed as
information only. No function here takes a performance parameter. A verdict is produced only on or after a registered read date: the first read, at FIRST_READ,
clips the data at that date so it never changes afterwards; a lane that was NOT_ENOUGH_DATA then gets one more read, final, at FINAL_READ. Before the first read
the numbers are information only. Verdict words are FALSIFIED, NOT_YET_FALSIFIED and NOT_ENOUGH_DATA. Nothing here means "trade".

Usage: python -m scalper.opening
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import forward as FW
from . import lstrats as L
from .scalps import MIN_N, STRESS, Z_BAR, load as load_markets

OW1_START = 1791820800      # 2026-10-12 16:00:00 UTC; only markets that close after this are judged
FIRST_READ = 1793664000     # 2026-11-03 00:00:00 UTC, 21 full days later; the first and the only read for a lane with enough data
FINAL_READ = 1794787200     # 2026-11-16 00:00:00 UTC; a second and final read, only for a lane that was NOT_ENOUGH_DATA at the first
LEFT_S = 600                # the minute candle that ends 10 minutes before the close
LANES = {"F": (0.82, 0.87), "U": (0.20, 0.30)}
MIN_DAYS = FW.MIN_DAYS


def _date(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def lane_entries(markets: list[tuple], after: int = OW1_START, upto: int | None = None) -> dict[str, list[dict]]:
    """{"F": entries, "U": entries} on markets that close after `after` (and, if given, at or before `upto`). U loses any market F took (one leg per market)."""
    ms = [m for m in markets if m[3] > after and (upto is None or m[3] <= upto)]
    f = L.hold_rule(ms, LEFT_S, LANES["F"])
    taken = {e["ticker"] for e in f}
    u = [e for e in L.hold_rule(ms, LEFT_S, LANES["U"]) if e["ticker"] not in taken]
    return {"F": f, "U": u}


def exploratory_entries(markets: list[tuple]) -> dict[str, list[dict]]:
    """The same two lanes on markets that closed at or before OW1_START: seen before the rules were fixed, so information only and never a verdict."""
    return lane_entries(markets, after=0, upto=OW1_START)


def verdicts(markets: list[tuple], now_ts: float) -> dict[str, dict]:
    """{lane: {"first": word or None, "final": word or None}}. None means the read date has not come. The first read clips at FIRST_READ; the final read exists
    only for a lane whose first read was NOT_ENOUGH_DATA, and clips at FINAL_READ."""
    out = {lane: {"first": None, "final": None} for lane in LANES}
    if now_ts >= FIRST_READ:
        first = lane_entries(markets, upto=FIRST_READ)
        for lane in LANES:
            out[lane]["first"] = FW.verdict(first[lane])[0]
    if now_ts >= FINAL_READ:
        final = lane_entries(markets, upto=FINAL_READ)
        for lane in LANES:
            if out[lane]["first"] == "NOT_ENOUGH_DATA":
                out[lane]["final"] = FW.verdict(final[lane])[0]
    return out


def numbers(name: str, entries: list[dict]) -> str:
    """The figures printed for a lane whether or not a verdict is allowed. Same judge, same halves as every other readout."""
    s = FW.stats(entries)
    if not s:
        return f"{name}: n={len(entries)}  (too few to compute)"
    z = f"{s['z']:+.2f}" if s["days"] >= 2 else "n/a (one day)"          # one cluster has no spread to measure
    return (f"{name}: n={s['n']} on {s['days']} day(s)  gross {s['gross']*100:+.2f}c  net {s['mean']*100:+.2f}c  z {z}  1st half {s['h1']*100:+.2f}c  "
            f"2nd half {s['h2']*100:+.2f}c  fees x{STRESS} {s['stress']*100:+.2f}c  win {s['win']*100:.1f}% at mean price {s['price']*100:.1f}c")


def report(markets: list[tuple], now_ts: float) -> str:
    fwd = [m for m in markets if m[3] > OW1_START]
    days = sorted({_date(m[3]) for m in fwd})
    lines = [f"OW1 forward window: {len(fwd)} markets closing after {_date(OW1_START)} 16:00 UTC" + (f" ({days[0]} to {days[-1]}, {len(days)} days)" if days else " (none yet)")]
    cur = lane_entries(markets)
    lines.append("")
    for lane, label in (("F", "F early favourite 0.82-0.87"), ("U", "U early underdog 0.20-0.30")):
        lines.append(numbers(label, cur[lane]))
    if now_ts < FIRST_READ:
        lines.append(f"\nNo verdict before the registered read ({_date(FIRST_READ)}): the numbers above are information only and decide nothing.")
    else:
        v = verdicts(markets, now_ts)
        lines.append("")
        for lane in LANES:
            row = v[lane]
            word = f"first read ({_date(FIRST_READ)}): {row['first']}"
            if row["first"] == "NOT_ENOUGH_DATA":
                word += f"; final read ({_date(FINAL_READ)}): {row['final'] if row['final'] else 'not yet'}"
            lines.append(f"VERDICT {lane} (n>={MIN_N}, days>={MIN_DAYS}, z>={Z_BAR}, both halves, fees x{STRESS}): {word}")
    old = exploratory_entries(markets)
    lines.append(f"\nExploratory, markets closing at or before {_date(OW1_START)} (looked at BEFORE the rules were fixed; information only, never a verdict):")
    for lane, label in (("F", "F"), ("U", "U")):
        lines.append("  " + numbers(label, old[lane]))
    lines.append("\nNo verdict word here means trade. NOT_YET_FALSIFIED is permission to keep testing forward and nothing more.")
    return "\n".join(lines)


def main() -> None:
    markets, _ = load_markets()
    if not markets:
        print("No data. Run: python -m scalper.backfill")
        return
    print(report(markets, datetime.now(timezone.utc).timestamp()))


if __name__ == "__main__":
    main()
