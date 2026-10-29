"""LIVEWATCH: a nightly look at the live L1 record against L1's history, flagging only a CHANGE. Research only; it reads, it never acts.
Usage: python -m scalper.livewatch run
Reads the owner's read-only nightly report (kalshiNightlyReport, last 720 hours, one row per order) with the token in the environment
variable KALSHI_REPORT_TOKEN (read inside Python, never printed or written). Raw rows are saved ONLY to the scratchpad (LIVEWATCH_RAW_DIR,
default below), never to git. kalshi-scalper/workers/LIVEWATCH.md gets aggregates only, newest first, time in US Central.

Per market (gold, Bitcoin, Ethereum, Dogecoin, XRP): settled, losses, win rate, PF, net (dollars at the real sizes, after fees, from
settledPnl), PF by price paid (88-91c, 91-94c, 94-97c), and the last 7 days against the 23 days before.
Price paid: the report's avgFill is empty, so the price is solved from settledPnl and the filled count: the whole-cent p in 0.80 to 0.99
for which a win gives C(1-p) - fee or a loss gives -Cp - fee (fee 7% x C x p x (1-p) rounded up per order) to the cent. Exits (sold at
the 25c line) and rows with no exact match have no price and are counted under "price unknown".
Flags (only these): (1) last 7 days' loss rate above the market's history loss rate with a one-sided binomial p under 0.05;
(2) last 7 days' PF under 0.8 with at least 30 settled. History loss rate = L1's history (`scalper.tstop1.load()`, the 6 minute look,
88c to 97c, held), per series, restricted to markets closing before the report window starts so the two never overlap. A loss in the
live record = settledPnl below zero (an exit counts as a loss). Live includes 10 minute entries; history is the 6 minute look only.
"""
from __future__ import annotations

import json
import math
import os
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .fees import taker_fee
from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
URL = "https://us-central1-shwoopnet.cloudfunctions.net/kalshiNightlyReport?hours=720&orders=1"
RAW_DIR = Path(os.environ.get("LIVEWATCH_RAW_DIR", "/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad/livewatch"))
OUT = DATA_DIR.parent / "workers" / "LIVEWATCH.md"
MARKETS = {"gold": "KXGOLD15M", "Bitcoin": "KXBTC15M", "Ethereum": "KXETH15M", "Dogecoin": "KXDOGE15M", "XRP": "KXXRP15M"}
BANDS = [("88-91c", 0.88, 0.91), ("91-94c", 0.91, 0.94), ("94-97c", 0.94, 0.975)]
P_FLAG, PF_FLAG, PF_MIN_N = 0.05, 0.8, 30


def fetch() -> dict:
    tok = os.environ.get("KALSHI_REPORT_TOKEN")
    if not tok:
        raise SystemExit("KALSHI_REPORT_TOKEN is not set; nothing fetched")
    req = urllib.request.Request(URL, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"report_{datetime.now(timezone.utc):%Y%m%dT%H%M}Z.json").write_text(json.dumps(d))
    return d


def pf(xs):
    w, l = sum(x for x in xs if x > 0), -sum(x for x in xs if x < 0)
    return w / l if l > 0 else (float("inf") if w > 0 else 0.0)


def fmt_pf(x):
    return "n/a" if x == 0 else ("no loss" if x == float("inf") else f"{x:.2f}")


def price_paid(o):
    c, pnl = o.get("count") or 0, o.get("settledPnl")
    if not c or pnl is None or o.get("result") == "exit":
        return None
    won = pnl > 0
    for cents in range(80, 100):
        p = cents / 100
        v = (c * (1 - p) if won else -c * p) - taker_fee(p, int(c))
        if abs(v - pnl) < 0.005:
            return p
    return None


