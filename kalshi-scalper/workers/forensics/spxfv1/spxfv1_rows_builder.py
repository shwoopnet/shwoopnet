#!/usr/bin/env python3
"""SPXFV1 build 2: the ROWS BUILDER (Forensics desk, Nov 13, 2026; the Head of R&D's order of 16:57Z; research only; no Kalshi request, no network in this file).
It turns landed pull-run folders and a private Databento file into the two CSVs the History Miner's `spxfv1b.py` (9032013a, at 3ecd0925) reads. The input spec was read from that code, not from the Testing Desk's build.

  windows CSV  (columns: ticker, event_ticker, close_ts, yes_bid, yes_ask, result)
      one row per KXINX15M market in the settled list answers. close_ts = the market's close_time as epoch seconds (UTC). yes_bid and yes_ask = the close of the YES bid and ask of the 1 minute candle
      whose end_period_ts is exactly close_ts - 120 (the decision candle). A market with no such candle, or a candle with no bid or no ask on a side, gets 0.0 for a missing bid and 1.0 for a missing ask:
      build 2 reads 0 < bid < ask < 1 as the only quote, so these become its "no_quote" (counted here as well, by reason, in the builder's own counts). result: yes and no as listed; any other settled result
      (for example scalar) is "void"; a market with no result at all is written "empty", which makes build 2 stop (its rule S6) rather than guess.
      A market closing on or after 2026-12-01T00:00:00Z STOPS the builder: that is the held-out block, and this builder reads no field of it.
  futures CSV  (columns: ts_event_s, symbol, instrument_id, close)
      from a Databento ohlcv-1m CSV pulled with ES.c.0 (continuous). ts_event_s = ts_event / 1e9 (a Databento bar's ts_event is the bar START), symbol = "ES.c.0" (the continuous symbol that was asked for; the resolved
      contract is in instrument_id, which changes at a roll), close as a decimal. Any row whose symbol column is not a futures contract of the ES family, any non 1 minute spacing is NOT checked here (build 2 does that).
  canonical extract hash  sha256 over the sorted lines "<ts_event_s>,<instrument_id>,<close with two decimals>\\n" (ES ticks are 0.25, so two decimals are exact), sorted by (ts_event_s, instrument_id):
      printed by `futures`; the Testing Desk prints the same for its file so both builds can be shown to see identical bars.
Guards: every input folder passes the HELDOUT_ name check and listed_runs_guard (HELDOUT_PULL_RUNS.md); the futures input and output must lie OUTSIDE the git working tree (Databento data is never committed).
usage: python3 -I spxfv1_rows_builder.py windows --lists <run...> --candles <run...> --out <windows.csv>
       python3 -I spxfv1_rows_builder.py futures --databento <ohlcv-1m csv from the pull> --out <futures.csv>"""
import sys, os, csv, json, gzip, hashlib, calendar, time, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from listed_runs_guard import refuse_listed

SERIES = "KXINX15M"
HELD_FIRST = calendar.timegm(time.strptime("2026-12-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ"))
DECISION_BACK = 120
REPO = os.path.realpath(os.path.join(HERE, "..", "..", "..", ".."))


class Stop(Exception):
    pass


