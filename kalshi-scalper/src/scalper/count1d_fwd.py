"""COUNT1D: forward-only test of the COUNT1 pace model on the DAILY Truth Social post-count brackets (workers/COUNT1D_REGISTRATION.md). Research only.

    python -m scalper.count1d_fwd snapshot [--date YYYY-MM-DD]   record the day in progress at the registered look (information only, no outcome)
    python -m scalper.count1d_fwd gate                           the SOURCE gate on settled forward days (reads which bracket won, no price, no P&L)
    python -m scalper.count1d_fwd takeup                         information-only take-up, refuses before 20 snapshot days
    python -m scalper.count1d_fwd forward [--force-info]         THE one read: at 150 forward trades or 2027-03-01, once (fwdread guard)

Only ET days starting on or after 2026-11-04 are ever used. Public Kalshi API and CNN's public archive; no key, no order. The model, fee, selection and quote
rules are imported unchanged from count1.py.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from . import api
from . import count1 as c1
from . import fwdread as fr
from .candlefield import quote_close
from .paths import DATA_DIR

ET = c1.ET
SERIES = "KXTRUTHSOCIALD"
LOOK_H = 12.0
FWD_START = datetime(2026, 11, 4, tzinfo=ET).astimezone(timezone.utc)
DUE = fr.utc(2027, 3, 1)
TRADES_DUE = 150
GATE_MIN_DAYS, GATE_SHARE, TAKEUP_MIN_DAYS = 20, 0.90, 20
SNAP_AFTER_MIN = 16          # the 15 minute fill window must be complete, as in the read
SNAP_FIELDS = ["date", "ticker", "strike_type", "floor_strike", "cap_strike", "look_utc", "archive_count_c", "mu", "p_model", "signal_ask", "fill_ask",
               "in_band", "signal", "selected", "archive_fetched_utc", "archive_latest_post_utc"]
SNAP_FILE = DATA_DIR / "count1d_snapshots.csv"
SLEEP = 0.4


# ------------------------------------------------------------------ data sources (replaced in tests)

def get_posts():
    """(sorted UTC datetimes of every archive post, fetch time)."""
    req = urllib.request.Request(c1.ARCHIVE, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    return sorted(datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")) for x in d), datetime.now(timezone.utc)


def list_markets():
    """Every KXTRUTHSOCIALD market that closes after the forward start (any status)."""
    out, cursor = [], None
    while True:
        p = {"series_ticker": SERIES, "min_close_ts": int(FWD_START.timestamp()), "limit": 1000}
        if cursor:
            p["cursor"] = cursor
        d = api._get("/markets", p)
        out += d.get("markets", [])
        cursor = d.get("cursor")
        if not cursor:
            return out


def get_candles(ticker, look):
    """[(end_ts, ask close)] one minute candles in [look - 60 min, look + 15 min]."""
    a, b = int((look - timedelta(minutes=60)).timestamp()), int((look + timedelta(minutes=15)).timestamp())
    d = api._get(f"/series/{SERIES}/markets/{ticker}/candlesticks", {"start_ts": a, "end_ts": b, "period_interval": 1})
    time.sleep(SLEEP)
    return [(x["end_period_ts"], quote_close(x.get("yes_ask"))) for x in d.get("candlesticks", [])]


# ------------------------------------------------------------------ pure pieces

def forward_events(markets):
    """[(period start, event ticker, markets, (start, end))] for daily periods starting on or after FWD_START, by date."""
    ev = {}
    for m in markets:
        ev.setdefault(m["event_ticker"], []).append(m)
    out = []
    for e, L in ev.items():
        per = c1.parse_period(L[0])
        if per and per[0] >= FWD_START and (per[1] - per[0]) <= timedelta(hours=26):
            out.append((per[0], e, L, per))
    return sorted(out, key=lambda x: x[0])


def day_rows(posts, per, L, candles, r=c1.R_DISP):
    """Per-bracket rows for one day: dicts with ticker, p, sig, ask. Skipped (no valid quote) markets are counted."""
    look, c, mu, pmf = c1.model(posts, per[0], per[1], LOOK_H, r)
    rows, skipped = [], 0
    for m in L:
        q = c1.fill_ask(candles.get(m["ticker"]) or [], look)
        if not q:
            skipped += 1
            continue
        rows.append({"m": m, "ticker": m["ticker"], "p": c1.bracket_prob(m, c, pmf), "sig": q[0], "ask": q[1]})
    return look, c, mu, rows, skipped


def day_selected(rows):
    return {t for t, _p, _a in c1.select([(x["ticker"], x["p"], x["ask"]) for x in rows])}


def source_total_ok(posts, per, L):
    """True/False: the archive total over the ET day (definition D1, every post) is inside the winning bracket; None when not settled."""
    win = [m for m in L if m.get("result") == "yes"]
    if not win or any(m.get("result") not in ("yes", "no") for m in L):
        return None
    tot = sum(1 for x in posts if per[0] <= x < per[1])
    return c1.bracket_prob(win[0], tot, [1.0]) > 0


def gate_status(oks):
    """oks: source_total_ok per settled forward day in date order. Latched: any prefix of >= 20 days under 90% is VOID."""
    n = len(oks)
    if n < GATE_MIN_DAYS:
        return "PENDING", n, (sum(oks) / n if n else None)
    hit = 0
    for i, ok in enumerate(oks, 1):
        hit += bool(ok)
        if i >= GATE_MIN_DAYS and hit / i < GATE_SHARE:
            return "VOID", n, sum(oks) / n
    return "OK", n, sum(oks) / n


def verdict(n, mean, pf, h1, h2, ctrl_mean, gate):
    if gate == "VOID":
        return "VOID"
    if n < TRADES_DUE:
        return "NOT_ENOUGH_DATA"
    if mean <= 0 or pf < 1.5 or h1 <= 0 or h2 <= 0 or (mean - ctrl_mean) < 0.01:
        return "FALSIFIED"
    return "SURVIVES (forward only; nothing is promoted)"


# ------------------------------------------------------------------ snapshot / takeup

def _cap(x):
    return "" if x is None else x


def snapshot(argv, now=None, posts_fn=None, markets_fn=None, candles_fn=None, path=None, out=print):
    now = now or datetime.now(timezone.utc)
    path = path or SNAP_FILE
    day = None
    if "--date" in argv:
        day = datetime.strptime(argv[argv.index("--date") + 1], "%Y-%m-%d").replace(tzinfo=ET)
    else:
        day = now.astimezone(ET).replace(hour=0, minute=0, second=0, microsecond=0)
    start = day.astimezone(timezone.utc)
    if start < FWD_START:
        out(f"REFUSED: {day:%Y-%m-%d} is before 2026-11-04 (the registered forward start). Nothing was read.")
        return 2
    look = start + timedelta(hours=LOOK_H)
    if now < look + timedelta(minutes=SNAP_AFTER_MIN):
        out(f"REFUSED: the fill window is not complete until {(look + timedelta(minutes=SNAP_AFTER_MIN)).astimezone(ET):%Y-%m-%d %H:%M} ET. Nothing was read.")
        return 2
    posts, fetched = (posts_fn or get_posts)()
    ev = [e for e in forward_events((markets_fn or list_markets)()) if e[0] == start]
    if not ev:
        out(f"No forward event found for {day:%Y-%m-%d}. Nothing was written.")
        return 2
    _, _e, L, per = ev[0]
    cf = candles_fn or get_candles
    candles = {m["ticker"]: cf(m["ticker"], look) for m in L}
    look, cnt, mu, rows, skipped = day_rows(posts, per, L, candles)
    chosen = day_selected(rows)
    have = set()
    if path.exists():
        with open(path, newline="") as fh:
            have = {(r["date"], r["ticker"]) for r in csv.DictReader(fh)}
    new = path.exists() is False
    path.parent.mkdir(parents=True, exist_ok=True)
    wrote = 0
    with open(path, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(SNAP_FIELDS)
        for x in rows:
            key = (f"{day:%Y-%m-%d}", x["ticker"])
            if key in have:
                continue
            ok = c1.LOW <= x["ask"] <= c1.HARD
            m = x["m"]
            w.writerow([key[0], x["ticker"], m["strike_type"], _cap(m.get("floor_strike")), _cap(m.get("cap_strike")), look.isoformat(), cnt, round(mu, 3),
                        round(x["p"], 5), x["sig"], x["ask"], int(ok), int(ok and x["p"] >= c1.RATIO * x["ask"]), int(x["ticker"] in chosen),
                        fetched.isoformat(), posts[-1].isoformat() if posts else ""])
            wrote += 1
    out(f"snapshot {day:%Y-%m-%d}: c={cnt} mu={mu:.1f} brackets quoted {len(rows)} skipped {skipped} selected {len(chosen)} rows written {wrote} -> {path}")
    return 0


def takeup(argv=(), path=None, out=print):
    path = path or SNAP_FILE
    if not path.exists():
        out("REFUSED: no snapshot file yet.")
        return 2
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    days = sorted({r["date"] for r in rows})
    if len(days) < TAKEUP_MIN_DAYS:
        out(f"REFUSED: {len(days)} snapshot days, the first take-up look needs {TAKEUP_MIN_DAYS}. Nothing was printed.")
        return 2
    sel = {d: sum(int(r["selected"]) for r in rows if r["date"] == d) for d in days}
    sig = {d: sum(int(r["signal"]) for r in rows if r["date"] == d) for d in days}
    out(f"TAKE-UP (information only, no outcome): {len(days)} days {days[0]} to {days[-1]}; selected trades {sum(sel.values())} = {sum(sel.values()) / len(days):.2f} a day; "
        f"days with a trade {sum(1 for v in sel.values() if v)}; signals before the 2 a day cap {sum(sig.values())}.")
    per_day = sum(sel.values()) / len(days)
    if per_day > 0:
        out(f"At this rate 150 trades need about {150 / per_day / 30.4:.0f} months from the start; registered guess was 0.1 to 0.6 a day. Decides nothing.")
    return 0


# ------------------------------------------------------------------ gate / read

def _settled_days(markets_fn=None):
    return [e for e in forward_events((markets_fn or list_markets)())]


def gate(argv=(), posts_fn=None, markets_fn=None, out=print):
    posts, _ = (posts_fn or get_posts)()
    oks = []
    for _s, e, L, per in _settled_days(markets_fn):
        ok = source_total_ok(posts, per, L)
        if ok is not None:
            oks.append((per[0], ok))
            out(f"  {per[0].astimezone(ET):%Y-%m-%d} archive-D1 total inside the winning bracket: {'yes' if ok else 'NO'}")
    st, n, share = gate_status([o for _t, o in sorted(oks)])
    out(f"SOURCE GATE: {st}; settled forward days {n}; inside {'n/a' if share is None else f'{share:.1%}'} (bar {GATE_SHARE:.0%} on every prefix from {GATE_MIN_DAYS} days; VOID is latched)")
    return 1 if st == "VOID" else 0


def _collect(posts, events, now, candles_fn, r=c1.R_DISP):
    """Per forward day with a complete fill window: (start, L, rows, chosen). Quotes only, no outcome read."""
    out = []
    for s, _e, L, per in events:
        if now < s + timedelta(hours=LOOK_H, minutes=SNAP_AFTER_MIN):
            continue
        look = s + timedelta(hours=LOOK_H)
        cand = {m["ticker"]: candles_fn(m["ticker"], look) for m in L}
        _l, _c, _mu, rows, skipped = day_rows(posts, per, L, cand, r)
        out.append((s, L, rows, day_selected(rows), skipped))
    return out


def trade_count(now, posts_fn=None, markets_fn=None, candles_fn=None):
    posts, _ = (posts_fn or get_posts)()
    days = _collect(posts, forward_events((markets_fn or list_markets)()), now, candles_fn or get_candles)
    return len(days), sum(len(d[3]) for d in days)


def _stats(v):
    if not v:
        return {"n": 0, "mean": 0.0, "pf": 0.0}
    return {"n": len(v), "mean": sum(v) / len(v), "pf": fr.pf(v)}


def read(now, posts_fn=None, markets_fn=None, candles_fn=None):
    posts, _ = (posts_fn or get_posts)()
    events = forward_events((markets_fn or list_markets)())
    cf = candles_fn or get_candles
    oks = sorted((per[0], source_total_ok(posts, per, L)) for _s, _e, L, per in events)
    oks = [o for _t, o in oks if o is not None]
    gst, gn, gsh = gate_status(oks)
    settled = [e for e in events if source_total_ok(posts, e[3], e[2]) is not None]
    res = {}
    for r in (c1.R_DISP, 4.0, 30.0):
        days = _collect(posts, settled, now, cf, r)
        trades, ctrl, skip = [], [], 0
        for di, (s, L, rows, chosen, sk) in enumerate(days):
            skip += sk
            half = 0 if di < len(days) // 2 else 1
            for x in rows:
                pay = 1.0 if x["m"]["result"] == "yes" else 0.0
                net = pay - x["ask"] - c1.fee(x["ask"])
                if c1.LOW <= x["ask"] <= c1.HARD:
                    ctrl.append(net)
                if x["ticker"] in chosen:
                    trades.append((half, net))
        res[r] = (len(days), skip, trades, ctrl)
    nd, skip, trades, ctrl = res[c1.R_DISP]
    allv = [t[1] for t in trades]; st = _stats(allv); h1 = _stats([t[1] for t in trades if t[0] == 0]); h2 = _stats([t[1] for t in trades if t[0] == 1]); cs = _stats(ctrl)
    v = verdict(st["n"], st["mean"], st["pf"], h1["mean"], h2["mean"], cs["mean"], gst)
    per_day = st["n"] / nd if nd else 0.0
    lines = [f"days scored {nd} (skipped markets {skip}); SOURCE GATE {gst} ({gn} settled days, inside {'n/a' if gsh is None else f'{gsh:.1%}'})",
             f"rule: n {st['n']} mean {st['mean'] * 100:+.2f}c PF {fr.fpf(st['pf'])}; halves n {h1['n']} {h1['mean'] * 100:+.2f}c, n {h2['n']} {h2['mean'] * 100:+.2f}c",
             f"control (all cheap brackets): n {cs['n']} mean {cs['mean'] * 100:+.2f}c PF {fr.fpf(cs['pf'])}",
             "sensitivity (never used to choose): " + "; ".join(f"r={r:g}: n {len(res[r][2])} mean {_stats([t[1] for t in res[r][2]])['mean'] * 100:+.2f}c" for r in (4.0, 30.0)),
             f"take-up {per_day:.2f} trades a day" + (f"; 150 trades in about {(TRADES_DUE - st['n']) / per_day / 30.4:.0f} more months" if per_day > 0 and st["n"] < TRADES_DUE else ""),
             f"VERDICT: {v}"]
    body = (f"{v}; days {nd}; gate {gst} {gn} days {'n/a' if gsh is None else f'{gsh:.1%}'}; n {st['n']} mean {st['mean'] * 100:+.2f}c PF {fr.fpf(st['pf'])}; "
            f"halves {h1['mean'] * 100:+.2f}c/{h2['mean'] * 100:+.2f}c; control n {cs['n']} {cs['mean'] * 100:+.2f}c; registration COUNT1D.")
    return lines, body


SPEC = fr.Spec(
    id="COUNT1D",
    title="forward read of KXTRUTHSOCIALD daily post-count brackets (ET days from 2026-11-04, CNN archive definition D1)",
    sources=["workers/COUNT1D_REGISTRATION.md"],
    rule=[
        "A trade needs fill ask in [0.03, 0.30] (hard limit 0.30). Signal: p_model >= 3 x fill ask.",
        "If ANY prefix of 20 or more days is under 90%, the test is VOID, latched",
        "**NOT_ENOUGH_DATA**: fewer than 150 trades at the read.",
        "**FALSIFIED**: at 150 or more trades, mean net after fees not above 0, or PF under 1.5",
    ],
    window=["settled KXTRUTHSOCIALD ET days starting on or after 2026-11-04; archive posts; one minute candles [look - 60 min, look + 15 min] per bracket; results"],
    due=None,
    due_note="at 150 forward trades or on 2027-03-01, whichever is first",
)


def forward(argv, now=None, posts_fn=None, markets_fn=None, candles_fn=None, out=print):
    now = now or datetime.now(timezone.utc)

    def ready(n):
        if n >= DUE:
            return None
        nd, nt = trade_count(n, posts_fn, markets_fn, candles_fn)
        return None if nt >= TRADES_DUE else f"{nt} forward trades on {nd} days, under {TRADES_DUE}, and not yet {DUE:%Y-%m-%d}."

    def info():
        nd, nt = trade_count(now, posts_fn, markets_fn, candles_fn)
        return [f"forward days with a complete fill window: {nd}; selected trades so far (quotes only, no outcome): {nt}"]

    return fr.run(SPEC, argv, lambda: read(now, posts_fn, markets_fn, candles_fn), info, now=now, ready=ready, out=out)


main_fwd = fr.cli(forward)


def main(argv):
    if len(argv) > 1 and argv[1] == "snapshot":
        return snapshot(argv[2:])
    if len(argv) > 1 and argv[1] == "gate":
        return gate(argv[2:])
    if len(argv) > 1 and argv[1] == "takeup":
        return takeup(argv[2:])
    return main_fwd(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
