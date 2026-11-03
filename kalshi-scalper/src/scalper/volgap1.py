"""VOLGAP1 (workers/VOLGAP1_REGISTRATION.md): when the realised volatility of the last 15 minutes runs well above the volatility the
hourly ladder implies, are the cheap far strikes underpriced? Hourly Bitcoin (KXBTCD), Ethereum (KXETHD) and gold (KXGOLDH) ladders,
look 25 minutes before the close, OKX 1 minute klines for the realised volatility ONLY (the model's centre comes from the ladder itself,
so no spot level or basis enters). Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.
Nothing here means trade; there is no promote verb.
    python -m scalper.volgap1 fetch   (resumable; OKX klines, settled markets near the spot, Kalshi 1 minute candles)
    python -m scalper.volgap1 run     (the one scored read; refused a second time)
Reuses lag15's fee, windows, statistics code unchanged.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

from . import api
from . import lag15 as L

UTC = timezone.utc
CACHE = Path(os.environ.get("VOLGAP1_CACHE", "/tmp/volgap1_cache"))
RESULT = CACHE / "volgap1_result.txt"
ASSETS = {"KXBTCD": "BTC-USDT", "KXETHD": "ETH-USDT", "KXGOLDH": "XAU-USDT-SWAP"}
NEAR = {"KXBTCD": 0.015, "KXETHD": 0.02, "KXGOLDH": 0.01}   # strikes fetched: |ln(K/spot at the look)| within this (spot only, no outcome)
GROUPS = {"CRYPTO": ["KXBTCD", "KXETHD"], "GOLD": ["KXGOLDH"]}
LO_CLOSE = 1787788800        # 2026-08-27 00:00:00 UTC, first close in the sample
HI_CLOSE = 1793577600        # 2026-11-03 00:00:00 UTC, closes strictly before this
LOOK_S = 1500                # 25 minutes before the close
TAU_MIN = 24.0 + 1.0 / 3.0   # variance horizon in minutes: 24 to the start of the final 60 s average, plus 60 s / 3
NRET = 15                    # one minute log returns in the realised volatility (16 closes)
MAX_SPREAD = 0.05            # ask - bid, used for fit strikes, trade strikes and the fill candle
QUOTE_AGE_S = 120
FIT_MID = (0.03, 0.97)       # a strike joins the fit when its YES mid lies in this range
MIN_FIT, MIN_R2 = 6, 0.90
HI_RATIO, LO_RATIO = 1.5, 0.67
TAIL = (0.03, 0.30)          # price band of a cheap tail; 0.30 is the hard cap at the fill
FILL_SLIP = 0.03             # the fill may be at most this far above the look price
EDGE = 0.08                  # model probability minus price minus exact fee
NEAR_PRICE = 0.10            # the comparator / control rule buys the tail whose price is nearest this
NRUN = 728740
C = L.C
ND = NormalDist()


def realised_per_min(closes: list) -> float | None:
    """16 consecutive one minute closes ending at the look: root mean square of the 15 log returns (drift ignored). None if any is missing or all equal."""
    if len(closes) != NRET + 1 or any(c is None or c <= 0 for c in closes):
        return None
    r = [math.log(closes[i + 1] / closes[i]) for i in range(NRET)]
    s = math.sqrt(sum(x * x for x in r) / NRET)
    return s if s > 0 else None


def fit_ladder(points: list):
    """points: [(K, yes_mid)] with mid in FIT_MID. OLS of z = probit(1 - mid) on ln K; z = (ln K - m) / s.
    Returns (m, s, r2, n) or None (fewer than MIN_FIT points, flat or reversed slope, or R^2 under MIN_R2)."""
    pts = [(math.log(k), ND.inv_cdf(1 - mid)) for k, mid in points if FIT_MID[0] <= mid <= FIT_MID[1] and k > 0]
    n = len(pts)
    if n < MIN_FIT:
        return None
    mx, mz = sum(x for x, _ in pts) / n, sum(z for _, z in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    if sxx <= 0:
        return None
    sxz = sum((x - mx) * (z - mz) for x, z in pts)
    szz = sum((z - mz) ** 2 for _, z in pts)
    b = sxz / sxx
    if b <= 0 or szz <= 0:
        return None
    a = mz - b * mx
    r2 = (sxz * sxz) / (sxx * szz)
    if r2 < MIN_R2:
        return None
    return (-a / b, 1.0 / b, r2, n)


def p_yes_model(K: float, m: float, s_total: float) -> float:
    """P(settlement above K) for a lognormal with log-median m and total std s_total over the horizon."""
    return 1 - ND.cdf((math.log(K) - m) / s_total)


def two_sided(bid, ask) -> bool:
    return bid is not None and ask is not None and 0 < bid < ask < 1 and ask - bid <= MAX_SPREAD + 1e-9


def look_quote(cs: list, look: int):
    """latest candle (end_ts, bid, ask, vol) ending at or before the look and at most QUOTE_AGE_S old, two sided and tight; else None."""
    best = None
    for c in cs:
        if c[0] <= look and look - c[0] <= QUOTE_AGE_S and two_sided(c[1], c[2]):
            if best is None or c[0] > best[0]:
                best = c
    return best


def fill_quote(cs: list, look: int):
    for c in cs:
        if c[0] == look + 60 and two_sided(c[1], c[2]):
            return c
    return None


def tail_options(q):
    """q: a quote (end, bid, ask, vol). The YES tail and the NO tail whose price is inside TAIL; [(side, price)]."""
    out = []
    if TAIL[0] <= q[2] <= TAIL[1]:
        out.append(("yes", q[2]))
    if TAIL[0] <= 1 - q[1] <= TAIL[1]:
        out.append(("no", 1 - q[1]))
    return out


def resolve_fill(cs, look, side, price):
    """Fill at the next candle's ask (NO: 1 - bid). None (no trade) if no tight two sided candle, the price is above the cap or more than FILL_SLIP above the look price."""
    f = fill_quote(cs, look)
    if f is None:
        return None
    p = f[2] if side == "yes" else 1 - f[1]
    if p > TAIL[1] + 1e-9 or p > price + FILL_SLIP + 1e-9 or p < 0.01:
        return None
    return p


