#!/usr/bin/env python3
"""INPLAYJUMP stage 2 (Amendments 2 and 3): candle job files from the INPLAYJUMP_LISTS answers. Offline: sends nothing. NO window is anchored on the close; nothing is shortened from the end.
  clock families (e-soccer, table tennis, e-basketball):  window = S - 5 minutes forward to the close (S = the ticker's US Eastern start; PREMOVE withdrawn, Amendment 5)
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
    import heldout_guard_v2 as heldout_guard; heldout_guard.refuse_heldout(folder, "read_lists")
    man = json.load(open(os.path.join(folder, "manifest.json"))); mk = {}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row: continue
        b = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            c, o = iso_ts(m.get("close_time") or ""), iso_ts(m.get("open_time") or "")
            if m.get("ticker") and c: mk[m["ticker"]] = dict(series=m["ticker"].split("-")[0], event=m.get("event_ticker", ""), close=c, open=o)     # the result field is NOT read; no list is filtered on it
    return mk
def skip_start(hours, tickers, open_ts, close_ts):
    """Amendment 5 (Desk B, 774889fd; Amendment 3 and 4 wording withdrawn). Hourly candles from the open. For each contract and hour H: bid range = max(bid high, bid open, last present bid close before H) minus min(bid low, bid open, last present bid close before H);
    ask range the same. Skip H iff, for EVERY contract, bid range + ask range < 0.04 - 3e-9 (Amendment 6). An hour with NO hourly candle for a contract is dead for that contract (contributes nothing); an hour with no candle for any contract is a dead hour and is skipped.
    The first hour uses its own open and can be skipped like any other. (An hour's open lies inside [low, high], so it adds nothing to a range; scorekit candles carry no open field.) A present candle with a missing high, low or close price is NOT skipped.
    hours: {ticker: [(end_ts, bid_high, bid_low, bid_close, ask_high, ask_low, ask_close)]} hourly candles (end_ts the hour's END). Returns the START ts of the minute window: 30 minutes before the first hour that is not skipped (None if every hour is skipped)."""
    by = {tk: {h[0]: h for h in hours.get(tk, [])} for tk in tickers}
    first_end = (open_ts // 3600 + 1) * 3600; last_end = -(-close_ts // 3600) * 3600
    lastc = {tk: (None, None) for tk in tickers}
    for e in range(first_end, last_end + 1, 3600):
        skip = True
        for tk in tickers:
            h = by[tk].get(e)
            if h is None: continue                                                   # dead for this contract
            if None in (h[1], h[2], h[3], h[4], h[5], h[6]): skip = False; break
            bv = [h[1], h[2]] + ([lastc[tk][0]] if lastc[tk][0] is not None else []); av = [h[4], h[5]] + ([lastc[tk][1]] if lastc[tk][1] is not None else [])
            if (max(bv) - min(bv)) + (max(av) - min(av)) >= 0.04 - 3e-9: skip = False; break
        for tk in tickers:
            h = by[tk].get(e)
            if h is not None and h[3] is not None and h[6] is not None: lastc[tk] = (h[3], h[6])
        if not skip: return e - 3600 - 1800
    return None
def screen_checks(hours, minutes):
    """Amendment 5, point 3, per tennis family from pulled data: (a) minute candles that fall in an hour with no hourly candle; (b) minute closes whose bid or ask lies outside that hour's own low to high.
    hours: {ticker: {end_ts: (bid_high, bid_low, ask_high, ask_low)}}; minutes: {ticker: [(end_ts, bid_close, ask_close)]}. Either count above zero: that family's screen is void (pull it in full from the open, or drop it under the ceiling)."""
    a = b = 0
    for tk, ms in minutes.items():
        for (e, bc, ac) in ms:
            he = (e + 3599) // 3600 * 3600; h = hours.get(tk, {}).get(he)
            if h is None: a += 1; continue
            if (bc is not None and not (h[1] - 1e-9 <= bc <= h[0] + 1e-9)) or (ac is not None and not (h[3] - 1e-9 <= ac <= h[2] + 1e-9)): b += 1
    return a, b
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
    import heldout_guard_v2 as heldout_guard; heldout_guard.refuse_heldout(folder, "candles builder")
    if hourly: heldout_guard.refuse_heldout(hourly, "candles builder hourly")
    S = json.load(open(series_path)); mk = read_lists(folder); reqs, per, alltk = [], collections.Counter(), set()
    if mode == "clock":
        for f, items in families(S, mk, True):
            lead = 5 * 60                                                             # PREMOVE withdrawn (Desk B, Amendment 5): windows start at S; 5 minutes before S are kept so the minutes t-1 of the first in-play minute and the placebo's e-5 exist
            its = sorted(((t, (clock_start(t) or m["close"] - 90 * 60) - lead, m["close"]) for t, m in items), key=lambda x: (x[1], x[0]))
            pack(its, None, reqs, per, f["family"], 1, 1); alltk.update(t for t, _, _ in its)
        name, purpose = "INPLAYJUMP_C", "INPLAYJUMP stage 2: 1 minute candles, window S minus 5 minutes to the close"
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
                st = skip_start(hours, tks, min((mk[t]["open"] or mk[t]["close"] - 20 * 3600) for t in tks), max(mk[t]["close"] for t in tks))
                for t in tks:
                    if st is None: per[f["family"] + " all hours empty (no minute pull)"] += 0; continue
                    its.append((t, st, mk[t]["close"]))
            its.sort(key=lambda x: (x[1], x[0])); pack(its, None, reqs, per, f["family"], 1, 1); alltk.update(t for t, _, _ in its)
        name, purpose = "INPLAYJUMP_TM", "INPLAYJUMP tennis pass 2: 1 minute candles from 30 minutes before the first non-empty hour to the close"
    else: sys.exit(__doc__)
    n = write(reqs, outdir, name, purpose)
    print("mode %s | contracts %d | candle requests %d | jobs %d | per family %s" % (mode, len(alltk), len(reqs), n, dict(per)))
def selftest():
    H = 3600; O = 10 * H + 600; C = 15 * H + 1200                      # open 10:10, close 15:20: hourly ends from 11:00 to 16:00
    q = lambda e, bh, bl, bc, ah, al, ac: (e, bh, bl, bc, ah, al, ac)
    flat = lambda e: q(e, .50, .49, .50, .52, .51, .52)          # ranges 0.01 + 0.01 = 0.02 < 0.04
    E = [11 * H + k * H for k in range(6)]
    allflat = {"A": [flat(e) for e in E], "B": [flat(e) for e in E]}
    assert skip_start(allflat, ["A", "B"], O, C) is None                                           # every hour skipped
    h2 = {"A": [flat(E[0]), flat(E[1]), q(E[2], .80, .50, .80, .82, .51, .82)] + [flat(e) for e in E[3:]], "B": [flat(e) for e in E]}
    assert skip_start(h2, ["A", "B"], O, C) == E[2] - H - 1800                                      # the first hour can be skipped: window starts 30 minutes before hour index 2
    # an hour that starts from a prior close far from its range is NOT skipped (prior close 0.30, hour 0.49 to 0.50)
    h3 = {"A": [q(E[0], .30, .29, .30, .32, .31, .32), q(E[1], .50, .49, .50, .52, .51, .52)], "B": [flat(E[0]), flat(E[1])]}
    assert skip_start(h3, ["A", "B"], O, E[1]) == E[1] - H - 1800
    # a present candle with a missing price is never skipped
    h4 = {"A": [flat(E[0]), q(E[1], .50, .49, None, .52, .51, .52)], "B": [flat(E[0]), flat(E[1])]}
    assert skip_start(h4, ["A", "B"], O, E[1]) == E[1] - H - 1800
    # a dead hour (no candle for any contract) is skipped; a contract missing a candle contributes nothing
    h5 = {"A": [flat(E[0]), flat(E[2])], "B": [flat(E[0]), flat(E[2])]}
    assert skip_start(h5, ["A", "B"], O, E[2]) is None
    h6 = {"A": [flat(E[0]), q(E[1], .80, .50, .80, .82, .51, .82)], "B": [flat(E[0])]}
    assert skip_start(h6, ["A", "B"], O, E[1]) == E[1] - H - 1800
    # sum exactly 0.04 is NOT skipped, 0.03 is
    assert skip_start({"A": [q(E[0], .50, .48, .50, .52, .50, .52)]}, ["A"], O, E[0]) == E[0] - H - 1800
    assert skip_start({"A": [q(E[0], .50, .48, .50, .51, .50, .51)]}, ["A"], O, E[0]) is None
    # self-checks: a minute outside its hour's range, and a minute in an hour with no hourly candle
    hrs = {"A": {E[0]: (.50, .49, .52, .51)}}
    assert screen_checks(hrs, {"A": [(E[0] - 600, .49, .51)]}) == (0, 0)
    assert screen_checks(hrs, {"A": [(E[0] - 600, .60, .51)]}) == (0, 1)
    assert screen_checks(hrs, {"A": [(E[0] + 600, .49, .51)]}) == (1, 0)
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
