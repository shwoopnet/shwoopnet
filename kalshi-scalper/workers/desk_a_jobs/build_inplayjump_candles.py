#!/usr/bin/env python3
"""INPLAYJUMP stage 2 (Amendments 2 and 3): candle job files from the INPLAYJUMP_LISTS answers. Offline: sends nothing. NO window is anchored on the close; nothing is shortened from the end.
  clock families (e-soccer, table tennis, e-basketball):  window = S - 70 minutes (S = the ticker's US Eastern start; the 70 serves PREMOVE as well, Head 19:04Z) forward to the close
      python3 -I build_inplayjump_candles.py clock <INPLAYJUMP_SERIES.json> <lists run folder> <outdir>
  tennis (ITF, challenger), pass 1: HOURLY candles from the market's OPEN forward to the close (Amendment 2, point 2)
      python3 -I build_inplayjump_candles.py tennis_hourly <INPLAYJUMP_SERIES.json> <lists run folder> <outdir>
  tennis, pass 2: minute candles from 30 minutes before the first hour that is not provably empty, forward to the close (Amendment 3's skip test, see skip_start)
      python3 -I build_inplayjump_candles.py tennis_minutes <INPLAYJUMP_SERIES.json> <lists run folder> <outdir> <hourly answers folder> <scorekit dir>
  tennis, plain pull (every minute from the open; the same decisions as the two pass retrieval):
      python3 -I build_inplayjump_candles.py tennis_plain <INPLAYJUMP_SERIES.json> <lists run folder> <outdir>
  python3 -I build_inplayjump_candles.py selftest
Development matches only (market closes inside the family's development window; the Tie contract never). Contracts of consecutive matches (by start, then ticker) are batched so that tickers <= 100 and (window minutes x tickers) <= 9,000
(one batched request has ONE time range for all its tickers). At most 380 requests a job file (the 200 MB run cap). Prints the request count per family. The close is used only to decide WHICH matches are in the development window and where a window ENDS."""
import gzip, json, os, sys, calendar, time, re, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "desk_a_verify"))
from inplayjump import clock_start
def iso_ts(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def read_lists(folder):
    man = json.load(open(os.path.join(folder, "manifest.json"))); mk = {}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row: continue
        b = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            c, o = iso_ts(m.get("close_time") or ""), iso_ts(m.get("open_time") or "")
            if m.get("ticker") and c: mk[m["ticker"]] = dict(series=m["ticker"].split("-")[0], event=m.get("event_ticker", ""), close=c, open=o)     # the result field is NOT read; no list is filtered on it
    return mk
def skip_start(hours, tickers):
    """Amendment 3. hours: {ticker: [(end_ts, bid_high, bid_low, bid_close, ask_high, ask_low, ask_close)]} sorted hourly candles from the open (None for a missing price).
    Hour H (the i-th candle) is SKIPPED only if, for EVERY contract, (bid range over {bid_high_H, bid_low_H, bid_close_{H-1}}) + (ask range over {ask_high_H, ask_low_H, ask_close_{H-1}}) < 0.20 and hour H-1 has a two-sided close; the first hour after the open is never skipped;
    a missing or one-sided hour is never skipped. Returns the end_ts of the START of the minute window: 30 minutes before the first hour that is not skipped (None if every hour is skipped)."""
    ends = sorted({h[0] for hs in hours.values() for h in hs}); by = {tk: {h[0]: h for h in hs} for tk, hs in hours.items()}
    def rng(vals): return (max(vals) - min(vals)) if all(v is not None for v in vals) else None
    for i, e in enumerate(ends):
        if i == 0: return e - 3600 - 1800
        ok = True
        for tk in tickers:
            h, p = by.get(tk, {}).get(e), by.get(tk, {}).get(ends[i - 1])
            if h is None or p is None or p[3] is None or p[6] is None or h[1] is None or h[2] is None or h[4] is None or h[5] is None: ok = False; break
            r = rng([h[1], h[2], p[3]]); a = rng([h[4], h[5], p[6]])
            if r is None or a is None or r + a >= 0.20 - 1e-12: ok = False; break
        if not ok: return e - 3600 - 1800
    return None
def pack(items, lead_of, reqs, per, fam, period, interval_minutes):
    """items: [(ticker, start_ts, end_ts)] sorted; greedy packs; request window = min start to max end."""
    cur = []
    def flush(cur):
        reqs.append(dict(id="c%05d" % len(reqs), path="/markets/candlesticks", params={"market_tickers": ",".join(t for t, _, _ in cur), "start_ts": min(s for _, s, _ in cur), "end_ts": max(e for _, _, e in cur), "period_interval": period})); per[fam] += 1
    for it in items:
        trial = cur + [it]; span = (max(e for _, _, e in trial) - min(s for _, s, _ in trial)) / 60.0 / interval_minutes
        if cur and (len(trial) > 100 or span * len(trial) > 9000): flush(cur); cur = [it]
        else: cur = trial
    if cur: flush(cur)
def write(reqs, outdir, name, purpose):
    os.makedirs(outdir, exist_ok=True); n = 0
    for i in range(0, len(reqs), 380):
        ch = reqs[i:i + 380]; n += 1
        tk = sorted({t for r in ch for t in r["params"]["market_tickers"].split(",")}); sers = sorted({t.split("-")[0] for t in tk})
        job = {"job_id": "%s%d" % (name, n), "owner": "DESK_A", "registration": "kalshi-scalper/workers/inplayjump/INPLAYJUMP_REGISTRATION.md", "purpose": "%s (part %d)" % (purpose, n)[:400],
               "heldout": "none: development windows only", "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
               "series_allowlist": sers, "ticker_allowlist": tk, "max_requests": len(ch), "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
               "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out; three in a row end the run; no other address, no proxy, no retry around a refusal"}, "requests": ch}
        json.dump(job, open(os.path.join(outdir, "%s%d.json" % (name, n)), "w"), indent=1)
    return n
