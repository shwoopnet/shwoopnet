"""MADE-UP SOCDERIV fixture inputs for a second build (Testing Desk). NOT for the second builder to read: it carries the intended boundary of each case.
Usage: python3 make_socderiv_fixtures.py <out folder>. Everything is invented. Prices are whole cents. No result is meaningful (the field says so)."""
import calendar, gzip, json, os, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import socderiv as s

F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
BASE = calendar.timegm((2026, 10, 1, 12, 0, 0))
A8 = ["EPL", "LALIGA", "SERIEA", "BUNDESLIGA", "LIGUE1", "MLS", "LIGAMX", "BRASILEIRO"]
LAMS = [(1.4, 1.1), (1.5, 1.2), (1.6, 1.3), (1.5, 1.1), (1.4, 1.3)]


def cents(p): return max(1, min(99, int(round(p * 100))))


def quote(p, lo=1, hi=1, shift=0):
    m = cents(p) + shift
    return max(1, m - lo) / 100.0, min(99, m + hi) / 100.0


def game_specs(name):
    """-> {league: [game dict, oldest first]} per case."""
    def mk(n, **kw): return [dict(kw) for _ in range(n)]
    S = {}
    if name == "case_01": S = {lg: mk(50) for lg in A8[:3]}
    elif name == "case_02": S = {A8[0]: mk(50), A8[1]: mk(50), A8[2]: mk(49)}
    elif name == "case_03": S = {lg: mk(55, btts=(2, 2)) for lg in A8[:3]}
    elif name == "case_04": S = {lg: mk(55, btts=(2, 3)) for lg in A8[:3]}
    elif name == "case_05": S = {lg: [dict(fill=(i < 30)) for i in range(60)] for lg in A8[:5]}                       # 300 derivable, 150 filled
    elif name == "case_06":
        S = {lg: [dict(fill=(i < 30)) for i in range(60)] for lg in A8[:5]}; S[A8[5]] = [dict(fill=False)]                     # 301 derivable, 150 filled
    elif name in ("case_07", "case_08", "case_09"):
        tf, pf = {"case_07": (20, 10), "case_08": (20, 11), "case_09": (19, 0)}[name]
        S = {lg: mk(50) for lg in A8[:4]}; flat = [g for lg in A8[:4] for g in S[lg]]
        for i in range(tf): flat[i * 10]["edge"] = 15
        for i in range(pf): flat[i * 10 + 5 if pf else 0]["pert"] = 20
    elif name == "case_10": S = {lg: [dict(edge=15) if i < 10 else {} for i in range(70)] for lg in A8[:3]}             # oldest 10 per league beyond the 60 cap carry a big edge
    elif name == "case_11": S = {lg: [dict(close_min=(99, 100, 135, 136)[i % 4]) for i in range(60)] for lg in A8[:3]}
    elif name == "case_12": S = {lg: [dict(empty=i % 4) for i in range(60)] for lg in A8[:3]}; [g.update(tie_empty=True) for lg in A8[:3] for g in S[lg][:7]]
    elif name == "case_15": S = {lg: mk(50) for lg in A8[:3]}                                                                  # real ticker layout, efficient, 150 games
    elif name == "case_16":                                                                                                     # real ticker layout and the leg-shape edge cases
        S = {lg: mk(50) for lg in A8[:3]}
        S[A8[0]][0].update(codes=("CR", "CRU")); S[A8[0]][1].update(two_btts=True); S[A8[0]][2].update(no_btts=True); S[A8[0]][3].update(bad_tie=True)
    elif name == "case_13": S = {lg: mk(40, btts=(2, 3)) for lg in A8[:3]}                                                    # under 150 filled and over the cost line
    elif name == "case_14": S = {lg: [dict(fill=(i < 20)) for i in range(60)] for lg in A8[:3]}                           # under 150 filled and under half filled
    return S