def binom_sf(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    if k <= 0:
        return 1.0
    return min(1.0, sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def history_rates(before_ts: int) -> dict:
    from .tstop1 import load
    n, l = defaultdict(int), defaultdict(int)
    for r in load():
        if r["close_ts"] < before_ts:
            n[r["series"]] += 1
            l[r["series"]] += 1 - r["won"]
    return {s: (l[s] / n[s], n[s]) for s in n}


def tally(rows):
    v = [o["settledPnl"] for o in rows]
    los = sum(1 for x in v if x < 0)
    return dict(n=len(v), losses=los, wr=(1 - los / len(v)) if v else None, pf=pf(v), net=sum(v))


def run():
    d = fetch()
    now = datetime.now(timezone.utc)
    since = datetime.fromisoformat(d["sinceUtc"].replace("Z", "+00:00"))
    cut7 = now - timedelta(days=7)
    rows = [o for o in d.get("orders", []) if o.get("settledPnl") is not None and (o.get("count") or 0) > 0]
    for o in rows:
        o["t"] = datetime.fromisoformat(o["ts"].replace("Z", "+00:00"))
        o["series"] = (o.get("ticker") or "").split("-")[0]
        o["p"] = price_paid(o)
    H = history_rates(int(since.timestamp()))
    lines = [f"## {datetime.now(CT):%Y-%m-%d %H:%M} CT (report window {since.astimezone(CT):%Y-%m-%d %H:%M} CT to now; last 7 days = since {cut7.astimezone(CT):%Y-%m-%d %H:%M} CT)", ""]
    if d.get("ordersTruncated"):
        lines.append("Note: the report truncated its order rows (2,000 cap); the older part of the window is missing.\n")
    lines += ["| Market | Settled | Losses | Win rate | PF | Net | PF 88-91c (held) | PF 91-94c (held) | PF 94-97c (held) | exits, unpriced | Last 7d: n, losses, PF, net | 23d before: n, losses, PF, net | History loss rate (n) |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    flags = []
    for name, s in MARKETS.items():
        rs = [o for o in rows if o["series"] == s]
        a, r7, r23 = tally(rs), tally([o for o in rs if o["t"] >= cut7]), tally([o for o in rs if o["t"] < cut7])
        bands = [fmt_pf(pf([o["settledPnl"] for o in rs if o["p"] is not None and lo <= o["p"] < hi])) + f" ({sum(1 for o in rs if o['p'] is not None and lo <= o['p'] < hi)})" for _, lo, hi in BANDS]
        ex = sum(1 for o in rs if o.get("result") == "exit")
        unk = f"{ex}, {sum(1 for o in rs if o['p'] is None) - ex}"
        hr, hn = H.get(s, (None, 0))
        wr_s = "" if a["wr"] is None else f"{100 * a['wr']:.1f}%"
        lines.append(f"| {name} | {a['n']} | {a['losses']} | {wr_s} | {fmt_pf(a['pf'])} | ${a['net']:+.2f} | " + " | ".join(bands) +
                     f" | {unk} | {r7['n']}, {r7['losses']}, {fmt_pf(r7['pf'])}, ${r7['net']:+.2f} | {r23['n']}, {r23['losses']}, {fmt_pf(r23['pf'])}, ${r23['net']:+.2f} | "
                     + (f"{100 * hr:.2f}% ({hn})" if hr is not None else "none") + " |")
        if hr is not None and r7["n"] > 0:
            p = binom_sf(r7["losses"], r7["n"], hr)
            if p < P_FLAG:
                flags.append(f"{name}: last 7 days {r7['losses']} losses in {r7['n']} ({100 * r7['losses'] / r7['n']:.1f}%) against a history loss rate of {100 * hr:.2f}%, one-sided binomial p {p:.4f}")
        if r7["n"] >= PF_MIN_N and r7["pf"] < PF_FLAG:
            flags.append(f"{name}: last 7 days PF {fmt_pf(r7['pf'])} on {r7['n']} settled (under {PF_FLAG} with at least {PF_MIN_N})")
    lines += ["", "**Flags:** " + ("; ".join(flags) if flags else "none (no market's last 7 days differ from its history by the two registered tests)"),
              "", "Dollars at the real sizes, after fees, settled orders only (an exit counts as a loss). PF by price paid covers held-to-settlement orders only (an exit's buy price cannot be solved from its result, so exits, most of the losses, are left out of those three columns and the bands read high); count of orders in brackets. Information only; nothing here changes a live rule.", ""]
    block = "\n".join(lines) + "\n"
    head = "# LIVEWATCH: live L1 record against its history (newest first; aggregates only; `python -m scalper.livewatch run`)\n\n"
    old = OUT.read_text() if OUT.exists() else head
    body = old[len(head):] if old.startswith(head) else old
    OUT.write_text(head + block + body)
    print(block)
    return flags


if __name__ == "__main__":
    {"run": run}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
