#!/usr/bin/env python3
"""KXINX15M candle QUOTE PROFILE (Forensics desk, Nov 13, 2026; the Head of R&D's order of 22:22Z, for SPXSCALP's first check). COUNTS ONLY.
Runs on the landed SPXOI1_CANDLES run (after landed_run_precheck.py says COMPLETE). It reads ONLY yes_bid.close_dollars and yes_ask.close_dollars and end_period_ts of each candle.
It never reads volume_fp, open_interest_fp, price, any result or settlement field, so no outcome, P&L or open interest can reach it.
Per window (ticker), over the candle minutes the pull returned (30 minutes before the close to 120 seconds before it), it counts minutes that are:
  two_sided      0 < yes_bid < yes_ask < 1 (both prices on a whole cent)
  spread_1c, spread_2c, spread_3c, spread_over3c    among two-sided minutes, yes_ask minus yes_bid in cents (exactly 1, 2, 3, more than 3); the four add up to two_sided
  cheap_20_30    among two-sided minutes, the cheap side's ask is 20c to 30c INCLUSIVE; cheap ask = min(yes_ask, 100 minus yes_bid) in cents (the NO ask is one minus the YES bid)
  not_two_sided  both prices present and whole cents but not two-sided (a bid of 0, an ask of 1, or a bid at or above the ask)
  missing_quote  a bid or an ask absent or not a number          off_cent    a price that is not a whole cent (excluded from every other count)
Window list = every ticker named in the manifest rows' market_tickers parameter; a ticker with no candle is counted in windows_no_candles. A candle end time that appears twice (pages) is counted once,
the first answer kept; a second answer with different prices is counted in duplicate_conflicts. Prices are read as exact decimals (integer cents), never as floats.
Refuses: a run listed in HELDOUT_PULL_RUNS.md (listed_runs_guard), any path in or resolving into a HELDOUT_ folder, any ticker dated 2026-12-01 or later (the SPXFV1 and SPXOI1 held-out starts 2026-12-01),
and a run that is not COMPLETE by its manifest.
usage: python3 -I kxinx15m_quote_profile.py <run folder> [--json <out.json>]"""
import sys, os, json, gzip, re, collections
from decimal import Decimal, InvalidOperation

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from listed_runs_guard import refuse_listed

HELD_FROM = (2026, 12, 1)
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
CATS = ("candles", "two_sided", "spread_1c", "spread_2c", "spread_3c", "spread_over3c", "cheap_20_30", "not_two_sided", "missing_quote", "off_cent")


def refuse_heldout(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)): raise SystemExit("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % path)


def ticker_date(t):
    m = re.match(r"^[A-Z0-9]+-(\d{2})([A-Z]{3})(\d{2})", t)
    if not m or m.group(2) not in MON: return None
    return (2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)))


def cents(d):
    """The price as whole cents (int), None when absent or not a number, 'off' when not a whole cent."""
    if d is None: return None
    try: x = Decimal(str(d))
    except (InvalidOperation, ValueError): return None
    if not x.is_finite(): return None
    c = x * 100
    return int(c) if c == c.to_integral_value() else "off"


def one_candle(bid, ask):
    """The category names this minute adds to, from its two prices in cents."""
    if bid is None or ask is None: return ["missing_quote"]
    if bid == "off" or ask == "off": return ["off_cent"]
    if not (0 < bid < ask < 100): return ["not_two_sided"]
    out = ["two_sided"]; s = ask - bid
    out.append("spread_1c" if s == 1 else "spread_2c" if s == 2 else "spread_3c" if s == 3 else "spread_over3c")
    if 20 <= min(ask, 100 - bid) <= 30: out.append("cheap_20_30")
    return out


def profile(folder):
    refuse_heldout(folder); refuse_listed(folder)
    man = json.load(open(os.path.join(folder, "manifest.json"))); rows = man.get("rows", [])
    if man.get("status") != "complete": raise SystemExit("REFUSED: the run's manifest status is %r, not complete" % man.get("status"))
    wanted = []
    for r in rows:
        for t in str((r.get("params") or {}).get("market_tickers", "")).split(","):
            if t and t not in wanted: wanted.append(t)
    for t in wanted:
        d = ticker_date(t)
        if d is None: raise SystemExit("REFUSED: a ticker with no readable date: " + t)
        if d >= HELD_FROM: raise SystemExit("REFUSED: a ticker dated on or after the 2026-12-01 held-out start: " + t)
    seen = {t: {} for t in wanted}; other = set(); conflicts = collections.Counter(); dups = collections.Counter()
    for r in rows:
        if r.get("status") != 200 or not r.get("file"): continue
        path = os.path.join(folder, r["file"]); refuse_heldout(path)
        body = json.load(gzip.open(path, "rt"))
        for m in (body.get("markets") or []) if isinstance(body, dict) else []:
            t = m.get("market_ticker")
            if t not in seen: other.add(t); continue
            for c in m.get("candlesticks") or []:
                ts = c.get("end_period_ts")
                if not isinstance(ts, int): continue
                yb = c.get("yes_bid"); ya = c.get("yes_ask")
                pair = (cents(yb.get("close_dollars") if isinstance(yb, dict) else None), cents(ya.get("close_dollars") if isinstance(ya, dict) else None))
                if ts in seen[t]:
                    dups[t] += 1
                    if seen[t][ts] != pair: conflicts[t] += 1
                    continue
                seen[t][ts] = pair
    per = []; tot = collections.Counter(); no_candles = 0
    for t in wanted:
        c = collections.Counter()
        for ts, (b, a) in seen[t].items():
            c["candles"] += 1
            for k in one_candle(b, a): c[k] += 1
        if c["candles"] == 0: no_candles += 1
        per.append({"ticker": t, **{k: c[k] for k in CATS}, "duplicate_answers": dups[t], "duplicate_conflicts": conflicts[t]})
        for k in CATS: tot[k] += c[k]
    w2 = sum(1 for p in per if p["two_sided"] > 0); wb = sum(1 for p in per if p["cheap_20_30"] > 0)
    return {"run": os.path.basename(os.path.normpath(folder)), "windows": len(wanted), "windows_no_candles": no_candles, "windows_with_a_two_sided_minute": w2, "windows_with_a_cheap_20_30_minute": wb,
            "totals": {k: tot[k] for k in CATS}, "duplicate_answers": sum(dups.values()), "duplicate_conflicts": sum(conflicts.values()), "other_tickers_in_answers_ignored": len(other),
            "ticker_dates": [min(ticker_date(t) for t in wanted), max(ticker_date(t) for t in wanted)] if wanted else None, "per_window": per}


def main(argv):
    if not argv or argv[0].startswith("-"): print(__doc__); return 2
    out = profile(argv[0]); j = None
    if "--json" in argv: j = argv[argv.index("--json") + 1]
    if j: open(j, "w").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    t = out["totals"]
    print("run", out["run"], "| windows", out["windows"], "| no candles", out["windows_no_candles"], "| with a two-sided minute", out["windows_with_a_two_sided_minute"], "| with a cheap 20-30c minute", out["windows_with_a_cheap_20_30_minute"])
    print("minutes:", ", ".join("%s %d" % (k, t[k]) for k in CATS), "| duplicate answers", out["duplicate_answers"], "conflicts", out["duplicate_conflicts"], "| other tickers ignored", out["other_tickers_in_answers_ignored"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
