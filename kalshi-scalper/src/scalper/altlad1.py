"""ALTLAD1 (workers/ALTLAD1_REGISTRATION.md): altcoin above/below ladders, CHEAP side only (ask 3c to 30c), against an OKX spot
reference and a Student t nowcast; looks at 30 and 10 minutes before the close. Research only: nothing here places an order and
there is deliberately no favourite-side rule or output (owner rule). Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA,
NOT_RUNNABLE. No promote verb.

Usage (cache lives OUTSIDE the repo, ALTLAD1_CACHE; every step resumable):
  python -m scalper.altlad1 markets   settled markets closing BEFORE the frozen cut (the cut and later are never listed or stored)
  python -m scalper.altlad1 okx       OKX 1 minute klines for the coins
  python -m scalper.altlad1 fit       df of the t tail, first two thirds of development dates, OKX only
  python -m scalper.altlad1 candles   Kalshi minute candles for the pre-filtered strikes (md5 event order, one thread)
  python -m scalper.altlad1 census    treated-trade count per look (quotes and OKX only, no result read)
  python -m scalper.altlad1 score     ONE scored run (refused a second time)
"""
from __future__ import annotations

import bisect
import hashlib
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
from .calibration import cluster_mean_z

UTC = timezone.utc
CACHE = Path(os.environ.get("ALTLAD1_CACHE", "/tmp/altlad1_cache"))
RESULT = CACHE / "altlad1_result.txt"
CUT = L.ts("2026-10-03T16:00:00Z")           # frozen: nothing closing at or after this is listed, fetched or joined
COINS = {"KXSOLD": "SOL", "KXXRPD": "XRP", "KXDOGED": "DOGE", "KXHYPED": "HYPE", "KXBNBD": "BNB", "KXZECD": "ZEC", "KXZECH": "ZEC",
         "KXNEARD": "NEAR", "KXNEARH": "NEAR", "KXTOND": "TON", "KXTONH": "TON", "KXSHIBAD": "SHIB", "KXXLMD": "XLM",
         "KXRIPPLED": "XRP", "KXLINKD": "LINK", "KXDOTD": "DOT", "KXAVAXD": "AVAX", "KXLTCD": "LTC", "KXBCHD": "BCH"}
LOOKS = {"A": 1800, "B": 600}
VOL_MIN, MIN_RET = 240, 200
DFS = (3, 4, 5, 6, 8, 12, 30)
P_LO, P_HI = 0.03, 0.97
ASK_LO, ASK_HI, RATIO, MAX_PER_EVENT = 0.03, 0.30, 3.0, 2
STALE_S = 900
C = L.C
NMAX = 150
NRUN = 730347
CANDLE_LO, CANDLE_HI = 2400, 540            # candles cover close-2400 .. close-540 (both looks)


# ------------------------------------------------------------------ model
_TABLES: dict = {}


def t_cdf(x: float, df: float) -> float:
    """Student t CDF from a once-built table (trapezoid on a 0.005 grid to 80, then the tail is saturated); symmetric."""
    tab = _TABLES.get(df)
    if tab is None:
        c = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)
        h, n = 0.005, 16000
        acc, cum, prev = 0.0, [0.0], c
        for i in range(1, n + 1):
            cur = c * (1 + (i * h) ** 2 / df) ** (-(df + 1) / 2)
            acc += 0.5 * (prev + cur) * h
            cum.append(acc)
            prev = cur
        _TABLES[df] = tab = (h, cum)
    h, cum = tab
    a = abs(x) / h
    i = int(a)
    if i >= len(cum) - 1:
        area = cum[-1]
    else:
        area = cum[i] + (cum[i + 1] - cum[i]) * (a - i)
    area = min(area, 0.5)
    return 0.5 + area if x > 0 else 0.5 - area


def t_logpdf(x: float, df: float) -> float:
    return (math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi)
            - (df + 1) / 2 * math.log(1 + x * x / df))


def scale_of(sig_min: float, H: float, df: float) -> float:
    return sig_min * math.sqrt(H) * math.sqrt((df - 2) / df)


def p_yes(S: float, K: float, sig_min: float, H: float, df: float | None) -> float:
    """P(price at the close > K); df None = Gaussian (information only). Variance matched to sig_min^2 H, zero drift."""
    sd = sig_min * math.sqrt(H)
    if sd <= 0 or S <= 0 or K <= 0:
        return float("nan")
    if df is None:
        return 1.0 - L.phi(math.log(K / S) / sd)
    return 1.0 - t_cdf(math.log(K / S) / scale_of(sig_min, H, df), df)


