"""FEDIMPL1 (workers/FEDIMPL1_REGISTRATION.md): cheap outcomes of Kalshi's FOMC markets against a rate implied by the 1 month Treasury bill.
Research only, nothing here means trade.
    python -m scalper.fedimpl1 fetch     (resumable: FRED DFF and DGS1MO, FOMC markets, hourly candles around each look)
    python -m scalper.fedimpl1 run       (the one scored read of the first two thirds of meetings; refused a second time)
    python -m scalper.fedimpl1 forward    (signal and trade at the next look; prints, places nothing)
"""
from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import api
from .calibration import cluster_mean_z
from .paths import DATA_DIR

D = DATA_DIR / "fedimpl1"
RESULT = DATA_DIR / "fedimpl1_result.txt"
NY = ZoneInfo("America/New_York")
SIGMA, MAXSPREAD, LO, HI, RATIO, C = 10.0, 0.10, 0.03, 0.30, 3.0, 10
SIG_HOUR, FILL_HOUR = 19, 20            # UTC; signal candle ends at or before 19:00, fill candle at or before 20:00
MIN_TRADES, STOP_N, BAR_PF = 150, 30, 1.5
OUTCOMES = {"C26": (-1e9, -37.5), "C25": (-37.5, -12.5), "H0": (-12.5, 12.5), "H25": (12.5, 37.5), "H26": (37.5, 1e9)}


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def fee(p, c=C):
    return math.ceil(round(7.0 * c * p * (1 - p), 9)) / 100.0       # dollars, 7% x C x p x (1-p) cents rounded up


def load_fred(name):
    out = {}
    for r in list(csv.reader(open(D / f"{name}.csv")))[1:]:
        try:
            out[date.fromisoformat(r[0])] = float(r[1])
        except ValueError:
            pass
    return out


def prev_business_day(d):
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def last_on_or_before(s, d, back=7):
    for k in range(back + 1):
        if (d - timedelta(days=k)) in s:
            return s[d - timedelta(days=k)]
    return None


