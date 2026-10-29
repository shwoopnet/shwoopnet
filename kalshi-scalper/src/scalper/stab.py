"""STAB: weekly stability check of L1 exactly as live trades it now, on public 15 minute candles. Research only, read-only: no hypothesis,
no try, no verdict word, nothing here changes a live rule.
Usage: python -m scalper.stab week   (refreshes data/fresh.sqlite with `scalper.fresh_update` first, then writes a section at the top of
                                      workers/STABILITY.md and marks the week in data/stab_last_week; `scalper.autoscore` runs it on its
                                      first pass on or after Monday 01:00 US Central)

The live rule, as read from functions/kalshiLiveLib.js on 2026-10-29 (read only):
  L1_SERIES order gold, XRP, Bitcoin, Dogecoin, Ethereum, then the probes; PAUSED_SERIES = XRP and the three probes, so the
  candidates are gold, Bitcoin, Dogecoin, Ethereum, all at the 6 minute look (EARLY_PROBE_SERIES holds only paused XRP and gas).
  Band 0.88 to 0.97: YES at its ask, else NO at 1 minus the YES bid (l1Pick / lstrats.favorite), held to settlement.
  SMOOTH_SERIES (Bitcoin, Ethereum): pathShape's smooth climb on the bought side's mids, at least 4 earlier candles, every minute change
  >= -0.005 and a climb >= 0.10 (plain float arithmetic, as in the JS).
  CAPPED_SERIES (Bitcoin, Ethereum, XRP, Dogecoin): one order per 15 minute window, first in L1_SERIES order wins (Bitcoin, then
  Dogecoin, then Ethereum); gold is outside the rule.
Approximations (stated in every section):
  - the decision quote is the 1 minute candle ending exactly 360 s before the close (live decides on the market's quote at 330 to 400 s);
  - the smooth path is every candle of the market up to and including that decision candle, candles without a bid or ask skipped
    (sideMids skips non-finite quotes the same way); live may also see the in-progress minute;
  - every order is assumed to fill (live: an unfilled order does not hold the crypto window), 1 contract per market, so the window
    dollar cap, the loss stop and the 25c exit are not modelled (the exit only ever sells a falling position; held-to-settlement here).
Per market: entries, losses, loss rate, PF and net per contract at 1 contract with the rounded fee (ceil of 7% x p x (1-p) in cents).
Flags (only these): (1) the 7 day loss rate above the market's long-run rate with a one-sided binomial p under 0.01, against the
`scalper.tstop1.load()` history (6 minute look, no smooth gate, no window rule) OR against this live rule's own history, both before the
7 day window; (2) the 4 week PF under 0.8 on at least 100 entries.
"""
from __future__ import annotations

import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .l1studies import fee
from .lstrats import favorite
from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
ROOT = DATA_DIR.parent
OUT = ROOT / "workers" / "STABILITY.md"
MARK = DATA_DIR / "stab_last_week"
LEFT, BAND = 360, (0.88, 0.97)
ORDER = ["KXGOLD15M", "KXXRP15M", "KXBTC15M", "KXDOGE15M", "KXETH15M"]   # L1_SERIES order (probes after; all paused)
PAUSED = {"KXXRP15M"}                                                   # plus the probes, which are not loaded at all
LIVE = [s for s in ORDER if s not in PAUSED]
SMOOTH = {"KXBTC15M", "KXETH15M"}
CAPPED = {"KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"}
SMOOTH_MIN_STEP, SMOOTH_MIN_CLIMB = 0.005, 0.10
NAMES = {"KXGOLD15M": "gold", "KXBTC15M": "Bitcoin", "KXDOGE15M": "Dogecoin", "KXETH15M": "Ethereum"}
SOURCES = ["l1b", "book", "e3b", "alts2", "fresh"]          # oldest first; a later file's copy of a market replaces an earlier one
P_FLAG, PF_FLAG, PF_MIN_N = 0.01, 0.8, 100


def load(series=LIVE) -> dict:
    """ticker -> (series, [(end, bid, ask)] with both quotes present, close_ts, result)."""
    mk = {}
    q = ",".join("?" * len(series))
    for name in SOURCES:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        mine = defaultdict(list)
        meta = {tk: (s, c, r) for tk, s, c, r in db.execute(f"SELECT ticker, series, close_ts, result FROM market WHERE series IN ({q})", series)}
        for tk, end, b, a in db.execute(f"SELECT ticker, end_ts, bid_c, ask_c FROM candle WHERE series IN ({q}) ORDER BY ticker, end_ts", series):
            if b is not None and a is not None:
                mine[tk].append((end, b, a))
        for tk, (s, c, r) in meta.items():
            if mine.get(tk):
                mk[tk] = (s, mine[tk], c, r)
        db.close()
    return mk


