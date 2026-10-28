"""MENT1 (README, Pre-registration: MENT1): earnings-call word markets against the word's own history. Discovery lane, research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
    python -m scalper.ment1 fetch   (resumable: markets and hourly candles into data/ment1/)
    python -m scalper.ment1 run     (the one read; refused a second time)
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from datetime import datetime

from . import api
from .calibration import cluster_mean_z
from .paths import DATA_DIR

D = DATA_DIR / "ment1"
RESULT = DATA_DIR / "ment1_result.txt"
PRIOR_W, MIN_POOL, EDGE, DEC_H = 5, 15, 0.08, 8
MIN_EVENTS, MIN_TRADES, BAR_PF, BAR_C, BAR_Z = 100, 100, 1.5, 0.02, 2.5


def fee(p, m=1.0):
    return m * 0.07 * p * (1 - p)


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def fetch():
    D.mkdir(exist_ok=True)
    mp = D / "markets.json"
    ms = json.loads(mp.read_text()) if mp.exists() else {}
    if not ms:
        sers = [x["ticker"] for x in api._get("/series", {"category": "Mentions"})["series"] if x["ticker"].startswith("KXEARNINGSMENTION")]
        for s in sers:
            for path, extra, src in (("/historical/markets", {}, "hist"), ("/markets", {"status": "settled"}, "live")):
                cur = None
                while True:
                    p = {"series_ticker": s, "limit": 1000, **extra}
                    if cur:
                        p["cursor"] = cur
                    r = api._get(path, p)
                    for m in r.get("markets", []):
                        if m.get("result") in ("yes", "no"):
                            ms[m["ticker"]] = {"t": m["ticker"], "s": s, "ev": m["event_ticker"], "res": m["result"], "close": m["close_time"], "src": src}
                    cur = r.get("cursor")
                    if not cur or not r.get("markets"):
                        break
        mp.write_text(json.dumps(ms)); print(len(ms), "markets", flush=True)
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for i, (tk, m) in enumerate(ms.items()):
        if tk in have:
            continue
        close = ts(m["close"])
        try:
            path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{m['s']}/markets/{tk}/candlesticks"
            d = api._get(path, {"start_ts": close - 4 * 86400, "end_ts": close, "period_interval": 60})
            have[tk] = [(c["end_period_ts"], api.f((c.get("yes_bid") or {}).get("close_dollars")), api.f((c.get("yes_ask") or {}).get("close_dollars"))) for c in d.get("candlesticks", [])]
        except Exception:
            have[tk] = []
        if i % 100 == 0:
            cp.write_text(json.dumps(have)); print(i, len(ms), flush=True)
        time.sleep(0.12)
    cp.write_text(json.dumps(have)); print("done", flush=True)


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__); return
    if argv[1] == "fetch":
        fetch(); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    ms = json.loads((D / "markets.json").read_text()); cd = json.loads((D / "candles.json").read_text())
    ev_close = defaultdict(list)
    for m in ms.values():
        ev_close[m["ev"]].append(ts(m["close"]))
    ev_dec = {e: min(v) - DEC_H * 3600 for e, v in ev_close.items()}
    word = lambda m: m["t"].split("-")[-1]
    comp = lambda m: m["s"]
    # chronological order by decision time
    order = sorted(ms.values(), key=lambda m: ev_dec[m["ev"]])
    trades = []
    for m in order:
        dec = ev_dec[m["ev"]]
        w = word(m); c = comp(m)
        pool_n = pool_k = n = k = 0
        for q in ms.values():
            if q["ev"] == m["ev"] or ev_close[q["ev"]] and max(ev_close[q["ev"]]) >= dec or word(q) != w:
                continue
            pool_n += 1; pool_k += q["res"] == "yes"
            if q["s"] == c:
                n += 1; k += q["res"] == "yes"
        if pool_n < MIN_POOL:
            continue
        pooled = pool_k / pool_n
        fair = (k + PRIOR_W * pooled) / (n + PRIOR_W)
        cs = [x for x in cd.get(m["t"], []) if x[0] <= dec and x[1] is not None and x[2] is not None and 0 < x[1] < x[2] < 1]
        if not cs:
            continue
        bid, ask = cs[-1][1], cs[-1][2]
        yes = m["res"] == "yes"
        if fair - ask >= EDGE:
            net = (1.0 if yes else 0.0) - ask - fee(ask); st = (1.0 if yes else 0.0) - ask - fee(ask, 1.2)
        elif bid - fair >= EDGE:
            net = (0.0 if yes else 1.0) - (1 - bid) - fee(1 - bid); st = (0.0 if yes else 1.0) - (1 - bid) - fee(1 - bid, 1.2)
        else:
            continue
        trades.append((dec, m["ev"], net, st))
    def pf(xs):
        w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0); return w / l if l else float("inf")
    lines = []
    if not trades:
        RESULT.write_text("MENT1 NOT_ENOUGH_DATA: no trades\n"); print("no trades"); return
    trades.sort(); nets = [t[2] for t in trades]; sts = [t[3] for t in trades]
    evs = sorted({t[1] for t in trades}, key=lambda e: ev_dec[e]); idx = {e: i for i, e in enumerate(evs)}
    h1 = [t[2] for t in trades if idx[t[1]] < len(evs) // 2]; h2 = [t[2] for t in trades if idx[t[1]] >= len(evs) // 2]
    m_, _, z = cluster_mean_z([(t[1], t[2]) for t in trades])
    lr = sum(1 for x in nets if x < 0) / len(nets)
    if len(evs) < MIN_EVENTS or len(trades) < MIN_TRADES:
        verdict = "NOT_ENOUGH_DATA"
    elif pf(nets) < BAR_PF or pf(h1) < 1 or pf(h2) < 1:
        verdict = "FALSIFIED"
    elif z >= BAR_Z and m_ >= BAR_C and pf(sts) >= 1.2:
        verdict = "NOT_YET_FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    lines.append(f"MENT1 {verdict}: PF {pf(nets):.2f} (fees x1.2 {pf(sts):.2f}), loss rate {100 * lr:.0f}%, {len(trades)} trades on {len(evs)} independent events (company-quarters), mean {100 * m_:+.2f}c, event-clustered z {z:+.2f}, halves PF {pf(h1):.2f} / {pf(h2):.2f}, markets considered {len(ms)}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
