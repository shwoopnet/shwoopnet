"""PPW1 (workers/PPW1_REGISTRATION.md): CHEAP1-C, CHEAP1-M and SCALEIN1 on L1's history. Research only: nothing here places an order.
Usage: python -m scalper.ppw1 ab   (thirds A and B)   then   python -m scalper.ppw1 c   (holdout third C, once)
"""
from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from .calibration import cluster_mean_z
from .l1studies import fee, pf
from .paths import DATA_DIR
from . import tstop1

CT = ZoneInfo("America/Chicago")
CRYPTO = ["KXXRP15M", "KXBTC15M", "KXDOGE15M", "KXETH15M"]      # L1_SERIES order among CAPPED_SERIES
LIVE5 = {"KXGOLD15M", "KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M"}
VOL_DBS = ["alts2", "alts3", "alts4", "book", "l1b", "e3b", "fresh", "rep"]
DONE_AB = DATA_DIR / "ppw1_ab_result.txt"
DONE_C = DATA_DIR / "ppw1_c_result.txt"


def day(ts):
    return datetime.fromtimestamp(ts, CT).date().isoformat()


def leg(price, won, c=1, m=1.0):
    return won - price - fee(price, c, m)


def volumes(keys):
    need = defaultdict(set)
    for tk, e in keys:
        need[tk].add(e)
    vol = {}
    for name in VOL_DBS:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        tks = list(need)
        for i in range(0, len(tks), 500):
            chunk = tks[i:i + 500]
            q = "SELECT ticker, end_ts, volume FROM candle WHERE ticker IN (%s)" % ",".join("?" * len(chunk))
            for tk, e, v in db.execute(q, chunk):
                if e in need[tk] and (tk, e) not in vol and v is not None:
                    vol[(tk, e)] = v
    return vol


def stats(units):
    """units: list of dicts with day, legs [(price, won)], vol0 flag. Net per contract over the unit's contracts."""
    out = {}
    for c in (1, 10):
        nets = [sum(leg(p, w, c) for p, w in u["legs"]) / len(u["legs"]) for u in units]
        out[f"pf{c}"] = pf(nets)
        out[f"net{c}"] = 100 * sum(nets) / len(nets) if nets else 0.0
    st = [sum(leg(p, w, 1, 1.2) for p, w in u["legs"]) / len(u["legs"]) for u in units]
    out["pf_stress"] = pf(st); out["net_stress"] = 100 * sum(st) / len(st) if st else 0.0
    legs = [(p, w) for u in units for p, w in u["legs"]]
    wins = [leg(p, w) for p, w in legs if w == 1]
    out["n"] = len(units); out["legs"] = len(legs)
    out["losses"] = sum(1 for _, w in legs if w == 0)
    out["loss_rate"] = 100 * out["losses"] / len(legs) if legs else 0.0
    out["ppw"] = 100 * sum(wins) / len(wins) if wins else 0.0
    out["z"] = cluster_mean_z([(u["day"], sum(leg(p, w) for p, w in u["legs"]) / len(u["legs"])) for u in units])[2]
    return out


def fmt(name, s):
    return (f"  {name:<22} n {s['n']:>5} legs {s['legs']:>5} loss {s['losses']:>4} ({s['loss_rate']:5.2f}%) per win {s['ppw']:+6.2f}c "
            f"net {s['net1']:+6.2f}c PF1 {s['pf1']:.3f} PF10 {s['pf10']:.3f} net10 {s['net10']:+6.2f}c stress PF {s['pf_stress']:.3f} net {s['net_stress']:+6.2f}c z {s['z']:+5.2f}")


def unit(r, extra=None, vol=None):
    legs = [(r["price"], r["won"])]
    v0 = vol.get((r["ticker"], r["close_ts"] - 360)) == 0 if vol is not None else False
    if extra:
        legs.append(extra[:2]); v0 = v0 or extra[2] == 0
    return {"day": day(r["close_ts"]), "legs": legs, "vol0": v0, "win": r["win"]}