def families(S, mk, want_clock):
    for f in S["families_ranked_by_events"]:
        if (f["in_play"] == "clock") != want_clock: continue
        lo, hi = iso_ts(f["development"]["closes_from"]), iso_ts(f["development"]["closes_before"])
        yield f, [(t, m) for t, m in mk.items() if m["series"] in f["series"] and lo <= m["close"] < hi and not t.endswith("-TIE")]
def main(mode, series_path, folder, outdir, hourly=None, scorekit_dir=None):
    S = json.load(open(series_path)); mk = read_lists(folder); reqs, per, alltk = [], collections.Counter(), set()
    if mode == "clock":
        for f, items in families(S, mk, True):
            its = sorted(((t, (clock_start(t) or m["close"] - 90 * 60) - 70 * 60, m["close"]) for t, m in items), key=lambda x: (x[1], x[0]))
            pack(its, None, reqs, per, f["family"], 1, 1); alltk.update(t for t, _, _ in its)
        name, purpose = "INPLAYJUMP_C", "INPLAYJUMP stage 2: 1 minute candles, window S minus 70 minutes to the close"
    elif mode == "tennis_hourly":
        for f, items in families(S, mk, False):
            its = sorted(((t, m["open"] or m["close"] - 20 * 3600, m["close"]) for t, m in items), key=lambda x: (x[1], x[0]))
            pack(its, None, reqs, per, f["family"], 60, 60); alltk.update(t for t, _, _ in its)
        name, purpose = "INPLAYJUMP_TH", "INPLAYJUMP tennis pass 1: HOURLY candles from the market open to the close"
    elif mode == "tennis_plain":
        for f, items in families(S, mk, False):
            its = sorted(((t, m["open"] or m["close"] - 20 * 3600, m["close"]) for t, m in items), key=lambda x: (x[1], x[0]))
            pack(its, None, reqs, per, f["family"], 1, 1); alltk.update(t for t, _, _ in its)
        name, purpose = "INPLAYJUMP_TP", "INPLAYJUMP tennis: 1 minute candles from the market open to the close"
    elif mode == "tennis_minutes":
        sys.path.insert(0, scorekit_dir); import scorekit
        hc = scorekit.candles(hourly)
        for f, items in families(S, mk, False):
            ev = collections.defaultdict(list)
            for t, m in items: ev[m["event"]].append(t)
            its = []
            for e, tks in ev.items():
                hours = {t: [(c["ts"], c["bid_high"], c["bid_low"], c["bid"], c["ask_high"], c["ask_low"], c["ask"]) for c in hc.get(t, [])] for t in tks}
                st = skip_start(hours, tks)
                for t in tks:
                    if st is None: per[f["family"] + " all hours empty (no minute pull)"] += 0; continue
                    its.append((t, st, mk[t]["close"]))
            its.sort(key=lambda x: (x[1], x[0])); pack(its, None, reqs, per, f["family"], 1, 1); alltk.update(t for t, _, _ in its)
        name, purpose = "INPLAYJUMP_TM", "INPLAYJUMP tennis pass 2: 1 minute candles from 30 minutes before the first non-empty hour to the close"
    else: sys.exit(__doc__)
    n = write(reqs, outdir, name, purpose)
    print("mode %s | contracts %d | candle requests %d | jobs %d | per family %s" % (mode, len(alltk), len(reqs), n, dict(per)))
