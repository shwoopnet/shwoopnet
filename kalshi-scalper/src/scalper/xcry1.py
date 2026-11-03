"""XCRY1 (workers/XCRY1_REGISTRATION.md): a cross-series price-lead trade. When Bitcoin spot moved at least 1.0 trailing-sigma between
360 s and 180 s before the close, buy the cheaper side (ask 0.05 to 0.50) of an altcoin 15 minute market in the SAME direction at the
180 s look, held to settlement. The mirror (cheaper side AGAINST the move) is a CONTROL, reported only. Research only; there is no
promote verb. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
    PYTHONPATH=src python -m scalper.xcry1 fetch   (resumable; settled markets, Kalshi 1 minute candles, OKX BTC-USDT klines)
    PYTHONPATH=src python -m scalper.xcry1 run     (the one scored read; refused a second time)
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

from . import api, lag15
from .lag15 import fee, pnl, quote_at, stats, thirds, volume_ok

UTC = timezone.utc
CACHE = Path(os.environ.get("XCRY1_CACHE", "/tmp/xcry1_cache"))
RESULT = CACHE / "xcry1_result.txt"
ASSETS = ("KXHYPE15M", "KXNEAR15M", "KXZEC15M", "KXBNB15M")   # fixed universe; never Bitcoin, Ethereum, Dogecoin, gold
BTC = "BTC-USDT"
LOOK_S, BACK_S = 180, 360          # trade look and the start of the Bitcoin signal window, seconds before the close
TRIG_MULT = 1.0                    # relative trigger, fixed, not tuned
SIG_MINUTES, MIN_RETURNS = 1440, 1000
LO, HI = 0.05, 0.50                # the cheaper side
MAX_SPREAD, MIN_LISTED_VOL = 0.10, 1000.0
C = 10
BAR_PF, BAR_Z, MIN_TRADES, MIN_MEAN_C = 1.5, 5.27, 150, 2.0
NRUN = 728704
pick = lag15.pick


def btc_end(btc: dict, t: int):
    """Close of the 1 minute kline that ENDS at t (opens at t - 60)."""
    return btc.get(t - 60)


def btc_signal(btc: dict, close: int):
    """(z, direction) from Bitcoin data at or before the look (close - 180 s). None when Bitcoin data are missing.
    ret = ln(end(look) / end(look - 180 s)) ; sigma = RMS of the 3 minute log returns ending every minute over the 1,440 minutes
    ending at the look (needs MIN_RETURNS valid ones)."""
    look = close - LOOK_S
    a, b = btc_end(btc, look), btc_end(btc, close - BACK_S)
    if not a or not b or a <= 0 or b <= 0:
        return None
    rs = []
    for k in range(SIG_MINUTES):
        t = look - 60 * k
        x, y = btc_end(btc, t), btc_end(btc, t - 180)
        if x and y and x > 0 and y > 0:
            rs.append(math.log(x / y))
    if len(rs) < MIN_RETURNS:
        return None
    sig = math.sqrt(sum(r * r for r in rs) / len(rs))
    if sig <= 0:
        return None
    ret = math.log(a / b)
    return ret / sig


def decide(close: int, candles: list, btc: dict):
    """Uses data at or before the look only. Returns None (no Bitcoin signal, no valid quote or volume) or
    dict(z, trig, follow=(side, price)|None, control=(side, price)|None)."""
    look = close - LOOK_S
    z = btc_signal(btc, close)
    q = quote_at(candles, look)
    if z is None or q is None or not volume_ok(candles, look) or q[2] - q[1] > MAX_SPREAD + 1e-9:
        return None
    bid, ask = q[1], q[2]
    out = {"z": z, "trig": abs(z) >= TRIG_MULT, "follow": None, "control": None}
    if not out["trig"]:
        return out
    yes, no = ("yes", ask), ("no", round(1 - bid, 6))
    up = z > 0
    f, c = (yes, no) if up else (no, yes)
    if LO <= f[1] <= HI:
        out["follow"] = f
    if LO <= c[1] <= HI:
        out["control"] = c
    return out


def verdict(S: dict, S12: dict, pooled: dict, w3_read: bool):
    why = []
    if pooled["n"] < MIN_TRADES:
        return "NOT_ENOUGH_DATA", [f"trades {pooled['n']} under {MIN_TRADES}"]
    for w in (("W1", "W2", "W3") if w3_read else ("W1", "W2")):
        if S[w]["pf"] < BAR_PF:
            why.append(f"{w} PF {S[w]['pf']:.2f} under {BAR_PF}")
        if S12[w]["mean"] <= 0:
            why.append(f"{w} not positive at fees x1.2")
    if why:
        return "FALSIFIED", why
    if pooled["mean"] < MIN_MEAN_C or pooled["z"] < BAR_Z:
        return "NOT_YET_FALSIFIED", [f"pooled z {pooled['z']:+.2f} (bar {BAR_Z}) / mean {pooled['mean']:+.2f}c: below the deflated bar, not a pass"]
    return "NOT_YET_FALSIFIED", []


def payoff_ratio(rows) -> float | None:
    w = [x for _, x in rows if x > 0]
    l = [-x for _, x in rows if x < 0]
    return (sum(w) / len(w)) / (sum(l) / len(l)) if w and l else None


# ---------------------------------------------------------------- fetch
def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    mp = CACHE / "markets.json"
    markets = json.loads(mp.read_text()) if mp.exists() else {}
    if not markets:
        for s in ASSETS:
            for m in api.settled_markets(s, 0, 2**31 - 1):
                if m.get("result") in ("yes", "no"):
                    markets[m["ticker"]] = {"s": s, "close": lag15.ts(m["close_time"]), "res": m["result"], "vol": api.f(m.get("volume_fp") or m.get("volume"))}
        mp.write_text(json.dumps(markets)); print(len(markets), "markets", flush=True)
    cp = CACHE / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    by = defaultdict(list)
    for tk, m in markets.items():
        if tk not in have:
            by[m["close"]].append(tk)
    closes = sorted(by)
    groups = [closes[i:i + 4] for i in range(0, len(closes), 4)]
    pause = 0.3
    for i, g in enumerate(groups):
        tks = [t for c in g for t in by[c]]
        lo, hi = g[0] - 600, g[-1] - LOOK_S
        for attempt in range(12):
            try:
                req = urllib.request.Request(api.BASES[1] + "/markets/candlesticks?" + urllib.parse.urlencode({"market_tickers": ",".join(tks), "start_ts": lo, "end_ts": hi, "period_interval": 1}))
                d = json.load(urllib.request.urlopen(req, timeout=30))
                got = {x.get("market_ticker") or x.get("ticker"): x for x in d.get("markets", [])}
                for tk in tks:
                    close = markets[tk]["close"]
                    cs = (got.get(tk) or {}).get("candlesticks", [])
                    have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask")), api.f(c.get("volume_fp") or c.get("volume"))) for c in cs if close - 900 < c["end_period_ts"] <= close - LOOK_S]
                pause = max(0.25, pause * 0.9)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    pause = min(pause * 1.3, 1.5)
                time.sleep(1 + attempt)
            except Exception:
                time.sleep(1 + attempt)
        else:
            print("skip", g[0], flush=True)
        if i % 50 == 0:
            cp.write_text(json.dumps(have)); print("candles", i, len(groups), "pause", round(pause, 2), flush=True)
        time.sleep(pause)
    cp.write_text(json.dumps(have))
    kp = CACHE / f"klines_{BTC}.json"
    if not kp.exists():
        lo = min(m["close"] for m in markets.values()) - 25 * 3600
        hi = max(m["close"] for m in markets.values())
        k = lag15.okx_klines(BTC, lo, hi)
        kp.write_text(json.dumps({str(a): b for a, b in k.items()})); print(BTC, len(k), "klines", flush=True)
    print("done", flush=True)


# ---------------------------------------------------------------- run
def day_of(close: int) -> str:
    return datetime.fromtimestamp(close, UTC).strftime("%Y-%m-%d")


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT); return
    markets = json.loads((CACHE / "markets.json").read_text())
    cands = json.loads((CACHE / "candles.json").read_text())
    btc = {int(a): b for a, b in json.loads((CACHE / f"klines_{BTC}.json").read_text()).items()}
    out = [f"XCRY1 run {datetime.now(UTC).isoformat()} N={NRUN} z bar {BAR_Z} cost: fee 7% x C x p x (1-p) rounded up, C={C}, taker at the ask"]
    elig = {}   # tk -> decision (eligibility never reads an outcome)
    listed_ok = defaultdict(list)
    for tk, m in markets.items():
        listed_ok[m["s"]].append(m["vol"] or 0.0)
    assets = [s for s in ASSETS if len(listed_ok[s]) >= MIN_LISTED_VOL and sum(listed_ok[s]) / len(listed_ok[s]) >= MIN_LISTED_VOL]
    out.append(f"markets {len(markets)}; assets passing the listing rule: {', '.join(assets)}")
    for tk, m in markets.items():
        if m["s"] not in assets:
            continue
        d = decide(m["close"], [tuple(c) for c in cands.get(tk, [])], btc)
        if d:
            elig[tk] = d
    trig = [tk for tk, d in elig.items() if d["trig"]]
    fol = [tk for tk in trig if elig[tk]["follow"]]
    ctl = [tk for tk in trig if elig[tk]["control"]]
    out.append(f"eligible markets {len(elig)}; Bitcoin trigger fired in {len(trig)}; follow trades {len(fol)}; control trades {len(ctl)}")
    win = thirds([day_of(markets[tk]["close"]) for tk in elig])
    rows = {k: {w: [] for w in ("W1", "W2", "W3")} for k in ("follow", "control", "follow12", "control12")}
    seqs = []
    for tk in sorted(trig, key=lambda t: markets[t]["close"]):
        m, d = markets[tk], elig[tk]
        w, day = win[day_of(m["close"])], day_of(m["close"])
        for k in ("follow", "control"):
            if d[k]:
                side, price = d[k]
                rows[k][w].append((day, pnl(side, price, m["res"])))
                rows[k + "12"][w].append((day, pnl(side, price, m["res"], 1.2)))
    S = {w: stats(rows["follow"][w]) for w in ("W1", "W2", "W3")}
    S12 = {w: stats(rows["follow12"][w]) for w in S}
    K = {w: stats(rows["control"][w]) for w in S}
    ok = S["W1"]["pf"] >= BAR_PF and S["W2"]["pf"] >= BAR_PF
    for w in ("W1", "W2"):
        out.append(lag15.line("follow " + w, S[w]) + f" | fees x1.2 mean {S12[w]['mean']:+.2f}c | payoff ratio {payoff_ratio(rows['follow'][w])}")
        out.append(lag15.line("control " + w, K[w]))
    if ok:
        out.append(lag15.line("follow W3 (holdout, read because W1 and W2 passed)", S["W3"]))
        out.append(lag15.line("control W3", K["W3"]))
    else:
        out.append("W3 holdout: not read (W1 and W2 did not both pass)")
    read = ("W1", "W2", "W3") if ok else ("W1", "W2")
    pooled_rows = [r for w in read for r in rows["follow"][w]]
    P = stats(pooled_rows)
    word, why = verdict(S, S12, P, ok)
    out.append(lag15.line("follow pooled (windows read)", P))
    out.append(lag15.line("control pooled (windows read)", stats([r for w in read for r in rows["control"][w]])))
    # win rate, payoff ratio, streaks (windows read, in time order)
    ordered = []
    for tk in sorted(fol, key=lambda t: markets[t]["close"]):
        m = markets[tk]
        if win[day_of(m["close"])] in read:
            side, price = elig[tk]["follow"]
            ordered.append((m["close"], (m["res"] == "yes") == (side == "yes"), pnl(side, price, m["res"])))
    wins = [x for _, x, _ in ordered]
    wr = sum(wins) / len(wins) if wins else 0.0
    out.append(f"follow win rate {wr*100:.1f}% on {len(wins)}; payoff ratio (avg win / avg loss) {payoff_ratio(pooled_rows)}; mean entry price {sum(pnl_price for pnl_price in [elig[tk]['follow'][1] for tk in fol if win[day_of(markets[tk]['close'])] in read])/max(1,len(wins)):.3f}")
    from . import streaks
    es = streaks.empirical_streaks(wins)
    dist = streaks.longest_losing_run_distribution(wr, 100) if wins else {}
    out.append(f"streaks: longest losing run {es['longest_losing_run']}; 100 trades at win rate {wr*100:.1f}%: p95 {dist.get('p95')} p99 {dist.get('p99')}; P(>=1 ten-loss run in 100) {streaks.prob_run_at_least(10, wr, 100):.3f}")
    for a in assets:
        ra = [(markets[tk]["close"], tk) for tk in fol if markets[tk]["s"] == a and win[day_of(markets[tk]["close"])] in read]
        pa = stats([(day_of(c), pnl(elig[tk]["follow"][0], elig[tk]["follow"][1], markets[tk]["res"])) for c, tk in ra])
        out.append(lag15.line("  by asset " + a, pa))
    out.append(f"XCRY1: {word}" + (" | " + "; ".join(why) if why else ""))
    # OICORE overlap (Bitcoin windows 2026-08-06 .. 2026-10-27 from the forward ledger); information only
    try:
        from . import fals4, oirel
        from .fwdeval import NoData
        from .fwdledger import net_per_contract
        from .oidrift import _ledger_windows
        oi = {}
        for w in _ledger_windows(fals4.START, fals4.FORWARD_TS):
            try:
                t = oirel.decide(w)
            except NoData:
                continue
            if t:
                oi[w["close_ts"]] = net_per_contract(t, w["result"], 10)
        mine = [(markets[tk]["close"], pnl(*elig[tk]["follow"], markets[tk]["res"])) for tk in fol if win[day_of(markets[tk]["close"])] in read]
        lo_ts, hi_ts = min(oi) if oi else 0, max(oi) if oi else 0
        inr = [x for x in mine if lo_ts <= x[0] <= hi_ts]
        both = [x for x in inr if x[0] in oi]
        out.append(f"OICORE (OIREL research rule, Bitcoin) windows {len(oi)} in {day_of(lo_ts) if oi else '-'}..{day_of(hi_ts) if oi else '-'}; XCRY1 trades in that span {len(inr)}; in a window where OICORE also fires {len(both)} ({100*len(both)/max(1,len(inr)):.1f}%)")
        dx, do = defaultdict(float), defaultdict(float)
        for c, x in inr:
            dx[day_of(c)] += x
        for c, x in oi.items():
            do[day_of(c)] += x
        days = sorted(set(dx) & set(do))
        if len(days) > 3:
            a, b = [dx[d] for d in days], [do[d] for d in days]
            ma, mb = sum(a) / len(a), sum(b) / len(b)
            sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((x - mb) ** 2 for x in b))
            out.append(f"daily PnL correlation XCRY1 vs OICORE over {len(days)} days: {sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sa*sb):+.2f}" if sa and sb else "daily correlation undefined")
    except Exception as e:  # information only
        out.append(f"OICORE overlap not computed: {type(e).__name__}: {e}")
    txt = "\n".join(out)
    print(txt)
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(txt + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
