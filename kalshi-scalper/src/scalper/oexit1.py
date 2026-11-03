"""OEXIT1 (workers/OEXIT1_REGISTRATION.md): OICORE with and without selling half at k times the entry price.
Research only; nothing here places an order, reads a key or decides anything live.
    python -m scalper.oexit1 run     (once; refuses a second run)
Entry, fill and fee come from gen6.window_rows / oicorex1.window_list (not re-implemented).
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone

from . import gen6, oicorex1, streaks
from .paths import DATA_DIR

ROOT_W = DATA_DIR.parent / "workers"
OUT = ROOT_W / "OEXIT1_result.json"
TH = oicorex1.BTC_THRESH
MULTS = (3.0, 2.0, 4.0)


def fee_usd(p, c):
    """7% x C x p x (1 - p), rounded up to the cent, in dollars."""
    return math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / 100


def side_bid(q, yes):
    """Bid close of the side held from a candle tuple (bid_c, ask_c, vol, oi)."""
    return gen6._sq(q, yes)[0]


def simulate(price, yes, cs, ct, win, c, mult=None):
    """Net dollars of one OICORE entry at `price` for c contracts, held (mult None) or with half sold.
    cs: {end_ts: (bid_c, ask_c, vol, oi)}; win: True if the side held wins. Returns (net, sold, sale_price)."""
    settle = 1.0 if win else 0.0
    net = c * (settle - price) - fee_usd(price, c)
    if mult is None:
        return net, False, None
    keys = sorted(k for k in cs if ct - 120 < k <= ct)
    for i, k in enumerate(keys):
        if side_bid(cs[k], yes) >= mult * price - 1e-9:
            if i + 1 >= len(keys):
                return net, False, None          # showed 3x on the last candle: no later candle to sell on
            sp = side_bid(cs[keys[i + 1]], yes)
            if sp is None or sp <= 0:
                return net, False, None          # no bid: the order does not execute
            h = c // 2
            if h < 1:
                return net, False, None
            # half sold at sp, rest settles: replace h contracts' settlement by the sale, add the sale fee
            net = net + h * (sp - settle) - fee_usd(sp, h)
            return net, True, sp
    return net, False, None


def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def summarize(nets):
    if not nets:
        return {"n": 0}
    wins = [x > 0 for x in nets]
    st = streaks.empirical_streaks(wins)
    pw = sum(wins) / len(wins)
    return {"n": len(nets), "pf": pf(nets), "win": pw, "net": sum(nets), "longest_loss": st["longest_losing_run"],
            "p10_in_100": streaks.prob_run_at_least(10, pw, 100)}


def fired_trades(lo, hi):
    """OICORE entries in order of close: dict(ct, day, yes, fill, win, cs)."""
    out = []
    for tk, ct, res, cs in oicorex1.window_list("KXBTC15M", lo, hi):
        rows, _ = gen6.window_rows("KXBTC15M", ct, cs, {})
        doi_i = gen6.FEATS.index("doi")
        for r in rows:
            if r["L"] == 180 and r["feats"][doi_i] > TH:
                out.append({"tk": tk, "ct": ct, "day": datetime.fromtimestamp(ct, timezone.utc).strftime("%Y-%m-%d"),
                            "yes": bool(r["yes"]), "fill": r["fill"], "win": (res == "yes") == bool(r["yes"]), "cs": cs})
                break
    return out


def split_dates(days):
    d = sorted(set(days)); n = len(d)
    a, b = round(n / 3), round(2 * n / 3)
    hist = d[:b]
    h = len(hist) // 2
    return {"H1": set(hist[:h]), "H2": set(hist[h:]), "HOLD": set(d[b:])}, d


def evaluate(T, c=10, mults=MULTS):
    """T: trades as from fired_trades. Per subset: dict of 'without' and each mult."""
    sets, dates = split_dates([t["day"] for t in T])
    sets["HIST"] = sets["H1"] | sets["H2"]
    res = {"dates": {"n": len(dates), "first": dates[0], "last": dates[-1], **{k: [min(v), max(v)] for k, v in sets.items() if v}}}
    sim = {m: [simulate(t["fill"], t["yes"], t["cs"], t["ct"], t["win"], c, m) for t in T] for m in (None,) + tuple(mults)}
    for name, ds in sets.items():
        ix = [i for i, t in enumerate(T) if t["day"] in ds]
        res[name] = {"without": summarize([sim[None][i][0] for i in ix])}
        for m in mults:
            r = summarize([sim[m][i][0] for i in ix])
            r["sold"] = sum(1 for i in ix if sim[m][i][1])
            r["flipped_to_win"] = sum(1 for i in ix if sim[m][i][0] > 0 and sim[None][i][0] <= 0)
            r["flipped_to_loss"] = sum(1 for i in ix if sim[m][i][0] <= 0 and sim[None][i][0] > 0)
            res[name][f"x{m}"] = r
    return res


def live(path, mults=MULTS):
    """Live list: same rule at the price paid, filled count. Returns (rows, summary)."""
    M = oicorex1.load_series("KXBTC15M", 0, 2 ** 40)
    byclose = {v[0]: (k, v) for k, v in M.items()}
    rows = []
    for r in csv.DictReader(open(path)):
        if int(r["filled"]) == 0:
            continue
        ct = int(datetime.strptime(r["close_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
        yes = r["side"] == "yes"; price = float(r["price"]); c = int(r["filled"])
        hit = byclose.get(ct)
        if hit is None or hit[1][1] not in ("yes", "no"):
            rows.append({**r, "missing": True}); continue
        tk, (_, res, cs, _f) = hit
        cs6 = oicorex1.gen6_cs(cs)
        win = (res == "yes") == yes
        row = {"close": r["close_utc"], "side": r["side"], "price": price, "filled": c, "recorded_pnl": float(r["pnl_usd"]),
               "model_without": simulate(price, yes, cs6, ct, win, c)[0], "win": win}
        for m in mults:
            n, sold, sp = simulate(price, yes, cs6, ct, win, c, m)
            row[f"x{m}"] = n; row[f"sold{m}"] = sold
        rows.append(row)
    ok = [x for x in rows if not x.get("missing")]
    summ = {"orders": len(rows), "scored": len(ok), "missing": len(rows) - len(ok),
            "recorded": summarize([x["recorded_pnl"] for x in ok]),
            "without": summarize([x["model_without"] for x in ok])}
    for m in mults:
        s = summarize([x[f"x{m}"] for x in ok]); s["sold"] = sum(1 for x in ok if x[f"sold{m}"]); summ[f"x{m}"] = s
    return rows, summ


def run():
    if OUT.exists():
        print("Refusing to run again: OEXIT1 already read"); return
    T = fired_trades(gen6.DISC[0], 2 ** 40)
    # parity with the history scorer (no exit, per-contract fee as gen6): discovery and validation PF
    par = {}
    for nm, (lo, hi) in (("disc", gen6.DISC), ("val", gen6.VAL["KXBTC15M"])):
        S = [t for t in T if lo <= t["ct"] < hi]
        par[nm] = summarize([simulate(t["fill"], t["yes"], t["cs"], t["ct"], t["win"], 10)[0] for t in S])
    res = {"history": evaluate(T), "parity": par}
    rows, summ = live(ROOT_W / "OICORE_LIVE_ORDERS.csv")
    res["live"] = summ; res["live_rows"] = rows
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "live_rows"}, indent=1, default=str))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    else:
        print(__doc__)
