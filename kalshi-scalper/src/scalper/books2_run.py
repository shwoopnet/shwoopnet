"""BOOKS2 runner: markets (settled lists, structure + results kept apart), candles (batched), score (one run). See books2.py."""
from __future__ import annotations

import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import api, backfill
from .books2 import (CACHE, KSER, LEAD, PRIOR_SD, RATIO, W3_START, cheap_side, dk_lines, fee, fit_sd, games, look, net,
                     p_margin_over, p_total_over, pf, pick_treated, side_prob, zstat)


def _suffix(ev):
    return ev.split("-", 1)[1]


def _game_table():
    """event suffix -> dict(series, gid, start, line L, spread S, home code), only games with a DK line."""
    out = {}
    for s, gid, st, ev, h, a in games():
        ln = dk_lines(gid)
        if not ln:
            continue
        out[_suffix(ev)] = dict(series=s, gid=gid, start=st, L=ln[0], S=ln[1], event=ev)
    return out


def _home_codes():
    import sqlite3
    from .books2 import DB
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    return {_suffix(e): ht.split("-")[-1] for e, ht in c.execute("select event, home_ticker from match")}


def markets():
    tab = _game_table()
    out = CACHE / "markets.jsonl"
    seen = set()
    f = open(out, "w")
    lo = int(datetime(2026, 8, 25, tzinfo=timezone.utc).timestamp())
    hi = W3_START + 86400
    for gs, (ts, ss) in KSER.items():
        for fam, ser in (("T", ts), ("S", ss)):
            n = 0
            for m in api.settled_markets(ser, lo, hi):
                suf = _suffix(m["event_ticker"])
                g = tab.get(suf)
                if not g or g["series"] != gs or m["ticker"] in seen:
                    continue
                seen.add(m["ticker"])
                f.write(json.dumps(dict(fam=fam, ser=ser, ticker=m["ticker"], suf=suf, k=m.get("floor_strike"), result=m.get("result"))) + "\n")
                n += 1
            print(ser, n, flush=True)
    f.close()


def _model(fam, g, sd, k, team_home):
    if fam == "T":
        return p_total_over(k, g["L"], sd)
    mu = -g["S"]
    return p_margin_over(k, mu if team_home else -mu, sd)


def _strike_plan(sd_prior=True):
    """Fetch-economy prune: strikes at least 0.5 x PRIOR_SD from the centre. Uses only the DK line and the strike."""
    tab, hc = _game_table(), _home_codes()
    plan = defaultdict(list)
    for line in open(CACHE / "markets.jsonl"):
        r = json.loads(line)
        g = tab[r["suf"]]
        k = r["k"]
        if k is None:
            continue
        if r["fam"] == "T":
            dist = abs(k - g["L"])
        else:
            team = r["ticker"].split("-")[-1].rstrip("0123456789")
            mu = -g["S"] if team == hc[r["suf"]] else g["S"]
            dist = abs(k - mu)
        if dist >= 0.5 * PRIOR_SD[(r["fam"], g["series"])]:
            plan[(r["suf"], r["fam"])].append(r["ticker"])
    return tab, plan


def candles():
    tab, plan = _strike_plan()
    outp = CACHE / "candles.jsonl"
    done = set()
    if outp.exists():
        done = {json.loads(l)["key"] for l in open(outp)}
    jobs = []
    for (suf, fam), tks in plan.items():
        g = tab[suf]
        for i in range(0, len(tks), 8):
            key = f"{suf}|{fam}|{i}"
            if key not in done:
                jobs.append((key, g["start"], tks[i:i + 8]))
    print("jobs", len(jobs), "markets", sum(len(v) for v in plan.values()), flush=True)
    fh = open(outp, "a")

    def run(job):
        key, st, tks = job
        try:
            got = api.batch_candlesticks(tks, st - 6 * 3600, st - 60)
        except RuntimeError as e:
            return key, None
        rec = {}
        for tk in tks:
            cs = {}
            for c in got.get(tk, []):
                end = c.get("end_period_ts")
                b = backfill._d(c.get("yes_bid"), "close_dollars")
                a = backfill._d(c.get("yes_ask"), "close_dollars")
                if end is not None and b is not None and a is not None:
                    cs[int(end)] = (b, a)
            rec[tk] = cs
        return key, rec

    n = 0
    with ThreadPoolExecutor(2) as ex:
        for key, rec in ex.map(run, jobs):
            if rec is None:
                continue
            fh.write(json.dumps(dict(key=key, c=rec)) + "\n")
            fh.flush()
            n += 1
            if n % 100 == 0:
                print("done", n, flush=True)
    print("candles complete", n, flush=True)


def _residual_sds(tab, fam_games, scores, hc):
    """sd per (family, series) from the first two thirds of that league's games with a line and a score (ordered by start)."""
    sds, cut = {}, {}
    for s in KSER:
        gl = sorted([g for g in tab.values() if g["series"] == s], key=lambda g: g["start"])
        k = (2 * len(gl)) // 3
        cut[s] = gl[k]["start"] if gl else None
        fit = [g for g in gl[:k] if g["gid"] in scores]
        sds[("T", s)] = fit_sd([sum(scores[g["gid"]]) - g["L"] for g in fit])
        sds[("S", s)] = fit_sd([(scores[g["gid"]][0] - scores[g["gid"]][1]) + g["S"] for g in fit])
        sds[("n", s)] = len(fit)
    return sds, cut