def reference(dff, bill, dday):
    """E in bps, U0 (percent) for the meeting on dday; None when the spread window has under 4 observations or a level is missing."""
    look = prev_business_day(dday)
    reff, rbill = last_on_or_before(dff, look), last_on_or_before(bill, look)
    if reff is None or rbill is None:
        return None
    sp = sorted(bill[d] - dff[d] for d in (dday - timedelta(days=k) for k in range(33, 41)) if d in bill and d in dff)
    if len(sp) < 4:
        return None
    s = sp[len(sp) // 2] if len(sp) % 2 else 0.5 * (sp[len(sp) // 2 - 1] + sp[len(sp) // 2])
    e = 100.0 * ((rbill - reff) - s)
    l0 = 0.25 * math.floor((reff - 0.04) / 0.25 + 1e-9)
    return {"E": e, "U0": round(l0 + 0.25, 2), "reff": reff, "rbill": rbill, "s": s, "look": look}


def p_outcome(e, key):
    lo, hi = OUTCOMES[key]
    a = 0.0 if lo < -1e8 else phi((lo - e) / SIGMA)
    b = 1.0 if hi > 1e8 else phi((hi - e) / SIGMA)
    return b - a


def p_above(e, u0, k):
    j = round((k - u0) * 100 / 25.0)
    return 1 - phi((25 * j + 12.5 - e) / SIGMA)


def pick(o):
    o = o or {}
    return api.f(o.get("close_dollars") if o.get("close_dollars") is not None else o.get("close"))


def quote(cs, hour_utc, look):
    """Last hourly candle ending at or before hour_utc on the look date with a two sided book: (bid, ask) or None."""
    cut = int(datetime(look.year, look.month, look.day, hour_utc, tzinfo=timezone.utc).timestamp())
    best = None
    for c in cs:
        t = c.get("end_period_ts")
        if t is not None and t <= cut and (best is None or t > best[0]):
            best = (t, pick(c.get("yes_bid")), pick(c.get("yes_ask")))
    if best is None:
        return None
    _, b, a = best
    if b is None or a is None or not (0 < b < a < 1):
        return None
    return b, a


def decide(model_yes, sig, fill):
    """The registered trade on one market: sig and fill are (bid, ask). Returns {side, ask, p, fill} or a reason string."""
    if sig is None or fill is None:
        return "nodata"
    if sig[1] - sig[0] > MAXSPREAD + 1e-9:
        return "wide"
    if LO - 1e-9 <= sig[1] <= HI + 1e-9:
        side, ask, p, fa = "yes", sig[1], model_yes, fill[1]
    elif LO - 1e-9 <= 1 - sig[0] <= HI + 1e-9:
        side, ask, p, fa = "no", 1 - sig[0], 1 - model_yes, 1 - fill[0]
    else:
        return "notcheap"
    if p + 1e-12 < RATIO * ask:
        return "model"
    if not (LO - 1e-9 <= fa <= HI + 1e-9):
        return "limit"
    return {"side": side, "ask": ask, "p": p, "fill": round(fa, 4)}


def net_c(fillp, win):
    """Cents per contract after fee, C = 10."""
    return 100 * ((1 - fillp if win else -fillp) - fee(fillp) / C)


def fetch_text(u):
    return subprocess.run(["curl", "-sS", "-m", "60", u], capture_output=True, text=True, check=True).stdout


def cmd_fetch():
    D.mkdir(parents=True, exist_ok=True)
    for n in ("DFF", "DGS1MO"):
        if not (D / f"{n}.csv").exists():
            (D / f"{n}.csv").write_text(fetch_text(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={n}"))
    mk = D / "markets.json"
    if not mk.exists():
        allm = []
        for ser in ("KXFEDDECISION", "KXFED"):
            for path, src in (("/historical/markets", "hist"), ("/markets", "live")):
                cur = None
                while True:
                    p = {"series_ticker": ser, "limit": 1000}
                    if path == "/markets":
                        p["status"] = "settled"
                    if cur:
                        p["cursor"] = cur
                    d = api._get(path, p)
                    for m in d.get("markets", []):
                        m["_src"], m["_ser"] = src, ser
                        allm.append(m)
                    cur = d.get("cursor")
                    if not cur:
                        break
        mk.write_text(json.dumps(allm))
    allm = json.loads(mk.read_text())
    cf = D / "candles.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    dff, bill = load_fred("DFF"), load_fred("DGS1MO")
    for ev, dday, ms in meetings(allm):
        ref = reference(dff, bill, dday)
        if ref is None:
            continue
        for m in ms:
            if not wanted(m, ref):
                continue
            tk = m["ticker"]
            if tk in cache:
                continue
            look = ref["look"]
            s = int(datetime(look.year, look.month, look.day, 12, tzinfo=timezone.utc).timestamp())
            e = int(datetime(look.year, look.month, look.day, 21, tzinfo=timezone.utc).timestamp())
            path = f"/historical/markets/{tk}/candlesticks" if m["_src"] == "hist" else f"/series/{m['_ser']}/markets/{tk}/candlesticks"
            try:
                cache[tk] = api._get(path, {"start_ts": s, "end_ts": e, "period_interval": 60}).get("candlesticks", [])
            except Exception as ex:                  # a market with no candle history is NoData, not a no-trade
                cache[tk] = {"error": str(ex)[:120]}
            cf.write_text(json.dumps(cache))
            time.sleep(0.35)
    print("fetched", len(cache), "markets")


def meetings(allm):
    """Meetings = KXFEDDECISION events, decision date = Eastern date of close_time. Returns [(event, date, [all markets of that month in either series])]."""
    ev = {}
    for m in allm:
        if m["_ser"] == "KXFEDDECISION":
            ev.setdefault(m["event_ticker"], []).append(m)
    out = []
    for et, ms in ev.items():
        ct = datetime.fromisoformat(ms[0]["close_time"].replace("Z", "+00:00")).astimezone(NY).date()
        suffix = et.split("-", 1)[1]
        kx = [m for m in allm if m["_ser"] == "KXFED" and m["event_ticker"].split("-", 1)[1] == suffix]
        seen, uniq = set(), []
        for m in ms + kx:
            if m["ticker"] not in seen:
                seen.add(m["ticker"])
                uniq.append(m)
        out.append((et, ct, uniq))
    return sorted(out, key=lambda x: x[1])


def key_of(m):
    return m["ticker"].rsplit("-", 1)[1]


def wanted(m, ref):
    if m["_ser"] == "KXFEDDECISION":
        return key_of(m) in OUTCOMES
    k = m.get("floor_strike")
    return k is not None and abs(k - ref["U0"]) <= 0.50 + 1e-9


def model_yes(m, ref):
    if m["_ser"] == "KXFEDDECISION":
        return p_outcome(ref["E"], key_of(m))
    return p_above(ref["E"], ref["U0"], m["floor_strike"])


def settle_yes(m):
    r = m.get("result")
    return None if r not in ("yes", "no") else r == "yes"


def score(rows, label):
    n = len(rows)
    if n == 0:
        return f"{label}: n=0"
    nets = [r["net"] for r in rows]
    gw = sum(x for x in nets if x > 0)
    gl = -sum(x for x in nets if x < 0)
    pf = gw / gl if gl > 0 else float("inf")
    wins = sum(r["win"] for r in rows)
    mean, se, z = cluster_mean_z([(r["meeting"], r["net"]) for r in rows])
    return f"{label}: n={n} win={wins / n:.1%} avgfill={sum(r['fill'] for r in rows) / n:.3f} mean={mean:+.2f}c PF={pf:.2f} meeting-clustered z={z:+.2f}"


def cmd_run():
    if RESULT.exists():
        sys.exit("refused: fedimpl1 run was already executed (" + str(RESULT) + ")")
    allm = json.loads((D / "markets.json").read_text())
    cache = json.loads((D / "candles.json").read_text())
    dff, bill = load_fred("DFF"), load_fred("DGS1MO")
    mts = meetings(allm)
    nscore = math.ceil(len(mts) * 2 / 3)
    scored, hold = mts[:nscore], mts[nscore:]
    rows, skips, unscored = [], {}, 0
    for et, dday, ms in scored:
        ref = reference(dff, bill, dday)
        if ref is None:
            unscored += 1
            continue
        for m in ms:
            if not wanted(m, ref):
                continue
            cs = cache.get(m["ticker"])
            if not isinstance(cs, list):
                skips["nodata"] = skips.get("nodata", 0) + 1
                continue
            res = decide(model_yes(m, ref), quote(cs, SIG_HOUR, ref["look"]), quote(cs, FILL_HOUR, ref["look"]))
            if isinstance(res, str):
                skips[res] = skips.get(res, 0) + 1
                continue
            w = settle_yes(m)
            if w is None:
                skips["unsettled"] = skips.get("unsettled", 0) + 1
                continue
            win = w if res["side"] == "yes" else not w
            rows.append({"meeting": et, "day": str(dday), "ticker": m["ticker"], "ser": m["_ser"], "side": res["side"], "fill": res["fill"],
                         "p": res["p"], "win": win, "net": net_c(res["fill"], win), "E": ref["E"]})
    rows.sort(key=lambda r: r["day"])
    half = [r for r in rows if r["day"] < (scored[len(scored) // 2][1].isoformat())] if scored else []
    h2 = [r for r in rows if r not in half]
    L = [f"FEDIMPL1 run. meetings {len(mts)}, scored {len(scored)} ({scored[0][1]} to {scored[-1][1]}), holdout {len(hold)} (first {hold[0][1] if hold else None}, UNREAD), unscored for reference {unscored}",
         f"skips: {skips}", score(rows, "ALL"), score(half, "first half"), score(h2, "second half"),
         score([r for r in rows if r["ser"] == "KXFEDDECISION"], "R1 KXFEDDECISION"), score([r for r in rows if r["ser"] == "KXFED"], "R2 KXFED")]
    stress = []
    for r in rows:
        stress.append(100 * ((1 - r["fill"] if r["win"] else -r["fill"]) - 1.2 * fee(r["fill"]) / C))
    gw, gl = sum(x for x in stress if x > 0), -sum(x for x in stress if x < 0)
    L.append(f"fees x1.2 PF={gw / gl if gl else float('inf'):.2f}")
    L.append("by price: " + "; ".join(f"fill<{b}: n={sum(1 for r in rows if r['fill'] < b and r['fill'] >= pb)} wins={sum(1 for r in rows if r['fill'] < b and r['fill'] >= pb and r['win'])}" for pb, b in ((0, .06), (.06, .12), (.12, .2), (.2, .31))))
    L.append("model p mean among trades %.3f vs win rate %.3f" % (sum(r["p"] for r in rows) / len(rows) if rows else 0, sum(r["win"] for r in rows) / len(rows) if rows else 0))
    per = len(rows) / max(1, len(scored))
    L.append(f"trades per meeting {per:.2f}; 40 trades take {40 / per / 8 * 12 if per else float('inf'):.1f} months, 150 take {150 / per / 8 * 12 if per else float('inf'):.1f} months at 8 meetings a year")
    L.append("per meeting: " + ", ".join(f"{r['day']}:{r['ticker'].split('-', 1)[1]} {r['side']}@{r['fill']:.2f} p{r['p']:.2f} {'W' if r['win'] else 'L'}" for r in rows))
    verdict = "NOT_ENOUGH_DATA" if len(rows) < MIN_TRADES else "SEE_RULES"
    gwa, gla = sum(r["net"] for r in rows if r["net"] > 0), -sum(r["net"] for r in rows if r["net"] < 0)
    pf_all = gwa / gla if gla else float("inf")
    mh = lambda xs: sum(r["net"] for r in xs) / len(xs) if xs else 0
    early = len(rows) >= STOP_N and (pf_all < 1.0 or not (mh(half) > 0 and mh(h2) > 0))
    L.append(f"verdict: {verdict}; STOPPED_EARLY flag (n>={STOP_N} and PF<1.0 or a half not positive): {early}")
    txt = "\n".join(L)
    RESULT.write_text(txt)
    print(txt)


def cmd_forward():
    """Print the registered signal for the next decision whose look is today or later. Fetches live candles; places nothing."""
    allm = []
    for ser in ("KXFEDDECISION", "KXFED"):
        d = api._get("/markets", {"series_ticker": ser, "limit": 1000})
        for m in d.get("markets", []):
            m["_ser"], m["_src"] = ser, "live"
            allm.append(m)
    dff, bill = load_fred("DFF"), load_fred("DGS1MO")
    today = datetime.now(timezone.utc).date()
    for et, dday, ms in meetings(allm):
        look = prev_business_day(dday)
        if look < today:
            continue
        ref = reference(dff, bill, dday)
        print(et, "decision", dday, "look", look, "reference", ref)
        if ref is None or look > today:
            return
        for m in ms:
            if not wanted(m, ref):
                continue
            s = int(datetime(look.year, look.month, look.day, 12, tzinfo=timezone.utc).timestamp())
            e = int(datetime(look.year, look.month, look.day, 21, tzinfo=timezone.utc).timestamp())
            cs = api._get(f"/series/{m['_ser']}/markets/{m['ticker']}/candlesticks", {"start_ts": s, "end_ts": e, "period_interval": 60}).get("candlesticks", [])
            print(m["ticker"], decide(model_yes(m, ref), quote(cs, SIG_HOUR, look), quote(cs, FILL_HOUR, look)))
            time.sleep(0.35)
        return


if __name__ == "__main__":
    {"fetch": cmd_fetch, "run": cmd_run, "forward": cmd_forward}[sys.argv[1]]()
