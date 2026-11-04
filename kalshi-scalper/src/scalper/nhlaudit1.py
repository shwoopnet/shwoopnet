"""NHLAUDIT1: read-only audit of the NHLALL1 combined read. Independent re-implementation from the raw caches (does not import nhlall1).
Reads /home/user/.cache/nhlall1/nhlall1.sqlite (quotes, append only) and data/nhlg1.sqlite (kmarket result, game). No network, no writes
except the JSON/markdown output the caller asks for. Only games with every rung fetched are read; the 25 NHLG1 events (excluded=1) and the
post-cut events are never touched (the cache holds none of the latter).
  python -m scalper.nhlaudit1 [out.json]
"""
from __future__ import annotations
import hashlib, json, math, random, sqlite3, statistics as st, sys
from collections import defaultdict
from pathlib import Path

CACHE = "/home/user/.cache/nhlall1/nhlall1.sqlite"
SRC = Path(__file__).resolve().parents[2] / "data" / "nhlg1.sqlite"
C, LEAD = 10, 120


def fee_cents_order(p):  # whole-cent ceil of 7% * C * p * (1-p), written independently (integer cents, small epsilon guard)
    x = 0.07 * C * p * (1 - p) * 100
    return math.ceil(x - 1e-7) / 100


def pnl(win, p, fee_mult=1.0, fee_round=True):
    f = fee_cents_order(p) if fee_round else 0.07 * C * p * (1 - p)
    return (1.0 if win else 0.0) - p - fee_mult * f / C


def load():
    c = sqlite3.connect(CACHE)
    s = sqlite3.connect(SRC)
    res = dict(s.execute("SELECT ticker,result FROM kmarket"))
    goals = {}
    gmeta = {r[0]: r[1:] for r in s.execute("SELECT id,start_ts,hs,as_ FROM game")}
    done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    candles = defaultdict(list)
    for tk, e, b, a in c.execute("SELECT ticker,end_ts,bid,ask FROM candle"):
        candles[tk].append((e, b, a))
    rungs = defaultdict(list)
    for tk, ev, vol in c.execute("SELECT ticker,event,volume FROM rung"):
        rungs[ev].append((tk, vol))
    games = [(ev, gid, stt) for ev, gid, stt, ex in c.execute("SELECT event,gid,start_ts,excluded FROM gm") if not ex]
    return res, done, candles, rungs, games, gmeta


def look(cs, stt, lead=LEAD):
    ok = [(e, b, a) for e, b, a in cs if e <= stt - lead and b is not None and a is not None and 0 <= b < a <= 1 and a - b <= 0.10 + 1e-12]
    return max(ok) if ok else None


def build(lead=LEAD, salt="", need=8):
    res, done, candles, rungs, games, gmeta = load()
    G = []
    for ev, gid, stt in games:
        tks = [t for t, _ in rungs[ev]]
        if not tks or any(t not in done for t in tks):
            continue
        quotes, drop_res, drop_q = [], 0, 0
        for tk, vol in rungs[ev]:
            q = look(candles[tk], stt, lead)
            if q is None:
                drop_q += 1
                continue
            if res.get(tk) not in ("yes", "no"):
                drop_res += 1
                continue
            quotes.append(dict(tk=tk, lag=stt - q[0], bid=q[1], ask=q[2], yes=res[tk] == "yes", vol=vol))
        if len(quotes) < need:
            G.append(dict(ev=ev, stt=stt, usable=False, nq=len(quotes), allr=len(tks), gid=gid, goals=gmeta.get(gid), quotes=quotes))
            continue
        cheap = []
        for q in quotes:
            if 0.03 <= q["ask"] <= 0.30:
                cheap.append(dict(q, side="yes", price=q["ask"], win=q["yes"]))
            elif 0.03 <= 1 - q["bid"] <= 0.30:
                cheap.append(dict(q, side="no", price=1 - q["bid"], win=not q["yes"]))
        G.append(dict(ev=ev, stt=stt, usable=True, nq=len(quotes), allr=len(tks), gid=gid, goals=gmeta.get(gid), cheap=cheap, quotes=quotes,
                      lsum=sum(q["ask"] for q in quotes)))
    return G


def pick(cheap, salt=""):
    # registered rule: sha1(ticker) with empty salt
    return sorted(cheap, key=lambda r: hashlib.sha1((salt + r["tk"]).encode()).hexdigest())[:2]


def cl_stats(trades, key, fee_mult=1.0):
    by = defaultdict(list)
    for t in trades:
        by[t[key]].append(pnl(t["win"], t["price"], fee_mult))
    xs = [x for L in by.values() for x in L]
    n = len(xs)
    m = sum(xs) / n
    se = math.sqrt(sum(sum(v - m for v in L) ** 2 for L in by.values())) / n
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return dict(n=n, clusters=len(by), mean_c=100 * m, se_c=100 * se, z=m / se, lo95_c=100 * (m - 1.96 * se), pf=g / l if l else float("inf"),
                win=sum(t["win"] for t in trades) / n, price=sum(t["price"] for t in trades) / n)


