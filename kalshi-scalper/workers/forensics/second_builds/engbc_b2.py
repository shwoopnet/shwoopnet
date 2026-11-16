#!/usr/bin/env python3
"""ENGINE1 BATCH C (ENGC1ETHMOM fa0c08a4, ENGC2OIACC 2a6d51f5, ENGC3TOD 07a64f42, ENGC4GOLDX ef0442d7) INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026). Written from the four spec files (commit 75f4affed), the ENGB4XBTC conventions and Desk A's rulings of 2026-11-16 23:22Z (all eight confirmed) ONLY. Desk A's engine1_batchc.py, its runner and any print were not opened before this file was committed.
Features: C1 ethmom3 and C4 goldmom3 = mid(e) - mid(e - 180) of the feature market (KXETH15M, KXGOLD15M) with the SAME close_ts, mid = (bid + ask) / 2 of whatever the candle carries, both candles present with a bid and an ask, NO two sided test; classes up, flat, down by sign with 1e-12. C1 targets the 18 series without ETH, C4 the 9 crypto series (BTC, ETH, DOGE, XRP, BNB, HYPE, SOL, NEAR, ZEC). C2 oiacc = (oi(e) - oi(e - 180)) - (oi(e - 180) - oi(e - 360)), all three candles present with a non-null open interest, on all 19 series. C3 todct = the America/Chicago clock of e in 4 bands (hour // 6), CDT (UTC-5) for the whole development window; every entry has a band. The TARGET entry candle must be two sided with the side ask 5 to 94 cents (as always).
Everything else as engb4xbtc_b2.py (SEARCH gate with 3 a day, VALIDATE bar, day clustered one sided p, BH). m lines: 6,290,660 + the spec's own tries, and the whole-batch line 'carried + all of batch C' = 6,290,660 + 1,201,824.
usage: python3 -I engbc_b2.py <C1|C2|C3|C4> <archive_extract.sqlite> | python3 -I engbc_b2.py --selftest"""
import sys, os, collections, calendar, sqlite3, multiprocessing, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_rank_b2 as P
import engb4xbtc_b2 as E
CARRIED = 6290660; BATCH_TRIES = 303264 + 320112 + 426816 + 151632
CRYPTO9 = ["KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M", "KXBNB15M", "KXHYPE15M", "KXSOL15M", "KXNEAR15M", "KXZEC15M"]
SPEC = {"C1": {"tries": 303264, "feat": "KXETH15M", "classes": ("up", "flat", "down")}, "C2": {"tries": 320112, "feat": None, "classes": ("up", "flat", "down")},
        "C3": {"tries": 426816, "feat": None, "classes": ("ct00", "ct06", "ct12", "ct18")}, "C4": {"tries": 151632, "feat": "KXGOLD15M", "classes": ("up", "flat", "down")}}
def cross_move(fm, e):
    if fm is None: return None
    q, p = fm.c.get(e), fm.c.get(e - 180)
    if q is None or p is None or None in (q[0], q[1], p[0], p[1]): return None
    return (q[0] + q[1]) / 2 - (p[0] + p[1]) / 2
def oiacc(m, e):
    a, b, c = m.c.get(e), m.c.get(e - 180), m.c.get(e - 360)
    if a is None or b is None or c is None or a[4] is None or b[4] is None or c[4] is None: return None
    return (a[4] - b[4]) - (b[4] - c[4])
