"""NPBKBO1 (workers/NPBKBO1_REGISTRATION.md): CHEAP side (ask 3c to 30c) of Kalshi NPB and KBO match winners vs team Elo plus starter quality.
Research only. Nothing here means trade; no promote verb. No favourite-side result is computed or printed.

    python -m scalper.npbkbo1 games    (league results and starters from npb.jp and koreabaseball.com, public pages, cached)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

D = Path(os.environ.get("NPBKBO1_DIR", "/tmp/npbkbo1"))
UA = {"User-Agent": "Mozilla/5.0"}
CUT_DATE = date(2026, 10, 3)


def http(url, data=None, headers=None, retries=4):
    h = dict(UA)
    h.update(headers or {})
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa
            last = e
            time.sleep(3 * (i + 1))
    raise last


def flat(html):
    x = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    x = re.sub(r"<[^>]+>", "|", x)
    return re.sub(r"[\s|]*\|[\s|]*", "|", x)


def parse_npb_game(html):
    x = flat(html)
    m = re.search(r"\|([A-Za-z][^|]+)\|(\d+)\|([A-Za-z][^|]+)\|(\d+)\|[^|]+\|T - ", x)
    if not m:
        return None
    home, hs, away, as_ = m.group(1).strip(), int(m.group(2)), m.group(3).strip(), int(m.group(4))
    segs = re.split(r"IP\|BF\|H\|BB\|HB\|SO\|ER\|", x)[1:]
    if len(segs) < 2:
        return None
    names = []
    for s in segs[:2]:
        nm = s.split("|")[0]
        names.append(re.sub(r",?\s*\(.*\)$", "", nm).strip().rstrip(","))
    return dict(home=home, away=away, hs=hs, as_=as_, a_sp=names[0], h_sp=names[1])


def npb(sleep=1.0):
    out = D / "npb_games.json"
    have = json.loads(out.read_text()) if out.exists() else {}
    d = date(2026, 3, 20)
    while d <= CUT_DATE:
        key = d.strftime("%Y%m%d")
        if key + "_idx" not in have:
            try:
                h = http(f"https://npb.jp/bis/eng/2026/games/gm{key}.html")
                links = sorted(set(re.findall(r'href="\./(s%s\d+\.html)"|href="/bis/eng/2026/games/(s%s\d+\.html)"' % (key, key), h)))
                links = sorted({a or b for a, b in links})
                have[key + "_idx"] = links
            except Exception as e:  # noqa
                have[key + "_idx"] = []
                print("idx miss", key, e, flush=True)
            time.sleep(sleep)
        for L in have[key + "_idx"]:
            if L in have:
                continue
            try:
                g = parse_npb_game(http("https://npb.jp/bis/eng/2026/games/" + L))
                have[L] = (g | {"date": key}) if g else {"date": key, "none": True}
            except Exception as e:  # noqa
                have[L] = {"date": key, "none": True, "err": str(e)}
            time.sleep(sleep)
        if d.day == 1 or d == CUT_DATE:
            out.write_text(json.dumps(have))
            print("npb through", key, sum(1 for k in have if not k.endswith("_idx") and not have[k].get("none")), flush=True)
        d += timedelta(days=1)
    out.write_text(json.dumps(have))


SHORT_KEYS = (("yomiuri", "YOM"), ("hanshin", "HAN"), ("hiroshima", "HIR"), ("yokohama", "YOK"), ("dena", "YOK"), ("chunichi", "CHU"), ("yakult", "YAK"),
              ("softbank", "SOF"), ("nippon", "NIP"), ("orix", "ORI"), ("seibu", "SEI"), ("rakuten", "RAK"), ("lotte", "LOT"))


def npb_homes(sleep=1.0):
    """The game page's header lists the WINNER first, not the home club (found at fit time: 'home win rate 1.0'). The day page lists
    'Home|runs|Game n|Venue|runs|Away' (Hanshin at Koshien, Hiroshima at Mazda Stadium), so the true home club comes from there."""
    out = D / "npb_home.json"
    have = json.loads(out.read_text()) if out.exists() else {}
    d = date(2026, 3, 20)
    while d <= CUT_DATE:
        key = d.strftime("%Y%m%d")
        if key not in have:
            x = flat(http(f"https://npb.jp/bis/eng/2026/games/gm{key}.html"))
            pairs = []
            for m in re.finditer(r"\|([A-Za-z][A-Za-z-]+)\|\d+\|Game \d+\|[^|]+\|\d+\|([A-Za-z][A-Za-z-]+)(?=\|)", x):
                a, b = m.group(1).lower(), m.group(2).lower()
                ka = next((v for k, v in SHORT_KEYS if k in a), None)
                kb = next((v for k, v in SHORT_KEYS if k in b), None)
                pairs.append((ka, kb))
            have[key] = pairs
            time.sleep(sleep)
        d += timedelta(days=1)
    out.write_text(json.dumps(have))
    print("homes done", sum(len(v) for v in have.values()), flush=True)


def kbo(sleep=1.0):
    out = D / "kbo_games.json"
    have = json.loads(out.read_text()) if out.exists() else {}
    d = date(2026, 3, 20)
    while d <= CUT_DATE:
        key = d.strftime("%Y%m%d")
        if key not in have:
            try:
                body = urllib.parse.urlencode({"leId": 1, "srId": 0, "date": key}).encode()
                r = http("https://www.koreabaseball.com/ws/Main.asmx/GetKboGameList", data=body,
                         headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                  "X-Requested-With": "XMLHttpRequest",
                                  "Referer": "https://www.koreabaseball.com/Schedule/GameCenter/Main.aspx"})
                j = json.loads(r)
                have[key] = [{k: g.get(k) for k in ("G_ID", "AWAY_ID", "HOME_ID", "T_PIT_P_ID", "T_PIT_P_NM", "B_PIT_P_ID", "B_PIT_P_NM",
                                                    "GAME_STATE_SC", "CANCEL_SC_ID", "T_SCORE_CN", "B_SCORE_CN", "SR_ID", "G_TM")}
                             for g in j.get("game", [])]
            except Exception as e:  # noqa
                print("kbo miss", key, e, flush=True)
            time.sleep(sleep)
        d += timedelta(days=1)
    out.write_text(json.dumps(have))
    print("kbo done", sum(len(v) for v in have.values()), flush=True)


# ---------------------------------------------------------------- model, fetch, run
import hashlib
import math
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .tennis1 import net_cents, profit_factor, summary, treated, fee

ET = ZoneInfo("America/New_York")
CUT = "2026-10-03T16:00"
KGRID, HGRID, BGRID = (4.0, 8.0, 12.0, 16.0, 24.0), (0.0, 10.0, 20.0, 30.0, 40.0), (0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0)
MIN_PRIOR_GAMES, SHRINK, LOOK_S, MIN_TRADES = 20, 8.0, 120, 150
EV = re.compile(r"^(KX[A-Z]+)-(\d{2}[A-Z]{3}\d{6})(.+)$")
NPB_KEYS = (("giants", "YOM"), ("tigers", "HAN"), ("carp", "HIR"), ("baystars", "YOK"), ("dragons", "CHU"), ("swallows", "YAK"),
            ("hawks", "SOF"), ("fighters", "NIP"), ("buffaloes", "ORI"), ("lions", "SEI"), ("eagles", "RAK"), ("marines", "LOT"))
KBO_ID = {"HT": "kia", "SS": "samsung", "LG": "lg", "OB": "doosan", "KT": "kt", "SK": "ssg", "LT": "lotte", "HH": "hanwha", "NC": "nc", "WO": "kiwoom"}
KBO_NAME = {"Doosan Bears": "doosan", "Hanwha Eagles": "hanwha", "KT Wiz": "kt", "Kia Tigers": "kia", "Kiwoom Heroes": "kiwoom",
            "LG Twins": "lg", "Lotte Giants": "lotte", "NC Dinos": "nc", "SSG Landers": "ssg", "Samsung Lions": "samsung"}


def npb_key(name):
    n = name.lower()
    for k, v in NPB_KEYS:
        if k in n:
            return v
    return None


def league_games():
    """Unified list per league: (date 'YYYYMMDD', home, away, home_pts, away_pts, home_sp, away_sp) with ties and unparsed dropped."""
    out = {"NPB": [], "KBO": []}
    dropped = defaultdict(int)
    homes = json.loads((D / "npb_home.json").read_text())
    for k, g in json.loads((D / "npb_games.json").read_text()).items():
        if k.endswith("_idx"):
            continue
        if g.get("none"):
            dropped["npb unparsed or cancelled"] += 1
            continue
        w, l = npb_key(g["home"]), npb_key(g["away"])   # header order: winner first (tie games dropped below)
        if not w or not l or g["hs"] == g["as_"]:
            dropped["npb tie or unknown team"] += 1
            continue
        hm = [p for p in homes.get(g["date"], []) if set(p) == {w, l}]
        if len(hm) != 1:
            dropped["npb home club not found uniquely (doubleheader or parse)"] += 1
            continue
        h, a = hm[0]
        hpts, apts = (g["hs"], g["as_"]) if h == w else (g["as_"], g["hs"])
        out["NPB"].append((g["date"], h, a, hpts, apts, g["h_sp"], g["a_sp"]))
    for d, gs in json.loads((D / "kbo_games.json").read_text()).items():
        for g in gs:
            try:
                if str(g["GAME_STATE_SC"]) != "3" or str(g["CANCEL_SC_ID"]) != "0" or g["SR_ID"] not in (0, "0"):
                    continue
                hs, as_ = int(g["B_SCORE_CN"]), int(g["T_SCORE_CN"])
            except (TypeError, ValueError):
                continue
            if hs == as_ or g["HOME_ID"] not in KBO_ID or g["AWAY_ID"] not in KBO_ID:
                dropped["kbo tie or unknown"] += 1
                continue
            out["KBO"].append((d, KBO_ID[g["HOME_ID"]], KBO_ID[g["AWAY_ID"]], hs, as_,
                               str(g["B_PIT_P_ID"] or "") or None, str(g["T_PIT_P_ID"] or "") or None))
    for L in out:
        out[L].sort(key=lambda r: (r[0], r[1], r[2]))
    return out, dict(dropped)


def walk(games, K, h, b, record=False):
    """Walk-forward over one league's games by date. Predictions for a date use only state from earlier dates.
    Returns (log-loss over games with both clubs >= MIN_PRIOR_GAMES prior games, n, preds{(date,home,away): (p_home, qualified)})."""
    elo, ngames = defaultdict(lambda: 1500.0), defaultdict(int)
    sres, sn = defaultdict(float), defaultdict(int)
    ll, n, preds = 0.0, 0, {}
    i = 0
    while i < len(games):
        j = i
        while j < len(games) and games[j][0] == games[i][0]:
            j += 1
        day = games[i:j]
        upd = []
        for d, ho, aw, hs, as_, hsp, asp in day:
            ph_elo = 1.0 / (1.0 + 10 ** (-(elo[ho] + h - elo[aw]) / 400.0))
            sqh = sres[(ho, hsp)] / (sn[(ho, hsp)] + SHRINK) if hsp else 0.0
            sqa = sres[(aw, asp)] / (sn[(aw, asp)] + SHRINK) if asp else 0.0
            x = (elo[ho] + h - elo[aw]) + b * 400.0 * (sqh - sqa)
            p = 1.0 / (1.0 + 10 ** (-x / 400.0))
            qual = ngames[ho] >= MIN_PRIOR_GAMES and ngames[aw] >= MIN_PRIOR_GAMES
            if qual:
                y = 1.0 if hs > as_ else 0.0
                ll -= y * math.log(p) + (1 - y) * math.log(1 - p)
                n += 1
            if record:
                preds[(d, ho, aw)] = preds.get((d, ho, aw), []) + [(p, qual)]
            upd.append((ho, aw, hs > as_, ph_elo, hsp, asp))
        for ho, aw, hw, ph_elo, hsp, asp in upd:
            elo[ho] += K * ((1.0 if hw else 0.0) - ph_elo)
            elo[aw] -= K * ((1.0 if hw else 0.0) - ph_elo)
            ngames[ho] += 1
            ngames[aw] += 1
            if hsp:
                sres[(ho, hsp)] += (1.0 if hw else 0.0) - ph_elo
                sn[(ho, hsp)] += 1
            if asp:
                sres[(aw, asp)] += (0.0 if hw else 1.0) - (1 - ph_elo)
                sn[(aw, asp)] += 1
        i = j
    return ll, n, preds


def fit():
    lg, dropped = league_games()
    split = {}
    for L, gs in lg.items():
        dates = sorted({g[0] for g in gs})
        split[L] = dates[int(len(dates) * 2 / 3) - 1]   # last date of the fit third
    best = None
    for h in HGRID:
        for b in BGRID:
            tot, ks = 0.0, {}
            for L, gs in lg.items():
                fit_games = [g for g in gs if g[0] <= split[L]]
                bl = min((walk(fit_games, K, h, b)[0], K) for K in KGRID)
                ks[L] = bl[1]
                tot += bl[0]
            if best is None or tot < best[0]:
                best = (tot, h, b, ks)
    res = dict(h=best[1], b=best[2], K=best[3], split=split, dropped=dropped, n={L: len(g) for L, g in lg.items()})
    # information: the same fit with b = 0 (Elo only) on the fit third and both models out of sample on the last third
    info = {}
    for L, gs in lg.items():
        for tag, bb in (("model", res["b"]), ("elo_only", 0.0)):
            ll, n, _ = walk(gs, res["K"][L], res["h"], bb)
            ll0, n0, _ = walk([g for g in gs if g[0] <= split[L]], res["K"][L], res["h"], bb)
            info[f"{L} {tag} out-of-sample log-loss"] = round((ll - ll0) / max(n - n0, 1), 4)
            info[f"{L} {tag} out-of-sample n"] = n - n0
    res["info"] = info
    (D / "fit.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def start_ts(ev):
    m = EV.match(ev)
    dt = datetime.strptime(m.group(2), "%y%b%d%H%M").replace(tzinfo=ET)
    return int(dt.timestamp()), dt.astimezone(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")


def universe():
    """Matched, qualified Kalshi events: {event: dict(first, src, series, start, dkey, ho, aw, p_first, close)} and funnel counts."""
    ms = json.loads((D / "markets_full.json").read_text())
    fitres = json.loads((D / "fit.json").read_text())
    lg, _ = league_games()
    preds = {}
    for L, gs in lg.items():
        preds[L] = walk(gs, fitres["K"][L], fitres["h"], fitres["b"], record=True)[2]
    ev = defaultdict(list)
    for t, m in ms.items():
        ev[m["event_ticker"]].append(m)
    uni, funnel = {}, defaultdict(int)
    for e, mk in ev.items():
        series = mk[0]["series"]
        L = "NPB" if series == "KXNPBGAME" else "KBO"
        funnel[L + " events"] += 1
        if len(mk) != 2 or not EV.match(e):
            funnel[L + " not two-market or unparsed"] += 1
            continue
        st, jd = start_ts(e)
        key = (lambda n: npb_key(n)) if L == "NPB" else (lambda n: KBO_NAME.get(n))
        ka = [key(m["yes_sub_title"]) for m in mk]
        if None in ka or ka[0] == ka[1]:
            funnel[L + " team name unmapped"] += 1
            continue
        cands = [(jd, ka[0], ka[1]), (jd, ka[1], ka[0])]
        hits = [(c, preds[L][c]) for c in cands if c in preds[L]]
        if len(hits) != 1 or len(hits[0][1]) != 1:
            funnel[L + " no unique league game (unmatched or doubleheader)"] += 1
            continue
        (d, ho, aw), pl = hits[0]
        p_home, qual = pl[0]
        if not qual:
            funnel[L + " under 20 prior games"] += 1
            continue
        mk.sort(key=lambda m: m["ticker"])
        first = mk[0]
        team_first = ka[mk.index(first)]
        p_first = p_home if team_first == ho else 1 - p_home
        other = mk[1]["ticker"]
        uni[e] = dict(first=first["ticker"], other=other, src=first["src"], series=series, L=L, start=st, p={first["ticker"]: p_first, other: 1 - p_first},
                      res=first["result"], close=first["close_time"])
        funnel[L + " qualified"] += 1
    return uni, dict(funnel)


def md5_key(ev):
    return hashlib.md5(ev.encode()).hexdigest()


def fetch(budget_s=2 * 3600):
    from . import api
    from .candlefield import quote_close
    uni, funnel = universe()
    order = sorted(uni, key=md5_key)
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    t0 = time.time()
    print(len(order), "qualified events", funnel, flush=True)
    for ev in order:
        if time.time() - t0 > float(os.environ.get("NK1_BUDGET_S", budget_s)):
            print("time box reached", len(have), flush=True)
            break
        if ev in have:
            continue
        g = uni[ev]
        path = f"/historical/markets/{g['first']}/candlesticks" if g["src"] == "hist" else f"/series/{g['series']}/markets/{g['first']}/candlesticks"
        try:
            d = api._get(path, {"start_ts": g["start"] - 6 * 3600, "end_ts": g["start"], "period_interval": 1})
            have[ev] = [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
        except Exception as e:  # noqa
            print("skip", ev, e, flush=True)
        time.sleep(1.4)
        if len(have) % 25 == 0:
            cp.write_text(json.dumps(have))
            print(len(have), "of", len(order), f"{(time.time() - t0) / 60:.0f} min", flush=True)
    cp.write_text(json.dumps(have))
    print("done", len(have), flush=True)


def cheap_side(yes_bid, yes_ask):
    if yes_bid is None or yes_ask is None or not (0 < yes_bid < yes_ask < 1):
        return None
    ya, na = round(yes_ask, 4), round(1 - yes_bid, 4)
    if 0.03 <= ya <= 0.30:
        return "yes", ya
    if 0.03 <= na <= 0.30:
        return "no", na
    return None


def look(candles, start):
    best = None
    for end, b, a in candles:
        if end <= start - LOOK_S and b is not None and a is not None and 0 < b < a < 1 and (best is None or end > best[0]):
            best = (end, b, a)
    return (best[1], best[2]) if best else None


def run():
    from .calibration import cluster_mean_z
    rp = D / "npbkbo1_result.txt"
    if rp.exists():
        print("refused: already run")
        return
    uni, funnel = universe()
    candles = json.loads((D / "candles.json").read_text())
    rows, nolook, nocheap = [], 0, 0
    for ev, u in uni.items():
        if ev not in candles:
            continue
        q = look(candles[ev], u["start"])
        if q is None:
            nolook += 1
            continue
        cs = cheap_side(*q)
        if cs is None:
            nocheap += 1
            continue
        side, ask = cs
        won = (u["res"] == "yes") if side == "yes" else (u["res"] == "no")
        p_side = u["p"][u["first"]] if side == "yes" else u["p"][u["other"]]
        rows.append(dict(ev=ev, L=u["L"], net=net_cents(ask, won), won=won, ask=ask, start=u["start"], p=p_side, tr=treated(p_side, ask),
                         day=datetime.fromtimestamp(u["start"], ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")))
    starts = sorted(u["start"] for u in uni.values())
    mid = starts[len(starts) // 2]
    third = starts[int(len(starts) * 2 / 3)]
    stress = lambda r: r["net"] - 0.2 * fee(r["ask"]) / 10 * 100
    L_ = [f"qualified events {len(uni)} (candles fetched {len(candles)}), no look {nolook}, no cheap side {nocheap}, cheap-side rows {len(rows)}, treated {sum(r['tr'] for r in rows)}",
          f"funnel {json.dumps(funnel)}"]

    def line(tag, rs):
        if not rs:
            L_.append(f"{tag}: n 0")
            return
        s = summary([(r["ev"], r["net"], r["won"], r["ask"]) for r in rs])
        m, se, z = cluster_mean_z([(r["day"], r["net"]) for r in rs])
        pf2 = profit_factor([stress(r) for r in rs])
        L_.append(f"{tag}: n {s['n']}, win {s['win']:.3f}, mean ask {s['ask']*100:.1f}c, mean net {s['mean']:.2f}c, PF {s['pf']:.2f}, z {z:.2f}, PF x1.2 {pf2:.2f}")

    tr = [r for r in rows if r["tr"]]
    line("CONTROL all cheap-side", rows)
    line("TREATED", tr)
    line("treated D1", [r for r in tr if r["start"] < mid])
    line("treated D2", [r for r in tr if r["start"] >= mid])
    line("info treated last third of pre-cut (out of sample)", [r for r in tr if r["start"] >= third])
    for L in ("NPB", "KBO"):
        line(f"info treated {L}", [r for r in tr if r["L"] == L])
        line(f"info control {L}", [r for r in rows if r["L"] == L])
    line("info not treated (cheap side, model under 3x ask)", [r for r in rows if not r["tr"]])
    if len(tr) < MIN_TRADES:
        v = "NOT_ENOUGH_DATA"
    else:
        m1 = [r["net"] for r in tr if r["start"] < mid]
        m2 = [r["net"] for r in tr if r["start"] >= mid]
        pf = profit_factor([r["net"] for r in tr])
        v = "NOT_YET_FALSIFIED" if (m1 and m2 and sum(m1) > 0 and sum(m2) > 0 and pf >= 1.5) else "FALSIFIED"
    L_.append("VERDICT " + v)
    txt = "\n".join(L_)
    rp.write_text(txt)
    print(txt)


if __name__ == "__main__":
    D.mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == "games":
        kbo()
        npb()
    elif cmd == "homes":
        npb_homes()
    elif cmd == "fit":
        fit()
    elif cmd == "fetch":
        fetch()
    elif cmd == "run":
        run()
