"""INCENT1 scorer. usage: incent1_analyze.py OUTDIR  (reads chosen.json, pass*.json)"""
import json, glob, sys, statistics as S
sys.path.insert(0, __file__.rsplit("/scalper/", 1)[0])
from scalper import incent1 as I

def fl(x, d=0.0):
    try: return float(x)
    except Exception: return d

def main(d):
    chosen = {p["market_ticker"]: p for p in json.load(open(d + "/chosen.json"))}
    import datetime as D
    dt = lambda s: D.datetime.fromisoformat(s.replace("Z", "+00:00"))
    passes = [json.load(open(f)) for f in sorted(glob.glob(d + "/pass*.json"))]
    byt = {}
    for k, ps in enumerate(passes):
        for r in ps: byt.setdefault(r["ticker"], {})[k] = r
    res = []; nop = 0
    for t, rs in byt.items():
        p = chosen[t]; T = fl(p.get("target_size_fp"), 1000.0)
        days = (dt(p["end_date"]) - dt(p["start_date"])).total_seconds() / 86400
        pool = p["period_reward"] / 1e4 / days
        out = {"ticker": t, "pool_day": pool, "days": days, "T": T}
        ok = False
        for case, clip in (("pess", False), ("cent", False), ("opt", True)):
            per = []; samp = []
            for k, r in sorted(rs.items()):
                last = fl(r["last"]) or None; vol = fl(r["vol24"])
                s = I.score_lane(r["book"], T, last, vol, pool, days, clip=clip)
                if s is None: continue
                samp.append(s)
                per.append(I.lane_value([s], T, pool, days, vol, case))
            if not samp: break
            ok = True
            vol = fl(rs[max(rs)]["vol24"])
            v = I.lane_value(samp, T, pool, days, vol, case)
            out[case] = v; out[case + "_per"] = [x["net100"] for x in per]
            if case == "pess": out["absdollars"] = v["reward"]
            if case == "pess":
                out["depth"] = samp[-1]["depth"]; out["counts"] = [s["counts"] for s in samp]
                out["vol24"] = vol; out["price"] = (samp[-1]["py"], samp[-1]["pn"])
        if ok: res.append(out)
        else: nop += 1
    json.dump(res, open(d + "/scored.json", "w"))
    n = len(res)
    print("passes", len(passes), "markets read", len(byt), "scored", n, "no_price", nop)
    for case in ("pess", "cent", "opt"):
        rew = [r[case]["reward100"] for r in res]; net = [r[case]["net100"] for r in res]
        cost = [r[case]["cost100"] for r in res]
        q = lambda xs, f: sorted(xs)[int(f * (len(xs) - 1))]
        pos = sum(1 for x in net if x > 0.10)
        stable = sum(1 for r in res if sum(1 for x in r[case + "_per"] if x > 0.10) >= 2)
        fl_pos = sum(1 for r in res if r[case]["net_floor100"] > 0.10)
        print(case, "fill-floor stress: positive", fl_pos, "median net_floor100 %.3f" % q(sorted(r[case]["net_floor100"] for r in res), .5))
        print(case, "reward100/day median %.3f p25 %.3f p75 %.3f p90 %.3f max %.3f | cost100 median %.3f | net100 median %.3f p90 %.3f | pos(>0.10) %d (%.1f%%) | pos in >=2 passes %d" %
              (q(rew, .5), q(rew, .25), q(rew, .75), q(rew, .9), max(rew), q(cost, .5), q(net, .5), q(net, .9), pos, 100 * pos / n, stable))
    print("verdict(pess pooled)", I.verdict([r["pess"]["net100"] for r in res]))
    # why zero
    z = [r for r in res if r["pess"]["reward100"] == 0]
    nof = sum(1 for r in res if not any(r["counts"]))
    print("zero reward lanes", len(z), "of which never two-sided target (no f)", nof)
    thin = [r for r in res if min(r["depth"]) < 200]
    print("last-pass side depth <200 on a side:", len(thin), "; both sides >=1000:", sum(1 for r in res if min(r["depth"]) >= 1000))
    print("median depth yes/no", S.median(r["depth"][0] for r in res), S.median(r["depth"][1] for r in res), "median vol24", S.median(r["vol24"] for r in res))
    # by pool band
    res.sort(key=lambda r: r["pool_day"])
    for b in range(6):
        band = res[b * n // 6:(b + 1) * n // 6]
        print("pool band %d ($%.1f-%.1f/day) n=%d: pess net100 median %.3f, central reward100 median %.3f, positive pess %d, central net pos %d" % (
            b, band[0]["pool_day"], band[-1]["pool_day"], len(band), S.median(r["pess"]["net100"] for r in band), S.median(r["cent"]["reward100"] for r in band),
            sum(1 for r in band if r["pess"]["net100"] > .1), sum(1 for r in band if r["cent"]["net100"] > .1)))
    top = sorted(res, key=lambda r: -r["pess"]["net100"])[:8]
    for r in top:
        print("TOP", r["ticker"], "pool/day %.1f" % r["pool_day"], "depth", r["depth"], "vol24 %.0f" % r["vol24"], "prices", r["price"], "pess net100 %.2f reward %.2f cost %.2f cap %.0f f %.2f" % (r["pess"]["net100"], r["pess"]["reward100"], r["pess"]["cost100"], r["pess"]["cap"], r["pess"]["f"]), "cent net %.2f" % r["cent"]["net100"])

if __name__ == "__main__":
    main(sys.argv[1])
