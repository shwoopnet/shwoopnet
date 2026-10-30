"""ETHFUNNEL (workers/ETHFUNNEL_REGISTRATION.md): where Ethereum windows drop out of the live smooth-climb rule. A measurement, 0 tries, research only.
Replicates functions/kalshiLiveLib.js (l1Pick, pathShape, smoothGate, one crypto order per window, list order, PAUSED_SERIES) on the 1 minute candles on file.
NO outcomes are read: the market table's `result` column is never selected. Usage: python -m scalper.ethfunnel run [--scratch PATH_TO_live_report.json]
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .analyze import valid_quote
from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
SOURCES = ["alts2", "alts3", "alts4", "book", "l1b", "e3b", "fresh"]
ETH, BTC, DOGE = "KXETH15M", "KXBTC15M", "KXDOGE15M"
LEFT = 360
LO, HI = 0.88 - 1e-9, 0.97 + 1e-9
MIN_STEP, MIN_CLIMB, MIN_EARLIER = 0.005, 0.10, 4
LIVE_START = int(datetime(2026, 10, 23, 18, 30, tzinfo=timezone.utc).timestamp())
DAYS = 78
RESULT = DATA_DIR / "ethfunnel_result.txt"


def load():
    """{ticker: {"s", "close", "c": [(end, bid_c, ask_c)]}} for the three series. Candles only; no result column."""
    by = {}
    for name in SOURCES:
        db = sqlite3.connect(f"file:{DATA_DIR / (name + '.sqlite')}?mode=ro", uri=True)
        mine = defaultdict(lambda: {"c": [], "close": 0, "s": ""})
        q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.close_ts FROM candle c JOIN market m ON m.ticker = c.ticker "
             "WHERE c.series IN (?,?,?) ORDER BY c.ticker, c.end_ts")
        for s, tk, end, bc, ac, close_ts in db.execute(q, (ETH, BTC, DOGE)):
            if tk in by:
                continue
            m = mine[tk]
            m["close"] = close_ts; m["s"] = s
            if bc is not None and ac is not None:
                m["c"].append((end, bc, ac))
        by.update(mine)
    return by


def pick(bid, ask):
    """l1Pick: (side, price) or None. YES at its ask first, else NO at 1 minus the bid; prices rounded to 4 places."""
    if not valid_quote(bid, ask):
        return None
    ra = round(ask, 4)
    if LO <= ra <= HI:
        return ("yes", ra)
    no = round(1 - bid, 4)
    if LO <= no <= HI:
        return ("no", no)
    return None


def shape(cs, side):
    """pathShape on the candles up to the decision candle: (earlier, minStep or None, climb), plain floats."""
    path = [((b + a) / 2) if side == "yes" else 1 - (b + a) / 2 for _, b, a in cs]
    earlier = len(path) - 1
    steps = [path[i] - path[i - 1] for i in range(1, len(path))]
    return earlier, (min(steps) if steps else None), path[-1] - path[0]


def decide(m):
    """For one market: None if no usable decision candle, else dict(inband, side, earlier, minstep, climb)."""
    t = m["close"] - LEFT
    cs = [c for c in m["c"] if c[0] <= t]
    dec = next((c for c in cs if c[0] == t), None)
    if dec is None:
        return {"state": "nocandle"}
    if not valid_quote(dec[1], dec[2]):
        return {"state": "badquote"}
    p = pick(dec[1], dec[2])
    if p is None:
        return {"state": "outband"}
    earlier, mn, climb = shape(cs, p[0])
    return {"state": "inband", "side": p[0], "earlier": earlier, "minstep": mn, "climb": climb,
            "p3": earlier >= MIN_EARLIER, "p4": mn is not None and mn >= -MIN_STEP, "p5": climb >= MIN_CLIMB}


def smooth(d):
    return d["state"] == "inband" and d["p3"] and d["p4"] and d["p5"]


def windows(by):
    """{close_ts: {series: market}} for the three series."""
    w = defaultdict(dict)
    for tk, m in by.items():
        w[m["close"]][m["s"]] = (tk, m)
    return w


def funnel(w, lo_t, hi_t):
    """Stage counts for Ethereum windows whose decision time is in [lo_t, hi_t]."""
    S = defaultdict(int)
    steps = []
    onecent = {"pass": 0, "fail": 0}
    blocked = {"btc": 0, "doge": 0, "both": 0}
    q7_windows, s6_windows = [], []
    for close in sorted(w):
        t = close - LEFT
        if not (lo_t <= t <= hi_t) or ETH not in w[close]:
            continue
        tk, m = w[close][ETH]
        if not m["c"]:
            continue
        S[1] += 1
        d = decide(m)
        S["nocandle" if d["state"] == "nocandle" else "badquote" if d["state"] == "badquote" else "outband" if d["state"] == "outband" else "x"] += 1
        if d["state"] != "inband":
            continue
        S[2] += 1
        S[3] += d["p3"]; S[4] += d["p4"]; S[5] += d["p5"]
        S["no_step"] += d["minstep"] is None
        if d["minstep"] is not None:
            steps.append(d["minstep"])
            if abs(d["minstep"] + MIN_STEP) < 1e-9:
                onecent["pass" if d["minstep"] >= -MIN_STEP else "fail"] += 1
        if smooth(d):
            S[6] += 1; s6_windows.append(close)
            b = BTC in w[close] and smooth(decide(w[close][BTC][1]))
            g = DOGE in w[close] and decide(w[close][DOGE][1])["state"] == "inband"
            if b and g: blocked["both"] += 1
            elif b: blocked["btc"] += 1
            elif g: blocked["doge"] += 1
            if not (b or g):
                S[7] += 1; q7_windows.append(close)
    return S, steps, onecent, blocked, s6_windows, q7_windows


def quantiles(v):
    v = sorted(v)
    n = len(v)
    if not n:
        return {}
    pick_ = lambda f: v[min(n - 1, int(f * (n - 1) + 0.5))]
    return {k: pick_(f) for k, f in [("min", 0), ("p5", .05), ("p10", .10), ("p25", .25), ("p50", .5), ("p75", .75), ("p90", .90), ("p95", .95), ("max", 1)]}


BINS = [("below -0.10", None, -0.10), ("-0.10 to -0.05", -0.10, -0.05), ("-0.05 to -0.02", -0.05, -0.02), ("-0.02 to the threshold (fails)", -0.02, None),
        ("passes the threshold, below 0", None, 0.0), ("0 or above (no pullback)", 0.0, None)]


def histogram(v):
    out = defaultdict(int)
    for x in v:
        if x < -0.10: out[0] += 1
        elif x < -0.05: out[1] += 1
        elif x < -0.02: out[2] += 1
        elif not (x >= -MIN_STEP): out[3] += 1
        elif x < 0: out[4] += 1
        else: out[5] += 1
    return [(BINS[i][0], out[i]) for i in range(len(BINS))]


def parity(w, report_path, lo_t, hi_t):
    """Replay against the private order export (fields ts, ticker, status only; never result, settledPnl or avgFill). Counts only."""
    rows = json.load(open(report_path))["orders"]
    recs = defaultdict(dict)   # series -> {ticker: status}
    for o in rows:
        tk = o.get("ticker", "")
        recs[tk.split("-")[0]][tk] = o.get("status")
    del rows
    gen_t = int(json.load(open(report_path))["generatedAt"] and datetime.fromisoformat(json.load(open(report_path))["generatedAt"].replace("Z", "+00:00")).timestamp())
    hi = min(hi_t, gen_t)
    held = ("filled", "sending", "unknown")
    out = {}
    for ser in (ETH, BTC, DOGE):
        n = mism = 0
        kinds = defaultdict(int)
        statuses = defaultdict(int)
        for close in sorted(w):
            t = close - LEFT
            if not (lo_t <= t <= hi) or ser not in w[close]:
                continue
            tk, m = w[close][ser]
            if not m["c"]:
                continue
            d = decide(m)
            xrp_tk = [k for k in recs.get("KXXRP15M", {}) if k.endswith(tk.split("-", 1)[1])]
            xrp_held = any(recs["KXXRP15M"][k] in held for k in xrp_tk)
            b = BTC in w[close] and smooth(decide(w[close][BTC][1]))
            g = DOGE in w[close] and decide(w[close][DOGE][1])["state"] == "inband"
            if ser == BTC:
                would = smooth(d) and not xrp_held
            elif ser == DOGE:
                would = d["state"] == "inband" and not b and not xrp_held
            else:
                would = smooth(d) and not b and not g and not xrp_held
            actual = tk in recs.get(ser, {})
            if actual: statuses[recs[ser][tk]] += 1
            n += 1
            if would != actual:
                mism += 1
                kinds["replay yes, no record" if would else "record, replay no"] += 1
        out[ser] = (n, mism, dict(kinds), dict(statuses))
    return out, hi


def fmt_ct(ts):
    return datetime.fromtimestamp(ts, CT).strftime("%Y-%m-%d %I:%M %p CT")


def table(S, label):
    rows = [("1 all windows", S[1], None),
            ("2 a side at 0.88 to 0.97 at the look", S[2], S[1]),
            ("3 at least 4 earlier candles (on stage 2)", S[3], S[2]),
            ("4 worst one minute step -0.005 or better (on stage 2)", S[4], S[2]),
            ("5 climb 0.10 or more (on stage 2)", S[5], S[2]),
            ("6 all of the above = the live rule", S[6], S[2]),
            ("7 live rule and no other crypto order first", S[7], S[6])]
    out = [f"### {label}", "", "| Stage | Windows | Share of all windows | Share of the previous stage |", "|---|---|---|---|"]
    for name, n, prev in rows:
        a = f"{100 * n / S[1]:.2f}%" if S[1] else "n/a"
        b = "" if prev is None else (f"{100 * n / prev:.1f}%" if prev else "n/a")
        out.append(f"| {name} | {n} | {a} | {b} |")
    out += ["", f"Stage 1 to 2 loss: {S['outband']} windows had no side in the band, {S['nocandle']} had no candle ending exactly 360 s before the close, {S['badquote']} had an invalid quote at the look. Stage 4 failures include {S['no_step']} in-band windows with a path too short to have a step.", ""]
    return out


def run(argv):
    if RESULT.exists():
        print("refused: result exists"); return
    scratch = argv[argv.index("--scratch") + 1] if "--scratch" in argv else None
    by = load()
    w = windows(by)
    eth_closes = sorted(c for c in w if ETH in w[c] and w[c][ETH][1]["c"])
    last = eth_closes[-1]
    A = (last - LEFT - DAYS * 86400, last - LEFT)
    B = (LIVE_START, last - LEFT)
    out = [f"ETHFUNNEL raw result. Windows on file for Ethereum: {len(eth_closes)}, first decision {fmt_ct(eth_closes[0] - LEFT)}, last {fmt_ct(last - LEFT)}.", ""]
    res = {}
    for label, (lo, hi) in [("Run A: last 78 days", A), ("Run B: live days since 2026-10-23 18:30 UTC (1:30 PM CT)", B)]:
        S, steps, onecent, blocked, s6, q7 = funnel(w, lo, hi)
        res[label] = (S, steps, onecent, blocked, s6, q7)
        out += table(S, f"{label} ({fmt_ct(lo)} to {fmt_ct(hi)})")
        days = (hi - lo) / 86400
        out.append(f"Span {days:.2f} days. Stage 6 per day {S[6] / days:.2f}, stage 7 per day {S[7] / days:.2f}.")
        out.append(f"Contention at stage 6 (windows where the live gate passes but Bitcoin or Dogecoin would be taken first): total {S[6] - S[7]}; Bitcoin only {blocked['btc']}, Dogecoin only {blocked['doge']}, both {blocked['both']}.")
        out.append("Worst one minute step of in-band windows, quantiles: " + ", ".join(f"{k} {v:+.4f}" for k, v in quantiles(steps).items()) + f" (n {len(steps)}).")
        out.append("Histogram of the same values: " + "; ".join(f"{n} {c}" for n, c in histogram(steps)) + ".")
        out.append(f"Windows whose worst step is exactly a one cent pullback (float arithmetic decides): passed {onecent['pass']}, failed {onecent['fail']}.")
        if label.startswith("Run B"):
            out.append("Stage 6 windows (decision time): " + ", ".join(fmt_ct(c - LEFT) for c in s6))
            out.append("Stage 7 windows (decision time): " + ", ".join(fmt_ct(c - LEFT) for c in q7))
        out.append("")
    if scratch:
        par, hi = parity(w, scratch, LIVE_START, last - LEFT)
        out.append(f"Parity against the private export (counts only), live period to {fmt_ct(hi)}:")
        for ser, (n, mm, kinds, st) in par.items():
            out.append(f"- {ser}: windows {n}, disagreements {mm} ({100 * mm / n:.2f}%), {kinds}; record statuses {st}")
    else:
        out.append("Parity: NOT checked (no export given).")
    text = "\n".join(out)
    print(text)
    RESULT.write_text(text + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run(sys.argv)
