"""DRIFT: a nightly check that the bot still does what L1's history rule does on the same markets and minutes. Research only; it reads, it never acts.
Usage: python -m scalper.drift run     (the AUTO loop runs it once a day, right after `scalper.livewatch run`)

Live rows: the newest raw report the live watcher saved in the scratchpad (LIVEWATCH_RAW_DIR) if it is under 3 hours old, else one fresh read
of the report endpoint through `livewatch.fetch()` (KALSHI_REPORT_TOKEN is read inside Python, never printed). Raw rows stay in the scratchpad;
kalshi-scalper/workers/DRIFT.md gets aggregates only, newest first, time in US Central.

History rule (`lstrats.favorite`, the same rule every L1 study uses): the candle that ENDS exactly 360 s (6 minute look) or 600 s (10 minute look)
before the close, YES at its closing ask, NO at 1 minus its closing bid, entered when that price is 0.88 to 0.97, held to settlement. Candles from
data/fresh.sqlite (refreshed by `scalper.fresh_update`, which the AUTO loop runs every 6 hours), then the older research files for markets fresh
does not hold. Nothing earlier or later than the exact minute is substituted; a missing candle is counted as "no candle", never as "no entry".

Per market (gold, Bitcoin, Ethereum, Dogecoin, XRP), last 7 and last 30 days (by the order's send time, or the market's close for history entries):
1. Coverage. Every live order sent (filled or not): the history rule's decision at the order's own look (entryLead, or from the send time when an
   old order has none: more than 8 minutes before the close is the 10 minute look). Same side and in band = match; else "history: no entry",
   "history: other side" or "no candle". And every history entry at the bot's look for that market (the look of the nearest live order of that
   market in time) with no live order on that market, labelled by the first reason that fits: not live yet (before that market's first
   live order in the report, less 90 minutes); XRP after its last live order (paused in code
   2026-10-28); bot not trading (no live order on any market within 90 minutes); one crypto per window (another of Bitcoin, Ethereum, XRP and
   Dogecoin has a filled order closing in the same window); smooth gate (Bitcoin or Ethereum after 2026-10-23 15:15 UTC whose history path to the
   decision candle is not a smooth climb: 4 or more earlier candles, no minute step under -0.005, climb 0.10 or more; the history path stops at the
   decision candle, the bot's read may include the next minute's partial candle, so this label is approximate); else "other" (loss stop, window
   cap, shard money, a quote that differed at send time, anything this cannot see).
2. Slippage. Held filled orders only (exits cannot be priced): price paid (solved from settledPnl and count, `livewatch.price_paid`) minus the
   history candle's closing ask of the SAME side at the decision minute, in cents. Positive = the bot paid more than the candle's close.
3. Result drift. Live loss rate (filled and settled, settledPnl below zero, an exit counts as a loss) against the history rule's loss rate on the
   same market at the bot's look, restricted to the US Central days on which that market had a filled live order; and on the matched orders
   (both took the same side), the live loss rate against the history rule's own outcome for those same markets (held to settlement).
Flags (only these): slippage mean above 1c with at least 30 priced orders; a coverage mismatch share above 20% with at least 30 orders in the
denominator (live orders the history rule would not have taken, of those with a candle; or "other" misses, of all history entries the bot did not
take). Information only; nothing here changes a live rule.
"""
from __future__ import annotations

import bisect
import json
import sqlite3
import statistics as st
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import livewatch as LW
from .lstrats import favorite
from .paths import DATA_DIR

CT, ET = ZoneInfo("America/Chicago"), ZoneInfo("America/New_York")
OUT = DATA_DIR.parent / "workers" / "DRIFT.md"
MARKETS = LW.MARKETS
SERIES = set(MARKETS.values())
CAPPED = {"KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"}
SMOOTH = {"KXBTC15M", "KXETH15M"}
SMOOTH_FROM = int(datetime(2026, 10, 23, 15, 15, tzinfo=timezone.utc).timestamp())   # last 10 minute Bitcoin order 15:05Z; first smooth-gated look after it
BAND = (0.88, 0.97)
SOURCES = ["fresh", "rep", "book", "l1b", "e3b", "alts2", "alts3", "alts4"]        # first file holding a ticker wins
RAW_MAX_AGE_S = 3 * 3600
SLIP_FLAG_C, COV_FLAG, FLAG_MIN_N = 1.0, 0.20, 30
OFF_GAP_S = 90 * 60
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def close_from_ticker(tk: str) -> int | None:
    """KXGOLD15M-26OCT291400-00 closes 2026-10-29 14:00 US Eastern."""
    try:
        p = tk.split("-")[1]
        dt = datetime(2000 + int(p[:2]), MON[p[2:5]], int(p[5:7]), int(p[7:9]), int(p[9:11]), tzinfo=ET)
        return int(dt.timestamp())
    except Exception:
        return None


