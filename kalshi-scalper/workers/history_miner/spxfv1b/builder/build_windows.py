"""SPXFV1 rows builder, Kalshi half (History Miner, Nov 13, 2026). Writes spxfv1b.py's windows CSV from one SPXOI1_LISTS run and one SPXOI1_CANDLES run
(PR 907 job files). Written from the job file text and EXPECTED_BY_HAND.md, committed first. Development dates only: a list market closing at or after
2026-12-01T00:00:00Z stops the build. Prints counts only; writes nothing but the CSV it is given.
Usage: python3 -I build_windows.py <lists run folder> <candles run folder> <out.csv>"""
import csv, gzip, hashlib, json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import hm_guard  # noqa: E402

HELDOUT_FIRST = 1796083200          # 2026-12-01T00:00:00Z
DECISION_LAG = 120                  # the decision candle ends at close - 120 s


class Stop(Exception):
    pass


def iso(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def load_run(folder):
    """{request id: [page bodies in order]}; the run must be complete and every job request answered on pages 1..k at 200 with no cursor left."""
    m = json.load(open(os.path.join(folder, "manifest.json")))
    if m.get("status") != "complete":
        raise Stop("run not complete: %s" % folder)
    root = os.path.realpath(folder)
    by = {}
    for r in m.get("rows", []):
        if r.get("truncated"):
            raise Stop("truncated row %s" % r.get("id"))
        if not r.get("file"):
            raise Stop("row %s has no file" % r.get("id"))
        p = os.path.realpath(os.path.join(folder, r["file"]))
        if os.path.commonpath([root, p]) != root:
            raise Stop("file outside run: %s" % r["file"])
        hm_guard.refuse_all([p])
        raw = gzip.open(p, "rb").read()
        if r.get("sha256") and hashlib.sha256(raw).hexdigest() != r["sha256"]:
            raise Stop("sha256 mismatch %s" % r["file"])
        if r.get("bytes") is not None and len(raw) != r["bytes"]:
            raise Stop("bytes mismatch %s" % r["file"])
        by.setdefault(r["id"], []).append((r, json.loads(raw)))
    out = {}
    for q in m["job"]["requests"]:
        rows = sorted(by.get(q["id"], []), key=lambda x: x[0].get("page", 1))
        if not rows or [x[0].get("page", 1) for x in rows] != list(range(1, len(rows) + 1)):
            raise Stop("request %s not answered on pages 1..k" % q["id"])
        if any(x[0].get("status") != 200 for x in rows):
            raise Stop("request %s has a non-200 page" % q["id"])
        if rows[-1][1].get("cursor"):
            raise Stop("request %s left a cursor" % q["id"])
        out[q["id"]] = [x[1] for x in rows]
    return out


def side(c, k, missing):
    o = c.get(k)
    if isinstance(o, dict) and o.get("close_dollars") not in (None, ""):
        return float(o["close_dollars"])
    return missing


def build(lists_dir, candles_dir, out_path):
    hm_guard.refuse_all([lists_dir, candles_dir, out_path])
    markets = {}
    for pages in load_run(lists_dir).values():
        for pg in pages:
            for mk in pg.get("markets") or []:
                t = mk["ticker"]
                if not t.startswith("KXINX15M-"):
                    continue
                close = iso(mk["close_time"])
                if close >= HELDOUT_FIRST:
                    raise Stop("held-out market in a development build: %s" % t)
                markets[t] = {"ticker": t, "event_ticker": mk["event_ticker"], "close_ts": close, "result": mk.get("result") or ""}
    candles = {}
    for pages in load_run(candles_dir).values():
        for pg in pages:
            for mk in pg.get("markets") or []:
                for c in mk.get("candlesticks") or []:
                    candles[(mk["market_ticker"], int(c["end_period_ts"]))] = c
    counts = {"rows": 0, "quoted": 0, "missing_side": 0, "no_candle": 0}
    rows = []
    for m in sorted(markets.values(), key=lambda m: (m["close_ts"], m["ticker"])):
        c = candles.get((m["ticker"], m["close_ts"] - DECISION_LAG))
        if c is None:
            b, a = 0.0, 1.0
            counts["no_candle"] += 1
        else:
            b, a = side(c, "yes_bid", None), side(c, "yes_ask", None)
            if b is None or a is None:
                counts["missing_side"] += 1
            else:
                counts["quoted"] += 1
            b = 0.0 if b is None else b
            a = 1.0 if a is None else a
        counts["rows"] += 1
        rows.append([m["ticker"], m["event_ticker"], m["close_ts"], repr(b), repr(a), m["result"]])
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ticker", "event_ticker", "close_ts", "yes_bid", "yes_ask", "result"])
        w.writerows(rows)
    return counts


if __name__ == "__main__":
    try:
        print(json.dumps(build(*sys.argv[1:4])), file=sys.stderr)
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