def decide_hour(close: int, strikes: list, candles: dict, klines: dict):
    """strikes: [(ticker, K)] of one hourly event. Uses data at or before the look (close - LOOK_S) for every choice; the fill candle is
    the next minute. Returns None (no kline vol or no fit) or a dict: ratio, fit, model trade, nearest trade, tail list for calibration."""
    look = close - LOOK_S
    closes = [klines.get(look - 60 - 60 * (NRET - i)) for i in range(NRET + 1)]   # the kline opening at look-60 ends AT the look
    sr = realised_per_min(closes)
    if sr is None:
        return None
    quotes = {}
    for tk, K in strikes:
        cs = [tuple(c) for c in candles.get(tk, [])]
        q = look_quote(cs, look)
        if q is not None:
            quotes[tk] = (K, q, cs)
    fit = fit_ladder([(K, (q[1] + q[2]) / 2) for K, q, _ in quotes.values()])
    if fit is None:
        return None
    m, s, r2, nfit = fit
    s_r = sr * math.sqrt(TAU_MIN)
    ratio = s_r / s
    best, near, tails = None, None, []
    for tk, (K, q, cs) in quotes.items():
        p = p_yes_model(K, m, s_r)
        for side, price in tail_options(q):
            pm = p if side == "yes" else 1 - p
            e = pm - price - L.fee_exact(price)
            tails.append({"tk": tk, "side": side, "look": price, "pm": pm, "mid": (q[1] + q[2]) / 2})
            if e >= EDGE and (best is None or e > best["e"] or (e == best["e"] and price < best["look"])):
                best = {"tk": tk, "side": side, "look": price, "e": e}
            d = abs(price - NEAR_PRICE)
            if near is None or d < near["d"] or (d == near["d"] and price < near["look"]):
                near = {"tk": tk, "side": side, "look": price, "d": d}
    for t in (best, near):
        if t is not None:
            t["price"] = resolve_fill(quotes[t["tk"]][2], look, t["side"], t["look"])
    return {"close": close, "ratio": ratio, "s": s, "s_r": s_r, "r2": r2, "nfit": nfit, "best": best, "near": near, "tails": tails}