def path_shape(cands, side, t):
    """pathShape on the side's mids up to the decision candle (end <= t)."""
    mids = [((b + a) / 2 if side == "yes" else 1 - (b + a) / 2) for e, b, a in cands if e <= t]
    if not mids:
        return False
    steps = [v - mids[i] for i, v in enumerate(mids[1:])]
    earlier = len(mids) - 1
    return earlier >= 4 and bool(steps) and min(steps) >= -SMOOTH_MIN_STEP and (mids[-1] - mids[0]) >= SMOOTH_MIN_CLIMB


def entries(mk: dict) -> list[dict]:
    """Live-rule entries, one per market at most, with the one crypto order per window rule applied in L1_SERIES order."""
    cand = defaultdict(dict)
    for tk, (s, cs, close, res) in mk.items():
        if res not in ("yes", "no"):
            continue
        t = close - LEFT
        c = next((x for x in cs if x[0] == t), None)
        if c is None:
            continue
        pick = favorite(c[1], c[2], BAND)
        if pick is None:
            continue
        side, price = pick
        if s in SMOOTH and not path_shape(cs, side, t):
            continue
        won = 1 if (res == "yes") == (side == "yes") else 0
        cand[close][s] = {"ticker": tk, "series": s, "close_ts": close, "side": side, "price": price, "won": won, "net": won - price - fee(price, 1)}
    out = []
    for close, by in cand.items():
        taken = False
        for s in ORDER:
            e = by.get(s)
            if not e:
                continue
            if s in CAPPED:
                if taken:
                    continue
                taken = True
            out.append(e)
    return sorted(out, key=lambda e: e["close_ts"])


def pf(xs):
    w, l = sum(x for x in xs if x > 0), -sum(x for x in xs if x < 0)
    return w / l if l > 0 else (float("inf") if w > 0 else 0.0)


def fmt_pf(x):
    return "n/a" if x == 0 else ("no loss" if x == float("inf") else f"{x:.2f}")


