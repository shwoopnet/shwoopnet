"""Live-account diagnosis from an order export (the page's "Copy all orders" / "Copy order diagnostics" CSV). Read-only; places nothing.

Usage: python -m scalper.live_diag ORDERS.csv [RESULTS.json]
  ORDERS.csv    columns found by name (any order, extras ignored): time or ts, ticker, side, status, fillCount, avgFill, avgFee; optional: entryLead, rise3, seenBid, seenAsk,
                bidSize, askSize, settledPnl (or pnl), result. Settled profit is taken from settledPnl when present, else computed at the ACTUAL fill price and fee from the
                market's public result, held to settlement (exit-watch sales are not modelled; an exited order is scored as a held loss and says so).
  RESULTS.json  optional {ticker: "yes"|"no"}; without it the public Kalshi market endpoint is asked once per ticker.
It splits the record by series, entry time, side, 3 minute rise, spread, UTC hour block and day, compares each series' loss count with the history's loss rate (exact binomial
tail), and lists the worst orders. It states what is variance and what is not; it does not decide anything.
"""
from __future__ import annotations

import csv
import json
import math
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone

# history loss rates and net per contract (69 days, README tables), by series and entry minute: (loss rate, net cents)
HISTORY = {("KXGOLD15M", 6): (0.0530, 1.54), ("KXBTC15M", 6): (0.0648, 0.45), ("KXETH15M", 6): (0.0617, 0.60), ("KXXRP15M", 6): (0.0526, 1.47),
           ("KXDOGE15M", 6): (0.058, 1.71), ("KXNATGAS15M", 6): (0.0598, 0.52), ("KXBTC15M", 10): (0.0585, 2.53), ("KXXRP15M", 10): (0.0542, 2.91),
           ("KXNATGAS15M", 10): (0.0480, 3.19)}
FEE_RATE = 0.07


def fee(p: float) -> float:
    return FEE_RATE * p * (1 - p)


def binom_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_orders(path: str) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            r = {k.strip(): v for k, v in r.items() if k}
            ts = r.get("time") or r.get("ts") or ""
            try:
                t = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts and not ts.isdigit() else datetime.fromtimestamp(int(ts) / 1000, timezone.utc)
            except Exception:
                t = None
            rows.append({"t": t, "ticker": r.get("ticker", ""), "side": (r.get("side") or "").lower(), "status": r.get("status", ""), "count": fnum(r.get("fillCount")) or fnum(r.get("count")) or 0.0,
                         "fill": fnum(r.get("avgFill")), "fee": fnum(r.get("avgFee")), "lead": r.get("entryLead") or "", "rise3": fnum(r.get("rise3")), "rng5": fnum(r.get("rng5")),
                         "bid": fnum(r.get("seenBid")), "ask": fnum(r.get("seenAsk")), "pnl": fnum(r.get("settledPnl")) if r.get("settledPnl") not in (None, "") else fnum(r.get("pnl")),
                         "result": (r.get("result") or "").lower()})
    return rows


def paid(o: dict) -> float | None:
    """Price paid per contract on the order's own side: a NO order's avgFill is the YES-book price, so the price paid is 1 minus it."""
    if o["fill"] is None:
        return None
    return o["fill"] if o["side"] == "yes" else round(1 - o["fill"], 4)


def settle(rows: list[dict], results: dict) -> None:
    for o in rows:
        o["series"] = o["ticker"].split("-")[0]
        o["minute"] = None
        if o["lead"] in ("10m", "6m"):
            o["minute"] = 10 if o["lead"] == "10m" else 6
        p = paid(o)
        o["paid"] = p
        o["filled"] = o["count"] > 0 and p is not None
        o["est"] = False
        if not o["filled"]:
            o["pnl_c"], o["win"] = None, None
            continue
        res = o["result"] if o["result"] in ("yes", "no") else results.get(o["ticker"])
        if o["pnl"] is not None and res is None:
            o["pnl_c"], o["win"] = o["pnl"], o["pnl"] > 0                       # settledPnl is dollars for the whole order
            continue
        if res not in ("yes", "no"):
            o["pnl_c"], o["win"] = None, None                                    # not settled yet
            continue
        win = res == o["side"]
        per = (1.0 if win else 0.0) - p - (o["fee"] if o["fee"] is not None else fee(p))
        o["pnl_c"], o["win"], o["est"] = per * o["count"], win, o["pnl"] is None


