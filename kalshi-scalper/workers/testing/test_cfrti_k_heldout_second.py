"""Synthetic test for cfrti_k_heldout_second.py (Testing Desk second build). MADE-UP data only: invented perp mids, quotes and results; no Kalshi, no real file. Expectations are the hand case CFRTI_K_HELD_HAND_CASE.md.
Run: python3 -W ignore test_cfrti_k_heldout_second.py"""
import calendar, gzip, json, math, os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfrti_k_heldout_second as r
import scorekit as k

A = 0.0005; SD = A * math.sqrt(10 / 9) * math.sqrt(4 / 3)
T = lambda d, h, m: calendar.timegm((2026, 11, d, h, m, 0))
iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
def perp_for(C, z, drop_open=False, keep=11, flat=False):
    m = {}
    for j in range(keep):
        m[C - 120 - 60 * j] = 100.0 if (flat or j % 2 == 0) else 100.0 * math.exp(A)
    if not drop_open: m[C - 900] = 100.0 if flat else 100.0 * math.exp(-z * SD)
    return m
def cs(ts, bid, ask): return {"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % bid}, "yes_ask": {"close_dollars": "%.4f" % ask}, "volume_fp": "1.00"}
def mkrun(d, bodies):
    os.makedirs(d); rows = []
    for i, (rid, body) in enumerate(bodies):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(body)); rows.append({"id": rid, "page": 1, "status": 200, "file": f})
    json.dump({"job": {}, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

# --- pure pieces ---
assert abs(r.phi(0) - 0.5) < 1e-15
why, sd, z = r.signal(T(14, 0, 15), perp_for(T(14, 0, 15), 1.0)); assert why is None and abs(sd - SD) < 1e-12 and abs(z - 1.0) < 1e-9, (why, sd, z)
C = T(14, 0, 15)
assert r.signal(C, perp_for(C, 1.0, drop_open=True))[0] == "no opening minute"
assert r.signal(C, perp_for(C, 1.0, keep=6))[0].startswith("fewer than 6")          # 5 changes
assert r.signal(C, perp_for(C, 1.0, keep=7))[0] is None                              # exactly 6 changes
assert r.signal(C, perp_for(C, 1.0, flat=True))[0] == "sd zero"
# decide: the YES test comes first; edge exactly 5c passes by the 1e-9; spread 3c passes, 4c fails; band edges
r_, why = r.decide(0.20, 0.22, 0.27); assert r_[0] == "yes" and abs(r_[1] - 0.22) < 1e-12
assert r.decide(0.20, 0.22, 0.269)[1] == "edge under 5c"
r_, why = r.decide(0.72, 0.73, 0.67); assert r_[0] == "no" and abs(r_[1] - 0.28) < 1e-12          # YES ask .73 out of band, NO ask .28
assert r.decide(0.18, 0.21, 0.9)[0] is not None and r.decide(0.18, 0.22, 0.9)[1] == "spread above 3c"
assert r.decide(0.29, 0.30, 0.9)[0] is not None and r.decide(0.30, 0.31, 0.9)[0] is None
assert r.decide(0.04, 0.05, 0.9)[0] is not None and r.decide(0.03, 0.04, 0.9)[0] is None
# ran flag
assert r.ran_flag("no", 0.10, {"bid": 0.87, "ask": 0.88}) is True and r.ran_flag("no", 0.10, {"bid": 0.90, "ask": 0.91}) is False
assert r.ran_flag("yes", 0.10, {"bid": 0.10, "ask": 0.11}) is True and r.ran_flag("yes", 0.10, None) is None and r.ran_flag("yes", 0.10, {"bid": None, "ask": None}) is None

# --- end to end ---
W = [  # id, close, z, perp kwargs, decision quotes, next quotes, result
    ("H1", T(14, 0, 0), 1.0, {}, (.90, .91), (.90, .91), "no"), ("H2", T(14, 0, 30), -1.0, {}, (.09, .10), (.09, .10), "no"), ("H3", T(14, 0, 45), 1.0, {}, (.90, .91), (.87, .88), "void"),
    ("H4", T(14, 1, 0), 0.5, {}, (.70, .71), (.70, .71), "yes"), ("H5", T(14, 1, 15), 1.0, {}, (.90, .94), None, "no"), ("H6", T(14, 1, 30), 1.0, {"drop_open": True}, (.90, .91), None, "no"),
    ("H7", T(14, 1, 45), 1.0, {"keep": 6}, (.90, .91), None, "no"), ("H8", T(14, 2, 0), 1.0, {}, None, None, "no"), ("H9", T(14, 2, 15), 1.0, {"flat": True}, (.90, .91), None, "no"),
    ("N1", T(10, 0, 15), 1.0, {}, (.90, .91), (.90, .91), "no"), ("D1", T(6, 0, 15), 1.0, {}, (.90, .91), None, "no"),
    ("B0", T(8, 23, 45), 1.0, {}, (.90, .94), None, "no"), ("B1", T(9, 0, 0), 1.0, {}, (.90, .94), None, "no"), ("B2", T(13, 23, 45), 1.0, {}, (.90, .94), None, "no")]
with tempfile.TemporaryDirectory() as t:
    mrows, crows, perp = [], [], {}
    for name, C, z, kw, dq, nq, res in W:
        tk = "KXBTC15M-%s" % name
        m = {"ticker": tk, "event_ticker": "KXBTC15M-EV" + name, "open_time": iso(C - 900), "close_time": iso(C), "result": res, "strike_type": "greater_or_equal", "floor_strike": 100000.0, "volume_fp": "5.00"}
        if name == "H1": m["rules_primary"] = "If the simple average of the sixty seconds of CF Benchmarks' BRTI before the close is at least the simple average of the sixty seconds of BRTI before the open, then the market resolves to Yes."
        mrows.append(m)
        cl = []
        if dq: cl.append(cs(C - 120, *dq))
        if nq: cl.append(cs(C - 60, *nq))
        crows.append({"market_ticker": tk, "candlesticks": cl})
        perp.update(perp_for(C, z, **kw))
    pcs = [{"end_period_ts": ts, "bid": {"close": "%.4f" % (v - 0.5)}, "ask": {"close": "%.4f" % (v + 0.5)}} for ts, v in sorted(perp.items())]
    lists, cands, prun = os.path.join(t, "lists"), os.path.join(t, "cands"), os.path.join(t, "perp")
    mkrun(lists, [("L1", {"markets": mrows})]); mkrun(cands, [("C1", {"markets": crows})]); mkrun(prun, [("P1", {"market_ticker": "KXBTCPERP", "candlesticks": pcs})])
    mk, cc, pc = k.markets([lists]), k.candles([cands]), k.candles([prun])
    held, g = r.build(mk, cc, r.perp_mids(pc))
    assert g["windows_listed"] == 14 and g["closes_before_2026-11-14_not_read"] == 5 and g["heldout_windows"] == 9, g          # B0 08 Nov 23:45 not read, B1 09 Nov 00:00 and B2 13 Nov 23:45 not blind, H1 14 Nov 00:00 held-out
    assert g["traded_heldout"] == 3 and g["void_traded"] == 1 and "traded_not_blind" not in g, g
    assert g["edge under 5c"] == 1 and g["spread above 3c"] == 1 and g["no opening minute"] == 1 and g["fewer than 6 changes"] == 1 and g["no decision candle"] == 1 and g["sd zero"] == 1, g
    assert [x["ticker"][-2:] for x in held] == ["H1", "H2", "H3"] and [x["side"] for x in held] == ["no", "yes", "no"] and [x["ran"] for x in held] == [False, False, True]
    f = lambda p: 0.07 * p * (1 - p)
    nets = [0.9 - f(0.1), -0.1 - f(0.1), -f(0.1)]
    gr = r.group_report(held)
    reg = gr["registered_line_unrounded_fee"]
    assert reg["n"] == 3 and abs(reg["net"] - 0.7811) < 1e-9 and abs(reg["pf"] - nets[0] / (-nets[1] - nets[2])) < 1e-12 and abs(reg["pf"] - 7.9369) < 5e-5 and abs(reg["mean"] - 0.7811 / 3) < 1e-9 and abs(reg["win_rate"] - 1 / 3) < 1e-12
    r.MIN_ROWS = 3
    assert gr["LABEL"] == "NOT_ENOUGH_DATA, n = 3", gr["LABEL"]          # computed before MIN_ROWS was lowered: n 3 < 50
    assert r.group_report(held)["LABEL"].startswith("PASS")
    lb = gr["line_b_ran_rows_dropped"]
    assert lb["rows_with_a_next_candle"] == 3 and lb["ran_rows"] == 1 and abs(lb["ran_share"] - 1 / 3) < 1e-12 and lb["n_non_ran"] == 2 and abs(lb["pf_non_ran"] - 0.8937 / 0.1063) < 1e-3 and abs(lb["pf_non_ran"] - 8.4073) < 5e-4, lb
    ha = gr["haircut_a_random_34pct_drop"]
    allowed = {0.0, nets[0] / -nets[2] * -1 if False else 0.8937 / 0.0063, 0.8937 / 0.1063}
    assert ha["drop_count_per_draw"] == 1 and ha["draws"] == 1000 and any(abs(ha["median_pf"] - a) < 1e-3 for a in allowed) and any(abs(ha["p5_pf"] - a) < 1e-3 for a in allowed) and any(abs(ha["p95_pf"] - a) < 1e-3 for a in allowed), ha
    import random as _rnd, statistics as _st
    _g = _rnd.Random(20261114); _p = []; _n = [x for x in nets]
    for _ in range(1000):
        _drop = set(_g.sample(range(3), 1)); _p.append(k.pf([v for i, v in enumerate(_n) if i not in _drop]) or 0.0)
    _p.sort(); assert abs(ha["median_pf"] - _st.median(_p)) < 1e-9 and abs(ha["p5_pf"] - _p[49]) < 1e-9 and abs(ha["p95_pf"] - _p[949]) < 1e-9          # independent replica of the seeded draws and nearest-rank percentiles
    assert gr["INFORMATION_rounded_up_fee"]["net"] != reg["net"]
    rows10 = [dict(held[0], win=(i % 3 == 0), price=0.1 + 0.02 * i) for i in range(10)]          # ten distinct rows: the seeded draws are visible
    _g = _rnd.Random(20261114); _q = []; _nn = [r.net(x) for x in rows10]
    for _ in range(1000):
        _d = set(_g.sample(range(10), 3)); _q.append(k.pf([v for i, v in enumerate(_nn) if i not in _d]) or 0.0)
    _q.sort(); h10 = r.haircut_a(rows10)
    assert h10["drop_count_per_draw"] == 3 and abs(h10["median_pf"] - _st.median(_q)) < 1e-9 and abs(h10["p5_pf"] - _q[49]) < 1e-9 and abs(h10["p95_pf"] - _q[949]) < 1e-9 and _q[49] < _q[949], h10
    # replay and stale-ask on synthetic R6 polls: H1 only
    t0 = held[0]["t0"]
    polls = {held[0]["ticker"]: [{"t": t0 - 1, "yes_bids": [(0.80, 5.0)], "no_bids": []}, {"t": t0 + 6.5, "yes_bids": [(0.90, 5.0)], "no_bids": []}]}
    rp = r.replay_lines(held, polls)
    assert rp["+2 s"]["filled"] == 0 and rp["+6 s"]["filled"] == 1 and rp["+6 s"]["of_signals"] == 3 and abs(rp["+6 s"]["net"] - (0.9 - f(0.1))) < 1e-9, rp
    assert rp["rows_with_a_book_at_decision"] == 1 and rp["ask_not_on_the_book"] == 1 and "NO exchange-time offset" in rp["clock"], rp
    assert r.replay_lines(held, None).startswith("NOT COMPUTED")
    assert not any(x["ticker"].endswith(("N1", "B1", "B2", "B0", "D1")) for x in held)          # nothing before 2026-11-14T00:00Z is read
    # rules text check
    assert "simple average of the sixty seconds" in r.check_rules_text([lists])
    # the full read: refused before READ_DATE; committed marker; local marker; NOT_ENOUGH_DATA does not spend the read
    lm = os.path.join(t, "local.marker"); mkf = os.path.join(t, "REG.md"); open(mkf, "w").write("x\nREAD-ONCE MARKER: not yet read.\n")
    try: r.heldout_read(mkf, [lists], [cands], [prun], now=r.READ_DATE - 1, local_marker=lm); assert 0
    except SystemExit as e: assert "READ_DATE" in str(e)
    assert not os.path.exists(lm)
    r.MIN_ROWS = 50
    ne = r.heldout_read(mkf, [lists], [cands], [prun], now=r.READ_DATE + 1, local_marker=lm)
    assert ne == {"NOT_ENOUGH_DATA": "n = 3"} and not os.path.exists(lm)          # only the count; the read is not spent
    r.MIN_ROWS = 3
    full = r.heldout_read(mkf, [lists], [cands], [prun], now=r.READ_DATE + 1, local_marker=lm)
    assert os.path.exists(lm) and "HELD-OUT READ MADE" in open(lm).read() and full["HELDOUT"]["LABEL"].startswith("PASS") and "NOT_BLIND" not in " ".join(full)
    try: r.heldout_read(mkf, [lists], [cands], [prun], now=r.READ_DATE + 2, local_marker=lm); assert 0
    except SystemExit as e: assert "already made" in str(e)
    open(mkf, "w").write("READ-ONCE MARKER: READ ON 2026-11-20, commit abc\n")
    try: r.heldout_read(mkf, [lists], [cands], [prun], now=r.READ_DATE + 1, local_marker=os.path.join(t, "l2")); assert 0
    except RuntimeError as e: assert "already read" in str(e)
    # empty and odd results stop the run naming the window; a HELDOUT_ folder is refused; a wrong rules text stops
    try: r.build({"x": {"series": "KXBTC15M", "close": T(14, 5, 0), "result": "", "event": "e", "floor": 1.0}}, {}, {}); assert 0
    except SystemExit as e: assert "window x" in str(e)
    try: r.build({"x": {"series": "KXBTC15M", "close": T(14, 5, 0), "result": "scalar", "event": "e", "floor": 1.0}}, {}, {}); assert 0
    except SystemExit as e: assert "window x" in str(e) and "scalar" in str(e)
    hl = os.path.join(t, "HELDOUT_x"); os.makedirs(hl)
    try: r.heldout_read(mkf, [hl], [cands], [prun], now=r.READ_DATE + 1, local_marker=os.path.join(t, "l3")); assert 0
    except (SystemExit, RuntimeError): pass
    bad = os.path.join(t, "badlists"); mrows[0]["rules_primary"] = "The strike is something else entirely."; mkrun(bad, [("L1", {"markets": mrows})])
    try: r.check_rules_text([bad]); assert 0
    except SystemExit as e: assert "STOP" in str(e)
r.MIN_ROWS = 50
# label ladder on UNROUNDED figures: PASS / NO CALL / FAIL; under 50 only NOT_ENOUGH_DATA
mk_f = lambda n, pf, mean: {"n": n, "pf": pf, "mean": mean}
assert r.label(mk_f(50, 1.3, 0.01)).startswith("PASS") and r.label(mk_f(50, 1.2999999999, 0.01)).startswith("PASS") and r.label(mk_f(50, float("inf"), 0.2)).startswith("PASS")          # inside 1e-9
assert r.label(mk_f(50, 1.2999, 0.01)).startswith("NO CALL") and r.label(mk_f(50, 1.0, 0.0)).startswith("NO CALL") and r.label(mk_f(50, 1.0 - 1e-10, 0.0)).startswith("NO CALL") and r.label(mk_f(50, None, None)).startswith("NO CALL")
assert r.label(mk_f(50, 1.5, 0.0)).startswith("NO CALL")          # the card says a mean above 0: PF 1.5 with mean 0 cannot happen, but the label does not call PASS without it
assert r.label(mk_f(50, 0.9999, -0.01)).startswith("FAIL") and "CLOSED FOR GOOD" in r.label(mk_f(50, 0.5, -0.1))
assert r.label(mk_f(49, 2.0, 0.1)) == "NOT_ENOUGH_DATA, n = 49" and r.label(mk_f(30, 0.5, -0.1)) == "NOT_ENOUGH_DATA, n = 30"
print("test_cfrti_k_heldout_second: all checks passed")