def score():
    tab, hc = _game_table(), _home_codes()
    scores = json.load(open(CACHE / "scores.json"))
    sds, cut = _residual_sds(tab, None, scores, hc)
    print("sd fit", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in sds.items()})
    cands, res, strike = {}, {}, {}
    for l in open(CACHE / "markets.jsonl"):
        r = json.loads(l)
        res[r["ticker"]] = r["result"]
        strike[r["ticker"]] = r
    for l in open(CACHE / "candles.jsonl"):
        for tk, cs in json.loads(l)["c"].items():
            cands[tk] = {int(t): tuple(q) for t, q in cs.items()}
    entries = defaultdict(list)  # (fam, series, suf) -> rows
    cover = defaultdict(lambda: [0, 0])
    for tk, r in strike.items():
        if tk not in cands:
            continue
        g = tab[r["suf"]]
        s = g["series"]
        q = look(cands[tk], g["start"])
        cover[(r["fam"], s)][0] += 1
        if q is None:
            continue
        cover[(r["fam"], s)][1] += 1
        cs = cheap_side(q)
        if cs is None or sds[(r["fam"], s)] is None:
            continue
        side, ask = cs
        team_home = True
        if r["fam"] == "S":
            team_home = r["ticker"].split("-")[-1].rstrip("0123456789") == hc[r["suf"]]
        py = _model(r["fam"], g, sds[(r["fam"], s)], r["k"], team_home)
        p = side_prob(side, py)
        win = res[tk] == ("yes" if side == "Y" else "no")
        entries[(r["fam"], s, r["suf"])].append(dict(ask=ask, p=p, win=win, tk=tk, side=side, st=g["start"], k=r["k"],
                                                     day=datetime.fromtimestamp(g["start"], timezone.utc).date().isoformat()))
    out = []
    for fam in ("T", "S"):
        for part in ("test", "fit"):
            ctrl, trt = [], []
            for (f, s, suf), rows in entries.items():
                if f != fam:
                    continue
                intest = tab[suf]["start"] >= cut[s]
                if (part == "test") != intest:
                    continue
                ctrl += [dict(r, s=s, suf=suf) for r in rows]
                trt += [dict(r, s=s, suf=suf) for r in pick_treated(rows)]
            out.append(f"== family {fam} part {part} ({'out of sample' if part == 'test' else 'in sample for sd, information'})")
            gaps = sorted(r["p"] - r["ask"] for r in ctrl)
            n = len(gaps)
            if n:
                out.append(f"cheap strikes n {n} games {len({r['suf'] for r in ctrl})}; gap model p - ask median {gaps[n//2]*100:+.2f}c p90 {gaps[9*n//10]*100:+.2f}c")
                for s in KSER:
                    g2 = sorted(r["p"] - r["ask"] for r in ctrl if r["s"] == s)
                    if g2:
                        out.append(f"  {s}: n {len(g2)} median {g2[len(g2)//2]*100:+.2f}c p90 {g2[9*len(g2)//10]*100:+.2f}c")
                xs = [net(r["win"], r["ask"]) for r in ctrl]
                per = defaultdict(float)
                for r, x in zip(ctrl, xs):
                    per[r["suf"]] += x
                out.append(f"control: win {sum(r['win'] for r in ctrl)/n:.3f} vs ask {sum(r['ask'] for r in ctrl)/n:.3f} vs model {sum(r['p'] for r in ctrl)/n:.3f}; "
                           f"mean net {sum(xs)/n*100:+.2f}c PF {pf(xs):.2f} z(game) {zstat(list(per.values()))}")
                for lo_, hi_ in ((0.03, 0.10), (0.10, 0.20), (0.20, 0.30001)):
                    b = [r for r in ctrl if lo_ <= r["ask"] < hi_]
                    if b:
                        out.append(f"  ask {lo_:.2f}-{hi_:.2f}: n {len(b)} win {sum(r['win'] for r in b)/len(b):.3f} ask {sum(r['ask'] for r in b)/len(b):.3f} model {sum(r['p'] for r in b)/len(b):.3f}")
            out.append(f"treated (p >= {RATIO:g} x ask, 2 per game): n {len(trt)}")
            if trt:
                trt.sort(key=lambda r: (r["st"], r["tk"]))
                xs = [net(r["win"], r["ask"]) for r in trt]
                h = len(xs) // 2
                per = defaultdict(float)
                for r, x in zip(trt, xs):
                    per[r["suf"]] += x
                out.append(f"  win {sum(r['win'] for r in trt)/len(trt):.3f} vs ask {sum(r['ask'] for r in trt)/len(trt):.3f} vs model {sum(r['p'] for r in trt)/len(trt):.3f}; mean net {sum(xs)/len(xs)*100:+.2f}c PF {pf(xs):.2f}; "
                           f"x1.2 {sum(net(r['win'], r['ask'], 1.2) for r in trt)/len(trt)*100:+.2f}c; halves {sum(xs[:h])/max(1,h)*100:+.2f}c / {sum(xs[h:])/max(1,len(xs)-h)*100:+.2f}c; games {len(per)}")
    out.append("coverage (fetched strikes with a candle -> with a valid look): " + str({f"{k[0]} {k[1]}": tuple(v) for k, v in cover.items()}))
    text = "\n".join(out)
    print(text)
    (CACHE / "books2_result.txt").write_text(text)
