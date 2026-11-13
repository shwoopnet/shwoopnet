"""OIVER-SPREAD, BUILD 2 (History Miner, Nov 13, 2026), from Desk A's card 1 only (DESK_A_OICORE_VERSIONS_NOV13.md at 741092a7, sha256 e7b918b0);
Desk A's build was not read. Rules and hand figures in EXPECTED_BY_HAND.md (889d41d0), committed first; the Head's convention of 19:53Z (dated line there) governs: the decision quote is the candle ending close - 180 s (the input's yes_bid and yes_ask), C = 20, the price is the ask seen.
Development only: a held-out read is refused in this build. Prints aggregates only.
Usage: python3 -I oiver_spread2.py dev <windows.csv>"""
import csv, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

EPS = 1e-9
HELDOUT_FIRST = 1796083200          # 2026-12-01T00:00:00Z
OI_MIN = 86300                      # (g) inclusive
FLOOR, CEIL = 0.08, 0.50
SLIP = 0.0                          # (c) Head 19:53Z: the ask seen, no +1c (PR 895); filled at that ask, an UPPER BOUND on fills
C = 20                              # (b) Head 19:53Z: OICORE bottom step (PR 901), fee rounded up per order
SPREAD_MAX = 0.03                   # the version's one condition
WEEK = 604800
MIN_SIGNALS = 60


class Stop(Exception):
    pass


def fee(p):
    return math.ceil(round(100 * 0.07 * C * p * (1 - p), 6)) / 100 / C


def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return None if not xs else (math.inf if l == 0 else w / l)


def shown(x):
    return None if x is None else ("inf" if x == math.inf else round(x, 6))


def summary(nets, span):
    n = len(nets); h = n // 2
    return {"n": n, "pf": shown(pf(nets)), "net": round(sum(nets), 6), "mean": round(sum(nets) / n, 6) if n else None,
            "half1_pf": shown(pf(nets[:h])), "half2_pf": shown(pf(nets[h:])),
            "net_per_contract_week": round(sum(nets) * WEEK / span, 6) if span > 0 else None}


def run(mode, path):
    hm_guard.refuse_all([path])
    if mode != "dev":
        raise Stop("only a development read is built; a held-out read is refused")
    counts, parent, version, closes = {}, [], [], []

    def bump(k):
        counts[k] = counts.get(k, 0) + 1
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            close = int(r["close_ts"])
            if close >= HELDOUT_FIRST:
                bump("held_out_ignored"); continue
            if r["result"] not in ("yes", "no", "void"):
                raise Stop("result %r refused (%s)" % (r["result"], r["ticker"]))
            rows.append((close, r))
    for close, r in sorted(rows, key=lambda x: (x[0], x[1]["ticker"])):
        closes.append(close)
        try:
            rise = float(r["oi_180"]) - float(r["oi_360"])
        except (TypeError, ValueError):
            bump("no_oi"); continue
        if not math.isfinite(rise):
            bump("no_oi"); continue
        if rise < OI_MIN - EPS:
            bump("oi_below"); continue
        b, a = float(r["yes_bid"] or 0), float(r["yes_ask"] or 1)
        if not (0 < b < 1 and 0 < a < 1) or b >= a - EPS:
            bump("no_quote"); continue
        asks = {"yes": a, "no": 1 - b}
        side = "yes" if asks["yes"] <= asks["no"] + EPS else "no"      # (d) tie to YES
        ask = asks[side]
        if ask < FLOOR - EPS:
            bump("cheap_skipped"); continue
        if ask > CEIL + EPS:
            bump("out_of_band"); continue
        price = min(ask + SLIP, CEIL)
        fe = fee(price)
        res = r["result"]
        net = -fe if res == "void" else ((1 - price - fe) if res == side else (-price - fe))
        net = round(net, 9)
        parent.append(net)
        if a - b > SPREAD_MAX + EPS:
            bump("spread_wide"); continue
        version.append(net)
    span = (max(closes) - min(closes)) if closes else 0
    P, V = summary(parent, span), summary(version, span)
    removed = round(1 - len(version) / len(parent), 6) if parent else None
    take = {"pf_lift_ge_0.10": None if P["pf"] is None or V["pf"] is None else (pf(version) >= pf(parent) + 0.10 - EPS),
            "net_week_not_lower": None if P["net_per_contract_week"] is None else V["net_per_contract_week"] >= P["net_per_contract_week"] - EPS,
            "half2_not_worse": None if pf(parent[len(parent)//2:]) is None or pf(version[len(version)//2:]) is None else pf(version[len(version)//2:]) >= pf(parent[len(parent)//2:]) - EPS,
            "signals_ge_60": len(version) >= MIN_SIGNALS}
    kills = {"removed_more_than_half": removed is not None and removed > 0.5 + EPS,
             "pf_below_parent": pf(version) is not None and pf(parent) is not None and pf(version) < pf(parent) - EPS}
    label = "no evidence at n = %d" % len(version) if len(version) < MIN_SIGNALS else "development (not a verdict)"
    return {"removed_share": removed, "counts": counts, "parent": P, "version": V, "takeover_info": take, "kills_info": kills, "label": label}


if __name__ == "__main__":
    try:
        print(json.dumps(run(sys.argv[1], sys.argv[2])))
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