def selftest():
    q = lambda e, bh, bl, bc, ah, al, ac: (e, bh, bl, bc, ah, al, ac)
    flat = lambda e: q(e, .50, .49, .50, .52, .51, .52)          # ranges 0.01 + 0.01 = 0.02 plus the prior close inside the range: under 0.20
    E = [10 * 3600 + 3600 * k for k in range(6)]
    h = {"A": [flat(e) for e in E], "B": [flat(e) for e in E]}
    assert skip_start(h, ["A", "B"]) == E[0] - 3600 - 1800                                       # the first hour is never skipped: window starts 30 minutes before it
    # AS WRITTEN, the first hour after the open is never skipped (no prior close to test it against), and the minute window runs from the first non-skipped hour to the close,
    # so the window always starts 30 minutes before hour index 0 and the two-pass saves nothing. Flagged to Desk B and the Head; use the plain pull from the open (tennis_plain) unless they amend.
    for hh in (h, {"A": [flat(E[0]), flat(E[1]), q(E[2], .80, .50, .80, .82, .51, .82)], "B": [flat(e) for e in E[:3]]}, {"A": [q(E[0], .30, .29, .30, .32, .31, .32), q(E[1], .50, .49, .50, .52, .51, .52)], "B": [flat(E[0]), flat(E[1])]}):
        assert skip_start(hh, [t for t in hh]) == E[0] - 3600 - 1800
    # packing: one range per request
    reqs, per = [], collections.Counter(); pack([("T%d" % i, 1000 + 600 * i, 1000 + 600 * i + 7200) for i in range(30)], None, reqs, per, "F", 1, 1)
    assert all(len(r["params"]["market_tickers"].split(",")) <= 100 for r in reqs) and sum(len(r["params"]["market_tickers"].split(",")) for r in reqs) == 30
    for r in reqs:
        nt = len(r["params"]["market_tickers"].split(",")); assert (r["params"]["end_ts"] - r["params"]["start_ts"]) / 60 * nt <= 9000 + 1e-9
    print("BUILDER SELFTEST OK (skip rule incl. Amendment 3 boundary, packing limits)")
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["selftest"]: selftest()
    elif a[:1] in (["clock"], ["tennis_hourly"], ["tennis_plain"]) and len(a) == 4: main(*a)
    elif a[:1] == ["tennis_minutes"] and len(a) == 6: main(a[0], a[1], a[2], a[3], a[4], a[5])
    else: sys.exit(__doc__)