def fetch_results(tickers: list[str]) -> dict:
    from . import api
    out = {}
    for t in tickers:
        try:
            m = api._get(f"/markets/{t}").get("market", {})
            if m.get("result") in ("yes", "no"):
                out[t] = m["result"]
        except Exception:
            pass
    return out


def line(name: str, rows: list[dict], hist=None) -> str:
    s = [o for o in rows if o["pnl_c"] is not None]
    if not s:
        return f"  {name:26s} no settled orders"
    n, losses = len(s), sum(1 for o in s if not o["win"])
    pnl, contracts = sum(o["pnl_c"] for o in s), sum(o["count"] for o in s)
    avg = st.mean(o["paid"] for o in s)
    be = (1 - avg - fee(avg)) / (1 - avg - fee(avg) + avg + fee(avg))                # loss rate at which a contract of this price breaks even
    txt = f"  {name:26s} orders {n:4d} contracts {contracts:5.0f}  P/L {pnl:+8.2f}$ ({100 * pnl / contracts:+6.2f}c a contract)  losses {losses:3d} = {100 * losses / n:4.1f}% (break-even {100 * be:.1f}%)"
    if hist:
        lr, net = hist
        exp = lr * n
        p = binom_tail(losses, n, lr) if losses > exp else 1 - binom_tail(losses + 1, n, lr)
        txt += f" | history {100 * lr:.1f}% (expected {exp:.1f} losses, tail p {p:.2f}); history net {net:+.2f}c"
    return txt


def report(rows: list[dict]) -> str:
    out = []
    filled = [o for o in rows if o["filled"]]
    settled = [o for o in filled if o["pnl_c"] is not None]
    out.append(f"ORDERS {len(rows)}; filled {len(filled)}; settled {len(settled)} ({sum(1 for o in settled if o['est'])} computed from the public result, the rest from settledPnl); "
               f"first {min((o['t'] for o in rows if o['t']), default=None)}, last {max((o['t'] for o in rows if o['t']), default=None)}")
    out.append(line("ALL", settled))
    fees = sum((o["fee"] or 0) * o["count"] for o in settled)
    out.append(f"  fees in the P/L above ${fees:.2f}; contracts {sum(o['count'] for o in settled):.0f}")
    out.append("\nBY SERIES (against the history's loss rate at that entry minute):")
    for s in sorted({o["series"] for o in settled}):
        grp = [o for o in settled if o["series"] == s]
        for minute in sorted({o["minute"] for o in grp}, key=lambda x: (x is None, x)):
            g = [o for o in grp if o["minute"] == minute]
            h = HISTORY.get((s, minute if minute else 6))
            out.append(line(f"{s[2:-3]} {('%dm' % minute) if minute else '(no entryLead)'}", g, h))
    if any(o["minute"] for o in settled):
        out.append("\nBY ENTRY TIME:")
        for m in (10, 6):
            out.append(line(f"{m} minute", [o for o in settled if o["minute"] == m]))
    out.append("\nBY SIDE:")
    for sd in ("yes", "no"):
        out.append(line(f"{sd.upper()} favourite", [o for o in settled if o["side"] == sd]))
    if any(o["rise3"] is not None for o in settled):
        out.append("\nBY 3 MINUTE RISE (rise3, orders after the logging deploy only):")
        for name, fn in (("rise under 5c", lambda r: r < 0.05), ("rise 5c to 20c", lambda r: 0.05 <= r < 0.20), ("rise 20c or more", lambda r: r >= 0.20)):
            out.append(line(name, [o for o in settled if o["rise3"] is not None and fn(o["rise3"])]))
        out.append(line("no rise3 (before deploy)", [o for o in settled if o["rise3"] is None]))
    if any(o["bid"] is not None and o["ask"] is not None for o in settled):
        out.append("\nBY QUOTE SPREAD AT THE DECISION:")
        out.append(line("spread over 3c", [o for o in settled if o["bid"] is not None and o["ask"] is not None and o["ask"] - o["bid"] > 0.03]))
        out.append(line("spread 3c or less", [o for o in settled if o["bid"] is not None and o["ask"] is not None and o["ask"] - o["bid"] <= 0.03]))
    fl = flat_section(rows, settled)
    if fl:
        out.append(fl)
    out.append(crowd_section(settled))
    out.append("\nBY UTC HOUR BLOCK:")
    for name, lo, hi in (("Asia 00-07", 0, 7), ("Europe 07-13", 7, 13), ("US 13-21", 13, 21), ("late 21-24", 21, 24)):
        out.append(line(name, [o for o in settled if o["t"] and lo <= o["t"].hour < hi]))
    out.append("\nBY DAY (UTC):")
    byday = defaultdict(list)
    for o in settled:
        if o["t"]:
            byday[o["t"].strftime("%Y-%m-%d")].append(o)
    for d in sorted(byday):
        out.append(line(d, byday[d]))
    worst = sorted(settled, key=lambda o: o["pnl_c"])[:8]
    out.append("\nWORST ORDERS:")
    for o in worst:
        out.append(f"  {o['t'].strftime('%m-%d %H:%M') if o['t'] else '?'} {o['ticker']:34s} {o['side']:3s} paid {o['paid']:.3f} x{o['count']:.0f}  {o['pnl_c']:+.2f}$ lead {o['lead'] or '-'}")
    out.append("\nREADING: a group is only a leak if its P/L is negative AND its loss count is well above the history's expectation (tail p under about 0.10) on a few dozen orders; a handful of losses "
               "on 1-contract series is variance. Exit-watch sales are not modelled here (an exited order is scored as a held loss).")
    return "\n".join(out)