def binom_sf(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    if k <= 0 or n <= 0:
        return 1.0
    return min(1.0, sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def tally(es):
    v = [e["net"] for e in es]
    los = sum(1 for e in es if not e["won"])
    return dict(n=len(v), losses=los, lr=los / len(v) if v else None, pf=pf(v), net=sum(v) / len(v) if v else None)


def cell(t):
    if not t["n"]:
        return "0, -, -, -, -"
    return f"{t['n']}, {t['losses']}, {100 * t['lr']:.1f}%, {fmt_pf(t['pf'])}, {100 * t['net']:+.2f}c"


def windows(now: datetime):
    """(start of the 7 day window, end, start of the previous 4 weeks) as unix seconds: the newest 7 FULL US Central days."""
    end_day = now.astimezone(CT).date()                     # today, not full: the window ends at today's 00:00 CT
    end = datetime(end_day.year, end_day.month, end_day.day, tzinfo=CT)
    s7 = end - timedelta(days=7)
    s35 = s7 - timedelta(days=28)
    return int(s7.timestamp()), int(end.timestamp()), int(s35.timestamp()), s7.date(), (end - timedelta(days=1)).date(), s35.date()


def week_key(now: datetime) -> str:
    """The Monday 01:00 CT boundary at or before now (the week this run belongs to)."""
    n = now.astimezone(CT)
    mon = (n - timedelta(days=n.weekday())).replace(hour=1, minute=0, second=0, microsecond=0)
    if n < mon:
        mon -= timedelta(days=7)
    return mon.strftime("%Y-%m-%d")


def week():
    try:
        from . import fresh_update
        fresh_update.main()
        fresh_note = "fresh_update ran"
    except Exception as ex:                                  # a failed refresh still reports, on the data already stored
        fresh_note = f"fresh_update FAILED ({type(ex).__name__}: {str(ex)[:80]}); read on the data already stored"
    now = datetime.now(timezone.utc)
    s7, end, s35, d7a, d7b, d35 = windows(now)
    mk = load()
    ents = entries(mk)
    from .tstop1 import load as tload
    hist = defaultdict(lambda: [0, 0, []])                   # tstop1 history before the 7 day window: n, losses, nets
    hist_all = defaultdict(lambda: [0, 0, []])
    for r in tload():
        if r["series"] not in LIVE:
            continue
        net = r["won"] - r["price"] - fee(r["price"], 1)
        for h, ok in ((hist_all, True), (hist, r["close_ts"] < s7)):
            if ok:
                h[r["series"]][0] += 1; h[r["series"]][1] += 1 - r["won"]; h[r["series"]][2].append(net)
    rows, flags = [], []
    for s in LIVE:
        mine = [e for e in ents if e["series"] == s]
        t7 = tally([e for e in mine if s7 <= e["close_ts"] < end])
        t28 = tally([e for e in mine if s35 <= e["close_ts"] < s7])
        trule = tally([e for e in mine if e["close_ts"] < s7])
        nmk7 = sum(1 for tk, m in mk.items() if m[0] == s and s7 <= m[2] < end)
        hn, hl, hv = hist[s]
        an, al, av = hist_all[s]
        hr = hl / hn if hn else None
        p_t = binom_sf(t7["losses"], t7["n"], hr) if hr and t7["n"] else 1.0
        p_r = binom_sf(t7["losses"], t7["n"], trule["lr"]) if trule["lr"] and t7["n"] else 1.0
        name = NAMES[s]
        rows.append(f"| {name} | {nmk7} | {cell(t7)} | {cell(t28)} | {an}, {al}, {100 * al / an:.2f}%, {fmt_pf(pf(av))}, {100 * sum(av) / an:+.2f}c | "
                    f"{cell(trule)} | {p_t:.4f} / {p_r:.4f} |" if an else f"| {name} | {nmk7} | {cell(t7)} | {cell(t28)} | none | {cell(trule)} | - |")
        if t7["n"] and hr is not None and t7["lr"] > hr and p_t < P_FLAG:
            flags.append(f"{name}: 7 days {t7['losses']} losses in {t7['n']} ({100 * t7['lr']:.1f}%) against the tstop1 history {100 * hr:.2f}% (n {hn}), p {p_t:.4f}")
        if t7["n"] and trule["lr"] is not None and t7["lr"] > trule["lr"] and p_r < P_FLAG:
            flags.append(f"{name}: 7 days {t7['losses']} losses in {t7['n']} ({100 * t7['lr']:.1f}%) against this rule's own history {100 * trule['lr']:.2f}% (n {trule['n']}), p {p_r:.4f}")
        if t28["n"] >= PF_MIN_N and t28["pf"] < PF_FLAG:
            flags.append(f"{name}: previous 4 weeks PF {fmt_pf(t28['pf'])} on {t28['n']} entries (under {PF_FLAG} with at least {PF_MIN_N})")
    first = datetime.fromtimestamp(min(e["close_ts"] for e in ents), CT).date() if ents else "-"
    sec = [f"## {now.astimezone(CT).strftime('%Y-%m-%d %H:%M CT')}: 7 days {d7a} to {d7b} CT, previous 4 weeks {d35} to {d7a - timedelta(days=1)} CT",
           "",
           "| Market | Markets in the 7 days | 7 days: n, losses, loss rate, PF, net/contract | Previous 4 weeks: n, losses, loss rate, PF, net/contract | "
           "Long-run tstop1 (6 min, all history): n, losses, loss rate, PF, net/contract | This rule's history before the 7 days: n, losses, loss rate, PF, net/contract | p (7 day losses vs tstop1 / vs rule history) |",
           "|---|---|---|---|---|---|---|", *rows, "",
           "**Flags:** " + ("; ".join(flags) if flags else "none (no 7 day loss rate above its long-run rate at p < 0.01; no 4 week PF under 0.8 on 100 or more entries)"),
           "",
           f"L1 as live trades it on 2026-10-29: gold, Bitcoin, Dogecoin, Ethereum at the 6 minute look, band 88c to 97c, held to settlement; Bitcoin and Ethereum on the smooth climb only "
           f"(pathShape, at least 4 earlier candles, worst minute >= -0.005, climb >= 0.10); one order per window among Bitcoin, Dogecoin, Ethereum in that order; XRP and the probes paused. "
           f"1 contract, rounded fee, every order assumed filled; decision candle ends 360 s before the close; window cap, loss stop and 25c exit not modelled. "
           f"The tstop1 column has no smooth gate and no window rule (so for Bitcoin and Ethereum it is a different, ungated rule); its loss rate before the 7 day window is the flag baseline, and so is "
           f"the rule's own history (from {first}). Public candles ({fresh_note}). Information only; nothing here changes a live rule.", ""]
    head = "# STABILITY: L1 as live trades it, on public candles (newest first; aggregates only; `python -m scalper.stab week`)\n\n"
    body = OUT.read_text()[len(head):] if OUT.exists() and OUT.read_text().startswith(head) else ""
    OUT.write_text(head + "\n".join(sec) + "\n" + body)
    MARK.write_text(week_key(now))
    print("\n".join(sec))
    print("STAB done: " + ("; ".join(flags) if flags else "no flags"))


if __name__ == "__main__":
    {"week": week}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