def sigma_min(klines: dict, D: int):
    """RMS of 1 minute log returns of the OKX closes over the 240 minutes ending at D (zero mean); None under MIN_RET returns.
    A kline is keyed by its open second, so the close ending at t is klines[t - 60]."""
    rs = []
    for e in range(D - VOL_MIN * 60 + 60, D + 1, 60):
        a, b = klines.get(e - 120), klines.get(e - 60)
        if a and b and a > 0 and b > 0:
            rs.append(math.log(b / a))
    if len(rs) < MIN_RET:
        return None
    return math.sqrt(sum(r * r for r in rs) / len(rs))


def ref_state(klines: dict, close: int, Ls: int):
    """(S, sigma_min, H minutes) at D = close - Ls, or None."""
    D = close - Ls
    S = klines.get(D - 60)
    if not S:
        return None
    sg = sigma_min(klines, D)
    if sg is None:
        return None
    return S, sg, Ls / 60.0 - 0.5


def quote_at(cs: list, D: int):
    """Two sided quote in force at D + 60: latest candle ending at or before D + 60, at most STALE_S old; (bid, ask) or None."""
    best = None
    for c in cs:
        e = c[0]
        if e is None or e > D + 60 or D + 60 - e > STALE_S:
            continue
        if best is None or e > best[0]:
            best = c
    if best is None or best[1] is None or best[2] is None or not (0 < best[1] < best[2] < 1):
        return None
    return best[1], best[2]


def sides_at(S, sg, H, K, q, df):
    """Cheap-side candidates of one strike: list of dict(side, price, p_side, ratio)."""
    p = p_yes(S, K, sg, H, df)
    if not (P_LO <= p <= P_HI) or q is None:
        return []
    bid, ask = q
    out = []
    if ASK_LO <= ask <= ASK_HI:
        out.append({"side": "yes", "price": ask, "p": p, "pg": p_yes(S, K, sg, H, None)})
    nb = 1 - bid
    if ASK_LO <= nb <= ASK_HI:
        out.append({"side": "no", "price": nb, "p": 1 - p, "pg": 1 - p_yes(S, K, sg, H, None)})
    return out


def pick(cands: list) -> list:
    """Treated: model p >= 3 x price, the two with the largest p - price, ties by lower strike. cands carry 'K'."""
    ok = [c for c in cands if c["p"] >= RATIO * c["price"] - 1e-12]
    ok.sort(key=lambda c: (-(c["p"] - c["price"]), c["K"]))
    return ok[:MAX_PER_EVENT]


def net_c(side: str, price: float, res: str, mult: float = 1.0, slip: float = 0.0) -> float:
    return L.pnl(side, price + slip, res, mult) if slip == 0 else ((1.0 if (res == "yes") == (side == "yes") else 0.0) - price - slip - L.fee(price + slip, mult)) * 100


def stats(rows):
    return L.stats(rows)


# ------------------------------------------------------------------ df fit
def fit_df(zs: list) -> int:
    """Maximum likelihood df on the grid for standardized moves z = ln(S_close/S_D)/(sigma sqrt(H)) with variance-matched t."""
    best, bl = None, -1e300
    for df in DFS:
        sc = math.sqrt((df - 2) / df)
        ll = sum(t_logpdf(z / sc, df) - math.log(sc) for z in zs)
        if ll > bl:
            best, bl = df, ll
    return best


# ------------------------------------------------------------------ helpers
def day(ts_: int) -> str:
    return datetime.fromtimestamp(ts_, UTC).strftime("%Y-%m-%d")


def strike_of(m: dict):
    if m.get("floor_strike") is not None:
        return float(m["floor_strike"])
    cs = m.get("custom_strike") or {}
    if cs.get("floor_strike") not in (None, ""):
        return float(cs["floor_strike"])
    tail = m["ticker"].rsplit("-T", 1)
    try:
        return float(tail[1]) if len(tail) == 2 else None
    except ValueError:
        return None


def load(name, default):
    p = CACHE / name
    return json.loads(p.read_text()) if p.exists() else default


def save(name, obj):
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = CACHE / (name + ".tmp")
    tmp.write_text(json.dumps(obj))
    tmp.replace(CACHE / name)


def event_rank(ev: str) -> str:
    return hashlib.md5(f"ALTLAD1|{ev}".encode()).hexdigest()