def central_band(e):
    lt = datetime.datetime.fromtimestamp(e - 5 * 3600, datetime.timezone.utc)      # CDT, UTC-5, for the whole development window (DST ends 2026-11-01)
    return "ct%02d" % (lt.hour // 6 * 6)
def feature_class(mode, m, e, fm):
    if mode in ("C1", "C4"):
        x = cross_move(fm, e); return None if x is None else P.klass(x)
    if mode == "C2":
        x = oiacc(m, e); return None if x is None else P.klass(x)
    return central_band(e)
def work(args):
    mode, ser, mk, fby, ls = args; res = {}; nof = 0
    for B in E.BUCKETS:
        for sr in E.SIDES:
            for m in mk:
                en = E.entries(m, B, sr)
                if en is None: continue
                side, ca = en; e = m.close - B
                cls = feature_class(mode, m, e, fby.get(m.close) if fby else None)
                if cls is None: nof += 1; continue
                ph = "S" if m.close < ls else "V"; key = (B, sr, ca // 5, cls, ph); g = res.get(key)
                if g is None: g = res[key] = {"n": 0, **{ex: ([], [], []) for ex in E.EXITS}}
                g["n"] += 1; n1 = E.nets(m, B, side, 0.01); n2 = E.nets(m, B, side, 0.02)
                for ex in E.EXITS:
                    if n1[ex] is not None: g[ex][0].append(n1[ex]); g[ex][2].append((m.close, n1[ex]))
                    if n2[ex] is not None: g[ex][1].append(n2[ex])
    return ser, res, nof
def selftest():
    C = 43200 * 400 + 14 * 3600; e = C - 360                      # 14:00 UTC = 09:00 CDT, band ct06
    assert central_band(e) == "ct06" and central_band(C - C % 86400 + 11 * 3600) == "ct06" and central_band(C - C % 86400 + 10 * 3600 + 59 * 60) == "ct00" and central_band(C - C % 86400 + 23 * 3600) == "ct18"
    A = P.Mkt("A", "X", C, "yes", {e: (0.5, 0.52, 0, 0, 130), e - 180: (0.5, 0.52, 0, 0, 100), e - 360: (0.5, 0.52, 0, 0, 80)})
    assert oiacc(A, e) == (130 - 100) - (100 - 80) == 10 and P.klass(10) == "up"
    del A.c[e - 360]; assert oiacc(A, e) is None
    F = P.Mkt("F", "KXETH15M", C, "yes", {e: (0.50, 0.54, 0, 0, 0), e - 180: (0.50, 0.52, 0, 0, 0)}); assert abs(cross_move(F, e) - 0.01) < 1e-12 and cross_move(None, e) is None
    F.c[e - 180] = (None, 0.52, 0, 0, 0); assert cross_move(F, e) is None
    F.c[e - 180] = (0.60, 0.62, 0, 0, 0); F.c[e] = (0.59, 0.61, 0, 0, 0); assert abs(cross_move(F, e) + 0.01) < 1e-12 and P.klass(cross_move(F, e)) == "down"
    F.c[e - 180] = (0.5, 0.52, 0, 0, 0); F.c[e] = (0.5, 0.52, 0, 0, 0); assert P.klass(cross_move(F, e)) == "flat"      # locked or crossed candles still carry a mid
    assert 303264 + 320112 + 426816 + 151632 == 1201824 == BATCH_TRIES and CARRIED + BATCH_TRIES == 7492484
    print("selftest ok")
def main(a):
    if a[0] == "--selftest": return selftest()
    mode = a[0]; sp = SPEC[mode]; db = sqlite3.connect("file:%s?mode=ro" % a[1], uri=True); ms = {}
    for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market"): ms[tk] = P.Mkt(tk, ser, close, res, {})
    for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
        if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
    mk = collections.defaultdict(list)
    for m in sorted(ms.values(), key=lambda m: (m.close, m.tk)): mk[m.ser].append(m)
    allser = [s for s in sorted(P.LAST_SEARCH) if s in mk]
    targets = [s for s in allser if s != "KXETH15M"] if mode == "C1" else [s for s in CRYPTO9 if s in mk] if mode == "C4" else allser
    fby = {m.close: m for m in mk[sp["feat"]]} if sp["feat"] else None
    ls_of = {s: calendar.timegm(tuple(int(x) for x in P.LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in targets}
    tries = sp["tries"]; m_spec = CARRIED + tries; m_batch = CARRIED + BATCH_TRIES
    print("mode", mode, "targets", len(targets), "rules", len(targets) * len(E.BUCKETS) * 18 * 4 * len(sp["classes"]) * 6, "spec tries", tries, "m (carried + spec)", m_spec, "m (carried + all of batch C)", m_batch, flush=True)
    with multiprocessing.Pool(min(8, os.cpu_count() or 2)) as pool: out = {s: (r, n) for s, r, n in pool.map(work, [(mode, s, mk[s], fby, ls_of[s]) for s in targets], chunksize=1)}
    rows = []; ns = 0; nofeat = sum(v[1] for v in out.values())
    for s in targets:
        sc = [m.close for m in mk[s] if m.close < ls_of[s]]; vc = [m.close for m in mk[s] if m.close >= ls_of[s]]
        sdays = (max(sc) - min(sc)) / 86400 + 1; vdays = (max(vc) - ls_of[s]) / 86400; res = out[s][0]
        for (B, sr, band, cls, ph), g in res.items():
            if ph != "S" or g["n"] < 100: continue
            v = res.get((B, sr, band, cls, "V"))
            for ex in E.EXITS:
                x1, x2, _ = g[ex]
                if len(x1) < 100 or E.pfv(x1) < 1.3 or E.pfv(x2) < 1.0 or len(x1) / sdays < 3: continue
                ns += 1
                if v is None or v["n"] < 100: continue
                y1, y2, cn = v[ex]
                if len(y1) < 100 or E.pfv(y1) < 1.3 or E.pfv(y2) < 1.0: continue
                z, p, k = E.pval(cn); n = len(y1); rows.append({"series": s, "bucket": B, "side": sr, "band": band, "class": cls, "exit": ex, "n": n, "pf1": E.pfv(y1), "pf2": E.pfv(y2), "days": k, "p": p})
    print("no-feature skips (market-bucket windows)", nofeat, "| SEARCH passes (bar + 3 a day)", ns, "VALIDATE passes", len(rows))
    for lab, mm in (("carried + spec", m_spec), ("carried + all of batch C", m_batch)):
        k, o = E.bh([r["p"] for r in rows], mm); print("BH m", mm, "(%s)" % lab, "survivors", k)
    rows.sort(key=lambda r: (r["series"], r["bucket"], r["band"], r["side"], r["class"], r["exit"]))
    lines = ["series bucket band side class exit n pf1 pf2 days p"] + ["%s %d %d %s %s %s %d %.12f %.12f %d %.12e" % (r["series"], r["bucket"], r["band"], r["side"], r["class"], r["exit"], r["n"], r["pf1"], r["pf2"], r["days"], r["p"]) for r in rows]
    open(os.environ.get("OUTLIST", "/dev/null"), "w").write("\n".join(lines) + "\n")
if __name__ == "__main__": main(sys.argv[1:])