# ---------------------------------------------------------------- fetch
def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    klines = {}
    lo, hi = LO_CLOSE - LOOK_S - 6000, HI_CLOSE
    for s, inst in ASSETS.items():
        kp = CACHE / f"klines_{inst}.json"
        if not kp.exists():
            k = L.okx_klines(inst, lo, hi)
            kp.write_text(json.dumps({str(a): b for a, b in k.items()})); print(inst, len(k), "klines", flush=True)
        klines[s] = {int(a): b for a, b in json.loads(kp.read_text()).items()}
    mp = CACHE / "markets.json"
    markets = json.loads(mp.read_text()) if mp.exists() else {}
    if not markets:
        for s in ASSETS:
            n = 0
            for m in api.settled_markets(s, LO_CLOSE, HI_CLOSE - 1):
                k = m.get("floor_strike")
                if k is None or m.get("result") not in ("yes", "no") or (m.get("strike_type") != "greater"):
                    continue
                close = L.ts(m["close_time"])
                S = klines[s].get(close - LOOK_S - 60)
                if S and abs(math.log(float(k) / S)) <= NEAR[s]:
                    markets[m["ticker"]] = {"s": s, "ev": m["event_ticker"], "close": close, "k": float(k), "res": m["result"]}
                n += 1
            print(s, n, "listed", flush=True)
        mp.write_text(json.dumps(markets)); print(len(markets), "markets near spot", flush=True)
    cp = CACHE / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    by = defaultdict(list)
    for tk, m in markets.items():
        if tk not in have:
            by[m["close"]].append(tk)
    groups = []
    for c in sorted(by):
        for j in range(0, len(by[c]), 100):
            groups.append((c, by[c][j:j + 100]))
    pause = 0.3
    for i, (gc, tks) in enumerate(groups):
        look = gc - LOOK_S
        lo2, hi2 = look - 300, look + 60
        for attempt in range(12):
            try:
                req = urllib.request.Request(api.BASES[1] + "/markets/candlesticks?" + urllib.parse.urlencode({"market_tickers": ",".join(tks), "start_ts": lo2, "end_ts": hi2, "period_interval": 1}))
                d = json.load(urllib.request.urlopen(req, timeout=30))
                got = {x.get("market_ticker") or x.get("ticker"): x for x in d.get("markets", [])}
                for tk in tks:
                    cs = (got.get(tk) or {}).get("candlesticks", [])
                    have[tk] = [(c["end_period_ts"], L.pick(c.get("yes_bid")), L.pick(c.get("yes_ask")), api.f(c.get("volume_fp") or c.get("volume")))
                                for c in cs if lo2 < c["end_period_ts"] <= hi2]
                pause = max(0.25, pause * 0.9)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    pause = min(pause * 1.3, 1.5)
                time.sleep(1 + attempt)
            except Exception:
                time.sleep(1 + attempt)
        else:
            print("skip", gc, flush=True)
        if i % 50 == 0:
            cp.write_text(json.dumps(have)); print("candles", i, len(groups), "pause", round(pause, 2), flush=True)
        time.sleep(pause)
    cp.write_text(json.dumps(have))
    print("done", flush=True)


# ---------------------------------------------------------------- run
def day(close: int) -> str:
    return datetime.fromtimestamp(close, UTC).strftime("%Y-%m-%d")


def hours(markets, cands, klines, series):
    ev = defaultdict(list)
    for tk, m in markets.items():
        if m["s"] in series:
            ev[(m["s"], m["ev"], m["close"])].append((tk, m["k"]))
    rows, total = [], defaultdict(int)
    for (s, e, close), strikes in ev.items():
        total[s] += 1
        h = decide_hour(close, strikes, cands, klines[s])
        if h is not None:
            h["s"] = s
            rows.append(h)
    return rows, total


def rows_for(hs, markets, rule, win, which, mult=1.0):
    """[(day, pnl_cents)] of the hours in the windows `which` for a rule ('best' or 'near') among hours selected by `pick`."""
    out = []
    for h, t in hs:
        if t and t.get("price") is not None and win[day(h["close"])] in which:
            out.append((day(h["close"]), L.pnl(t["side"], t["price"], markets[t["tk"]]["res"], mult)))
    return out


