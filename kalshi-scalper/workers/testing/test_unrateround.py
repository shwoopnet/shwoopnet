"""Synthetic test for unrateround.py (made-up data, no Kalshi, no BLS). Run: python3 -W ignore test_unrateround.py"""
import calendar, csv, gzip, json, os, sys, tempfile, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import unrateround as u
u.VINTAGE_FROM = None            # the older tests use synthetic events from 2023; the vintage test at the end sets it
import kalshi_pull as kp

def mkrun(d, job, bodies):
    rows = []
    for i, r in enumerate(job["requests"]):
        if r["id"] in bodies:
            f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]]))
            rows.append({"id": r["id"], "status": 200, "file": f})
    json.dump({"job": job, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

jl = u.build_lists(); kp.check_job(jl); assert len(jl['requests']) == 4 and sum(r['max_pages'] for r in jl['requests']) == 8
random.seed(1)
with tempfile.TemporaryDirectory() as t:
    bls = os.path.join(t, "bls.csv"); lvl = 5.0
    with open(bls, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["year", "month", "unemployed", "labor_force"])
        for y in range(2009, 2027):
            for m in range(1, 13):
                lvl = max(3.0, lvl + random.gauss(0, 0.12)); w.writerow([y, m, round(lvl * 1600, 1), 160000])
    lv = u.levels(bls); sd, n = u.model_sd(lv); assert 0.05 < sd < 0.25 and n > 150, (sd, n)
    assert u.prev((2026, 1)) == (2025, 12)
    # probabilities: sums over a partition of strikes are 1
    mk = lambda ty, f, c: {"type": ty, "floor": f, "cap": c}
    ps = u.p_yes(mk("less", None, 4.3), 4.35, 0.1) + u.p_yes(mk("between", 4.3, 4.4), 4.35, 0.1) + u.p_yes(mk("greater", 4.4, None), 4.35, 0.1)
    assert abs(ps - 1) < 1e-9, ps
    j1 = jl
    # 40 events Feb 2023 .. (skip Jan), each with 3 markets around u0; the real outcome is drawn from the model
    markets = []; res_by_event = {}
    cl = lambda y, m: calendar.timegm((y, m, 5, 12, 30, 0))
    evs = [(y, m) for y in (2023, 2024, 2025, 2026) for m in range(1, 13) if (y, m) < (2026, 10)]
    f = lambda x: __import__("datetime").datetime.utcfromtimestamp(x).strftime("%Y-%m-%dT%H:%M:%SZ")
    for (y, m) in evs:
        e = "KXU3-%02d%s" % (y - 2000, calendar.month_abbr[m].upper()); u0 = lv[u.prev((y, m))]; hl = round(u0, 1)
        close = cl(y + (m == 12), m % 12 + 1)
        outcome = u0 + random.gauss(0, sd); head = round(outcome, 1)
        for ty, fl, cp in (("less", None, round(hl - 0.05, 1)), ("between", round(hl - 0.05, 1), round(hl + 0.05, 1)), ("greater", round(hl + 0.05, 1), None)):
            yes = (ty == "less" and head < cp) or (ty == "between" and fl <= head <= cp) or (ty == "greater" and head > fl)
            markets.append({"ticker": "%s-%s%s" % (e, ty[0].upper(), fl if ty != "less" else cp), "event_ticker": e, "close_time": f(close), "result": "yes" if yes else "no",
                            "strike_type": ty, "floor_strike": fl, "cap_strike": cp, "title": "Unemployment rate above"})
    d1 = os.path.join(t, "s1"); os.mkdir(d1); mkrun(d1, j1, {"live_KXU3": {"markets": markets}, "hist_KXU3": {"markets": []}, "live_KXUE": {"markets": []}, "hist_KXUE": {"markets": []}})
    ev = u.events_from(d1); assert all(u.event_month(e)[1] != 1 for e in ev)          # Januaries 2023 to 2026 excluded: 4
    assert len(ev) == len(evs) - 4, (len(ev), len(evs))
    assert u.events_report(d1)["label"].startswith("n = ")
    j2 = u.build_s2(d1, bls); kp.check_job(j2); assert 0 < len(j2["requests"]) <= 3 * len(ev) and all(r["params"]["end_ts"] < u.CUTOFF + 86400 for r in j2["requests"])
    # candles at the entry hour: priced at the model's probability + noise, always two-sided
    cands = {}
    for e, ms in ev.items():
        u0 = lv[u.prev(u.event_month(e))]; et = u.entry_ts(ms)
        for m in ms:
            p = u.p_yes(m, u0, sd) or 0.5; a = min(0.95, max(0.05, p + 0.02)); b = max(0.02, a - 0.03)
            cands[m["ticker"]] = [{"end_period_ts": et, "yes_bid": {"close_dollars": "%.4f" % b}, "yes_ask": {"close_dollars": "%.4f" % a}}]
    d2 = os.path.join(t, "s2"); os.mkdir(d2); mkrun(d2, j2, {r["id"]: {"markets": [{"market_ticker": r["id"], "candlesticks": cands[r["id"]]}]} for r in j2["requests"] if r["id"] in cands})
    out = u.score(d1, [d2], bls)
    assert out["trades"] >= 30 and out["label"] in ("on the paper list (unproven)", "off the list (failed the screen)"), out
    assert out["first_half"]["n"] + out["second_half"]["n"] == out["trades"] and "34 percent" in out["haircut_line"]
    # under 30 events -> no evidence
    d1b = os.path.join(t, "s1b"); os.mkdir(d1b); mkrun(d1b, j1, {"live_KXU3": {"markets": markets[:30]}, "hist_KXU3": {"markets": []}})
    assert u.events_report(d1b)["label"].startswith("no evidence at n = ")
    # held-out: a market closing on or after the cutoff is never an event
    late = dict(markets[0], title='Unemployment rate', event_ticker="KXU3-26NOV", close_time=f(u.CUTOFF + 86400)); d1c = os.path.join(t, "s1c"); os.mkdir(d1c); mkrun(d1c, j1, {"live_KXU3": {"markets": [late]}})
    assert u.events_from(d1c) == {}
    # stats: win/loss arithmetic
    s = u.stats([{"price": 0.5, "win": True}, {"price": 0.5, "win": False}]); assert abs(s["net"] + 2 * u.fee(0.5)) < 1e-3 and abs(s["pf"] - (0.5 - u.fee(0.5)) / (0.5 + u.fee(0.5))) < 1e-3
# vintage rule (Desk B's note): only events whose u0 month is 2026-01 or later are admissible, the rest are dropped and counted
with tempfile.TemporaryDirectory() as dv:
    mkrun(dv, jl, {"live_KXU3": {"markets": markets}, "hist_KXU3": {"markets": []}, "live_KXUE": {"markets": []}, "hist_KXUE": {"markets": []}})
    u.VINTAGE_FROM = None; all_n = len(u.events_from(dv)); u.VINTAGE_FROM = (2026, 1); kept = u.events_from(dv)
    assert all(u.prev(u.event_month(e)) >= (2026, 1) for e in kept) and 0 < len(kept) < all_n and u.events_from.excluded_for_vintage == all_n - len(kept)
    rep = u.events_report(dv); assert rep["excluded_u0_not_first_published"] == all_n - len(kept) and rep["label"].startswith("no evidence at n = %d" % len(kept)), rep
print("unrateround synthetic tests passed")