def live_report() -> dict:
    files = sorted(LW.RAW_DIR.glob("report_*.json")) if LW.RAW_DIR.exists() else []
    if files and time.time() - files[-1].stat().st_mtime < RAW_MAX_AGE_S:
        return json.loads(files[-1].read_text())
    return LW.fetch()


def load_markets(since_ts: int) -> dict:
    """{ticker: {"series", "close", "res", "c": {end: (bid, ask)}}} for the five markets closing at or after since_ts."""
    out: dict = {}
    for name in SOURCES:
        path = DATA_DIR / f"{name}.sqlite"
        if not path.exists():
            continue
        try:
            db = sqlite3.connect(path)
            q = ("SELECT c.ticker, c.series, c.end_ts, c.bid_c, c.ask_c, m.close_ts, m.result FROM candle c JOIN market m ON m.ticker = c.ticker "
                 f"WHERE m.close_ts >= ? AND m.series IN ({','.join('?' * len(SERIES))})")
            mine: dict = {}
            for tk, s, end, b, a, close, res in db.execute(q, (since_ts, *sorted(SERIES))):
                if tk in out:
                    continue
                m = mine.setdefault(tk, {"series": s, "close": close, "res": res, "c": {}})
                if b is not None and a is not None:
                    m["c"][end] = (b, a)
            out.update(mine)
        except sqlite3.Error:
            continue
    return out


def side_ask(bid: float, ask: float, side: str) -> float:
    return ask if side == "yes" else round(1 - bid, 4)


