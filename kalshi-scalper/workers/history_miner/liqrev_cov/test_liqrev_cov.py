"""Made-up data of EXPECTED_BY_HAND.md; prints MISMATCHES [] when liqrev_cov.py agrees with the hand file."""
import csv, gzip, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liqrev_cov as L

T0 = 1795132800
OKXC = ["t_start_ms", "t_end_ms", "uly", "requests", "pages", "rows_read", "rows_new", "rows_dup", "oldest_ts_ms", "newest_ts_ms", "stop_reason", "n429", "n5xx",
        "n_other_fail", "seen_keys", "note"]
R6C = ["close_time", "series", "ticker", "polls", "ok_polls", "n429", "batch_fallback", "max_gap_ms", "first_recv_ms", "last_recv_ms", "book_rows",
       "tape_pages", "tape_trades", "dupes_dropped", "tape_sum_count", "volume_fp", "result", "note"]


def iso(e):
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(e))


def write(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def okx(path, extra=None):
    rs = [("BTC-USDT", -3600, 3600), ("BTC-USDT", 3000, 7200), ("BTC-USDT", 9000, 12000), ("BTC-USDT", None, 12500), ("BTC-USD", -3600, 12000)] + (extra or [])
    write(path, OKXC, [{"t_start_ms": (T0 + ts) * 1000, "uly": u, "oldest_ts_ms": "" if o is None else (T0 + o) * 1000, "stop_reason": "x"} for u, o, ts in rs])


def r6(path):
    rs = [("KXBTC15M", "KXBTC15M-W1", T0 + 1800), ("KXBTC15M", "KXBTC15M-W2", T0 + 3840), ("KXBTC15M", "KXBTC15M-W3", T0 + 8100), ("KXBTC15M", "KXBTC15M-W8", T0 + 8700),
          ("KXBTC15M", "KXBTC15M-W4", T0 + 12000), ("KXETH15M", "KXETH15M-W5", T0 + 1800), ("KXBTC15M", "KXBTC15M-W1", T0 + 1800),
          ("KXBTC15M", "KXBTC15M-W7", L.iso("2026-11-30T00:15:00Z"))]
    write(path, R6C, [{"close_time": iso(c), "series": s, "ticker": t, "result": "SHOULD_NOT_BE_READ"} for s, t, c in rs])


bad = []
d = tempfile.mkdtemp()
op = os.path.join(d, "oklq", "2026-11-20", "0007", "coverage.csv.gz"); okx(op)
rp = os.path.join(d, "book15r6", "2026-11-20", "0000", "coverage.csv.gz"); r6(rp)
out = os.path.join(d, "out.csv")
NOW = L.iso("2026-11-30T01:00:00Z")
counts = L.build("dev", out, [op], [rp], now=NOW)
exp = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "EXPECTED_BY_HAND.md")).read().split("```\n")[1].split("```")[0]
txt = open(out).read()
if txt != exp:
    bad.append(("csv", txt))
if "SHOULD_NOT_BE_READ" in txt:
    bad.append(("result text leaked",))
if counts != {"windows": 5, "covered": 3, "no_liq_coverage": 2, "outside_block": 1, "other_series": 1, "duplicate": 1, "okx_rows": 5, "okx_no_interval": 1}:
    bad.append(("counts", counts))


def refused(fn, what, why):
    try:
        fn()
    except (L.Stop, SystemExit) as e:
        print("refused", what, "->", str(e)[:90])
        if why not in str(e):
            bad.append(("wrong reason", what, str(e)[:90]))
        return
    bad.append(("not refused", what))


refused(lambda: L.build("dev", out, [op], [rp], now=L.iso("2026-11-29T23:00:00Z")), "dev before Nov 30", "refused before")
refused(lambda: L.build("held", out, [op], [rp], now=L.iso("2027-01-01T12:00:00Z")), "held before Jan 2", "refused before")
late = os.path.join(d, "book15r6", "2026-11-30", "0000", "coverage.csv.gz"); r6(late)
refused(lambda: L.build("dev", out, [op], [late], now=NOW), "R6 folder 2026-11-30 in dev", "outside the dev block")
liq = os.path.join(d, "oklq", "2026-11-20", "0007", "liquidations.csv.gz"); write(liq, OKXC, [])
refused(lambda: L.build("dev", out, [liq], [rp], now=NOW), "a liquidations file", "not a coverage file")
odd = os.path.join(d, "oklq", "2026-11-21", "0007", "coverage.csv.gz"); okx(odd, [("ETH-USDT", 0, 100)])
refused(lambda: L.build("dev", out, [odd], [rp], now=NOW), "uly ETH-USDT", "uly")
hd = os.path.join(d, "HELDOUT_x"); os.makedirs(hd)
refused(lambda: L.build("dev", os.path.join(hd, "o.csv"), [op], [rp], now=NOW), "HELDOUT_ path", "HELDOUT")
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