def tag(G, salt=""):
    T = []
    for g in G:
        if not g["usable"]:
            continue
        for t in pick(g["cheap"], salt):
            T.append(dict(t, game=g["ev"], date=g["ev"][10:17], stt=g["stt"]))
    return T


def main(out=None):
    G = build()
    U = [g for g in G if g["usable"]]
    R = {"fully_fetched_games": len(G), "usable_games": len(U)}
    T = tag(G)
    R["headline"] = cl_stats(T, "game")
    R["headline_date"] = cl_stats(T, "date")
    R["headline_x12"] = cl_stats(T, "game", 1.2)
    R["side_counts"] = {s: sum(1 for t in T if t["side"] == s) for s in ("yes", "no")}
    R["wins"] = sum(t["win"] for t in T)
    R["dup_tickers"] = len(T) - len({t["tk"] for t in T})
    R["lag_s"] = dict(min=min(t["lag"] for t in T), median=st.median(t["lag"] for t in T), max=max(t["lag"] for t in T),
                      share_over_600=sum(t["lag"] > 600 for t in T) / len(T))
    cut = {}  # extra cuts counter
    # (2a) leave-k-out of the biggest winners (all winners pay the same ~ 1-p; remove largest 1-p-fee i.e. lowest price winners)
    W = sorted([t for t in T if t["win"]], key=lambda t: -pnl(True, t["price"]))
    leave = {}
    for k in (1, 2, 3, 5):
        keep = W[k:] + [t for t in T if not t["win"]]
        xs = [pnl(t["win"], t["price"]) for t in keep]
        g = sum(x for x in xs if x > 0)
        l = -sum(x for x in xs if x < 0)
        leave[k] = dict(n=len(xs), mean_c=100 * sum(xs) / len(xs), pf=g / l)
    R["leave_k_out_same_n_minus_k"] = leave
    # leave-k-out holding n fixed: replace removed winners with losses at same price (strictest)
    strict = {}
    for k in (1, 2, 3, 5):
        xs = [pnl(t["win"], t["price"]) for t in T if t not in W[:k]] + [pnl(False, t["price"]) for t in W[:k]]
        g = sum(x for x in xs if x > 0)
        l = -sum(x for x in xs if x < 0)
        strict[k] = dict(mean_c=100 * sum(xs) / len(xs), pf=g / l)
    R["leave_k_out_winners_flipped_to_losses"] = strict
    R["winner_prices"] = sorted(round(t["price"], 3) for t in W)
    R["share_of_gross_from_top5_winners"] = sum(pnl(True, t["price"]) for t in W[:5]) / sum(pnl(True, t["price"]) for t in W)
    # fee rounding: remove fee rounding entirely / one contract
    R["no_fee_rounding_mean_c"] = 100 * sum(pnl(t["win"], t["price"], 1.0, False) for t in T) / len(T)
    R["zero_fee_mean_c"] = 100 * sum(pnl(t["win"], t["price"], 0.0) for t in T) / len(T)
    R["one_cent_per_order_extra_mean_c"] = 100 * sum(pnl(t["win"], t["price"]) for t in T) / len(T) - 100 * 0.01 / C
    # (2b) bootstraps
    rng = random.Random(20261104)
    for key in ("game", "date"):
        cl = defaultdict(list)
        for t in T:
            cl[t[key]].append(pnl(t["win"], t["price"]))
        keys = list(cl)
        ms, pfs = [], []
        for _ in range(4000):
            xs = [x for k in (rng.choice(keys) for _ in keys) for x in cl[k]]
            ms.append(sum(xs) / len(xs))
            g = sum(x for x in xs if x > 0)
            l = -sum(x for x in xs if x < 0)
            pfs.append(g / l if l else 9)
        ms.sort()
        R["boot_" + key] = dict(p2_5=100 * ms[100], median=100 * ms[2000], p97_5=100 * ms[3900], p_mean_le_0=sum(m <= 0 for m in ms) / len(ms),
                                p_pf_lt_1_5=sum(p < 1.5 for p in pfs) / len(pfs))
    # (2c) salt re-draw 200 times
    nets, pfs, los, nn = [], [], [], []
    for i in range(200):
        Ti = tag(G, salt=f"salt{i}|")
        s = cl_stats(Ti, "game")
        nets.append(s["mean_c"])
        pfs.append(s["pf"])
        los.append(s["lo95_c"])
        nn.append(s["n"])
    q = lambda a, p: sorted(a)[int(p * (len(a) - 1))]
    R["redraw200"] = dict(n_set=sorted(set(nn)), net_p5=q(nets, .05), net_p25=q(nets, .25), net_median=q(nets, .5), net_p75=q(nets, .75), net_p95=q(nets, .95),
                          pf_median=q(pfs, .5), pf_p5=q(pfs, .05), pf_p95=q(pfs, .95), lo95_median=q(los, .5), lo95_p95=q(los, .95),
                          share_net_gt0=sum(x > 0 for x in nets) / 200, share_lo95_gt0=sum(x > 0 for x in los) / 200,
                          share_pf_ge_1_5=sum(x >= 1.5 for x in pfs) / 200, registered_salt_percentile_of_net=sum(x <= R["headline"]["mean_c"] for x in nets) / 200)
    # all-cheap uncapped as the salt-free expectation of the draw
    allc = [dict(t, game=g["ev"], date=g["ev"][10:17]) for g in U for t in g["cheap"]]
    R["uncapped"] = cl_stats(allc, "game")
    # (2d) calibration inside the pool, by price bucket (pool then uncapped)
    cal = {}
    for nm, S in (("pool150", T), ("uncapped", allc)):
        for lo, hi in ((0.03, 0.10), (0.10, 0.20), (0.20, 0.30001)):
            B = [t for t in S if lo <= t["price"] < hi]
            if B:
                cal[f"{nm}_{lo:.2f}-{min(hi,.30):.2f}"] = dict(n=len(B), win=sum(t["win"] for t in B) / len(B), price=sum(t["price"] for t in B) / len(B),
                                                               mean_c=100 * sum(pnl(t["win"], t["price"]) for t in B) / len(B))
    R["calibration"] = cal
    # zero-winner games
    byg = defaultdict(list)
    for t in T:
        byg[t["game"]].append(t["win"])
    R["games_in_pool"] = len(byg)
    R["games_zero_winners"] = sum(1 for v in byg.values() if not any(v))
    R["games_with_1"] = sum(1 for v in byg.values() if sum(v) == 1)
    R["games_with_2"] = sum(1 for v in byg.values() if sum(v) == 2)
    R["trades_per_game"] = dict(sorted({k: sum(1 for v in byg.values() if len(v) == k) for k in (1, 2)}.items()))
    # (1) availability: is usable-ladder status correlated with outcome? (game level: total goals; rung level: win rate of cheap-priced rungs)
    def goals_of(g):
        m = g["goals"]
        return (m[1] + m[2]) if m and m[1] is not None and m[2] is not None else None
    gu = [goals_of(g) for g in G if g["usable"] and goals_of(g) is not None]
    gn = [goals_of(g) for g in G if not g["usable"] and goals_of(g) is not None]
    R["availability"] = dict(usable_n=len(gu), unusable_n=len(gn), usable_mean_goals=st.mean(gu), unusable_mean_goals=st.mean(gn) if gn else None,
                             unusable_stdev=st.pstdev(gn) if gn else None)
    # scorer counts per game from the rung results (usable vs not), 1+ rungs with volume
    def scorers(g):
        return sum(1 for q in g["quotes"] if q["yes"])
    R["availability"]["usable_mean_scorers_in_quoted"] = st.mean(scorers(g) for g in U)
    R["availability"]["unusable_mean_scorers_in_quoted"] = st.mean(scorers(g) for g in G if not g["usable"] and g["quotes"]) if any(g["quotes"] for g in G if not g["usable"]) else None
    # volume-based rung inclusion: rungs are in the universe because total (incl in-game) volume > 0; compare volume of winners vs losers among pool
    wv = [t["vol"] for t in allc if t["win"]]
    lv = [t["vol"] for t in allc if not t["win"]]
    R["volume_lookahead"] = dict(median_vol_winners=st.median(wv), median_vol_losers=st.median(lv), n_w=len(wv), n_l=len(lv))
    # rung-level dropped-for-no-valid-quote vs kept: win rate (unusable-at-rung level, inside usable games)
    res, done, candles, rungs, games, gmeta = load()
    kept_w = kept = drop_w = drop = 0
    for g in U:
        got = {q["tk"] for q in g["quotes"]}
        for tk, vol in rungs[g["ev"]]:
            if res.get(tk) in ("yes", "no"):
                if tk in got:
                    kept += 1
                    kept_w += res[tk] == "yes"
                else:
                    drop += 1
                    drop_w += res[tk] == "yes"
    R["rung_quote_availability"] = dict(kept=kept, kept_yes_rate=kept_w / kept, dropped=drop, dropped_yes_rate=drop_w / drop if drop else None)
    # (extra DESCRIPTIVE cuts) look lead sensitivity 300, 600
    sens = {}
    for L in (300, 600):
        Gl = build(lead=L)
        Tl = tag(Gl)
        s = cl_stats(Tl, "game")
        sens[L] = dict(games=sum(g["usable"] for g in Gl), n=s["n"], mean_c=s["mean_c"], pf=s["pf"], lo95_c=s["lo95_c"])
    R["lead_sensitivity_descriptive"] = sens
    R["extra_cuts_looked_at"] = dict(
        leave_k_out=8, bootstraps=2, salt_redraws=200, price_buckets=2 * 3, availability_checks=4, lead_sensitivity=2, fee_variants=3, other="halves/dates reused from registered read")
    s = json.dumps(R, indent=1, default=str)
    if out:
        Path(out).write_text(s)
    print(s)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