def build_case(name, out):
    spec = s.load_cells()
    jl = s.build_lists(spec)
    ids = [r["id"] for r in jl["requests"] if r["id"].startswith("live_")]
    lists = {i: {"markets": [], "cursor": ""} for i in ids}
    games = []
    for lg, gl in game_specs(name).items():
        for i, g in enumerate(gl):
            ko = BASE + i * 3 * 3600 + A8.index(lg) * 600
            close = ko + g.get("close_min", 120) * 60; occ = ko + 180 * 60
            real = name in ("case_15", "case_16"); c1, c2 = g.get("codes", ("ARS", "LFC") if real else ("AAA", "BBB"))
            gk = ("26%s%02d%s%s" % (("SEP", "OCT", "NOV")[i // 28], i % 28 + 1, c1, c2)) if real else "26OCT%03dAAABBB" % i
            def M(series, sfx, **kw):
                return dict({"ticker": "%s-%s-%s" % (series, gk, sfx), "event_ticker": "%s-%s" % (series, gk), "open_time": F(close - 86400), "close_time": F(close), "occurrence_datetime": F(occ),
                             "expected_expiration_time": F(occ), "volume_fp": "10.00", "title": "MADE-UP", "strike_type": "greater", "result": "MADE-UP, never read"}, **kw)
            for sfx in (c1, c2, "DRAW" if g.get("bad_tie") else "TIE"): lists["live_KX%sGAME" % lg]["markets"].append(M("KX%sGAME" % lg, sfx, strike_type="custom" if not real else "structured"))
            for n_, kk in enumerate((0.5, 1.5, 2.5, 3.5, 4.5), 1): lists["live_KX%sTOTAL" % lg]["markets"].append(M("KX%sTOTAL" % lg, str(n_) if real else "T%s" % kk, floor_strike=kk))
            if not g.get("no_btts"):
                for sfx in (("BTTS", "BTTS2") if g.get("two_btts") else ("BTTS" if real else "YES",)): lists["live_KX%sBTTS" % lg]["markets"].append(M("KX%sBTTS" % lg, sfx, strike_type="custom"))
            for nm in ((c1 + "2", c2 + "2") if real else ("AAA2", "BBB2")): lists["live_KX%sTEAMTOTAL" % lg]["markets"].append(M("KX%sTEAMTOTAL" % lg, nm, floor_strike=1.5))
            games.append(dict(lg=lg, gk=gk, ko=ko, g=g, lam=LAMS[(i + A8.index(lg)) % len(LAMS)]))
    held = s.HELD_OUT_FROM + 7200
    if name == "case_01":   # one held-out game (closes after the window) that must never be sampled
        for sfx in ("AAA", "BBB", "TIE"):
            lists["live_KXEPLGAME"]["markets"].append(dict({"ticker": "KXEPLGAME-26NOV20HELDAAABBB-" + sfx, "event_ticker": "KXEPLGAME-26NOV20HELDAAABBB", "open_time": F(held - 86400), "close_time": F(held),
                "occurrence_datetime": F(held + 3600 - 7200 + 7200), "expected_expiration_time": F(held), "volume_fp": "1.00", "title": "MADE-UP", "strike_type": "custom", "result": "MADE-UP, never read"}))
    os.makedirs(os.path.join(out, name, "lists")); os.makedirs(os.path.join(out, name, "candles"))
    def mkrun(d, job, bodies):
        rows = []
        for i, r in enumerate(job["requests"]):
            if r["id"] in bodies:
                f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]])); rows.append({"index": i + 1, "id": r["id"], "page": 1, "status": 200, "file": f})
        json.dump({"job": job, "status": "complete", "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
    mkrun(os.path.join(out, name, "lists"), jl, lists)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        mkrun(tmp, jl, lists)
        gs, counts = s.games(spec, [tmp]); jc, _ = s.build_candles(spec, [tmp])
    by = {(g["league"], g["game"]): g for g in gs}
    cm = {}
    for G in games:
        sg = by.get((G["lg"], G["gk"]))
        if sg is None or G["g"].get("fill", True) is False: continue
        l1, l2 = G["lam"]; h, d_, a_ = s.p_winner(l1, l2); e = G["g"]
        price = {}
        for w in sg["winner"]: price[w] = d_ if w.endswith("-TIE") else (h if s.code(w) == sg["team1"] else a_)
        for t, kk in sg["totals"].items(): price[t] = s.over(l1 + l2, kk)
        near = min(sg["totals"], key=lambda t: abs(price[t] - 0.5))
        for t in sg["btts"]: price[t] = (1 - 2.718281828459045 ** -l1) * (1 - 2.718281828459045 ** -l2) - e.get("edge", 0) / 100.0
        for t, (tm, kk) in sg["teamtotals"].items(): price[t] = s.over(l1 if tm == sg["team1"] else l2, kk)
        for t, p in price.items():
            lo, hi = e.get("btts", (1, 1)) if t in sg["btts"] else (1, 1)
            shift = e.get("pert", 0) if t == near else 0
            cs = []
            for m in range(0, 13):
                b, a = quote(p, lo, hi, shift); empty = False
                if e.get("empty") is not None and m < 10:
                    v = e["empty"]
                    if t in sg["btts"] and v == 0: b, a = 0.0, 1.0
                    elif t in sg["btts"] and v == 1: b, a = 0.0, a
                    elif t in sg["btts"] and v == 2: b, a = b, 1.0
                    elif v == 3 and t in list(sg["totals"])[:3]: b, a = 0.0, 1.0
                if e.get("tie_empty") and t.endswith("-TIE"): b, a = 0.0, 1.0
                cs.append({"end_period_ts": sg["kickoff"] - 1800 - 60 * m, "yes_bid": {"close_dollars": "%.4f" % b}, "yes_ask": {"close_dollars": "%.4f" % a}, "volume_fp": "3.00"})
            cm[t] = cs
    bodies = {r["id"]: {"markets": [{"market_ticker": x, "candlesticks": cm[x]} for x in r["params"]["market_tickers"].split(",") if x in cm]} for r in jc["requests"]}
    mkrun(os.path.join(out, name, "candles"), jc, bodies)
    return counts


if __name__ == "__main__":
    out = sys.argv[1]
    for n in ["case_%02d" % i for i in range(1, 17)]:
        print(n, build_case(n, out))
