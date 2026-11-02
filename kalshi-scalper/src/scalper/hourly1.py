"""HOURLY1 (workers/HOURLY1_REGISTRATION.md): a spot-lognormal model against the quotes of Kalshi's hourly altcoin "above" ladders
(KXSOLD, KXXRPD, KXDOGED, KXHYPED) never named in the README. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED,
NOT_ENOUGH_DATA, NOT_RUNNABLE, OVERLAPS_L1. Nothing here means trade; there is no promote verb.
    python -m scalper.hourly1 fetch   (resumable; settled markets, OKX 1 minute klines, then Kalshi 1 minute candles for the strikes near spot)
    python -m scalper.hourly1 run     (the one scored read; refused a second time)
Reuses lag15's fee, quote, windows, statistics and verdict code unchanged.
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

from . import api
from . import lag15 as L

UTC = timezone.utc
CACHE = Path(os.environ.get("HOURLY1_CACHE", "/tmp/hourly1_cache"))
RESULT = CACHE / "hourly1_result.txt"
ASSETS = {"KXSOLD": "SOL-USDT", "KXXRPD": "XRP-USDT", "KXDOGED": "DOGE-USDT", "KXHYPED": "HYPE-USDT"}
GROUPS = {"SOL": ["KXSOLD"], "XRP": ["KXXRPD"], "DOGE+HYPE": ["KXDOGED", "KXHYPED"]}
LOOK_S = 600                 # seconds before the hourly close
TAU_S = 570                  # horizon: the centre of the final 60 s averaging window
NRET = 60                    # one minute log returns in the volatility estimate (61 closes)
NEAR = 0.02                  # fetch/consider strikes within 2% of the spot at the look (spot only, no outcome)
EDGE_A, EDGE_B = 0.08, 0.12  # Try A (verdict) and Try B (information only)
MIN_ENTRY, BAND, OVERLAP_SHARE = 0.20, (0.88, 0.97), 0.50
NRUN = 728720
C = L.C


def sigma_per_s(closes: list) -> float | None:
    """61 consecutive one minute closes ending at the look. RMS of the 60 log returns / sqrt(60); None if any close is missing or sigma is 0."""
    if len(closes) != NRET + 1 or any(c is None or c <= 0 for c in closes):
        return None
    r = [math.log(closes[i + 1] / closes[i]) for i in range(NRET)]
    s = math.sqrt(sum(x * x for x in r) / NRET) / math.sqrt(60)
    return s if s > 0 else None


def p_above(S: float, K: float, sigma: float, tau: float = TAU_S) -> float:
    """P(S_T > K), S_T lognormal with E[S_T] = S and variance sigma^2 * tau (sigma per sqrt second)."""
    v = sigma * math.sqrt(tau)
    return 1 - L.phi((math.log(K / S) + 0.5 * v * v) / v)


def decide_event(close: int, strikes: list, candles: dict, klines: dict, edge: float):
    """strikes: [(ticker, K)] of one event. Uses data at or before the look (close - 600 s) only.
    Returns (eligible list of (ticker, K, p, mid, bid, ask), best trade dict or None, banned count)."""
    look = close - LOOK_S
    closes = [klines.get(look - 60 - 60 * (NRET - i)) for i in range(NRET + 1)]   # the kline opening at look-60 ends AT the look
    sig = sigma_per_s(closes)
    if sig is None:
        return [], None, 0
    S = closes[-1]
    elig, best, banned = [], None, 0
    for tk, K in strikes:
        if abs(math.log(K / S)) > NEAR:
            continue
        cs = [tuple(c) for c in candles.get(tk, [])]
        q = L.quote_at(cs, look)
        if q is None or not L.volume_ok(cs, look) or q[2] - q[1] > L.MAX_SPREAD + 1e-9:
            continue
        bid, ask = q[1], q[2]
        p = p_above(S, K, sig)
        elig.append((tk, K, p, (bid + ask) / 2, bid, ask))
        e_yes = p - ask - L.fee_exact(ask)
        e_no = (1 - p) - (1 - bid) - L.fee_exact(1 - bid)
        if e_yes >= edge and e_yes >= e_no:
            side, price, e = "yes", ask, e_yes
        elif e_no >= edge:
            side, price, e = "no", 1 - bid, e_no
        else:
            continue
        if price < MIN_ENTRY:
            banned += 1
            continue
        if best is None or e > best["edge"] + 1e-12 or (abs(e - best["edge"]) <= 1e-12 and K < best["K"]):
            best = {"tk": tk, "K": K, "side": side, "price": price, "edge": e, "p": p}
    return elig, best, banned


# ---------------------------------------------------------------- fetch
def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    mp = CACHE / "markets.json"
    markets = json.loads(mp.read_text()) if mp.exists() else {}
    if not markets:
        for s in ASSETS:
            for m in api.settled_markets(s, 0, 2**31 - 1):
                if m.get("result") in ("yes", "no") and m.get("floor_strike") is not None and m.get("strike_type") == "greater":
                    markets[m["ticker"]] = {"s": s, "ev": m["event_ticker"], "close": L.ts(m["close_time"]), "k": float(m["floor_strike"]), "res": m["result"]}
        mp.write_text(json.dumps(markets)); print(len(markets), "markets", flush=True)
    lo = min(m["close"] for m in markets.values()) - LOOK_S - 6000
    hi = max(m["close"] for m in markets.values())
    klines = {}
    for s, inst in ASSETS.items():
        kp = CACHE / f"klines_{inst}.json"
        if not kp.exists():
            k = L.okx_klines(inst, lo, hi)
            kp.write_text(json.dumps({str(a): b for a, b in k.items()})); print(inst, len(k), "klines", flush=True)
        klines[s] = {int(a): b for a, b in json.loads(kp.read_text()).items()}
    # candidate strikes: near the spot at the look (spot only; no result is read here)
    cp = CACHE / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    by = defaultdict(list)
    for tk, m in markets.items():
        S = klines[m["s"]].get(m["close"] - LOOK_S - 60)
        if S and abs(math.log(m["k"] / S)) <= NEAR and tk not in have:
            by[m["close"]].append(tk)
    closes = sorted(by)
    groups, cur = [], []
    for c in closes:                                   # about 100 tickers per request
        if cur and sum(len(by[x]) for x in cur) + len(by[c]) > 100:
            groups.append(cur); cur = []
        cur.append(c)
    if cur:
        groups.append(cur)
    pause = 0.3
    for i, g in enumerate(groups):
        tks = [t for c in g for t in by[c]]
        lo2, hi2 = min(g) - LOOK_S - 420, max(g) - LOOK_S
        for attempt in range(12):
            try:
                req = urllib.request.Request(api.BASES[1] + "/markets/candlesticks?" + urllib.parse.urlencode({"market_tickers": ",".join(tks), "start_ts": lo2, "end_ts": hi2, "period_interval": 1}))
                d = json.load(urllib.request.urlopen(req, timeout=30))
                got = {x.get("market_ticker") or x.get("ticker"): x for x in d.get("markets", [])}
                for tk in tks:
                    close = markets[tk]["close"]
                    cs = (got.get(tk) or {}).get("candlesticks", [])
                    have[tk] = [(c["end_period_ts"], L.pick(c.get("yes_bid")), L.pick(c.get("yes_ask")), api.f(c.get("volume_fp") or c.get("volume")))
                                for c in cs if close - 3600 < c["end_period_ts"] <= close - LOOK_S]
                pause = max(0.25, pause * 0.9)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    pause = min(pause * 1.3, 1.5); time.sleep(1 + attempt)
                else:
                    time.sleep(1 + attempt)
            except Exception:
                time.sleep(1 + attempt)
        else:
            print("skip", g[0], flush=True)
        if i % 50 == 0:
            cp.write_text(json.dumps(have)); print("candles", i, len(groups), "pause", round(pause, 2), flush=True)
        time.sleep(pause)
    cp.write_text(json.dumps(have))
    print("done", flush=True)


# ---------------------------------------------------------------- run
def collect(markets, cands, klines, series, edge):
    """Per event of the given series: (market dict of the best trade or None, eligible list, banned). No outcome is read."""
    ev = defaultdict(list)
    for tk, m in markets.items():
        if m["s"] in series:
            ev[(m["s"], m["ev"], m["close"])].append((tk, m["k"]))
    rows = []
    for (s, e, close), strikes in ev.items():
        elig, best, banned = decide_event(close, strikes, cands, klines[s], edge)
        rows.append({"s": s, "close": close, "elig": elig, "best": best, "banned": banned})
    return rows


def day(close: int) -> str:
    return datetime.fromtimestamp(close, UTC).strftime("%Y-%m-%d")


def score_group(name, series, markets, cands, klines, out):
    out.append(f"--- GROUP {name} ({', '.join(series)})")
    scored = []
    for s in series:
        r = collect(markets, cands, klines, {s}, EDGE_A)
        trades = [x["best"]["price"] for x in r if x["best"]]
        sh = L.overlap_share(trades)
        tag = "OVERLAPS_L1 (not scored)" if trades and sh >= OVERLAP_SHARE else "scored"
        out.append(f"{s}: events with a model {sum(1 for x in r if x['elig'])}, eligible strikes {sum(len(x['elig']) for x in r)}, qualifying trades {len(trades)}, banned under {MIN_ENTRY} {sum(x['banned'] for x in r)}, share priced {BAND[0]} to {BAND[1]} {sh*100:.0f}% -> {tag}")
        if tag == "scored":
            scored.append(s)
    if not scored:
        out.append(f"GROUP {name}: OVERLAPS_L1 or no qualifying trades; nothing scored."); return
    for tag, edge in (("Try A edge 0.08 (verdict)", EDGE_A), ("Try B edge 0.12", EDGE_B)):
        rows = collect(markets, cands, klines, set(scored), edge)
        win = L.thirds([day(x["close"]) for x in rows if x["elig"]])
        el = [(day(x["close"]), e) for x in rows for e in x["elig"]]
        res = lambda tk: markets[tk]["res"] == "yes"
        bm = sum((e[2] - res(e[0])) ** 2 for x in rows for e in x["elig"]) / max(1, len(el))
        bk = sum((e[3] - res(e[0])) ** 2 for x in rows for e in x["elig"]) / max(1, len(el))
        out.append(f"{tag}: eligible strikes {len(el)} on {len(win)} dates; Brier model {bm:.4f} market mid {bk:.4f}")
        tr = {w: [] for w in ("W1", "W2", "W3")}
        tr12 = {w: [] for w in tr}
        for x in rows:
            b = x["best"]
            if not b:
                continue
            d = day(x["close"])
            r = markets[b["tk"]]["res"]
            tr[win[d]].append((d, L.pnl(b["side"], b["price"], r)))
            tr12[win[d]].append((d, L.pnl(b["side"], b["price"], r, 1.2)))
        S = {w: L.stats(tr[w]) for w in tr}
        S12 = {w: L.stats(tr12[w]) for w in tr}
        for w in ("W1", "W2"):
            out.append(L.line(w, S[w]) + f" | fees x1.2 mean {S12[w]['mean']:+.2f}c")
        ok = S["W1"]["pf"] >= L.BAR_PF and S["W2"]["pf"] >= L.BAR_PF
        w3 = ok and bm < bk
        pooled_rows = tr["W1"] + tr["W2"] + (tr["W3"] if w3 else [])
        out.append(L.line("W3 (holdout, read because W1 and W2 passed)", S["W3"]) if w3 else "W3 holdout: not read (W1 and W2 did not both pass, or Brier failed)")
        P = L.stats(pooled_rows)
        word, why = L.verdict(S, S12, bm, bk, w3, P)
        out.append(L.line("pooled (windows read)", P))
        out.append(f"{name} {tag}: {word}" + (" | " + "; ".join(why) if why else ""))


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT); return
    markets = json.loads((CACHE / "markets.json").read_text())
    cands = json.loads((CACHE / "candles.json").read_text())
    klines = {s: {int(a): b for a, b in json.loads((CACHE / f"klines_{inst}.json").read_text()).items()} for s, inst in ASSETS.items()}
    out = [f"HOURLY1 run {datetime.now(UTC).isoformat()} N={NRUN} z bar {L.BAR_Z} cost: fee 7% x C x p x (1-p) rounded up, C={C}, taker at the ask",
           f"markets {len(markets)}, with candles {sum(1 for t in markets if cands.get(t))}"]
    for name, series in GROUPS.items():
        score_group(name, series, markets, cands, klines, out)
    txt = "\n".join(out)
    print(txt)
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(txt + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