def count_trades(hs):
    return sum(1 for _, t in hs if t and t.get("price") is not None)


def quant(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else float("nan")


def score_group(name, series, markets, cands, klines, out):
    rows, total = hours(markets, cands, klines, series)
    out.append(f"--- GROUP {name} ({', '.join(series)})")
    out.append("closes with listed near-spot strikes: " + ", ".join(f"{s} {total[s]}" for s in series) + f"; with a vol and a fit: {len(rows)}")
    if not rows:
        out.append(f"{name}: NOT_RUNNABLE (no hour has a fit)"); return
    ratios = [h["ratio"] for h in rows]
    out.append("ratio realised/implied quantiles 5/25/50/75/95: " + " ".join(f"{quant(ratios, q):.2f}" for q in (.05, .25, .5, .75, .95)))
    hi = [h for h in rows if h["ratio"] >= HI_RATIO]
    lo = [h for h in rows if h["ratio"] <= LO_RATIO]
    out.append(f"trigger hours ratio >= {HI_RATIO}: {len(hi)} ({len(hi)/len(rows)*100:.1f}%); control hours ratio <= {LO_RATIO}: {len(lo)} ({len(lo)/len(rows)*100:.1f}%)")
    win = L.thirds([day(h["close"]) for h in rows])
    treated = [(h, h["best"]) for h in hi]
    alt = [(h, h["near"]) for h in hi]
    ctrl = [(h, h["near"]) for h in lo]
    ctrl_model = [(h, h["best"]) for h in lo]
    ntr = count_trades(treated)
    out.append(f"trades (outcome-free count, all windows): treated {ntr}, treated-alt nearest-0.10 {count_trades(alt)}, control nearest-0.10 {count_trades(ctrl)}, model rule in control hours {count_trades(ctrl_model)}; "
               f"treated with a model trade but no fill {sum(1 for _, t in treated if t and t.get('price') is None)}")
    res = {}
    for tag, hs in (("TREATED model edge", treated), ("TREATED-ALT nearest 0.10", alt), ("CONTROL nearest 0.10", ctrl), ("model rule in control hours", ctrl_model)):
        S = {w: L.stats(rows_for(hs, markets, None, win, (w,))) for w in ("W1", "W2")}
        S12 = {w: L.stats(rows_for(hs, markets, None, win, (w,), 1.2)) for w in ("W1", "W2")}
        res[tag] = (S, S12)
        wr = [x for x in rows_for(hs, markets, None, win, ("W1", "W2"))]
        for w in ("W1", "W2"):
            out.append(f"{tag} {L.line(w, S[w])} | fees x1.2 mean {S12[w]['mean']:+.2f}c")
        if wr:
            wins = sum(1 for _, x in wr if x > 0)
            gw = sum(x for _, x in wr if x > 0) / max(1, wins)
            ls = [x for _, x in wr if x <= 0]
            gl = -sum(ls) / max(1, len(ls))
            out.append(f"{tag} W1+W2: win rate {wins/len(wr)*100:.1f}% of {len(wr)}, mean win {gw:.1f}c, mean loss {gl:.1f}c, payoff ratio {gw/gl if gl else float('nan'):.2f}")
    # information: calibration of cheap tails by ratio bucket, windows W1 and W2 only
    out.append("calibration of cheap tails at the look (price 0.03 to 0.30, every strike and side), W1+W2 only: bucket n, mean price, win rate, model(realised) mean prob")
    for tag, f in (("ratio<=0.67", lambda r: r <= LO_RATIO), ("0.67<ratio<1.5", lambda r: LO_RATIO < r < HI_RATIO), ("ratio>=1.5", lambda r: r >= HI_RATIO)):
        n = w = 0; ps = pm = 0.0
        for h in rows:
            if win[day(h["close"])] == "W3" or not f(h["ratio"]):
                continue
            for t in h["tails"]:
                n += 1; ps += t["look"]; pm += t["pm"]
                w += ((markets[t["tk"]]["res"] == "yes") == (t["side"] == "yes"))
        out.append(f"  {tag}: n {n} price {ps/max(1,n):.3f} win {w/max(1,n):.3f} model {pm/max(1,n):.3f}")
    # verdict for Try A (treated) with the control check
    S, S12 = res["TREATED model edge"]
    Sa, _ = res["TREATED-ALT nearest 0.10"]
    Sc, _ = res["CONTROL nearest 0.10"]
    pa = L.stats(rows_for(alt, markets, None, win, ("W1", "W2")))
    pc = L.stats(rows_for(ctrl, markets, None, win, ("W1", "W2")))
    why = []
    if ntr < L.MIN_TRADES:
        out.append(f"{name} Try A: NOT_ENOUGH_DATA | trades {ntr} under {L.MIN_TRADES} (windows read below for information)")
        word, w3 = "NOT_ENOUGH_DATA", False
    else:
        for w in ("W1", "W2"):
            if S[w]["pf"] < L.BAR_PF:
                why.append(f"{w} PF {S[w]['pf']:.2f} under {L.BAR_PF}")
            if S12[w]["mean"] <= 0:
                why.append(f"{w} not positive at fees x1.2")
        if pc["n"] and pc["pf"] >= 1.0:
            why.append(f"control PF {pc['pf']:.2f} not under 1.0 (cheap tails do not lose in calm hours)")
        if pa["pf"] - pc["pf"] < 0.25:
            why.append(f"control behaves like treated (treated-alt PF {pa['pf']:.2f} minus control PF {pc['pf']:.2f} under 0.25)")
        w3 = not why
        if w3:
            S3 = L.stats(rows_for(treated, markets, None, win, ("W3",)))
            S3x = L.stats(rows_for(treated, markets, None, win, ("W3",), 1.2))
            out.append("TREATED model edge " + L.line("W3 (holdout, read because W1, W2 and the control passed)", S3) + f" | fees x1.2 mean {S3x['mean']:+.2f}c")
            if S3["pf"] < L.BAR_PF:
                why.append(f"W3 PF {S3['pf']:.2f} under {L.BAR_PF}")
            if S3x["mean"] <= 0:
                why.append("W3 not positive at fees x1.2")
        else:
            out.append("W3 holdout: not read (W1, W2 or the control did not pass)")
        P = L.stats(rows_for(treated, markets, None, win, ("W1", "W2", "W3") if w3 else ("W1", "W2")))
        out.append(L.line("pooled (windows read)", P))
        if not why and P["z"] < L.BAR_Z:
            word = "NOT_YET_FALSIFIED"; why.append(f"pooled z {P['z']:+.2f} under the deflated bar {L.BAR_Z}: not a finding")
        else:
            word = "FALSIFIED" if why else "NOT_YET_FALSIFIED"
        out.append(f"{name} Try A: {word}" + (" | " + "; ".join(why) if why else ""))
    # Try B: the control rule (nearest 0.10) on all hours is information; its verdict is the control line above.
    out.append(f"{name} control PF (nearest 0.10, ratio<=0.67, W1+W2) {pc['pf']:.2f} mean {pc['mean']:+.2f}c n {pc['n']}; treated-alt PF {pa['pf']:.2f} mean {pa['mean']:+.2f}c n {pa['n']}")


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT); return
    markets = json.loads((CACHE / "markets.json").read_text())
    cands = json.loads((CACHE / "candles.json").read_text())
    klines = {s: {int(a): b for a, b in json.loads((CACHE / f"klines_{inst}.json").read_text()).items()} for s, inst in ASSETS.items()}
    out = [f"VOLGAP1 run {datetime.now(UTC).isoformat()} N={NRUN} z bar {L.BAR_Z} cost: fee 7% x C x p x (1-p) rounded up, C={C}, taker at the next minute's ask",
           f"markets near spot {len(markets)}, with candles {sum(1 for t in markets if cands.get(t))}"]
    for name, series in GROUPS.items():
        score_group(name, series, markets, cands, klines, out)
    txt = "\n".join(out)
    print(txt)
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(txt + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
