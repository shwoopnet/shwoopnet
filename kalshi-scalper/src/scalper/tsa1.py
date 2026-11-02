"""TSA1 (workers/TSA1_REGISTRATION.md): Kalshi weekly TSA throughput ladder (KXTSAW, TSAW) against same-week-last-year x trailing YoY.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade; no promote verb.
    python -m scalper.tsa1 fetch   (resumable: market listings, then hourly candles for the registered universe, into data/tsa1/)
    python -m scalper.tsa1 run     (the one scored read; refused a second time)
The settled value of every weekly event is Kalshi's expiration_value (the number TSA published); tsa.gov itself is unreachable here.
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from . import api
from .calibration import cluster_mean_z
from .econnew1 import fee, line, pick, pnl, stats
from .paths import DATA_DIR

D = DATA_DIR / "tsa1"
RESULT = DATA_DIR / "tsa1_result.txt"
UTC = timezone.utc
SERIES = ("KXTSAW", "TSAW")
GAP, MAX_SPREAD, MAX_AGE_S, MIN_ERR = 0.08, 0.10, 6 * 3600, 30
UNIV = (0.10, 0.90)
BAR_PF, BAR_Z, MIN_MEAN_C, MIN_TRADES = 1.5, 5.27, 2.0, 150


def ev_date(event):
    return datetime.strptime(event.split("-", 1)[1][:7], "%y%b%d").date()


def strike_of(m):
    if m.get("floor_strike") is not None:
        return float(m["floor_strike"])
    t = (m.get("yes_sub_title") or "").replace(",", "")
    x = re.search(r"Above\s+([0-9.]+)\s*(million)?", t)
    if not x:
        return None
    v = float(x.group(1))
    return v * 1e6 if x.group(2) else v


def weekly_values(markets):
    """{sunday date: settled average} from expiration_value; an event with conflicting non-empty values is dropped."""
    vals = defaultdict(set)
    for m in markets:
        v = (m.get("expiration_value") or "").replace(",", "")
        if v:
            try:
                vals[ev_date(m["event_ticker"])].add(float(v))
            except ValueError:
                pass
    return {d: next(iter(s)) for d, s in vals.items() if len(s) == 1}


def centre(A, s):
    """c = A(s-364) x mean_k A(s-7k)/A(s-7k-364), k = 2..5; weeks <= s-14 only. None if any of the nine values is missing."""
    y = A.get(s - timedelta(days=364))
    rs = []
    for k in range(2, 6):
        a, b = A.get(s - timedelta(days=7 * k)), A.get(s - timedelta(days=7 * k + 364))
        if a is None or b is None or b <= 0:
            return None
        rs.append(a / b)
    if y is None or y <= 0:
        return None
    return y * sum(rs) / 4


def predictions(A):
    """{s: (centre, sorted earlier log errors)} for eligible events with at least MIN_ERR earlier errors (expanding)."""
    out, errs = {}, []
    for s in sorted(A):
        c = centre(A, s)
        if c is None:
            continue
        if len(errs) >= MIN_ERR:
            out[s] = (c, sorted(errs))
        errs.append(math.log(A[s] / c))
    return out


def fair(c, errs, strike):
    """P(A > K) = (count of errors with c exp(e) > K + 0.5) / (n + 1); errs sorted ascending."""
    if strike <= 0:
        return None
    need = math.log(strike / c)
    k = len(errs) - bisect_right(errs, need)
    return (k + 0.5) / (len(errs) + 1)


def look_ts(s):
    return int(datetime(s.year, s.month, s.day, 16, tzinfo=UTC).timestamp()) - 6 * 86400


def quote(cs, look):
    q = [c for c in cs if c[0] <= look and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and look - c[0] <= MAX_AGE_S]
    return (q[-1][1], q[-1][2]) if q else None


def entry(f, bid, ask, gap=GAP):
    if ask - bid > MAX_SPREAD + 1e-9:
        return None
    if f - ask - 0.07 * ask * (1 - ask) >= gap:
        return "yes", ask
    if bid - f - 0.07 * bid * (1 - bid) >= gap:
        return "no", 1 - bid
    return None


def thirds(events):
    ev = sorted(events)
    n = len(ev)
    cut1, cut2 = ev[n // 3], ev[(2 * n) // 3]
    return lambda s: "W1" if s < cut1 else ("W2" if s < cut2 else "W3")


# ---------------------------------------------------------------- data
def list_all():
    out = {}
    for path, src in (("/historical/markets", "hist"), ("/markets", "live")):
        for s in SERIES:
            cur = ""
            while True:
                q = {"series_ticker": s, "limit": 1000}
                if src == "live":
                    q["status"] = "settled"
                if cur:
                    q["cursor"] = cur
                d = api._get(path, q)
                for m in d["markets"]:
                    if m["ticker"] not in out or src == "hist":
                        m["src"] = src
                        m["series"] = s
                        out[m["ticker"]] = m
                cur = d.get("cursor")
                if not cur or not d["markets"]:
                    break
                time.sleep(0.5)
    return list(out.values())


def universe(markets):
    """Strikes of predicted events with model fair 0.10..0.90. No price is read."""
    A = weekly_values(markets)
    P = predictions(A)
    uni = {}
    for m in markets:
        if m.get("series", m["event_ticker"].split("-")[0]) not in SERIES:
            continue
        k = strike_of(m)
        s = ev_date(m["event_ticker"])
        if k is None or s not in P or m.get("result") not in ("yes", "no"):
            continue
        f = fair(P[s][0], P[s][1], k)
        if f is not None and UNIV[0] <= f <= UNIV[1]:
            uni[m["ticker"]] = dict(event=m["event_ticker"], s=s.isoformat(), strike=k, fair=f, res=m["result"], src=m.get("src", "hist"), series=m["event_ticker"].split("-")[0])
    return uni, P


def fetch():
    D.mkdir(parents=True, exist_ok=True)
    mp = D / "markets.json"
    if not mp.exists():
        mp.write_text(json.dumps(list_all()))
    markets = json.loads(mp.read_text())
    uni, _ = universe(markets)
    (D / "universe.json").write_text(json.dumps(uni))
    print("universe strikes", len(uni), "events", len({m["event"] for m in uni.values()}), flush=True)
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for i, (tk, m) in enumerate(uni.items()):
        if tk in have:
            continue
        L = look_ts(datetime.fromisoformat(m["s"]).date())
        try:
            path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{m['series']}/markets/{tk}/candlesticks"
            d = api._get(path, {"start_ts": L - 12 * 3600, "end_ts": L, "period_interval": 60})
            have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
        except Exception as e:
            print("skip", tk, e)
            continue
        if i % 25 == 0:
            cp.write_text(json.dumps(have))
            print(i, len(uni), flush=True)
        time.sleep(0.4)
    cp.write_text(json.dumps(have))
    print("done", len(have), flush=True)


# ---------------------------------------------------------------- run
def collect(uni, cands, win, mult=1.0, gap=GAP):
    rows = defaultdict(list)
    for tk, m in uni.items():
        s = datetime.fromisoformat(m["s"]).date()
        q = quote(cands.get(tk, []), look_ts(s))
        if not q:
            continue
        e = entry(m["fair"], q[0], q[1], gap)
        if e:
            rows[win(s)].append((m["event"], pnl(e[0], e[1], m["res"], mult)))
    return rows


def brier(uni, cands):
    mod = mkt = n = 0
    for tk, m in uni.items():
        s = datetime.fromisoformat(m["s"]).date()
        q = quote(cands.get(tk, []), look_ts(s))
        if not q or q[1] - q[0] > MAX_SPREAD + 1e-9:
            continue
        y = 1.0 if m["res"] == "yes" else 0.0
        mod += (m["fair"] - y) ** 2
        mkt += ((q[0] + q[1]) / 2 - y) ** 2
        n += 1
    return (mod / n, mkt / n, n) if n else (None, None, 0)


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT)
        return
    uni = json.loads((D / "universe.json").read_text())
    cands = json.loads((D / "candles.json").read_text())
    markets = json.loads((D / "markets.json").read_text())
    P = predictions(weekly_values(markets))
    win = thirds(list(P))
    out = [f"TSA1 run {datetime.now(UTC).isoformat()} N=728700 z bar {BAR_Z}", f"predicted events {len(P)}, universe strikes {len(uni)}, with candles {sum(1 for t in uni if t in cands)}"]
    mb, kb, nb = brier(uni, cands)
    if nb:
        out.append(f"Brier model {mb:.4f} market mid {kb:.4f} (strikes {nb})")
    S, S12 = {}, {}
    r1, r12 = collect(uni, cands, win), collect(uni, cands, win, 1.2)
    ok = True
    for w in ("W1", "W2"):
        S[w] = stats(r1[w])
        S12[w] = stats(r12[w])
        out.append(line(w, S[w]) + f" | fees x1.2 PF {S12[w]['pf']:.2f}")
        ok = ok and S[w]["pf"] >= BAR_PF
    ntr = sum(S[w]["n"] for w in S)
    pooled = [x for w in ("W1", "W2") for x in r1[w]]
    why = []
    if ok and nb and mb is not None and mb < kb:
        S["W3"], S12["W3"] = stats(r1["W3"]), stats(r12["W3"])
        out.append(line("W3 (holdout, read because W1 and W2 passed)", S["W3"]) + f" | fees x1.2 PF {S12['W3']['pf']:.2f}")
        pooled += r1["W3"]
        ntr += S["W3"]["n"]
    else:
        out.append("W3 holdout NOT read (W1 and W2 did not both pass, or the model Brier is not better than the market)")
    ps = stats(pooled)
    out.append(line("pooled read windows", ps))
    for g in (0.05, 0.12):
        rr = collect(uni, cands, win, 1.0, g)
        out.append(f"info gap {g}: " + " ".join(f"{w} n {len(rr[w])} PF {stats(rr[w])['pf']:.2f}" for w in ("W1", "W2", "W3")))
    if not nb:
        verdict, why = "NOT_RUNNABLE", ["no candles with a quote"]
    elif ntr < MIN_TRADES:
        verdict, why = "NOT_ENOUGH_DATA", [f"{ntr} trades under {MIN_TRADES}"]
    else:
        if any(S[w]["pf"] < BAR_PF for w in S):
            why.append("PF under 1.5 in a window")
        if any(S12[w]["pf"] < 1.0 for w in S12):
            why.append("not positive at fees x1.2")
        if not (mb < kb):
            why.append("model Brier not better than the market")
        if ps["z"] < BAR_Z:
            why.append(f"pooled z {ps['z']:.2f} under {BAR_Z}")
        if ps["mean"] < MIN_MEAN_C:
            why.append("pooled mean under 2c")
        verdict = "FALSIFIED" if why else "NOT_YET_FALSIFIED"
    out.append(f"VERDICT {verdict}: " + "; ".join(why))
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