# ------------------------------------------------------------------ fetch
def cmd_markets() -> None:
    for s in COINS:
        name = f"markets_{s}.json"
        if (CACHE / name).exists():
            continue
        out = {}
        try:
            for m in api.settled_markets(s, 0, CUT - 1):
                k = strike_of(m)
                st = (m.get("custom_strike") or {}).get("strike_type") or m.get("strike_type")
                if m.get("result") in ("yes", "no") and k is not None and st in ("greater", "custom") and L.ts(m["close_time"]) < CUT:
                    out[m["ticker"]] = {"ev": m["event_ticker"], "close": L.ts(m["close_time"]), "k": k, "res": m["result"][0]}
        except Exception as e:
            print(s, "ERR", str(e)[:80], flush=True)
            continue
        save(name, out)
        cl = sorted({v["close"] for v in out.values()})
        print(s, "markets", len(out), "events", len({v["ev"] for v in out.values()}), "first", day(cl[0]) if cl else None, "last", day(cl[-1]) if cl else None, flush=True)


def active_series():
    return {s: load(f"markets_{s}.json", {}) for s in COINS if (CACHE / f"markets_{s}.json").exists() and load(f"markets_{s}.json", {})}


def cmd_okx() -> None:
    ser = active_series()
    lo = min(v["close"] for m in ser.values() for v in m.values()) - 3600 * 6
    for coin in sorted({COINS[s] for s in ser}):
        name = f"klines_{coin}.json"
        if (CACHE / name).exists():
            continue
        try:
            k = L.okx_klines(f"{coin}-USDT", lo, CUT)
        except Exception as e:
            print(coin, "NOT_RUNNABLE", str(e)[:60], flush=True)
            save(name, {})
            continue
        save(name, {str(a): b for a, b in k.items()})
        print(coin, len(k), "klines", flush=True)


def klines_of(coin: str) -> dict:
    return {int(a): b for a, b in load(f"klines_{coin}.json", {}).items()}


def events_of(ser: dict):
    ev = defaultdict(list)
    for s, ms in ser.items():
        for tk, m in ms.items():
            ev[(s, m["ev"], m["close"])].append((tk, m["k"]))
    return ev


def dev_dates(ser: dict) -> list:
    return sorted({day(m["close"]) for ms in ser.values() for m in ms.values()})