def smooth_path(m: dict, side: str, t: int) -> bool:
    ends = sorted(e for e in m["c"] if e <= t)
    mids = [((m["c"][e][0] + m["c"][e][1]) / 2 if side == "yes" else 1 - (m["c"][e][0] + m["c"][e][1]) / 2) for e in ends]
    if len(mids) < 5:
        return False
    steps = [y - x for x, y in zip(mids, mids[1:])]
    return min(steps) >= -0.005 and mids[-1] - mids[0] >= 0.10


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def run():
    d = live_report()
    now = datetime.now(timezone.utc)
    since = datetime.fromisoformat(d["sinceUtc"].replace("Z", "+00:00"))
    orders = []
    for o in d.get("orders", []):
        s = (o.get("ticker") or "").split("-")[0]
        if s not in SERIES:
            continue
        close = close_from_ticker(o["ticker"])
        if close is None:
            continue
        ts = int(datetime.fromisoformat(o["ts"].replace("Z", "+00:00")).timestamp())
        lead = o.get("entryLead") or ("10m" if close - ts > 480 else "6m")
        orders.append({**o, "series": s, "close": close, "tsec": ts, "lead": lead, "left": 600 if lead == "10m" else 360,
                       "filled": (o.get("count") or 0) > 0 and o.get("status") == "filled"})
    all_ts = sorted(int(datetime.fromisoformat(o["ts"].replace("Z", "+00:00")).timestamp()) for o in d.get("orders", []))
    M = load_markets(int(since.timestamp()) - 3600)
    newest_candle = max((max(m["c"]) for m in M.values() if m["c"]), default=0)
    # Each live order against the history rule at its own look.
    for o in orders:
        m = M.get(o["ticker"])
        c = m["c"].get(o["close"] - o["left"]) if m else None
        o["h_ask_same"] = side_ask(c[0], c[1], o["side"]) if c else None
        pick = favorite(c[0], c[1], BAND) if c else None
        o["cov"] = "no candle" if c is None else ("match" if pick and pick[0] == o["side"] else ("history: other side" if pick else "history: no entry"))
        o["p"] = LW.price_paid(o) if o["filled"] else None
        o["slip"] = round(100 * (o["p"] - o["h_ask_same"]), 2) if o["p"] is not None and o["h_ask_same"] is not None else None
    # History entries at the bot's look per market, and why the bot did not take them.
    by_s: dict = defaultdict(list)
    for o in orders:
        by_s[o["series"]].append(o)
    for s in by_s:
        by_s[s].sort(key=lambda o: o["tsec"])
    live_tk = {o["ticker"] for o in orders}
    crypto_filled = defaultdict(set)
    for o in orders:
        if o["filled"] and o["series"] in CAPPED:
            crypto_filled[o["close"]].add(o["series"])
    hist = []
    for tk, m in M.items():
        s, close = m["series"], m["close"]
        if not by_s.get(s) or close > now.timestamp():
            continue
        ol = by_s[s]
        i = bisect.bisect_left([x["tsec"] for x in ol], close)
        near = min((ol[j] for j in (i - 1, i) if 0 <= j < len(ol)), key=lambda x: abs(x["tsec"] - close))
        left = near["left"]
        c = m["c"].get(close - left)
        pick = favorite(c[0], c[1], BAND) if c else None
        if not pick:
            continue
        h = {"ticker": tk, "series": s, "close": close, "side": pick[0], "price": pick[1], "res": m["res"], "left": left}
        h["lost"] = None if m["res"] not in ("yes", "no") else int((m["res"] == "yes") != (pick[0] == "yes"))
        if tk in live_tk:
            h["why"] = "taken"
        else:
            dec = close - left
            k = bisect.bisect_left(all_ts, dec - OFF_GAP_S)
            last_s = ol[-1]["tsec"]
            if dec < ol[0]["tsec"] - OFF_GAP_S:
                h["why"] = "not live yet"
            elif s == "KXXRP15M" and dec > last_s and close >= int(datetime(2026, 10, 27, 12, tzinfo=CT).timestamp()):
                h["why"] = "paused (XRP)"
            elif not (k < len(all_ts) and all_ts[k] <= dec + OFF_GAP_S):
                h["why"] = "bot not trading"
            elif s in CAPPED and crypto_filled[close] - {s}:
                h["why"] = "one crypto per window"
            elif s in SMOOTH and dec >= SMOOTH_FROM and not smooth_path(m, pick[0], dec):
                h["why"] = "smooth gate"
            else:
                h["why"] = "other"
        hist.append(h)
    cut = {"7d": now - timedelta(days=7), "30d": now - timedelta(days=30)}
    lines = [f"## {datetime.now(CT):%Y-%m-%d %H:%M} CT (report window {since.astimezone(CT):%Y-%m-%d %H:%M} CT to now; history candles up to "
             f"{datetime.fromtimestamp(newest_candle, CT):%Y-%m-%d %H:%M} CT)", ""]
    if d.get("ordersTruncated"):
        lines.append("Note: the report truncated its order rows (2,000 cap); the older part of the window is missing.\n")
    cov_rows, slip_rows, res_rows, flags = [], [], [], []
    for win, t0 in cut.items():
        t0s = int(t0.timestamp())
        for name, s in MARKETS.items():
            lo = [o for o in orders if o["series"] == s and o["tsec"] >= t0s]
            cc = Counter(o["cov"] for o in lo)
            withc = len(lo) - cc["no candle"]
            mism = withc - cc["match"]
            hs = [h for h in hist if h["series"] == s and h["close"] >= t0s]
            miss = [h for h in hs if h["why"] != "taken"]
            wc = Counter(h["why"] for h in miss)
            cov_rows.append(f"| {win} | {name} | {len(lo)} | {cc['match']} | {cc['history: no entry']} | {cc['history: other side']} | {cc['no candle']} | {pct(mism, withc)} | "
                            f"{len(hs)} | {len(hs) - len(miss)} | {wc['not live yet']} | {wc['paused (XRP)']} | {wc['bot not trading']} | {wc['one crypto per window']} | {wc['smooth gate']} | {wc['other']} | {pct(wc['other'], len(hs))} |")
            if withc >= FLAG_MIN_N and mism / withc > COV_FLAG:
                flags.append(f"{name} {win}: {mism} of {withc} live orders ({pct(mism, withc)}) are not what the history rule takes at that look")
            if len(hs) >= FLAG_MIN_N and wc["other"] / len(hs) > COV_FLAG:  # "not live yet" entries stay in the denominator: they are expected misses
                flags.append(f"{name} {win}: {wc['other']} of {len(hs)} history entries ({pct(wc['other'], len(hs))}) were not taken for no reason this can see")
            sl = [o["slip"] for o in lo if o["slip"] is not None]
            if sl:
                q = st.quantiles(sl, n=10) if len(sl) >= 10 else None
                dist = Counter(max(-2, min(3, round(x))) for x in sl)
                slip_rows.append(f"| {win} | {name} | {len(sl)} | {st.mean(sl):+.2f} | {st.median(sl):+.1f} | " + (f"{q[0]:+.1f} / {q[-1]:+.1f}" if q else "n/a") + " | "
                                 + " | ".join(str(dist[k]) for k in (-2, -1, 0, 1, 2, 3)) + " |")
                if len(sl) >= FLAG_MIN_N and st.mean(sl) > SLIP_FLAG_C:
                    flags.append(f"{name} {win}: slippage mean {st.mean(sl):+.2f}c on {len(sl)} held orders (above {SLIP_FLAG_C:.0f}c)")
            else:
                slip_rows.append(f"| {win} | {name} | 0 | n/a | n/a | n/a | 0 | 0 | 0 | 0 | 0 | 0 |")
            lf = [o for o in lo if o["filled"] and o.get("settledPnl") is not None]
            ll = sum(1 for o in lf if o["settledPnl"] < 0)
            days = {datetime.fromtimestamp(o["close"], CT).date() for o in lf}
            hd = [h for h in hs if h["lost"] is not None and datetime.fromtimestamp(h["close"], CT).date() in days]
            hl = sum(h["lost"] for h in hd)
            hm = {h["ticker"]: h for h in hs if h["lost"] is not None}
            mt = [o for o in lf if o["cov"] == "match" and o["ticker"] in hm]
            ml, mh = sum(1 for o in mt if o["settledPnl"] < 0), sum(hm[o["ticker"]]["lost"] for o in mt)
            un = [o for o in lf if o["cov"] != "match"]
            ul = sum(1 for o in un if o["settledPnl"] < 0)
            res_rows.append(f"| {win} | {name} | {len(lf)} | {ll} ({pct(ll, len(lf))}) | {len(days)} | {len(hd)} | {hl} ({pct(hl, len(hd))}) | {len(mt)} | {pct(ml, len(mt))} | {pct(mh, len(mt))} | {len(un)}, {ul} ({pct(ul, len(un))}) |")
    lines += ["**1. Coverage.** Live orders sent (filled or not) against the history rule at the order's own look; history entries at the bot's look the bot did not take, by reason.", "",
              "| Window | Market | Live orders | Match | History: no entry | History: other side | No candle | Mismatch share (of those with a candle) | History entries | Taken | Not live yet | Paused (XRP) | Bot not trading | One crypto per window | Smooth gate | Other | Other share |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|", *cov_rows, "",
              "**2. Slippage** (held filled orders: price paid minus the history candle's closing ask of the same side at the decision minute, cents; positive = paid more).", "",
              "| Window | Market | Priced | Mean | Median | 10th / 90th pct | <=-2c | -1c | 0c | +1c | +2c | >=+3c |", "|---|---|---|---|---|---|---|---|---|---|---|---|", *slip_rows, "",
              "**3. Result drift.** Live loss rate (filled, settled; an exit counts as a loss) against the history rule at the bot's look on the same market and the same US Central days; and on matched orders, live against the history rule's own outcome for the same markets.", "",
              "| Window | Market | Live settled | Live losses | Days | History entries those days | History losses | Matched | Live loss rate (matched) | History loss rate (matched) | Live orders the history rule would not take: settled, losses |",
              "|---|---|---|---|---|---|---|---|---|---|---|", *res_rows, "",
              "**Flags:** " + ("; ".join(flags) if flags else "none (slippage mean at most 1c, or under 30 priced orders; coverage mismatch at most 20%, or under 30 orders)"),
              "", "Aggregates only; raw rows stay in the scratchpad. A live order the history rule would not take is usually a quote that moved between the candle's close and the send a few seconds later; "
              "the bot reads the market object, the history reads the minute candle. Information only; nothing here changes a live rule.", ""]
    block = "\n".join(lines) + "\n"
    head = "# DRIFT: the bot's live orders against L1's history rule on the same markets and minutes (newest first; aggregates only; `python -m scalper.drift run`)\n\n"
    old = OUT.read_text() if OUT.exists() else head
    body = old[len(head):] if old.startswith(head) else old
    OUT.write_text(head + block + body)
    print(block)
    return flags


def run_all():
    flags = run()
    try:   # Dogecoin fill rate around the 3 to 5 contract deploy (owner, 2026-10-29); one failure never stops drift
        from .dogefill import run as dogefill
        dogefill()
    except Exception as ex:
        print(f"dogefill failed: {type(ex).__name__}: {str(ex)[:160]}")
    try:   # gold slippage by order size (owner, 2026-10-29: the second deposit hinges on it)
        from .goldslip import run as goldslip
        goldslip()
    except Exception as ex:
        print(f"goldslip failed: {type(ex).__name__}: {str(ex)[:160]}")
    try:   # visible size behind the Bitcoin open interest signals, from recorder R6 (OIFILL, 2026-10-30)
        from .oifill import run as oifill
        oifill()
    except Exception as ex:
        print(f"oifill failed: {type(ex).__name__}: {str(ex)[:160]}")
    return flags


if __name__ == "__main__":
    {"run": run_all}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
