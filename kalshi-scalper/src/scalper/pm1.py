"""PM1 (README, Pre-registration: PM1): Kalshi's noon Bitcoin ladder against Polymarket's price for the same strike. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.pm1 run   (once; a second run is refused)
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from . import api
from .calibration import cluster_mean_z
from .paths import DATA_DIR

RESULT = DATA_DIR / "pm1_result.txt"
DAYS, HOURS_ET, THRESH = 20, (8, 9, 10, 11), (0.04, 0.02, 0.06)
MIN_N, MIN_DAYS, BAR_C, BAR_Z, FALSIFY_C = 150, 8, 0.010, 2.0, 0.003
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def g(u: str):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research"}), timeout=30))


def poly_day(d):
    slug = f"bitcoin-above-on-{MONTHS[d.month - 1]}-{d.day}-{d.year}"
    ev = g(f"https://gamma-api.polymarket.com/events?slug={slug}")
    out = {}
    if not ev:
        return out
    for m in ev[0].get("markets", []):
        k = re.search(r"\$([\d,]+)", m.get("question", ""))
        if not k or not m.get("clobTokenIds"):
            continue
        tok = json.loads(m["clobTokenIds"])[0]
        try:
            h = g(f"https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60").get("history", [])
        except Exception:
            continue
        out[float(k.group(1).replace(",", ""))] = [(x["t"], x["p"]) for x in h]
        time.sleep(0.1)
    return out


def poly_at(h, t):
    best = None
    for ts, p in h:
        if ts <= t and t - ts <= 5400:
            best = p
    return best


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    today = datetime.now(timezone.utc).date()
    trades = {t: [] for t in THRESH}
    scanned_days = pairs = 0
    for back in range(1, DAYS + 1):
        d = today - timedelta(days=back)
        close = datetime(d.year, d.month, d.day, 16, 0, tzinfo=timezone.utc)  # noon EDT (before 2026-11-01)
        try:
            poly = poly_day(d)
        except Exception as e:
            print("poly fail", d, e); continue
        if not poly:
            continue
        cts = int(close.timestamp())
        ms = [m for m in api.settled_markets("KXBTCD", cts, cts) if m.get("floor_strike") is not None]
        by_k = {}
        for m in ms:
            k = round(m["floor_strike"] + 0.01)
            if k in poly:
                by_k[k] = m
        if not by_k:
            continue
        scanned_days += 1
        tk = [m["ticker"] for m in by_k.values()]
        got = api._get("/markets/candlesticks", {"market_tickers": ",".join(tk), "start_ts": cts - 6 * 3600, "end_ts": cts, "period_interval": 60})
        cdl = {x["market_ticker"]: {c["end_period_ts"]: c for c in x.get("candlesticks", [])} for x in got.get("markets", [])}
        for k, m in by_k.items():
            for hr in HOURS_ET:
                t = cts - (12 - hr) * 3600
                c = cdl.get(m["ticker"], {}).get(t)
                p = poly_at(poly[k], t)
                if c is None or p is None:
                    continue
                ask, bid = api.f((c.get("yes_ask") or {}).get("close_dollars")), api.f((c.get("yes_bid") or {}).get("close_dollars"))
                if ask is None or bid is None or not (0 < bid < ask < 1):
                    continue
                pairs += 1
                yes = m["result"] == "yes"
                for th in THRESH:
                    if p - ask >= th:
                        trades[th].append((str(d), (1.0 if yes else 0.0) - ask - fee(ask), (1.0 if yes else 0.0) - ask - fee(ask, 1.2)))
                    elif bid - p >= th:
                        trades[th].append((str(d), (0.0 if yes else 1.0) - (1 - bid) - fee(1 - bid), (0.0 if yes else 1.0) - (1 - bid) - fee(1 - bid, 1.2)))
        time.sleep(0.3)
    lines = [f"PM1: {scanned_days} days with both venues, {pairs} strike-time pairs"]
    verdict = "NOT_ENOUGH_DATA"
    for th in THRESH:
        v = trades[th]
        if len(v) < 20:
            lines.append(f"threshold {100 * th:.0f}c: {len(v)} trades"); continue
        days = sorted({x[0] for x in v}); cut = days[len(days) // 2]
        m, _, z = cluster_mean_z([(a, b) for a, b, _ in v])
        h1 = [b for a, b, _ in v if a < cut]; h2 = [b for a, b, _ in v if a >= cut]
        ms = sum(c for _, _, c in v) / len(v)
        ok = len(v) >= MIN_N and len(days) >= MIN_DAYS and m >= BAR_C and z >= BAR_Z and sum(h1) > 0 and sum(h2) > 0 and ms > 0
        lines.append(f"threshold {100 * th:.0f}c: n {len(v)} on {len(days)} days, net {100 * m:+.2f}c, z {z:+.2f}, halves {100 * sum(h1) / max(len(h1), 1):+.2f}/{100 * sum(h2) / max(len(h2), 1):+.2f}c, stress {100 * ms:+.2f}c {'PASS' if ok else ''}")
        if th == 0.04:
            verdict = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C and len(v) >= MIN_N) else "NOT_ENOUGH_DATA")
    lines.insert(1, f"VERDICT {verdict} (registered threshold 4c)")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