FLAT_RNG5, FLAT_RISE3 = 0.15, 0.05          # README FLAT2: rng5 <= 0.15 and |rise3| <= 0.05


def is_flat(o: dict):
    """True / False when both rng5 and rise3 were logged for the order, else None."""
    if o.get("rng5") is None or o.get("rise3") is None:
        return None
    return o["rng5"] <= FLAT_RNG5 and abs(o["rise3"]) <= FLAT_RISE3


def flat_section(rows: list[dict], settled: list[dict]) -> str:
    """Live FLAT check: the share of ordered entries that are FLAT per series (history says about 15%), and settled FLAT against not-FLAT. Information only; the filter is NOT live."""
    logged = [o for o in rows if is_flat(o) is not None]
    if not logged:
        return ""
    out = ["\nFLAT CHECK (orders with rng5 and rise3 logged; the FLAT filter is NOT live, this only measures the record):"]
    for s in sorted({o["ticker"].split("-")[0] for o in logged}):
        g = [o for o in logged if o["ticker"].split("-")[0] == s]
        out.append(f"  {s[2:-3]:6s} ordered {len(g):4d}, FLAT {sum(1 for o in g if is_flat(o)):4d} ({100 * sum(1 for o in g if is_flat(o)) / len(g):.0f}%)")
    sl = [o for o in settled if is_flat(o) is not None]
    if sl:
        out.append(line("FLAT settled", [o for o in sl if is_flat(o)]))
        out.append(line("not FLAT settled", [o for o in sl if not is_flat(o)]))
    return "\n".join(out)


def crowd_section(settled: list[dict]) -> str:
    """Settled fills grouped by market window (the time part of the ticker): one fill against two or more, as in README LIVE2."""
    by = defaultdict(list)
    for o in settled:
        by[o["ticker"].split("-")[1]].append(o)
    out = ["\nBY FILLS IN THE SAME WINDOW (README LIVE2: crowded two-fill windows lost 14.3% against 4.4%):"]
    for name, fn in (("1 fill", lambda n: n == 1), ("2 fills", lambda n: n == 2), ("3 or more", lambda n: n >= 3)):
        g = [o for v in by.values() if fn(len(v)) for o in v]
        out.append(line(name, g))
    return "\n".join(out)


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        print(__doc__)
        return
    rows = load_orders(argv[1])
    results = json.load(open(argv[2])) if len(argv) > 2 else {}
    need = sorted({o["ticker"] for o in rows if o["count"] > 0 and o["ticker"] not in results and o["pnl"] is None and o["result"] not in ("yes", "no")})
    if need and len(argv) <= 2:
        results.update(fetch_results(need))
    settle(rows, results)
    print(report(rows))


if __name__ == "__main__":
    main(sys.argv)