def _ts(s):
    try: return calendar.timegm(time.strptime(str(s)[:19] + "Z", "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None


def refuse_folder(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)): raise Stop("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % path)
    try: refuse_listed(path)
    except SystemExit as e: raise Stop(str(e))


def refuse_in_repo(path):
    r = os.path.realpath(path)
    if r == REPO or r.startswith(REPO + os.sep): raise Stop("REFUSED: %s is inside the git working tree; Databento data is never committed (scratch only)" % path)


def answers(folder):
    refuse_folder(folder)
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") == 200 and row.get("file") and not row.get("truncated"):
            yield json.load(gzip.open(os.path.join(folder, row["file"])))


def px(side):
    """The close of a candle price object, in dollars; None if absent. close_dollars first; a bare `close` above 1.0 is cents."""
    if not isinstance(side, dict): return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""): continue
        try: v = float(v)
        except (TypeError, ValueError): continue
        return v / 100.0 if (k == "close" and v > 1.0) else v
    return None


def read_markets(list_folders):
    out = {}
    for f in list_folders:
        for body in answers(f):
            for m in (body.get("markets", []) if isinstance(body, dict) else []):
                if not isinstance(m, dict) or not m.get("ticker"): continue
                t = str(m["ticker"])
                if t.split("-")[0] != SERIES: continue
                c = _ts(m.get("close_time"))
                if c is None: raise Stop("market %s has no readable close_time" % t)
                if c >= HELD_FIRST: raise Stop("REFUSED: market %s closes on or after 2026-12-01T00:00:00Z (the held-out block); this builder reads no field of it" % t)
                out[t] = {"event": m.get("event_ticker") or t, "close": c, "result": (m.get("result") or "").lower()}
    return out


def read_decision_quotes(candle_folders, markets):
    q = {}
    for f in candle_folders:
        for body in answers(f):
            nodes = body.get("markets") if isinstance(body, dict) and isinstance(body.get("markets"), list) else [body]
            for n in nodes:
                if not isinstance(n, dict) or not isinstance(n.get("candlesticks"), list): continue
                t = n.get("market_ticker") or n.get("ticker")
                if t not in markets: continue
                want = markets[t]["close"] - DECISION_BACK
                for c in n["candlesticks"]:
                    try: end = int(c["end_period_ts"])
                    except (KeyError, TypeError, ValueError): continue
                    if end == want: q[t] = (px(c.get("yes_bid")), px(c.get("yes_ask")))
    return q


def build_windows(lists, candles, out_csv):
    mk = read_markets(lists); q = read_decision_quotes(candles, mk); cnt = collections.Counter(); rows = []
    for t in sorted(mk, key=lambda t: (mk[t]["close"], t)):
        m = mk[t]; got = q.get(t)
        if got is None: bid, ask, why = 0.0, 1.0, "no_decision_candle"
        else:
            bid, ask = got; why = None
            if bid is None: bid = 0.0; why = "no_bid"
            if ask is None: ask = 1.0; why = (why + "+no_ask") if why else "no_ask"
        if why: cnt[why] += 1
        r = m["result"]; res = r if r in ("yes", "no") else ("void" if r else "empty")
        if res == "void": cnt["void"] += 1
        if res == "empty": cnt["empty_result"] += 1
        rows.append([t, m["event"], m["close"], repr(float(bid)), repr(float(ask)), res])
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ticker", "event_ticker", "close_ts", "yes_bid", "yes_ask", "result"]); w.writerows(rows)
    return {"markets": len(mk), "rows": len(rows), "counts": dict(cnt)}


def canonical_lines(rows):
    return "".join("%d,%d,%.2f\n" % (ts, iid, c) for ts, iid, c in sorted((ts, iid, c) for ts, iid, c in rows))


def build_futures(databento_csv, out_csv):
    refuse_in_repo(databento_csv); refuse_in_repo(out_csv)
    rows, bad = [], 0
    with open(databento_csv, newline="") as f:
        for r in csv.DictReader(f):
            try: ts = int(r["ts_event"]) // 1_000_000_000; iid = int(r["instrument_id"]); c = float(r["close"])
            except (KeyError, TypeError, ValueError): bad += 1; continue
            if not str(r.get("symbol", "")).startswith("ES"): raise Stop("futures row with symbol %r refused: the ES family only" % r.get("symbol"))
            rows.append((ts, iid, c))
    if len({ts for ts, _, _ in rows}) != len(rows): raise Stop("two bars with the same ts_event: the pull must be one continuous symbol, one schema")
    rows.sort()
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ts_event_s", "symbol", "instrument_id", "close"]); [w.writerow([ts, "ES.c.0", iid, "%.10f" % c]) for ts, iid, c in rows]
    return {"bars": len(rows), "unreadable_rows": bad, "canonical_extract_sha256": hashlib.sha256(canonical_lines(rows).encode()).hexdigest()}


def main(argv):
    if not argv or argv[0] not in ("windows", "futures"): print(__doc__); return 2
    a = collections.defaultdict(list); key = None
    for x in argv[1:]:
        if x.startswith("--"): key = x[2:]; a[key]
        elif key: a[key].append(x)
    try:
        if argv[0] == "windows":
            if not a["lists"] or not a["candles"] or not a["out"]: raise Stop("needs --lists, --candles and --out")
            if os.path.exists(a["out"][0]): raise Stop("%s exists" % a["out"][0])
            print(json.dumps(build_windows(a["lists"], a["candles"], a["out"][0]), indent=1))
        else:
            if not a["databento"] or not a["out"]: raise Stop("needs --databento and --out")
            if os.path.exists(a["out"][0]): raise Stop("%s exists" % a["out"][0])
            print(json.dumps(build_futures(a["databento"][0], a["out"][0]), indent=1))
    except Stop as e:
        print(str(e)); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
