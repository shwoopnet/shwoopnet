#!/usr/bin/env python3
"""INPLAYJUMP stage 2 (Amendments 2 and 3): candle job files from the INPLAYJUMP_LISTS answers. Offline: sends nothing. NO window is anchored on the close; nothing is shortened from the end.
  clock families (e-soccer, table tennis, e-basketball):  window = S forward to the close (table tennis S - 70 minutes, which also serves PREMOVE; S = the ticker's US Eastern start)
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
    if os.path.basename(os.path.normpath(folder)).startswith("HELDOUT_"): sys.exit("REFUSED: held-out folder (standing rule h)")
    man = json.load(open(os.path.join(folder, "manifest.json"))); mk = {}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row: continue
        b = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            c, o = iso_ts(m.get("close_time") or ""), iso_ts(m.get("open_time") or "")
            if m.get("ticker") and c: mk[m["ticker"]] = dict(series=m["ticker"].split("-")[0], event=m.get("event_ticker", ""), close=c, open=o)     # the result field is NOT read; no list is filtered on it
    return mk
def skip_start(hours, tickers):
    """Amendment 4 (Desk B, 6694911d): hourly candles from the open. For each contract and hour H: bid range over {bid high, bid low, bid open of H, bid close of H-1 if any}, ask range the same way. Hour H is SKIPPED only if, for EVERY contract of the match,
    bid range + ask range <= 0.03 AND every one of those values is present. (The open of an hour lies inside [low, high] by definition, so it adds nothing to a range; a missing high or low means a missing hour. The scorekit candle carries no open field, so an hour is 'present' when
    its high, low and close are present.) Returns the end_ts of the START of the minute window: 30 minutes before the first hour that may NOT be skipped (None if every hour may be skipped).
    hours: {ticker: [(end_ts, bid_high, bid_low, bid_close, ask_high, ask_low, ask_close)]} sorted."""
    ends = sorted({h[0] for hs in hours.values() for h in hs}); by = {tk: {h[0]: h for h in hs} for tk, hs in hours.items()}
    for i, e in enumerate(ends):
        ok = True
        for tk in tickers:
            h = by.get(tk, {}).get(e); p = by.get(tk, {}).get(ends[i - 1]) if i else None
            if h is None or None in (h[1], h[2], h[3], h[4], h[5], h[6]): ok = False; break
            bv = [h[1], h[2]] + ([p[3]] if p and p[3] is not None else []); av = [h[4], h[5]] + ([p[6]] if p and p[6] is not None else [])
            if (max(bv) - min(bv)) + (max(av) - min(av)) > 0.03 + 1e-9: ok = False; break
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
            lead = (70 if f["family"] == "TABLE_TENNIS" else 0) * 60                  # Desk B Amendment 3 of PREMOVE (Head 19:20Z): only table tennis widens, to S minus 70; e-soccer and e-basketball stay at S
            its = sorted(((t, (clock_start(t) or m["close"] - 90 * 60) - lead, m["close"]) for t, m in items), key=lambda x: (x[1], x[0]))
            pack(its, None, reqs, per, f["family"], 1, 1); alltk.update(t for t, _, _ in its)
        name, purpose = "INPLAYJUMP_C", "INPLAYJUMP stage 2: 1 minute candles, window S (table tennis S minus 70 minutes) to the close"
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
    flat = lambda e: q(e, .50, .49, .50, .52, .51, .52)          # ranges 0.01 + 0.01 = 0.02 <= 0.03
    E = [10 * 3600 + 3600 * k for k in range(6)]
    allflat = {"A": [flat(e) for e in E], "B": [flat(e) for e in E]}
    assert skip_start(allflat, ["A", "B"]) is None                                                 # every hour may be skipped
    # hour index 2 moves: hours 0 and 1 skipped, the minute window starts 30 minutes before hour index 2
    h2 = {"A": [flat(E[0]), flat(E[1]), q(E[2], .80, .50, .80, .82, .51, .82)] + [flat(e) for e in E[3:]], "B": [flat(e) for e in E]}
    assert skip_start(h2, ["A", "B"]) == E[2] - 3600 - 1800
    # the hour starts from a prior close far from its range (prior close 0.30, hour trades at 0.50): the prior close widens the range, NOT skipped
    h3 = {"A": [q(E[0], .30, .29, .30, .32, .31, .32), q(E[1], .50, .49, .50, .52, .51, .52)], "B": [flat(E[0]), flat(E[1])]}
    assert skip_start(h3, ["A", "B"]) == E[1] - 3600 - 1800
    # a missing value or hour is never skipped
    h4 = {"A": [flat(E[0]), q(E[1], .50, .49, None, .52, .51, .52)], "B": [flat(E[0]), flat(E[1])]}
    assert skip_start(h4, ["A", "B"]) == E[1] - 3600 - 1800
    h5 = {"A": [flat(E[0]), flat(E[1]), flat(E[2])], "B": [flat(E[0]), flat(E[2])]}
    assert skip_start(h5, ["A", "B"]) == E[1] - 3600 - 1800
    # range exactly 0.03 is skipped, 0.04 is not
    assert skip_start({"A": [q(E[0], .50, .48, .50, .52, .51, .52)]}, ["A"]) is None
    assert skip_start({"A": [q(E[0], .50, .47, .50, .52, .51, .52)]}, ["A"]) == E[0] - 3600 - 1800
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