def cmd_fit() -> None:
    ser = active_series()
    dates = dev_dates(ser)
    fit_dates = set(dates[: 2 * len(dates) // 3])
    out = {}
    for key, Ls in LOOKS.items():
        zs = []
        for (s, e, close) in events_of(ser):
            if day(close) not in fit_dates:
                continue
            kl = klines_of(COINS[s])
            st = ref_state(kl, close, Ls)
            Sc = kl.get(close - 60)
            if st is None or not Sc:
                continue
            S, sg, H = st
            zs.append(math.log(Sc / S) / (sg * math.sqrt(H)))
        out[key] = {"df": fit_df(zs) if zs else None, "n": len(zs)}
        print("look", key, out[key], flush=True)
    save("fit.json", out)


def cmd_candles() -> None:
    ser = active_series()
    fit = load("fit.json", {})
    have = load("candles.json", {})
    ev = events_of(ser)
    work = defaultdict(list)
    for (s, e, close), strikes in ev.items():
        kl = klines_of(COINS[s])
        for key, Ls in LOOKS.items():
            st = ref_state(kl, close, Ls)
            if st is None or not fit.get(key, {}).get("df"):
                continue
            S, sg, H = st
            for tk, K in strikes:
                p = p_yes(S, K, sg, H, fit[key]["df"])
                if P_LO <= p <= P_HI:
                    work[(s, e, close)].append(tk)
    work = {k: sorted(set(v)) for k, v in work.items()}
    order = sorted(work, key=lambda k: event_rank(k[1]))
    print("events to fetch", len(order), "tickers", sum(len(v) for v in work.values()), flush=True)
    pause, done, t0 = 0.3, 0, time.time()
    for i, k in enumerate(order):
        s, e, close = k
        todo = [t for t in work[k] if t not in have]
        for j in range(0, len(todo), 100):
            tks = todo[j:j + 100]
            for attempt in range(12):
                try:
                    q = {"market_tickers": ",".join(tks), "start_ts": close - CANDLE_LO, "end_ts": close - CANDLE_HI, "period_interval": 1}
                    req = urllib.request.Request(api.BASES[1] + "/markets/candlesticks?" + urllib.parse.urlencode(q))
                    d = json.load(urllib.request.urlopen(req, timeout=30))
                    got = {x.get("market_ticker") or x.get("ticker"): x for x in d.get("markets", [])}
                    for tk in tks:
                        cs = (got.get(tk) or {}).get("candlesticks", [])
                        have[tk] = [(c["end_period_ts"], L.pick(c.get("yes_bid")), L.pick(c.get("yes_ask")), api.f(c.get("volume_fp") or c.get("volume")))
                                    for c in cs if close - CANDLE_LO < c["end_period_ts"] <= close - CANDLE_HI]
                    pause = max(0.25, pause * 0.9)
                    break
                except urllib.error.HTTPError as ex:
                    if ex.code == 429:
                        pause = min(pause * 1.3, 2.0)
                    time.sleep(1 + attempt)
                except Exception:
                    time.sleep(1 + attempt)
            else:
                print("skip", k, flush=True)
            time.sleep(pause)
        done += 1
        if done % 40 == 0:
            save("candles.json", have)
            print("candles event", i + 1, "of", len(order), "pause", round(pause, 2), "min", round((time.time() - t0) / 60, 1), flush=True)
    save("candles.json", have)
    print("done", flush=True)


# ------------------------------------------------------------------ evaluate
def evaluate(ser, cands, klines_by_coin, fit, key, use_res: bool):
    """Per event of one look: list of treated trade dicts and control candidates. With use_res False no result is read."""
    Ls = LOOKS[key]
    df = fit[key]["df"]
    rows = []
    for (s, e, close), strikes in events_of(ser).items():
        kl = klines_by_coin[COINS[s]]
        st = ref_state(kl, close, Ls)
        if st is None:
            continue
        S, sg, H = st
        D = close - Ls
        allc = []
        for tk, K in strikes:
            cs = [tuple(c) for c in cands.get(tk, [])]
            q = quote_at(cs, D)
            for c in sides_at(S, sg, H, K, q, df):
                c = dict(c, K=K, tk=tk, res=ser[s][tk]["res"] if use_res else None)
                allc.append(c)
        treated = pick(allc)
        rows.append({"s": s, "e": e, "close": close, "day": day(close), "control": allc, "treated": treated})
    return rows


def bucket_lines(rows, tag):
    out = []
    def b(f, name, edges):
        for lo, hi in edges:
            xs = [c for r in rows for c in r["control"] if lo <= f(c) < hi]
            if xs:
                w = sum(1 for c in xs if (c["res"] == "y") == (c["side"] == "yes")) / len(xs)
                out.append(f"  {name} [{lo:g},{hi:g}): n {len(xs)} price {sum(c['price'] for c in xs)/len(xs):.3f} win {w:.3f} model t {sum(c['p'] for c in xs)/len(xs):.3f} gauss {sum(c['pg'] for c in xs)/len(xs):.3f}")
    out.append(f"{tag} calibration (every cheap strike-side, W1+W2):")
    b(lambda c: c["p"] / c["price"], "ratio", [(0, 1), (1, 3), (3, 1e9)])
    b(lambda c: c["p"], "model p", [(0.0, 0.09), (0.09, 0.2), (0.2, 0.4), (0.4, 1.01)])
    return out


def cmd_census() -> None:
    ser = active_series()
    fit = load("fit.json", {})
    cands = load("candles.json", {})
    kl = {c: klines_of(c) for c in {COINS[s] for s in ser}}
    dates = dev_dates(ser)
    for key in LOOKS:
        rows = evaluate(ser, cands, kl, fit, key, use_res=False)
        n = sum(len(r["treated"]) for r in rows)
        per = defaultdict(int)
        for r in rows:
            per[r["s"]] += len(r["treated"])
        print(f"look {key}: events with a model {len(rows)}, treated {n} on {len(dates)} dates, control strike-sides {sum(len(r['control']) for r in rows)}, per series {dict(per)}")


def verdict(Sw, S12, ctrl, pooled, key):
    if pooled["n"] < NMAX:
        return "NOT_ENOUGH_DATA", [f"treated trades {pooled['n']} under {NMAX}"]
    why = []
    for w in ("W1", "W2"):
        if Sw[w]["mean"] <= 0:
            why.append(f"{w} mean not above 0")
        if Sw[w]["pf"] < 1.5:
            why.append(f"{w} PF {Sw[w]['pf']:.2f} under 1.5")
        if S12[w]["mean"] <= 0:
            why.append(f"{w} not positive at fees x1.2")
        if Sw[w]["mean"] - ctrl[w]["mean"] <= 0:
            why.append(f"{w} treated minus control not positive")
    if not why and pooled["z"] < 5.27:
        why.append(f"pooled z {pooled['z']:+.2f} under 5.27")
    return ("FALSIFIED" if why else "NOT_YET_FALSIFIED"), why


def cmd_score() -> None:
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT)
        return
    ser = active_series()
    fit = load("fit.json", {})
    cands = load("candles.json", {})
    kl = {c: klines_of(c) for c in {COINS[s] for s in ser}}
    dates = dev_dates(ser)
    half = {d: ("W1" if i < len(dates) // 2 else "W2") for i, d in enumerate(dates)}
    out = [f"ALTLAD1 run {datetime.now(UTC).isoformat()} N={NRUN} z bar 5.27 cost: fee 7% x C x p x (1-p) rounded up, C={C}, taker at the quote at D+60; cheap side only (ask 3c to 30c)",
           f"series with markets: { {s: len(m) for s, m in ser.items()} }; dev dates {len(dates)} ({dates[0]} to {dates[-1]}); frozen cut {datetime.fromtimestamp(CUT, UTC).isoformat()} never listed",
           f"df fit (OKX only, first two thirds of dates): {fit}"]
    for key, Ls in LOOKS.items():
        rows = evaluate(ser, cands, kl, fit, key, use_res=True)
        tr = {w: [] for w in ("W1", "W2")}
        t12 = {w: [] for w in tr}
        ctl = {w: [] for w in tr}
        slip = []
        per = defaultdict(list)
        for r in rows:
            w = half[r["day"]]
            for c in r["treated"]:
                tr[w].append((r["e"], net_c(c["side"], c["price"], c["res"])))
                t12[w].append((r["e"], net_c(c["side"], c["price"], c["res"], 1.2)))
                slip.append((r["e"], net_c(c["side"], c["price"], c["res"], 1.0, 0.01)))
                per[r["s"]].append(net_c(c["side"], c["price"], c["res"]))
            for c in r["control"]:
                ctl[w].append((r["e"], net_c(c["side"], c["price"], c["res"])))
        Sw = {w: stats(tr[w]) for w in tr}
        S12 = {w: stats(t12[w]) for w in tr}
        Cw = {w: stats(ctl[w]) for w in tr}
        P = stats(tr["W1"] + tr["W2"])
        word, why = verdict(Sw, S12, Cw, P, key)
        out.append(f"=== RULE {key} (look {Ls // 60} minutes before the close): {word}" + (" | " + "; ".join(why) if why else ""))
        for w in ("W1", "W2"):
            out.append(f"{w} treated: " + L.line("", Sw[w]).lstrip(": ") + f" | x1.2 mean {S12[w]['mean']:+.2f}c || control: " + L.line("", Cw[w]).lstrip(": "))
        out.append("pooled treated: " + L.line("", P).lstrip(": ") + f" | +1c slip mean {stats(slip)['mean']:+.2f}c")
        wins = [1 for r in rows for c in r["treated"] if (c["res"] == "y") == (c["side"] == "yes")]
        nt = sum(len(r["treated"]) for r in rows)
        if nt:
            out.append(f"treated win rate {len(wins) / nt:.3f} vs mean price {sum(c['price'] for r in rows for c in r['treated']) / nt:.3f}, model p {sum(c['p'] for r in rows for c in r['treated']) / nt:.3f}")
        out.append("per series (descriptive): " + ", ".join(f"{s} n {len(v)} mean {sum(v)/len(v):+.1f}c" for s, v in sorted(per.items())))
        if P["n"] < NMAX and nt:
            nd = len({r["day"] for r in rows if r["treated"]}) or 1
            out.append(f"forward: {nt / len(dates):.2f} treated trades per development date; days to {NMAX} at this rate {NMAX / (nt / len(dates)):.0f} (forward read on or after 2026-12-04)")
        out += bucket_lines(rows, f"rule {key}")
    txt = "\n".join(out)
    print(txt)
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(txt + "\n")


def main(argv):
    cmds = {"markets": cmd_markets, "okx": cmd_okx, "fit": cmd_fit, "candles": cmd_candles, "census": cmd_census, "score": cmd_score}
    if not argv or argv[0] not in cmds:
        print(__doc__)
        return
    cmds[argv[0]]()


if __name__ == "__main__":
    main(sys.argv[1:])
