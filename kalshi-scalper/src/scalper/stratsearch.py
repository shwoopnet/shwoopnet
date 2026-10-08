"""The runner for the strategy search (protocol fixed in the README, "Pre-registration: the strategy search", before any strategy was run).

Stage 1 (`run`): every strategy in strategies.SPECS is simulated on W0s (information only), W0h, W1 and W2 with the repo's fill model: the signal is read
at candle js, the trade is made on candle js + 1 at the real ask (YES) or 1 minus the real bid (NO), the taker fee 0.07 p (1 - p) is charged on every leg,
a hold to settlement pays no exit fee and a fixed minute exit sells at the real bid. The out of sample windows are W0h, W1 and W2; W3 is never passed in.

`null` runs the valid fair market null over all strategies together. `w3` reads the locked window ONCE, for the survivors only, and refuses a second read.

No function here takes a goal, a deadline or a performance parameter, and the verdict words are only FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA and
NOT_RUNNABLE. A survivor is permission to test forward and nothing more.

Usage: python -m scalper.stratsearch run | null [reps] | w3
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from pathlib import Path
from statistics import NormalDist

from . import overnight as O
from . import strategies as ST
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DB
from .scalps import STRESS, fee

OUT = Path(__file__).resolve().parents[2] / "search3"
OOS = ("W0h", "W1", "W2")            # out of sample for every strategy (all are designed on W0s)
INFO = ("W0s",)
MIN_N = 300
Z_BAR = 2.1
SURVIVOR_Z = O.POOLED_Z              # 2.5, and the per window floor O.MIN_WINDOW_N = 50
RANK_MIN_N = 50
WORDS = ("FALSIFIED", "NOT_YET_FALSIFIED", "NOT_ENOUGH_DATA", "NOT_RUNNABLE")


# ---------------------------------------------------------------------------------------------------------------- loading

def load_world() -> ST.World:
    db = sqlite3.connect(DB)
    ms = {}
    for t, s, o, c, r, k in db.execute("SELECT ticker, series, open_ts, close_ts, result, strike FROM market"):
        if r in ("yes", "no"):
            ms[t] = ST.make_market(t, s, o, c, r, k, {})
    q = "SELECT ticker, end_ts, bid_o, bid_h, bid_l, bid_c, ask_o, ask_h, ask_l, ask_c, price_c, volume, oi FROM candle"
    for row in db.execute(q):
        m = ms.get(row[0])
        if m is None:
            continue
        d = row[1] - m["open"]
        if d % 60 == 0 and 1 <= d // 60 <= 15:
            m["cand"][d // 60] = tuple(row[2:])
    spot = dict(db.execute("SELECT ts, c FROM spot"))
    return ST.World(list(ms.values()), spot)


# ---------------------------------------------------------------------------------------------------------------- the fill model

def trade(m: dict, side: str, je: int, band: tuple, hold):
    """The trade on candle je, or (None, reason). `side` may be yes, no, under (the lower priced side) or over (the higher priced side).
    This is the ONLY function that reads the result of the market traded, and only to settle a hold."""
    c = m["cand"].get(je)
    if c is None or c[3] is None or c[7] is None or not valid_quote(c[3], c[7]):
        return None, "noquote"
    bid, ask = c[3], c[7]
    yes_p, no_p = ask, round(1 - bid, 4)
    if side == "under":
        side = "yes" if yes_p <= no_p else "no"
    elif side == "over":
        side = "yes" if yes_p >= no_p else "no"
    price = yes_p if side == "yes" else no_p
    if not (band[0] - 1e-9 <= price <= band[1] + 1e-9):
        return None, "band"
    mid = (bid + ask) / 2
    smid = mid if side == "yes" else 1 - mid
    rec = {"ticker": m["ticker"], "series": m["series"], "day": m["day"], "close": m["close"], "side": side, "price": price, "mid": smid, "kind": "hs"}
    if hold is None:
        win = 1.0 if m["res"] == side else 0.0
        rec["gross"] = win - price
        rec["net"] = win - price - fee(price)
        rec["stress"] = win - price - fee(price, STRESS)
        return rec, ""
    x = m["cand"].get(je + hold)
    if x is None or x[3] is None or x[7] is None or not valid_quote(x[3], x[7]):
        return None, "dropped"
    xb = x[3] if side == "yes" else round(1 - x[7], 4)
    xm = (x[3] + x[7]) / 2
    rec.update(kind="rt", exit=xb, delta=(xm if side == "yes" else 1 - xm) - smid, hexit=(x[7] - x[3]) / 2)
    rec["gross"] = xb - price
    rec["net"] = xb - fee(xb) - price - fee(price)
    rec["stress"] = xb - fee(xb, STRESS) - price - fee(price, STRESS)
    return rec, ""


def run_spec(w: ST.World, spec: dict, markets: list[dict]):
    """(trades, counts) of one strategy on a list of markets. First qualifying signal candle only; one trade per market."""
    out, counts = [], {"signals": 0, "noquote": 0, "band": 0, "dropped": 0}
    other = {ST.BTC: ST.GOLD, ST.GOLD: ST.BTC}
    for m in markets:
        if m["series"] not in spec["series"]:
            continue
        got = None
        for js in spec["js"]:
            r = spec["sig"](ST.Ctx(w, m, js))
            if r:
                got = (r, js)
                break
        if got is None:
            continue
        r, js = got
        traded = m
        if isinstance(r, tuple):
            r, who = r
            if who == "twin":
                traded = w.by[(other[m["series"]], m["open"])]
        counts["signals"] += 1
        t, why = trade(traded, r, js + 1, spec["band"], spec["hold"])
        if t is None:
            counts[why] += 1
            continue
        t["js"] = js
        out.append(t)
    return out, counts


# ---------------------------------------------------------------------------------------------------------------- statistics

def window_stats(tr: list[dict]) -> dict:
    n = len(tr)
    mean, se, z = cluster_mean_z([(t["day"], t["net"]) for t in tr])
    return {"n": n, "mean": mean if n else 0.0, "se": se, "z": z if n >= 2 else 0.0}


def pooled_stats(tr: list[dict]) -> dict:
    n = len(tr)
    s = window_stats(tr)
    mid = sorted(t["close"] for t in tr)[n // 2] if n else 0
    h1 = [t["net"] for t in tr if t["close"] < mid]
    h2 = [t["net"] for t in tr if t["close"] >= mid]
    s.update(h1=sum(h1) / len(h1) if h1 else 0.0, h2=sum(h2) / len(h2) if h2 else 0.0,
             stress=sum(t["stress"] for t in tr) / n if n else 0.0, gross=sum(t["gross"] for t in tr) / n if n else 0.0)
    return s


def common_bar(p: dict) -> bool:
    """K: n at least 300, mean positive with a day clustered z of at least 2.1, both halves positive, positive with fees x1.2."""
    return p["n"] >= MIN_N and p["mean"] > 0 and p["z"] >= Z_BAR and p["h1"] > 0 and p["h2"] > 0 and p["stress"] > 0


def survivor_test(per_window: list[dict], pooled_z: float) -> bool:
    """THE survivor test of the overnight run, literally its function: every out of sample window has at least 50 entries and a positive mean, and
    the pooled day clustered z is at least 2.5."""
    return O.passes([p["n"] for p in per_window], [p["mean"] for p in per_window], pooled_z)


def verdict_word(p: dict, k: bool, kplus: bool, surv: bool) -> str:
    """NOT_ENOUGH_DATA below 300 pooled out of sample entries; NOT_YET_FALSIFIED only if K, K+ and the survivor test all hold; else FALSIFIED."""
    if p["n"] < MIN_N:
        return "NOT_ENOUGH_DATA"
    return "NOT_YET_FALSIFIED" if (k and kplus and surv) else "FALSIFIED"


def sidak_z(n: int, alpha: float = 0.05) -> float:
    """The one sided z that a family of n independent noise tests clears with probability alpha."""
    return NormalDist().inv_cdf(1 - (1 - (1 - alpha) ** (1 / n)))


# ---------------------------------------------------------------------------------------------------------------- stage 1

def baseline_specs() -> dict[str, dict]:
    def mk(kind, band):
        return {"id": "B_" + kind, "series": ST.BOTH, "js": (7,), "hold": None, "band": band, "sig": (lambda c, _k=kind: _k)}
    return {"under": mk("under", ST.UNDER), "over": mk("over", ST.OVER)}


def evaluate_all(w: ST.World, wins: dict[str, list[dict]]) -> list[dict]:
    """Every strategy on W0s, W0h, W1, W2. `wins` must not contain W3: it is not looked at here."""
    assert "W3" not in wins, "W3 is locked"
    base_trades = {}
    for k, spec in baseline_specs().items():
        base_trades[k] = [t for name in OOS for t in run_spec(w, spec, wins[name])[0]]
    rows = []
    for spec in ST.SPECS:
        per, trades, counts = {}, {}, {}
        for name in INFO + OOS:
            trades[name], counts[name] = run_spec(w, spec, wins[name])
            per[name] = window_stats(trades[name])
        oos = [t for name in OOS for t in trades[name]]
        p = pooled_stats(oos)
        surv = survivor_test([per[n] for n in OOS], p["z"])
        k = common_bar(p)
        kplus, base_mean = True, None
        if spec["baseline"]:
            bt = [t for t in base_trades[spec["baseline"]] if t["series"] in spec["series"]]
            base_mean = sum(t["net"] for t in bt) / len(bt) if bt else 0.0
            kplus = p["mean"] > base_mean
        by_series = {s: window_stats([t for t in oos if t["series"] == s]) for s in sorted({t["series"] for t in oos})}
        rows.append({"id": spec["id"], "family": spec["family"], "name": spec["name"], "per_window": per, "pooled": p, "survivor_test": surv,
                     "K": k, "K_plus": kplus, "baseline_mean": base_mean, "verdict": verdict_word(p, k, kplus, surv), "counts": counts,
                     "by_series": by_series, "spec": describe(spec), "oos_trades": oos})
    rank(rows)
    return rows


def describe(spec: dict) -> dict:
    return {"id": spec["id"], "name": spec["name"], "family": spec["family"], "series_traded": list(spec["series"]), "signal_candles": list(spec["js"]),
            "entry_candle": "signal candle + 1", "exit": "settlement" if spec["hold"] is None else f"bid {spec['hold']} candles after entry",
            "entry_price_band": list(spec["band"]), "params": spec["params"], "universe": spec["universe"], "baseline": spec["baseline"]}


def rank(rows: list[dict]) -> None:
    """The pre-set ranking: pooled out of sample day clustered z, descending; fewer than 50 pooled entries ranks last; ties by mean."""
    key = lambda r: (r["pooled"]["z"] if r["pooled"]["n"] >= RANK_MIN_N else float("-inf"), r["pooled"]["mean"])
    for i, r in enumerate(sorted(rows, key=key, reverse=True)):
        r["rank"] = i + 1


def slim(r: dict) -> dict:
    f = lambda s: {k: (round(v, 6) if isinstance(v, float) and math.isfinite(v) else (None if isinstance(v, float) else v)) for k, v in s.items()}
    return {"rank": r["rank"], "id": r["id"], "name": r["name"], "family": r["family"], "verdict": r["verdict"], "survivor_test": r["survivor_test"],
            "common_bar_K": r["K"], "K_plus": r["K_plus"], "baseline_mean_cents": None if r["baseline_mean"] is None else round(r["baseline_mean"] * 100, 3),
            "pooled_oos": f({**r["pooled"], "mean_cents": r["pooled"]["mean"] * 100}), "per_window": {k: f(v) for k, v in r["per_window"].items()},
            "by_series_oos": {k: f(v) for k, v in r["by_series"].items()}, "counts": r["counts"], "spec": r["spec"]}


def save(rows: list[dict]) -> None:
    OUT.mkdir(exist_ok=True)
    ordered = sorted(rows, key=lambda r: r["rank"])
    (OUT / "all42.json").write_text(json.dumps([slim(r) for r in ordered], indent=1))
    (OUT / "top25.json").write_text(json.dumps([slim(r) for r in ordered[:25]], indent=1))


def table(rows: list[dict]) -> str:
    out = [f"{'rank':>4} {'id':>4} {'n':>6} {'mean c':>8} {'z':>7} {'1st':>7} {'2nd':>7} {'x1.2':>7}  {'W0h n/mean':>14} {'W1 n/mean':>14} {'W2 n/mean':>14}  surv  K   K+  verdict"]
    for r in sorted(rows, key=lambda r: r["rank"]):
        p, pw = r["pooled"], r["per_window"]
        cell = lambda k: f"{pw[k]['n']:>5}/{pw[k]['mean'] * 100:+6.2f}"
        out.append(f"{r['rank']:>4} {r['id']:>4} {p['n']:>6} {p['mean'] * 100:>+8.2f} {p['z']:>+7.2f} {p['h1'] * 100:>+7.2f} {p['h2'] * 100:>+7.2f} {p['stress'] * 100:>+7.2f}  "
                   f"{cell('W0h'):>14} {cell('W1'):>14} {cell('W2'):>14}  {str(r['survivor_test'])[0]:>4}  {str(r['K'])[0]:>2}  {str(r['K_plus'])[0]:>2}  {r['verdict']}")
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------------------------- the fair market null over all strategies

def prepare_null(rows: list[dict]) -> list[dict]:
    """Per strategy, the real out of sample entries as plain lists: window index, day index, half, cost of entry, own mid, and for round trips the
    realised mid change and exit half spread. Everything the null needs and nothing that says who won."""
    days: dict[str, int] = {}
    prep = []
    for r in rows:
        tr = r["oos_trades"]
        n = len(tr)
        cut = sorted(t["close"] for t in tr)[n // 2] if n else 0
        # trades are stored window by window in OOS order, so the window index follows from the counts
        win = []
        for wi, name in enumerate(OOS):
            win += [wi] * r["per_window"][name]["n"]
        prep.append({"id": r["id"], "n": n, "win": win, "day": [days.setdefault(t["day"], len(days)) for t in tr], "half": [0 if t["close"] < cut else 1 for t in tr],
                     "price": [t["price"] for t in tr], "c1": [t["price"] + fee(t["price"]) for t in tr], "cs": [t["price"] + fee(t["price"], STRESS) for t in tr],
                     "mid": [t["mid"] for t in tr], "rt": [t["kind"] == "rt" for t in tr], "delta": [t.get("delta", 0.0) for t in tr],
                     "hexit": [t.get("hexit", 0.0) for t in tr], "ndays": 0})
    for p in prep:
        p["ndays"] = len(days)
    return prep


def null_once(rng: random.Random, p: dict) -> tuple[float, bool, bool]:
    """One strategy, one repeat: (pooled z, passes the survivor test, passes the common bar), every entry given zero edge at its own decision price."""
    n = p["n"]
    if n < 2:
        return 0.0, False, False
    rand = rng.random
    wn, ws = [0, 0, 0], [0.0, 0.0, 0.0]
    dsum: dict[int, float] = {}
    dn: dict[int, int] = {}
    hsum, hn, tot, stot = [0.0, 0.0], [0, 0], 0.0, 0.0
    for wi, d, h, c1, cs, mid, rt, delta, hx in zip(p["win"], p["day"], p["half"], p["c1"], p["cs"], p["mid"], p["rt"], p["delta"], p["hexit"]):
        if rt:
            b = mid + (delta if rand() < 0.5 else -delta) - hx
            b = 0.001 if b < 0.001 else (0.999 if b > 0.999 else b)
            f = 0.07 * b * (1 - b)
            x, xs = b - f - c1, b - STRESS * f - cs
            # c1 already holds the entry price and entry fee, so only the exit leg is added here
        else:
            win = 1.0 if rand() < mid else 0.0
            x, xs = win - c1, win - cs
        wn[wi] += 1
        ws[wi] += x
        dsum[d] = dsum.get(d, 0.0) + x
        dn[d] = dn.get(d, 0) + 1
        hsum[h] += x
        hn[h] += 1
        tot += x
        stot += xs
    mean = tot / n
    se = math.sqrt(sum((dsum[d] - dn[d] * mean) ** 2 for d in dsum)) / n
    z = mean / se if se > 0 else 0.0
    means = [ws[i] / wn[i] if wn[i] else 0.0 for i in range(3)]
    surv = O.passes(wn, means, z)
    common = (n >= MIN_N and mean > 0 and z >= Z_BAR and hn[0] > 0 and hn[1] > 0 and hsum[0] / hn[0] > 0 and hsum[1] / hn[1] > 0 and stot > 0)
    return z, surv, common


def null_chunk(args):
    prep, reps, seed = args
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        best, surv, common, both = -9.0, 0, 0, 0
        for p in prep:
            z, s, c = null_once(rng, p)
            if p["n"] >= RANK_MIN_N and z > best:
                best = z
            surv += s
            common += c
            both += (s and c)
        out.append((best, surv, common, both))
    return out


def run_null(rows: list[dict], reps: int = 500, seed: int = 1, procs: int = 4) -> dict:
    import multiprocessing as mp
    prep = prepare_null(rows)
    chunks = [(prep, reps // procs + (1 if i < reps % procs else 0), seed * 1000 + i) for i in range(procs)]
    if procs > 1:
        with mp.get_context("fork").Pool(procs) as pool:
            parts = pool.map(null_chunk, chunks)
    else:
        parts = [null_chunk(c) for c in chunks]
    res = [x for part in parts for x in part]
    return {"reps": len(res), "best": [r[0] for r in res], "survivors": [r[1] for r in res], "common": [r[2] for r in res], "both": [r[3] for r in res]}


def null_report(rows: list[dict], nul: dict) -> dict:
    ranked = [r for r in rows if r["pooled"]["n"] >= RANK_MIN_N]
    real_best = max(r["pooled"]["z"] for r in ranked) if ranked else 0.0
    real_surv = sum(1 for r in rows if r["survivor_test"])
    real_common = sum(1 for r in rows if r["K"])
    real_both = sum(1 for r in rows if r["K"] and r["survivor_test"])
    reps = nul["reps"]
    b = sorted(nul["best"])
    q = lambda f: b[min(reps - 1, int(f * reps))]
    return {"reps": reps, "strategies": len(rows), "real_best_z": real_best, "null_best_median": q(0.5), "null_best_p95": q(0.95), "null_best_max": b[-1],
            "P_null_best_ge_real": sum(1 for x in b if x >= real_best) / reps,
            "real_survivors": real_surv, "P_null_survivors_ge_real": sum(1 for x in nul["survivors"] if x >= real_surv) / reps,
            "mean_null_survivors": sum(nul["survivors"]) / reps,
            "real_common_bar": real_common, "P_null_common_ge_real": sum(1 for x in nul["common"] if x >= real_common) / reps,
            "mean_null_common": sum(nul["common"]) / reps,
            "real_both": real_both, "P_null_both_ge_real": sum(1 for x in nul["both"] if x >= real_both) / reps,
            "expected_best_of_N": math.sqrt(2 * math.log(len(rows))), "sidak_5pct_z": sidak_z(len(rows))}


# ---------------------------------------------------------------------------------------------------------------- the locked window

W3_FILE = OUT / "w3_read_once.json"


def read_w3_once(w: ST.World, w3: list[dict], rows: list[dict]) -> dict:
    """Read the locked window ONCE, for the strategies that passed the survivor test only. A second call refuses."""
    if W3_FILE.exists():
        raise RuntimeError("W3 has already been read; a second read is not allowed")
    specs = {s["id"]: s for s in ST.SPECS}
    out = {}
    for r in rows:
        if r["survivor_test"]:
            tr, _ = run_spec(w, specs[r["id"]], w3)
            out[r["id"]] = window_stats(tr)
    OUT.mkdir(exist_ok=True)
    W3_FILE.write_text(json.dumps(out, indent=1, default=str))
    return out


# ---------------------------------------------------------------------------------------------------------------- command line

def main(argv: list[str]) -> None:
    cmd = argv[1] if len(argv) > 1 else "run"
    w = load_world()
    wins = O.windows(w.ms)
    if cmd == "w3":
        rows = json.loads((OUT / "all42.json").read_text())
        if not any(r["survivor_test"] for r in rows):
            print("No strategy passed the survivor test, so the locked window is not read.")
            return
        pseudo = [{"id": r["id"], "survivor_test": r["survivor_test"]} for r in rows]
        res = read_w3_once(w, wins["W3"], pseudo)
        for k, v in res.items():
            print(k, f"W3 n={v['n']} mean {v['mean'] * 100:+.2f}c z {v['z']:+.2f}")
        return
    oos_wins = {k: v for k, v in wins.items() if k != "W3"}
    print("windows (markets):", {k: len(v) for k, v in oos_wins.items()}, "(W3 locked, not read)")
    rows = evaluate_all(w, oos_wins)
    save(rows)
    print(table(rows))
    n = len(rows)
    print(f"\nN = {n}. survivor test alone: {sum(1 for r in rows if r['survivor_test'])}; common bar K alone: {sum(1 for r in rows if r['K'])}; "
          f"verdicts: " + ", ".join(f"{v} {sum(1 for r in rows if r['verdict'] == v)}" for v in WORDS[:3]))
    print(f"expected best of N noise strategies: z {math.sqrt(2 * math.log(n)):.2f}; family wise 5% bar (Sidak): z {sidak_z(n):.2f}")
    if cmd == "null":
        reps = int(argv[2]) if len(argv) > 2 else 500
        rep = null_report(rows, run_null(rows, reps))
        OUT.mkdir(exist_ok=True)
        (OUT / "null.json").write_text(json.dumps(rep, indent=1))
        for k, v in rep.items():
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")


if __name__ == "__main__":
    main(sys.argv)