def build(rows):
    keys = set()
    by_w = defaultdict(dict)
    for r in rows:
        keys.add((r["ticker"], r["close_ts"] - 360))
        by_w[r["close_ts"]][r["series"]] = r
        for e, b, a in r["path"]:
            keys.add((r["ticker"], e))
    vol = volumes(keys)
    pairs = {}
    # CHEAP1-C and the three-coin information read
    for label, group in (("C", CRYPTO), ("C3", [s for s in CRYPTO if s != "KXXRP15M"])):
        lst, chp, diff_same = [], [], [0, 0]
        for t, m in by_w.items():
            ins = [m[s] for s in group if s in m]
            if not ins:
                continue
            a = ins[0]
            b = min(ins, key=lambda r: (r["price"], group.index(r["series"])))
            ua, ub = unit(a, vol=vol), unit(b, vol=vol)
            ua["diff"] = ub["diff"] = a is not b
            if a is not b:
                diff_same[0 if a["side"] == b["side"] else 1] += 1
            lst.append(ua); chp.append(ub)
        pairs[label] = (lst, chp, diff_same)
    # CHEAP1-M
    lst, chp, diff_same = [], [], [0, 0]
    for t, m in by_w.items():
        g = m.get("KXGOLD15M")
        if not g:
            continue
        s = m.get("KXSILVER15M")
        b = s if s and s["price"] < g["price"] else g
        ua, ub = unit(g, vol=vol), unit(b, vol=vol)
        ua["diff"] = ub["diff"] = b is not g
        if b is not g:
            diff_same[0 if g["side"] == s["side"] else 1] += 1
        lst.append(ua); chp.append(ub)
    pairs["M"] = (lst, chp, diff_same)
    # SCALEIN1
    base, pos, adds = [], [], []
    for r in rows:
        if r["series"] not in LIVE5:
            continue
        add = None
        for e, b, a in r["path"]:
            if e > r["close_ts"] - 180:
                break
            ask = a if r["side"] == "yes" else round(1 - b, 4)
            if r["price"] - 0.06 - 1e-9 <= ask <= r["price"] - 0.03 + 1e-9 and 0 < ask < 1:
                add = (ask, r["won"], vol.get((r["ticker"], e)))
                break
        u0 = unit(r, vol=vol); u1 = unit(r, add, vol=vol)
        u0["diff"] = u1["diff"] = add is not None
        base.append(u0); pos.append(u1)
        if add:
            adds.append({"day": u0["day"], "legs": [add[:2]], "vol0": add[2] == 0, "win": r["win"], "diff": True})
    pairs["S"] = (base, pos, None, adds)
    return pairs


def compare(lst, chp, wins, out, label):
    keep = [i for i, u in enumerate(lst) if u["win"] in wins]
    for drop0 in (False, True):
        idx = [i for i in keep if not (drop0 and (lst[i]["vol0"] or chp[i]["vol0"]))]
        tag = "zero-volume fill candles dropped" if drop0 else "all"
        out.append(f" [{label}] {tag}")
        for w in sorted(wins):
            ii = [i for i in idx if lst[i]["win"] == w]
            dd = [i for i in ii if lst[i]["diff"]]
            a, b = stats([lst[i] for i in ii]), stats([chp[i] for i in ii])
            out.append(f" third {'ABC'[w]}: all units (lever bar: PF diff {b['pf1'] - a['pf1']:+.3f}, net diff {b['net1'] - a['net1']:+.2f}c)")
            out.append(fmt("comparison", a)); out.append(fmt("rule", b))
            if dd:
                out.append(f"   units where the choice differs: {len(dd)}")
                out.append(fmt("comparison (differ)", stats([lst[i] for i in dd])))
                out.append(fmt("rule (differ)", stats([chp[i] for i in dd])))
        obs = []
        for i in idx:
            na = sum(leg(p, x) for p, x in lst[i]["legs"]) / len(lst[i]["legs"])
            nb = sum(leg(p, x) for p, x in chp[i]["legs"]) / len(chp[i]["legs"])
            obs.append((lst[i]["day"], nb - na))
        m, se, z = cluster_mean_z(obs)
        out.append(f"   pooled over thirds {''.join('ABC'[w] for w in sorted(wins))}: difference rule minus comparison {100 * m:+.3f}c per unit, day-clustered z {z:+.2f}")


def main(argv):
    if len(argv) < 2 or argv[1] not in ("ab", "c"):
        print(__doc__); return
    cmd = argv[1]
    done = DONE_AB if cmd == "ab" else DONE_C
    if done.exists():
        print(f"Refusing to run again: {done} exists."); return
    if cmd == "c" and not DONE_AB.exists():
        print("Run ab first."); return
    rows = tstop1.load()
    P = build(rows)
    wins = {0, 1} if cmd == "ab" else {0, 1, 2}
    out = [f"PPW1 {cmd}: {len(rows)} L1 entries; thirds read: {''.join('ABC'[w] for w in sorted(wins))}"]
    for label, name in (("C", "CHEAP1-C (cheapest of BTC/ETH/XRP/DOGE vs list order)"), ("C3", "information: CHEAP1-C without XRP"),
                        ("M", "CHEAP1-M (silver when cheaper vs gold)")):
        lst, chp, ds = P[label]
        out.append(f"== {name}; differing windows same side {ds[0]}, opposite side {ds[1]}")
        compare(lst, chp, wins, out, label)
    base, pos, _, adds = P["S"]
    out.append(f"== SCALEIN1 (live five; add 1 at a 3c to 6c dip with >=180 s left); entries {len(base)}, adds {len(adds)}")
    for drop0 in (False, True):
        out.append(f" [add leg alone] {'zero-volume add candles dropped' if drop0 else 'all'}")
        for w in sorted(wins):
            aa = [u for u in adds if u["win"] == w and not (drop0 and u["vol0"])]
            if aa:
                out.append(f" third {'ABC'[w]}"); out.append(fmt("add leg", stats(aa)))
    out.append(" [position vs entry alone]")
    compare(base, pos, wins, out, "S")
    text = "\n".join(out)
    print(text)
    done.write_text(text + "\n")


if __name__ == "__main__":
    main(sys.argv)
